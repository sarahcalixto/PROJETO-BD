"""Componentes visuais e tratamento compartilhado de erros da interface."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import ServicoORMError


def aplicar_estilos() -> None:
    """Aplica somente ajustes que complementam o tema nativo do Streamlit."""
    st.html(
        """
        <style>
        [data-testid="stMainBlockContainer"] {
            max-width: 1480px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(15, 118, 110, 0.14);
        }

        [data-testid="stSidebar"][aria-expanded="true"] [data-testid="stLogoLink"] {
            height: 4.5rem;
            align-items: center;
        }

        [data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarLogo"] {
            width: 15rem !important;
            height: auto !important;
            max-width: 100% !important;
            max-height: 3.75rem !important;
        }

        div[data-testid="stForm"],
        div[data-testid="stExpander"] {
            border-color: rgba(15, 118, 110, 0.16);
        }

        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.25rem;
            }

            [data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarLogo"] {
                width: 13.5rem !important;
            }
        }
        </style>
        """
    )


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
    """Apresenta uma mensagem amigável e mantém o detalhe técnico acessível."""
    st.error(mensagem, icon=":material/error:")
    with st.expander("Ver detalhes técnicos", icon=":material/code:"):
        st.code(str(exc), language=None)


def executar_pagina(pagina: Callable[[], None]) -> None:
    """Isola erros de leitura sem esconder falhas de programação."""
    try:
        pagina()
    except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
        mostrar_erro_banco(exc)
