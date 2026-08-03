"""simulacao deterministica de duas transacoes concorrentes de escala"""

import logging
from datetime import date
from queue import Queue
from threading import Event, Thread
from time import monotonic

import psycopg
import pytest

from projeto_hospital.config import DatabaseConfig


LOGGER = logging.getLogger(__name__)


def executar_reajuste(
    conn: psycopg.Connection,
    *,
    data_origem: date,
    data_destino: date,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sp_reajustar_escala(
                1, %s, 'manha', %s, 'tarde'
            )
            """,
            (data_origem, data_destino),
        )
        row = cur.fetchone()

    assert row is not None
    return row[0]


def aguardar_bloqueio_no_postgresql(
    observer: psycopg.Connection,
    *,
    pid_bloqueado: int,
    pid_bloqueador: int,
    transacao_finalizada: Event,
    timeout: float = 5.0,
) -> None:
    limite = monotonic() + timeout
    intervalo_de_consulta = Event()

    while monotonic() < limite:
        with observer.cursor() as cur:
            cur.execute(
                """
                SELECT wait_event_type, pg_blocking_pids(%s)
                FROM pg_stat_activity
                WHERE pid = %s
                """,
                (pid_bloqueado, pid_bloqueado),
            )
            row = cur.fetchone()

        if row is not None:
            wait_event_type, bloqueadores = row
            if wait_event_type == "Lock" and pid_bloqueador in bloqueadores:
                return

        if transacao_finalizada.is_set():
            raise AssertionError(
                "A segunda transacao terminou sem aguardar o lock pessimista."
            )

        # a espera curta limita a frequencia da consulta
        intervalo_de_consulta.wait(0.01)

    raise AssertionError(
        "O PostgreSQL nao registrou a segunda transacao aguardando o lock."
    )


def test_duas_transacoes_confirmam_exatamente_uma_escala_conflitante(
    _prepared_database: DatabaseConfig,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=__name__)
    kwargs = _prepared_database.connection_kwargs
    origem_primeira = date(2030, 6, 1)
    origem_segunda = date(2030, 6, 2)
    destino = date(2030, 6, 3)

    # Duas origens válidas na mesma unidade disputam exatamente a mesma
    # combinação de unidade, data, turno e residente no destino.
    with psycopg.connect(**kwargs) as setup:
        with setup.cursor() as cur:
            cur.execute(
                """
                DELETE FROM escala
                WHERE id_atuacao_residente = 1
                  AND data_plantao IN (%s, %s, %s)
                """,
                (origem_primeira, origem_segunda, destino),
            )
            cur.execute(
                """
                INSERT INTO escala (
                    id_unidade, data_plantao, turno,
                    id_atuacao_residente, id_atuacao_preceptor
                ) VALUES
                    (1, %s, 'manha', 1, 6),
                    (1, %s, 'manha', 1, 6)
                RETURNING id
                """,
                (origem_primeira, origem_segunda),
            )
            id_primeira, id_segunda = (row[0] for row in cur.fetchall())

    primeira_atualizou = Event()
    liberar_primeiro_commit = Event()
    segunda_iniciou_chamada = Event()
    segunda_finalizou = Event()
    pids: Queue[tuple[str, int]] = Queue()
    resultados: Queue[tuple[str, str, int | None, str | None]] = Queue()

    def transacao_1() -> None:
        try:
            with psycopg.connect(**kwargs) as conn:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL lock_timeout = '8s'")
                    cur.execute("SET LOCAL statement_timeout = '12s'")
                pids.put(("t1", conn.info.backend_pid))

                quantidade = executar_reajuste(
                    conn,
                    data_origem=origem_primeira,
                    data_destino=destino,
                )
                LOGGER.info("transacao 1 atualizou a escala e manteve o lock")
                primeira_atualizou.set()

                if not liberar_primeiro_commit.wait(10):
                    raise TimeoutError(
                        "Timeout aguardando a liberacao do primeiro commit."
                    )

            LOGGER.info("transacao 1 confirmou a escala")
            resultados.put(("t1", "confirmada", quantidade, None))
        except Exception as error:
            primeira_atualizou.set()
            resultados.put(
                (
                    "t1",
                    "erro",
                    None,
                    getattr(error, "sqlstate", None) or type(error).__name__,
                )
            )

    def transacao_2() -> None:
        if not primeira_atualizou.wait(10):
            resultados.put(("t2", "erro", None, "TimeoutPrimeiraTransacao"))
            segunda_finalizou.set()
            return

        try:
            with psycopg.connect(**kwargs) as conn:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL lock_timeout = '8s'")
                    cur.execute("SET LOCAL statement_timeout = '12s'")
                pids.put(("t2", conn.info.backend_pid))
                segunda_iniciou_chamada.set()
                LOGGER.info("transacao 2 iniciou o reajuste conflitante")

                quantidade = executar_reajuste(
                    conn,
                    data_origem=origem_segunda,
                    data_destino=destino,
                )

            LOGGER.info("transacao 2 confirmou a escala")
            resultados.put(("t2", "confirmada", quantidade, None))
        except psycopg.Error as error:
            LOGGER.info("transacao 2 foi rejeitada: SQLSTATE %s", error.sqlstate)
            resultados.put(("t2", "rejeitada", None, error.sqlstate))
        except Exception as error:
            resultados.put(("t2", "erro", None, type(error).__name__))
        finally:
            segunda_finalizou.set()

    primeira = Thread(target=transacao_1, name="transacao-escala-1", daemon=True)
    segunda = Thread(target=transacao_2, name="transacao-escala-2", daemon=True)

    try:
        primeira.start()
        segunda.start()

        try:
            assert primeira_atualizou.wait(10), "A primeira transacao nao atualizou."
            assert segunda_iniciou_chamada.wait(10), "A segunda transacao nao iniciou."

            pids_por_transacao = dict(pids.get(timeout=5) for _ in range(2))
            with psycopg.connect(**kwargs, autocommit=True) as observer:
                aguardar_bloqueio_no_postgresql(
                    observer,
                    pid_bloqueado=pids_por_transacao["t2"],
                    pid_bloqueador=pids_por_transacao["t1"],
                    transacao_finalizada=segunda_finalizou,
                )
            LOGGER.info("transacao 2 esta bloqueada pela transacao 1")
        finally:
            liberar_primeiro_commit.set()
            primeira.join(timeout=15)
            segunda.join(timeout=15)

        assert not primeira.is_alive(), "A primeira transacao excedeu o timeout."
        assert not segunda.is_alive(), "A segunda transacao excedeu o timeout."

        resultados_por_transacao = {
            nome: (estado, quantidade, erro)
            for nome, estado, quantidade, erro in (
                resultados.get(timeout=2) for _ in range(2)
            )
        }
        assert resultados_por_transacao == {
            "t1": ("confirmada", 1, None),
            "t2": ("rejeitada", None, "23505"),
        }

        # o estado final e consultado por uma nova conexao, depois que ambas as
        # transacoes terminaram, de forma q n precisamos inferir a atomiciada
        # pelas excecoes apenas
        with psycopg.connect(**kwargs) as verificacao:
            with verificacao.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, id_unidade, data_plantao, turno::text
                    FROM escala
                    WHERE id IN (%s, %s)
                    ORDER BY id
                    """,
                    (id_primeira, id_segunda),
                )
                estado_final = cur.fetchall()
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM escala
                    WHERE id_atuacao_residente = 1
                      AND data_plantao = %s
                      AND turno = 'tarde'
                    """,
                    (destino,),
                )
                quantidade_no_destino = cur.fetchone()[0]

        assert estado_final == [
            (id_primeira, 1, destino, "tarde"),
            (id_segunda, 1, origem_segunda, "manha"),
        ]
        assert quantidade_no_destino == 1
        assert "transacao 2 esta bloqueada pela transacao 1" in caplog.messages
    finally:
        liberar_primeiro_commit.set()
        primeira.join(timeout=15)
        segunda.join(timeout=15)
        with psycopg.connect(**kwargs) as cleanup:
            with cleanup.cursor() as cur:
                cur.execute(
                    "DELETE FROM escala WHERE id IN (%s, %s)",
                    (id_primeira, id_segunda),
                )
