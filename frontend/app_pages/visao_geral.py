"""Resumo operacional do hospital."""

import streamlit as st

from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
    mostrar_metricas,
)
from projeto_hospital.ui.data import carregar_visao_geral


cabecalho_pagina(
    "Hospital",
    "Visão geral",
    "Indicadores operacionais e atendimentos mais recentes.",
)

try:
    resumo_df, recentes = carregar_visao_geral()
except Exception as exc:  # a conexão já foi validada no ponto de entrada
    mostrar_erro_banco(exc)
    st.stop()

resumo = resumo_df.iloc[0]
mostrar_metricas(
    [
        ("Pacientes", int(resumo["total_pacientes"]), None),
        ("Atendimentos hoje", int(resumo["atendimentos_hoje"]), None),
        ("Unidades", int(resumo["total_unidades"]), None),
        ("Procedimentos", int(resumo["procedimentos_realizados"]), None),
    ]
)

st.subheader("Atendimentos recentes")
if recentes.empty:
    mostrar_estado_vazio(
        "Nenhum atendimento",
        "Ainda não existem atendimentos registrados.",
    )
else:
    st.dataframe(
        recentes,
        hide_index=True,
        width="stretch",
        column_config={
            "id_atendimento": st.column_config.NumberColumn("Atendimento"),
            "data_hora": st.column_config.DatetimeColumn(
                "Data e hora", format="DD/MM/YYYY HH:mm"
            ),
            "paciente": "Paciente",
            "unidade": "Unidade",
            "duracao_minutos": st.column_config.NumberColumn(
                "Duração", format="%d min"
            ),
        },
    )
