"""Acesso a dados usado pelas páginas Streamlit."""

from __future__ import annotations

import pandas as pd
import psycopg
import streamlit as st
from psycopg.rows import dict_row

from projeto_hospital.config import load_database_config


@st.cache_resource(show_spinner=False)
def get_connection() -> psycopg.Connection:
    """Abre e mantém a conexão compartilhada durante a sessão Streamlit."""
    config = load_database_config()
    return psycopg.connect(row_factory=dict_row, **config.connection_kwargs)


def run_query(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
    """Executa SELECT e devolve o resultado como DataFrame."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except psycopg.Error:
        conn.rollback()
        raise


def run_command(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
    """Executa comando de escrita via função armazenada e confirma a transação."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall() if cur.description else []
        conn.commit()
        return pd.DataFrame(rows)
    except psycopg.Error:
        conn.rollback()
        raise


def listar_pacientes() -> pd.DataFrame:
    return run_query(
        """
        SELECT pac.id, pes.nome, pac.num_convenio, pac.grupo_sanguineo
        FROM paciente pac
        JOIN pessoa pes ON pes.id = pac.id
        ORDER BY pes.nome
        """
    )


def listar_atuacoes(tipo: str) -> pd.DataFrame:
    tabela = "atuacao_residente" if tipo == "residente" else "atuacao_preceptor"
    return run_query(
        f"""
        SELECT t.id, pes.nome, ap.data_inicio, ap.data_fim
        FROM {tabela} t
        JOIN atuacao_profissional ap ON ap.id = t.id
        JOIN profissional prof ON prof.id = ap.id_profissional
        JOIN pessoa pes ON pes.id = prof.id
        ORDER BY pes.nome
        """
    )


def listar_unidades() -> pd.DataFrame:
    return run_query("SELECT id, nome, tipo FROM unidade ORDER BY nome")


def listar_atendimentos_ids() -> pd.DataFrame:
    return run_query(
        """
        SELECT a.id, pes.nome AS paciente, a.data_hora
        FROM atendimento a
        JOIN paciente pac ON pac.id = a.id_paciente
        JOIN pessoa pes ON pes.id = pac.id
        ORDER BY a.data_hora DESC
        """
    )
