"""Ponto de entrada do painel Streamlit do Sistema de Gestão Hospitalar."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from projeto_hospital.ui.components import cabecalho_pagina
from projeto_hospital.ui.data import validar_banco


LOGGER = logging.getLogger(__name__)

st.set_page_config(
    page_title="Hospital Dra. Yuska Maritan Brito",
    page_icon=":material/local_hospital:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(
    Path(__file__).parent / "assets" / "hospital-logo.svg",
    size="large",
    icon_image=":material/local_hospital:",
)

try:
    validar_banco()
except Exception as exc:  # noqa: BLE001
    LOGGER.error(
        "Falha ao validar a disponibilidade do banco",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    with st.sidebar:
        st.badge("Sistema indisponível", icon=":material/cloud_off:", color="red")
    cabecalho_pagina(
        "Conexão",
        "Banco de dados indisponível",
        "O painel não conseguiu acessar os dados necessários.",
    )
    st.error(
        "Tente novamente em alguns instantes. Se o problema continuar, "
        "entre em contato com o suporte.",
        icon=":material/error:",
    )
    st.stop()

with st.sidebar:
    st.badge("Sistema disponível", icon=":material/cloud_done:", color="green")
    st.caption("Dados operacionais atualizados")

PAGES_DIR = Path(__file__).parent / "app_pages"
pagina = st.navigation(
    {
        "": [
            st.Page(
                PAGES_DIR / "visao_geral.py",
                title="Visão geral",
                icon=":material/dashboard:",
                default=True,
            )
        ],
        "Operações": [
            st.Page(
                PAGES_DIR / "atendimentos.py",
                title="Atendimentos",
                icon=":material/clinical_notes:",
            ),
            st.Page(
                PAGES_DIR / "pacientes.py",
                title="Pacientes",
                icon=":material/patient_list:",
            ),
            st.Page(
                PAGES_DIR / "escalas.py",
                title="Escalas",
                icon=":material/calendar_month:",
            ),
        ],
        "Análise": [
            st.Page(
                PAGES_DIR / "consultas_estatisticas.py",
                title="Consultas e estatísticas",
                icon=":material/query_stats:",
            ),
            st.Page(
                PAGES_DIR / "auditoria.py",
                title="Auditoria",
                icon=":material/fact_check:",
            ),
        ],
    },
    position="sidebar",
    expanded=True,
)
pagina.run()
