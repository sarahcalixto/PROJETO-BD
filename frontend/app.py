"""Ponto de entrada do painel Streamlit do Sistema de Gestão Hospitalar."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from projeto_hospital.ui.components import aplicar_estilos, cabecalho_pagina
from projeto_hospital.ui.data import validar_banco_etapa2
from projeto_hospital.ui.pages import criar_navegacao

st.set_page_config(
    page_title="Hospital Dra. Yuska Maritan Brito",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_estilos()
st.logo(
    Path(__file__).parent / "assets" / "hospital-logo.svg",
    size="large",
    icon_image=":material/local_hospital:",
)

try:
    validar_banco_etapa2()
except Exception as exc:  # noqa: BLE001
    with st.sidebar:
        st.badge("Banco desconectado", icon=":material/database_off:", color="red")
    cabecalho_pagina(
        "Conexão",
        "Banco de dados indisponível",
        "O painel não conseguiu acessar o PostgreSQL configurado.",
    )
    st.error(
        "Verifique o PostgreSQL, o arquivo `.env` e execute "
        "`uv run python scripts/preparar_banco.py`.",
        icon=":material/error:",
    )
    with st.expander("Ver detalhes técnicos", icon=":material/code:"):
        st.code(str(exc), language=None)
    st.stop()

with st.sidebar:
    st.badge("Banco conectado", icon=":material/database:", color="green")
    st.caption("SQLAlchemy + PostgreSQL")

criar_navegacao().run()
