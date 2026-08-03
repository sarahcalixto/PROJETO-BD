"""Componentes visuais e tratamento compartilhado de erros da interface."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import streamlit as st

from projeto_hospital.services import ServicoORMError


LOGGER = logging.getLogger(__name__)

MENSAGENS_SQLSTATE = {
    "23502": "Preencha todos os dados obrigatórios.",
    "23503": "Um dos registros selecionados não existe mais.",
    "23505": "Já existe um registro com os mesmos dados.",
    "23514": "Os dados informados não atendem às regras do sistema.",
    "40001": "Os dados foram alterados por outra operação. Tente novamente.",
    "40P01": "Houve um conflito entre operações simultâneas. Tente novamente.",
}


def cabecalho_pagina(categoria: str, titulo: str, descricao: str) -> None:
    """Renderiza um cabeçalho consistente para todas as páginas."""
    st.badge(categoria, color="primary")
    st.title(titulo)
    st.caption(descricao)


def mostrar_metricas(metricas: Sequence[tuple[str, str | int, str | None]]) -> None:
    """Mostra métricas em uma faixa que quebra linha em telas estreitas."""
    with st.container(horizontal=True, gap="small"):
        for rotulo, valor, ajuda in metricas:
            st.metric(rotulo, valor, help=ajuda, border=True, width="stretch")


def mostrar_estado_vazio(titulo: str, descricao: str) -> None:
    """Padroniza mensagens de ausência de resultados."""
    with st.container(border=True):
        st.info(f"**{titulo}**\n\n{descricao}", icon=":material/info:")


def mostrar_erro_banco(
    exc: Exception,
    mensagem: str = "Não foi possível carregar os dados desta página.",
) -> None:
    """Apresenta erro padronizado sem expor SQL, chaves ou detalhes internos."""
    origem = getattr(exc, "orig", exc)
    sqlstate = getattr(origem, "sqlstate", None)
    detalhe = str(exc) if isinstance(exc, ServicoORMError) else None
    if detalhe is None:
        detalhe = MENSAGENS_SQLSTATE.get(sqlstate)
    texto = f"{mensagem} {detalhe}" if detalhe else mensagem
    LOGGER.error(
        "Falha tratada na interface",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    st.error(texto, icon=":material/error:")
