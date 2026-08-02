"""Demonstração reproduzível de concorrência com sessões SQLAlchemy."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from queue import Queue
from threading import Event, Thread

from sqlalchemy import cast, delete, func, literal, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from projeto_hospital.orm import Escala


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ResultadoConcorrencia:
    segunda_aguardou_lock: bool
    confirmadas: int
    rejeitadas: int
    escalas_no_destino: int
    logs: tuple[str, ...]


def _reajustar(
    session: Session,
    origem: date,
    destino: date,
) -> int:
    return session.scalar(
        select(
            func.sp_reajustar_escala(
                1,
                origem,
                cast(literal("manha"), Escala.turno.type),
                destino,
                cast(literal("tarde"), Escala.turno.type),
            )
        )
    )


def demonstrar_concorrencia_escala(
    factory: sessionmaker[Session],
) -> ResultadoConcorrencia:
    """Executa duas transações, prova a espera e verifica o estado final."""

    origem_1 = date(2031, 6, 1)
    origem_2 = date(2031, 6, 2)
    destino = date(2031, 6, 3)
    datas = (origem_1, origem_2, destino)

    with factory.begin() as setup:
        setup.execute(
            delete(Escala).where(
                Escala.id_atuacao_residente == 1,
                Escala.data_plantao.in_(datas),
            )
        )
        primeira = Escala(
            id_unidade=1,
            data_plantao=origem_1,
            turno="manha",
            id_atuacao_residente=1,
            id_atuacao_preceptor=6,
        )
        segunda = Escala(
            id_unidade=2,
            data_plantao=origem_2,
            turno="manha",
            id_atuacao_residente=1,
            id_atuacao_preceptor=6,
        )
        setup.add_all((primeira, segunda))

    primeira_atualizou = Event()
    liberar_commit = Event()
    segunda_iniciou = Event()
    segunda_terminou = Event()
    resultados: Queue[tuple[str, str]] = Queue()
    mensagens: Queue[str] = Queue()

    def registrar(mensagem: str) -> None:
        LOGGER.info(mensagem)
        mensagens.put(mensagem)

    def transacao_1() -> None:
        try:
            with factory() as session:
                _reajustar(session, origem_1, destino)
                registrar("T1 atualizou e manteve o lock pessimista")
                primeira_atualizou.set()
                if not liberar_commit.wait(10):
                    raise TimeoutError("T1 não recebeu autorização para commit")
                session.commit()
                registrar("T1 confirmou")
                resultados.put(("T1", "confirmada"))
        except Exception as error:  # pragma: no cover - proteção do worker
            primeira_atualizou.set()
            resultados.put(("T1", f"erro:{type(error).__name__}"))

    def transacao_2() -> None:
        if not primeira_atualizou.wait(10):
            resultados.put(("T2", "erro:TimeoutT1"))
            segunda_terminou.set()
            return
        try:
            with factory() as session:
                segunda_iniciou.set()
                registrar("T2 iniciou o reajuste conflitante")
                _reajustar(session, origem_2, destino)
                session.commit()
                resultados.put(("T2", "confirmada"))
        except DBAPIError as error:
            sqlstate = getattr(error.orig, "sqlstate", None)
            registrar(f"T2 rejeitada com SQLSTATE {sqlstate}")
            resultados.put(("T2", "rejeitada"))
        finally:
            segunda_terminou.set()

    thread_1 = Thread(target=transacao_1, name="etapa2-t1", daemon=True)
    thread_2 = Thread(target=transacao_2, name="etapa2-t2", daemon=True)
    thread_1.start()
    thread_2.start()

    if not primeira_atualizou.wait(10) or not segunda_iniciou.wait(10):
        liberar_commit.set()
        raise TimeoutError("As transações não chegaram ao ponto de contenção")

    segunda_aguardou = not segunda_terminou.wait(0.25)
    if segunda_aguardou:
        registrar("T2 aguardou o lock de T1")
    liberar_commit.set()
    thread_1.join(15)
    thread_2.join(15)
    if thread_1.is_alive() or thread_2.is_alive():
        raise TimeoutError("A demonstração concorrente excedeu o limite")

    estados = dict(resultados.get(timeout=2) for _ in range(2))
    with factory() as verificacao:
        quantidade_destino = verificacao.scalar(
            select(func.count(Escala.id)).where(
                Escala.id_atuacao_residente == 1,
                Escala.data_plantao == destino,
                Escala.turno == "tarde",
            )
        )
    with factory.begin() as limpeza:
        limpeza.execute(
            delete(Escala).where(
                Escala.id_atuacao_residente == 1,
                Escala.data_plantao.in_(datas),
            )
        )

    logs = tuple(mensagens.get_nowait() for _ in range(mensagens.qsize()))
    return ResultadoConcorrencia(
        segunda_aguardou_lock=segunda_aguardou,
        confirmadas=sum(estado == "confirmada" for estado in estados.values()),
        rejeitadas=sum(estado == "rejeitada" for estado in estados.values()),
        escalas_no_destino=quantidade_destino or 0,
        logs=logs,
    )
