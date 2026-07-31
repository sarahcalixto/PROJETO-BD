"""Ponto de entrada do painel Streamlit do Sistema de Gestão Hospitalar."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from projeto_hospital.ui.components import aplicar_estilos, cabecalho_pagina
from projeto_hospital.ui.data import get_connection
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
    get_connection()
except Exception as exc:  # noqa: BLE001
    with st.sidebar:
        st.badge("Banco desconectado", icon=":material/database_off:", color="red")
    cabecalho_pagina(
        "Conexão",
        "Banco de dados indisponível",
        "O painel não conseguiu acessar o PostgreSQL configurado.",
    )
    st.error(
        "Verifique se o serviço está ativo e se as variáveis do arquivo `.env` estão corretas.",
        icon=":material/error:",
    )
    with st.expander("Ver detalhes técnicos", icon=":material/code:"):
        st.code(str(exc), language=None)
    st.stop()

with st.sidebar:
    st.badge("Banco conectado", icon=":material/database:", color="green")
    st.caption("Gestão hospitalar · SQL puro")

criar_navegacao().run()
