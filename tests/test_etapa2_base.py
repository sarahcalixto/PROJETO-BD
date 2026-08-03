"""Validação da base compartilhada da Etapa 2."""

from datetime import date

import psycopg
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers, selectinload, sessionmaker

from projeto_hospital.orm import (
    Atendimento,
    Base,
    Paciente,
    Pessoa,
    ProcedimentoRealizado,
    session_scope,
)


def test_metadata_contem_todas_as_relacoes_da_etapa_2() -> None:
    configure_mappers()

    assert {
        "pessoa",
        "paciente",
        "profissional",
        "atendimento",
        "procedimento",
        "procedimento_realizado",
        "escala",
        "internacao",
        "auditoria_atendimento",
    } <= set(Base.metadata.tables)
    assert "data_hora_inicio" in Base.metadata.tables["procedimento_realizado"].c
    assert "media_tempo_procedimento" in Base.metadata.tables["procedimento"].c


def test_schema_e_dados_da_etapa_2(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('internacao', 'auditoria_atendimento')
            """
        )
        colunas = {nome for (nome,) in cur.fetchall()}
        cur.execute("SELECT COUNT(*) FROM internacao WHERE data_hora_saida IS NULL")
        (internados,) = cur.fetchone()

    assert {"data_hora_entrada", "data_hora_saida", "operacao"} <= colunas
    assert internados == 2


def test_atuacoes_do_mesmo_profissional_nao_podem_se_sobrepor(
    conn: psycopg.Connection,
) -> None:
    with pytest.raises(psycopg.errors.ExclusionViolation):
        conn.execute(
            """
            INSERT INTO atuacao_profissional (
                id_profissional, tipo, data_inicio, data_fim
            ) VALUES (6, 'preceptor', CURRENT_DATE, NULL)
            """
        )


def test_atuacao_exige_exatamente_um_subtipo_compativel(
    conn: psycopg.Connection,
) -> None:
    id_profissional = conn.execute(
        """
        INSERT INTO pessoa (nome, cpf, data_nascimento, is_flamengo, telefone)
        VALUES ('Profissional sem subtipo', '79999999999', '1990-01-01', false, '81999999999')
        RETURNING id
        """
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO profissional (id, crm, data_admissao, especialidade)
        VALUES (%s, 'CRM-TESTE-799', CURRENT_DATE, 'Teste')
        """,
        (id_profissional,),
    )
    conn.execute(
        """
        INSERT INTO atuacao_profissional (
            id_profissional, tipo, data_inicio, data_fim
        ) VALUES (%s, 'residente', CURRENT_DATE, NULL)
        """,
        (id_profissional,),
    )
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("SET CONSTRAINTS trg_valida_especializacao_atuacao IMMEDIATE")


def test_escala_possui_unicidade_global_do_residente(
    conn: psycopg.Connection,
) -> None:
    definicao = conn.execute(
        """
        SELECT pg_get_constraintdef(oid)
        FROM pg_constraint
        WHERE conname = 'escala_residente_turno_uq'
        """
    ).fetchone()
    assert definicao is not None
    assert "data_plantao, turno, id_atuacao_residente" in definicao[0]


def test_paciente_nao_pode_ter_duas_internacoes_ativas(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur, pytest.raises(psycopg.errors.UniqueViolation):
        cur.execute(
            """
            INSERT INTO internacao (
                id_paciente, id_unidade, data_hora_entrada, data_hora_saida
            ) VALUES (1, 2, CURRENT_TIMESTAMP, NULL)
            """
        )


def test_relacionamentos_podem_ser_carregados_com_eager_loading(
    orm_session: Session,
) -> None:
    paciente = orm_session.scalar(
        select(Paciente)
        .where(Paciente.id == 1)
        .options(
            selectinload(Paciente.pessoa),
            selectinload(Paciente.atendimentos).selectinload(
                Atendimento.procedimentos
            ),
        )
    )

    assert paciente is not None
    assert paciente.pessoa.nome == "Gon Freecss"
    assert paciente.atendimentos
    assert all(
        isinstance(realizacao, ProcedimentoRealizado)
        for atendimento in paciente.atendimentos
        for realizacao in atendimento.procedimentos
    )


def test_session_scope_confirma_e_reverte_transacoes(
    orm_session_factory: sessionmaker[Session],
) -> None:
    pessoa = Pessoa(
        id=1000,
        nome="Teste de transação",
        cpf="99999999000",
        data_nascimento=date(2000, 1, 1),
        is_flamengo=False,
    )
    with session_scope(orm_session_factory) as session:
        session.add(pessoa)

    with orm_session_factory() as session:
        assert session.get(Pessoa, 1000) is not None

    with pytest.raises(IntegrityError), session_scope(orm_session_factory) as session:
        session.add(
            Pessoa(
                id=1001,
                nome="CPF duplicado",
                cpf="99999999000",
                data_nascimento=date(2001, 1, 1),
                is_flamengo=False,
            )
        )

    with orm_session_factory.begin() as session:
        assert session.get(Pessoa, 1001) is None
        session.delete(session.get(Pessoa, 1000))
