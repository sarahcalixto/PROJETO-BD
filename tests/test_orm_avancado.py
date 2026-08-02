"""Aceitação das consultas ORM avançadas da Etapa 2."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from projeto_hospital.orm import Paciente, Pessoa
from projeto_hospital.services import (
    percentual_alto_risco_por_residente,
    preceptores_de_pacientes_flamenguistas,
    ultimos_atendimentos_por_paciente,
)


def test_preceptores_de_pacientes_flamenguistas(orm_session: Session) -> None:
    resultados = preceptores_de_pacientes_flamenguistas(orm_session)
    assert [(item.id_atuacao_preceptor, item.nome) for item in resultados] == [
        (6, "Bruno Bucciarati"),
        (7, "Chrollo Lucilfer"),
        (8, "Roy Mustang"),
    ]


def test_ultimo_atendimento_inclui_relacionamentos_e_paciente_sem_atendimento(
    orm_session: Session,
) -> None:
    pessoa = Pessoa(
        id=700,
        nome="Paciente sem histórico",
        cpf="70000000000",
        data_nascimento=date(2000, 1, 1),
        is_flamengo=False,
    )
    pessoa.paciente = Paciente(num_convenio=None, grupo_sanguineo="O+")
    orm_session.add(pessoa)
    orm_session.flush()

    resultados = {
        item.id_paciente: item
        for item in ultimos_atendimentos_por_paciente(orm_session)
    }
    assert resultados[1].id_atendimento == 6
    assert resultados[1].residente == "Alphonse Elric"
    assert resultados[1].preceptor == "Bruno Bucciarati"
    assert [item.nome for item in resultados[1].procedimentos] == ["Sutura"]
    assert resultados[700].id_atendimento is None
    assert resultados[700].procedimentos == ()


def test_percentual_alto_risco_inclui_residente_com_zero(
    orm_session: Session,
) -> None:
    resultados = {
        item.id_atuacao_residente: item
        for item in percentual_alto_risco_por_residente(orm_session)
    }
    assert resultados[1].total_procedimentos == 3
    assert resultados[1].procedimentos_alto_risco == 0
    assert resultados[1].percentual_alto_risco == Decimal("0.00")
    assert resultados[2].total_procedimentos == 2
    assert resultados[2].procedimentos_alto_risco == 1
    assert resultados[2].percentual_alto_risco == Decimal("50.00")

    assert resultados[5].total_procedimentos == 2
