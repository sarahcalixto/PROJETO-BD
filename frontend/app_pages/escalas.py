"""Reajuste transacional das escalas de plantão."""

from datetime import date, timedelta

import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import ServicoORMError, reajustar_escala
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
)
from projeto_hospital.ui.data import executar_escrita, listar_escalas_origem


TURNOS = ("manha", "tarde", "noite")
ROTULOS = {"manha": "Manhã", "tarde": "Tarde", "noite": "Noite"}

cabecalho_pagina(
    "Escalas",
    "Escalas",
    "Mova todas as escalas de um residente para outra data e turno.",
)
escalas = listar_escalas_origem()
if escalas.empty:
    mostrar_estado_vazio("Nenhuma escala", "Não existem escalas para reajustar.")
    st.stop()

origem = st.selectbox(
    "Origem",
    escalas.itertuples(),
    format_func=lambda item: (
        f"{item.residente} — {item.data_plantao} — "
        f"{ROTULOS[item.turno]} — {item.unidade}"
    ),
)
with st.form("reajustar_escala", border=True):
    data_destino = st.date_input(
        "Data de destino",
        value=max(date.today(), origem.data_plantao) + timedelta(days=1),
    )
    turno_destino = st.selectbox(
        "Turno de destino",
        TURNOS,
        index=None,
        format_func=ROTULOS.get,
    )
    confirmar = st.checkbox("Confirmo o reajuste de todas as escalas desta origem")
    executar = st.form_submit_button(
        "Reajustar escala", type="primary", icon=":material/event_repeat:"
    )

if executar:
    if not confirmar or turno_destino is None:
        st.warning("Selecione o turno e confirme o reajuste.")
    else:
        try:
            resultado = executar_escrita(
                reajustar_escala,
                id_atuacao_residente=int(origem.id_atuacao_residente),
                data_origem=origem.data_plantao,
                turno_origem=origem.turno,
                data_destino=data_destino,
                turno_destino=turno_destino,
            )
            st.success(
                f"{resultado.quantidade_atualizada} escala(s) reajustada(s)."
            )
        except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
            mostrar_erro_banco(exc, "Não foi possível reajustar a escala.")
