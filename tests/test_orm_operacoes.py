"""Testes das operações da Etapa 1 reimplementadas com SQLAlchemy."""

from datetime import date, datetime

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from projeto_hospital.orm import (
    Atendimento,
    Paciente,
    Pessoa,
    ProcedimentoRealizado,
    session_scope,
)
from projeto_hospital.services import (
    EntidadeNaoEncontrada,
    RegraNegocioViolada,
    atualizar_convenio_paciente,
    calcular_tempo_medio_por_residente,
    inserir_atendimento_validado,
    listar_atendimentos_paciente,
    listar_procedimentos_atendimento,
    remover_procedimento_nao_faturado,
)


def _inserir_atendimento(session: Session, id_atendimento: int = 500) -> None:
    inserir_atendimento_validado(
        session,
        id_atendimento=id_atendimento,
        data_hora=datetime.now().replace(microsecond=0),
        duracao_minutos=30,
        id_paciente=1,
        id_atuacao_residente=1,
        id_atuacao_preceptor=6,
        id_unidade=1,
    )


def test_inserir_atendimento_validado_com_sucesso(orm_session: Session) -> None:
    _inserir_atendimento(orm_session)

    atendimento = orm_session.get(Atendimento, 500)
    assert atendimento is not None
    assert atendimento.id_paciente == 1


@pytest.mark.parametrize(
    ("alteracao", "erro"),
    [
        ({"duracao_minutos": 0}, RegraNegocioViolada),
        ({"id_paciente": 9999}, EntidadeNaoEncontrada),
        ({"id_atuacao_residente": 9999}, EntidadeNaoEncontrada),
        ({"id_atuacao_preceptor": 9999}, EntidadeNaoEncontrada),
        ({"id_unidade": 9999}, EntidadeNaoEncontrada),
        (
            {"data_hora": datetime(2000, 1, 1, 8, 0)},
            RegraNegocioViolada,
        ),
    ],
)
def test_inserir_atendimento_rejeita_dados_invalidos(orm_session: Session, alteracao: dict[str, object], erro: type[Exception]) -> None:
    parametros = {
        "id_atendimento": 501,
        "data_hora": datetime.now().replace(microsecond=0),
        "duracao_minutos": 30,
        "id_paciente": 1,
        "id_atuacao_residente": 1,
        "id_atuacao_preceptor": 6,
        "id_unidade": 1,
    }
    parametros.update(alteracao)

    with pytest.raises(erro):
        inserir_atendimento_validado(orm_session, **parametros)

    assert orm_session.get(Atendimento, 501) is None


def test_falha_reverte_operacoes_da_mesma_transacao(orm_session_factory: sessionmaker[Session]) -> None:
    with pytest.raises(IntegrityError), session_scope(orm_session_factory) as session:
        atualizar_convenio_paciente(session, 1, "CONVENIO-NAO-PERSISTE")
        _inserir_atendimento(session, id_atendimento=1)

    with orm_session_factory() as session:
        assert session.get(Paciente, 1).num_convenio == "CONV-2026-001"


def test_listar_atendimentos_paciente_em_ordem(orm_session: Session) -> None:
    resultados = listar_atendimentos_paciente(orm_session, 1)
    assert [resultado.id_atendimento for resultado in resultados] == [1, 6]


def test_listar_atendimentos_distingue_vazio_de_inexistente(orm_session: Session) -> None:
    pessoa = Pessoa(
        id=600,
        nome="Paciente sem atendimento",
        cpf="60000000000",
        data_nascimento=date(2000, 1, 1),
        is_flamengo=False,
    )
    pessoa.paciente = Paciente(num_convenio=None, grupo_sanguineo="O+")
    orm_session.add(pessoa)
    orm_session.flush()

    assert listar_atendimentos_paciente(orm_session, 600) == []

    with pytest.raises(EntidadeNaoEncontrada):
        listar_atendimentos_paciente(orm_session, 9999)


def test_listar_procedimentos_com_eager_loading(orm_session: Session) -> None:
    engine = orm_session.get_bind()
    comandos: list[str] = []

    def registrar_comando(*args: object) -> None:
        comandos.append(str(args[2]))

    event.listen(engine, "before_cursor_execute", registrar_comando)
    try:
        resultados = listar_procedimentos_atendimento(orm_session, 3)
        consultas_apos_servico = len(comandos)
        nomes = [resultado.nome for resultado in resultados]
    finally:
        event.remove(engine, "before_cursor_execute", registrar_comando)

    assert consultas_apos_servico == 3
    assert len(comandos) == consultas_apos_servico
    assert nomes == ["Aplicacao de medicacao"]
    assert resultados[0].quantidade == 2
    assert resultados[0].tempo_real_minutos == 15


def test_listar_procedimentos_distingue_vazio_de_inexistente(orm_session: Session) -> None:
    _inserir_atendimento(orm_session, id_atendimento=502)
    assert listar_procedimentos_atendimento(orm_session, 502) == []

    with pytest.raises(EntidadeNaoEncontrada):
        listar_procedimentos_atendimento(orm_session, 9999)


def test_atualizar_convenio_paciente(orm_session: Session) -> None:
    resultado = atualizar_convenio_paciente(orm_session, 1, "CONV-NOVO-ORM")
    assert resultado.id_paciente == 1
    assert resultado.num_convenio == "CONV-NOVO-ORM"
    assert orm_session.get(Paciente, 1).num_convenio == "CONV-NOVO-ORM"

    with pytest.raises(EntidadeNaoEncontrada):
        atualizar_convenio_paciente(orm_session, 9999, "X")


def test_remover_procedimento_nao_faturado(orm_session: Session) -> None:
    resultado = remover_procedimento_nao_faturado(orm_session, 2, 2)
    assert (resultado.id_atendimento, resultado.id_procedimento) == (2, 2)
    assert resultado.faturado is False
    assert orm_session.get(ProcedimentoRealizado, (2, 2)) is None


def test_remover_procedimento_rejeita_faturado_e_inexistente(orm_session: Session) -> None:
    with pytest.raises(RegraNegocioViolada):
        remover_procedimento_nao_faturado(orm_session, 1, 1)

    with pytest.raises(EntidadeNaoEncontrada):
        remover_procedimento_nao_faturado(orm_session, 9999, 9999)


def test_calcular_tempo_medio_por_residente(orm_session: Session) -> None:
    resultados = calcular_tempo_medio_por_residente(orm_session)
    medias = {
        resultado.id_atuacao_residente: float(resultado.tempo_medio_minutos)
        for resultado in resultados
    }

    assert medias[1] == pytest.approx(95 / 3)
    assert medias[2] == pytest.approx(42.5)
    assert medias[3] == pytest.approx(37.5)
    assert medias[4] == pytest.approx(50)
    assert medias[5] == pytest.approx(35)
