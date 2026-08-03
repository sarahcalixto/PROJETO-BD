"""Testes das consultas analíticas escritas com SQLAlchemy."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from projeto_hospital.orm import (
    AtuacaoProfissional,
    AtuacaoResidente,
    Pessoa,
    Profissional,
)
from projeto_hospital.services import (
    pacientes_sem_procedimento_alto_risco,
    plantoes_por_unidade_e_residente,
    preceptores_com_mais_de_cinco_atendimentos,
    ranking_residentes_por_atendimentos,
)


def test_ranking_residentes_por_atendimentos(orm_session: Session) -> None:
    resultados = ranking_residentes_por_atendimentos(orm_session)

    assert resultados[0].nome == "Narancia Ghirga"
    assert resultados[0].total_atendimentos == 4
    assert sum(resultado.total_atendimentos for resultado in resultados) == 10


def test_ranking_inclui_residente_sem_atendimentos(orm_session: Session) -> None:
    pessoa = Pessoa(
        id=700,
        nome="Residente sem atendimentos",
        cpf="70000000000",
        data_nascimento=date(2000, 1, 1),
        is_flamengo=False,
    )
    profissional = Profissional(
        crm="CRM-TESTE-700",
        data_admissao=date(2026, 1, 1),
        especialidade="Teste",
    )
    atuacao = AtuacaoProfissional(
        id=700,
        tipo="residente",
        data_inicio=date(2026, 1, 1),
    )
    atuacao.residente = AtuacaoResidente(
        tipo="residente",
        ano_residencia="R1",
    )
    profissional.atuacoes.append(atuacao)
    pessoa.profissional = profissional
    orm_session.add(pessoa)
    orm_session.flush()

    resultados = ranking_residentes_por_atendimentos(orm_session)
    resultado = next(
        item for item in resultados if item.nome == "Residente sem atendimentos"
    )
    assert resultado.total_atendimentos == 0


def test_preceptores_com_mais_de_cinco_atendimentos_no_mes(orm_session: Session) -> None:
    resultados = preceptores_com_mais_de_cinco_atendimentos(
        orm_session,
        date.today().replace(day=17),
    )
    assert [(item.nome, item.total_supervisionado) for item in resultados] == [
        ("Bruno Bucciarati", 7)
    ]


def test_preceptores_sem_resultado_em_outro_mes(orm_session: Session) -> None:
    mes_passado = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    assert (
        preceptores_com_mais_de_cinco_atendimentos(orm_session, mes_passado) == []
    )


def test_plantoes_por_unidade_e_residente(orm_session: Session) -> None:
    resultados = plantoes_por_unidade_e_residente(orm_session, date.today())
    linhas = {
        (item.unidade, item.residente, item.quantidade_plantoes)
        for item in resultados
    }

    assert ("Enfermaria Central", "Narancia Ghirga", 2) in linhas
    assert sum(item.quantidade_plantoes for item in resultados) == 6


def test_plantoes_incluem_unidades_sem_escala_no_mes(orm_session: Session) -> None:
    mes_passado = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    resultados = plantoes_por_unidade_e_residente(orm_session, mes_passado)

    assert len(resultados) == 3
    assert {item.unidade for item in resultados} == {
        "Enfermaria Central",
        "Pronto-Socorro Principal",
        "UTI Adulto",
    }
    assert all(item.residente is None for item in resultados)
    assert all(item.quantidade_plantoes == 0 for item in resultados)


def test_pacientes_sem_procedimento_de_alto_risco(orm_session: Session) -> None:
    resultados = pacientes_sem_procedimento_alto_risco(orm_session)
    assert {item.nome for item in resultados} == {
        "Gon Freecss",
        "Giorno Giovanna",
        "Winry Rockbell",
    }
