"""Cadastro ORM de escalas e garantias mantidas pelo PostgreSQL."""

from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from projeto_hospital.orm import AtuacaoPreceptor, AtuacaoResidente, Escala
from projeto_hospital.services import RegraNegocioViolada, criar_escala


def _criar(
    session: Session,
    *,
    data_plantao: date,
    id_unidade: int = 1,
    id_residente: int = 1,
    id_preceptor: int = 6,
):
    return criar_escala(
        session,
        id_unidade=id_unidade,
        data_plantao=data_plantao,
        turno="manha",
        id_atuacao_residente=id_residente,
        id_atuacao_preceptor=id_preceptor,
    )


def test_criar_escala_persiste_todos_os_campos(orm_session: Session) -> None:
    data_plantao = date(2041, 1, 10)

    resultado = _criar(
        orm_session,
        data_plantao=data_plantao,
        id_unidade=2,
        id_residente=3,
        id_preceptor=8,
    )

    escala = orm_session.get(Escala, resultado.id_escala)
    assert escala is not None
    assert resultado.id_unidade == escala.id_unidade == 2
    assert resultado.data_plantao == escala.data_plantao == data_plantao
    assert resultado.turno == escala.turno == "manha"
    assert resultado.id_atuacao_residente == escala.id_atuacao_residente == 3
    assert resultado.id_atuacao_preceptor == escala.id_atuacao_preceptor == 8


@pytest.mark.parametrize(
    ("modelo", "identificador", "papel"),
    [
        (AtuacaoResidente, 1, "residente"),
        (AtuacaoPreceptor, 6, "preceptora"),
    ],
)
def test_criar_escala_rejeita_atuacao_fora_da_vigencia(
    orm_session: Session,
    modelo,
    identificador: int,
    papel: str,
) -> None:
    atuacao_especializada = orm_session.get(modelo, identificador)
    assert atuacao_especializada is not None
    atuacao_especializada.atuacao.data_fim = date(2040, 1, 1)

    with pytest.raises(RegraNegocioViolada, match=papel):
        _criar(orm_session, data_plantao=date(2040, 1, 2))

    quantidade = orm_session.scalar(
        select(func.count(Escala.id)).where(Escala.data_plantao == date(2040, 1, 2))
    )
    assert quantidade == 0


def test_criar_escala_traduz_conflito_do_trigger_e_preserva_original(
    orm_session: Session,
) -> None:
    data_plantao = date(2041, 2, 10)
    original = _criar(orm_session, data_plantao=data_plantao, id_unidade=1)

    with pytest.raises(
        RegraNegocioViolada,
        match="Este residente já está escalado nesta data e turno",
    ), orm_session.begin_nested():
        _criar(orm_session, data_plantao=data_plantao, id_unidade=2)

    escalas = orm_session.scalars(
        select(Escala).where(
            Escala.data_plantao == data_plantao,
            Escala.turno == "manha",
            Escala.id_atuacao_residente == 1,
        )
    ).all()
    assert [escala.id for escala in escalas] == [original.id_escala]
    assert escalas[0].id_unidade == 1


def test_criar_escala_traduz_duplicacao_na_mesma_unidade(
    orm_session: Session,
) -> None:
    data_plantao = date(2041, 3, 10)
    original = _criar(orm_session, data_plantao=data_plantao, id_unidade=1)

    with pytest.raises(
        RegraNegocioViolada,
        match="Este residente já está escalado nesta data e turno",
    ), orm_session.begin_nested():
        _criar(orm_session, data_plantao=data_plantao, id_unidade=1)

    escalas = orm_session.scalars(
        select(Escala).where(
            Escala.data_plantao == data_plantao,
            Escala.turno == "manha",
            Escala.id_atuacao_residente == 1,
        )
    ).all()
    assert [escala.id for escala in escalas] == [original.id_escala]


def test_preceptor_pode_supervisionar_residentes_distintos_no_mesmo_turno(
    orm_session: Session,
) -> None:
    data_plantao = date(2041, 4, 10)

    primeira = _criar(
        orm_session,
        data_plantao=data_plantao,
        id_residente=1,
        id_preceptor=6,
    )
    segunda = _criar(
        orm_session,
        data_plantao=data_plantao,
        id_residente=2,
        id_preceptor=6,
    )

    assert primeira.id_atuacao_preceptor == segunda.id_atuacao_preceptor == 6
    assert primeira.id_atuacao_residente != segunda.id_atuacao_residente
