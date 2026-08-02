"""Demonstrações mensuráveis de loading, sessão e transação."""

from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, sessionmaker

from projeto_hospital.orm import Paciente, session_scope
from projeto_hospital.services import atualizar_convenio_paciente


def _contar_consultas(session: Session) -> tuple[list[str], object]:
    comandos: list[str] = []

    def registrar(*args: object) -> None:
        comandos.append(str(args[2]))

    event.listen(session.get_bind(), "before_cursor_execute", registrar)
    return comandos, registrar


def test_lazy_e_eager_loading_sao_mensuraveis(
    orm_session_factory: sessionmaker[Session],
) -> None:
    with orm_session_factory() as lazy_session:
        comandos_lazy, listener_lazy = _contar_consultas(lazy_session)
        try:
            paciente = lazy_session.get(Paciente, 1)
            assert paciente is not None
            assert paciente.pessoa.nome == "Gon Freecss"
            assert len(paciente.atendimentos) == 2
        finally:
            event.remove(
                lazy_session.get_bind(), "before_cursor_execute", listener_lazy
            )

    with orm_session_factory() as eager_session:
        comandos_eager, listener_eager = _contar_consultas(eager_session)
        try:
            paciente = eager_session.execute(
                select(Paciente)
                .where(Paciente.id == 1)
                .options(
                    joinedload(Paciente.pessoa),
                    joinedload(Paciente.atendimentos),
                )
            ).unique().scalar_one()
            assert paciente is not None
            consultas_apos_busca = len(comandos_eager)
            assert paciente.pessoa.nome == "Gon Freecss"
            assert len(paciente.atendimentos) == 2
        finally:
            event.remove(
                eager_session.get_bind(), "before_cursor_execute", listener_eager
            )

    assert len(comandos_lazy) == 3
    assert consultas_apos_busca == 1
    assert len(comandos_eager) == consultas_apos_busca


def test_session_scope_confirma_commit(
    orm_session_factory: sessionmaker[Session],
) -> None:
    with session_scope(orm_session_factory) as session:
        atualizar_convenio_paciente(session, 1, "COMMIT-ETAPA2")

    with orm_session_factory() as verificacao:
        assert verificacao.get(Paciente, 1).num_convenio == "COMMIT-ETAPA2"

    with session_scope(orm_session_factory) as limpeza:
        atualizar_convenio_paciente(limpeza, 1, "CONV-2026-001")


def test_session_scope_reverte_toda_transacao(
    orm_session_factory: sessionmaker[Session],
) -> None:
    try:
        with session_scope(orm_session_factory) as session:
            atualizar_convenio_paciente(session, 1, "NAO-PERSISTIR")
            session.add(Paciente(id=1))
    except IntegrityError:
        pass
    else:  # pragma: no cover - falha explícita mais legível
        raise AssertionError("A violação esperada não ocorreu")

    with orm_session_factory() as verificacao:
        assert verificacao.get(Paciente, 1).num_convenio == "CONV-2026-001"
