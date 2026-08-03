"""Atualização cadastral de pacientes."""

import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    ServicoORMError,
    atualizar_convenio_paciente,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
)
from projeto_hospital.ui.data import executar_escrita, listar_pacientes


cabecalho_pagina(
    "Pacientes",
    "Pacientes",
    "Atualize o número do convênio de um paciente cadastrado.",
)
pacientes = listar_pacientes()
if pacientes.empty:
    mostrar_estado_vazio("Nenhum paciente", "Não existem pacientes cadastrados.")
    st.stop()

paciente = st.selectbox(
    "Paciente",
    pacientes.itertuples(),
    format_func=lambda item: f"{item.nome} — {item.num_convenio or 'sem convênio'}",
)
with st.form("atualizar_convenio", border=True):
    convenio = st.text_input(
        "Número do convênio",
        value=paciente.num_convenio or "",
        help="Deixe vazio para remover o número informado.",
    )
    salvar = st.form_submit_button(
        "Salvar convênio", type="primary", icon=":material/save:"
    )

if salvar:
    try:
        resultado = executar_escrita(
            atualizar_convenio_paciente,
            int(paciente.id),
            convenio,
        )
        st.success(
            "Convênio atualizado para "
            f"{resultado.num_convenio or 'não informado'}."
        )
    except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
        mostrar_erro_banco(exc, "Não foi possível atualizar o paciente.")
