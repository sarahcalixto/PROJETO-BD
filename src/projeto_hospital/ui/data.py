"""Acesso a dados e sessões usado pelas páginas Streamlit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from datetime import date
from typing import Any, TypeVar

import pandas as pd
import streamlit as st
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session, aliased, sessionmaker

from projeto_hospital.orm import (
    Atendimento,
    AtuacaoPreceptor,
    AtuacaoProfissional,
    AtuacaoResidente,
    Escala,
    Paciente,
    Pessoa,
    Procedimento,
    ProcedimentoRealizado,
    Profissional,
    Unidade,
    create_database_engine,
    create_session_factory,
    session_scope,
)


T = TypeVar("T")


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    return create_database_engine()


@st.cache_resource(show_spinner=False)
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory(get_engine())


def validar_banco_etapa2() -> None:
    """Falha cedo quando o banco ainda não recebeu a migração final."""

    with get_engine().connect() as connection:
        pronto = connection.execute(
            text(
                """
                SELECT
                    to_regclass('public.internacao') IS NOT NULL
                    AND to_regclass('public.auditoria_atendimento') IS NOT NULL
                    AND to_regclass('public.vw_pacientes_internados') IS NOT NULL
                    AND EXISTS (
                        SELECT 1 FROM pg_proc
                        WHERE proname = 'sp_registrar_atendimento_completo'
                    )
                """
            )
        ).scalar_one()
    if not pronto:
        raise RuntimeError(
            "O banco ainda não está preparado para a Etapa 2. "
            "Execute: uv run python scripts/preparar_banco.py"
        )


def executar_leitura(servico: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    with get_session_factory()() as session:
        return servico(session, *args, **kwargs)


def executar_escrita(servico: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    with session_scope(get_session_factory()) as session:
        return servico(session, *args, **kwargs)


def run_query(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Lê views, auditoria ou catálogo com parâmetros nomeados."""

    with get_engine().connect() as connection:
        return pd.read_sql_query(text(sql), connection, params=params)


def dto_dataframe(items: list[Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [asdict(item) if is_dataclass(item) else item for item in items]
    )


def listar_pacientes() -> pd.DataFrame:
    with get_session_factory()() as session:
        rows = session.execute(
            select(
                Paciente.id,
                Pessoa.nome,
                Paciente.num_convenio,
                Paciente.grupo_sanguineo,
            )
            .join(Pessoa, Pessoa.id == Paciente.id)
            .order_by(Pessoa.nome)
        ).all()
    return pd.DataFrame(rows, columns=["id", "nome", "num_convenio", "grupo_sanguineo"])


def listar_atuacoes(tipo: str, data_referencia: date | None = None) -> pd.DataFrame:
    subtipo = AtuacaoResidente if tipo == "residente" else AtuacaoPreceptor
    with get_session_factory()() as session:
        statement = (
            select(
                subtipo.id,
                Pessoa.nome,
                Profissional.crm,
                AtuacaoProfissional.data_inicio,
                AtuacaoProfissional.data_fim,
            )
            .join(AtuacaoProfissional, AtuacaoProfissional.id == subtipo.id)
            .join(Profissional, Profissional.id == AtuacaoProfissional.id_profissional)
            .join(Pessoa, Pessoa.id == Profissional.id)
            .order_by(Pessoa.nome)
        )
        if data_referencia is not None:
            statement = statement.where(
                AtuacaoProfissional.data_inicio <= data_referencia,
                (AtuacaoProfissional.data_fim.is_(None))
                | (AtuacaoProfissional.data_fim >= data_referencia),
            )
        rows = session.execute(statement).all()
    return pd.DataFrame(
        rows,
        columns=["id", "nome", "crm", "data_inicio", "data_fim"],
    )


def listar_unidades() -> pd.DataFrame:
    with get_session_factory()() as session:
        rows = session.execute(
            select(Unidade.id, Unidade.nome, Unidade.tipo).order_by(Unidade.nome)
        ).all()
    return pd.DataFrame(rows, columns=["id", "nome", "tipo"])


def listar_procedimentos_catalogo() -> pd.DataFrame:
    with get_session_factory()() as session:
        rows = session.execute(
            select(
                Procedimento.id,
                Procedimento.codigo,
                Procedimento.nome,
                Procedimento.nivel_risco,
                Procedimento.tempo_medio_minutos,
            ).order_by(Procedimento.nome)
        ).all()
    return pd.DataFrame(
        rows,
        columns=["id", "codigo", "nome", "nivel_risco", "tempo_medio_minutos"],
    )


def listar_atendimentos_ids() -> pd.DataFrame:
    with get_session_factory()() as session:
        rows = session.execute(
            select(Atendimento.id, Pessoa.nome, Atendimento.data_hora)
            .join(Paciente, Paciente.id == Atendimento.id_paciente)
            .join(Pessoa, Pessoa.id == Paciente.id)
            .order_by(Atendimento.data_hora.desc())
        ).all()
    return pd.DataFrame(rows, columns=["id", "paciente", "data_hora"])


def listar_escalas_origem() -> pd.DataFrame:
    pessoa_residente = aliased(Pessoa)
    pessoa_preceptor = aliased(Pessoa)
    atuacao_residente = aliased(AtuacaoProfissional)
    atuacao_preceptor = aliased(AtuacaoProfissional)
    with get_session_factory()() as session:
        rows = session.execute(
            select(
                Escala.id,
                Escala.id_atuacao_residente,
                pessoa_residente.nome.label("residente"),
                Escala.data_plantao,
                Escala.turno,
                Unidade.nome.label("unidade"),
                pessoa_preceptor.nome.label("preceptor"),
            )
            .join(Unidade, Unidade.id == Escala.id_unidade)
            .join(AtuacaoResidente, AtuacaoResidente.id == Escala.id_atuacao_residente)
            .join(atuacao_residente, atuacao_residente.id == AtuacaoResidente.id)
            .join(
                pessoa_residente,
                pessoa_residente.id == atuacao_residente.id_profissional,
            )
            .join(AtuacaoPreceptor, AtuacaoPreceptor.id == Escala.id_atuacao_preceptor)
            .join(atuacao_preceptor, atuacao_preceptor.id == AtuacaoPreceptor.id)
            .join(
                pessoa_preceptor,
                pessoa_preceptor.id == atuacao_preceptor.id_profissional,
            )
            .order_by(Escala.data_plantao.desc(), Escala.turno, pessoa_residente.nome)
        ).all()
    return pd.DataFrame(
        rows,
        columns=[
            "id",
            "id_atuacao_residente",
            "residente",
            "data_plantao",
            "turno",
            "unidade",
            "preceptor",
        ],
    )


def carregar_visao_geral() -> tuple[pd.DataFrame, pd.DataFrame]:
    with get_session_factory()() as session:
        indicadores = session.execute(
            select(
                select(func.count(Paciente.id)).scalar_subquery().label("total_pacientes"),
                select(func.count(Atendimento.id))
                .where(func.date(Atendimento.data_hora) == func.current_date())
                .scalar_subquery()
                .label("atendimentos_hoje"),
                select(func.count(Unidade.id)).scalar_subquery().label("total_unidades"),
                select(func.count(ProcedimentoRealizado.id_procedimento))
                .scalar_subquery()
                .label("procedimentos_realizados"),
            )
        ).one()
        recentes = session.execute(
            select(
                Atendimento.id,
                Atendimento.data_hora,
                Pessoa.nome,
                Unidade.nome,
                Atendimento.duracao_minutos,
            )
            .join(Paciente, Paciente.id == Atendimento.id_paciente)
            .join(Pessoa, Pessoa.id == Paciente.id)
            .join(Unidade, Unidade.id == Atendimento.id_unidade)
            .order_by(Atendimento.data_hora.desc())
            .limit(8)
        ).all()
    return (
        pd.DataFrame(
            [indicadores],
            columns=[
                "total_pacientes",
                "atendimentos_hoje",
                "total_unidades",
                "procedimentos_realizados",
            ],
        ),
        pd.DataFrame(
            recentes,
            columns=[
                "id_atendimento",
                "data_hora",
                "paciente",
                "unidade",
                "duracao_minutos",
            ],
        ),
    )
