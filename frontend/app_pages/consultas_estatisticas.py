"""Consultas SQL, views e relatórios ORM exigidos pelo projeto."""

from datetime import date

import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    ServicoORMError,
    calcular_tempo_medio_espera,
    calcular_tempo_medio_por_residente,
    pacientes_sem_procedimento_alto_risco,
    percentual_alto_risco_por_residente,
    plantoes_por_unidade_e_residente,
    preceptores_com_mais_de_cinco_atendimentos,
    preceptores_de_pacientes_flamenguistas,
    ranking_residentes_por_atendimentos,
    ultimos_atendimentos_por_paciente,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
    mostrar_metricas,
)
from projeto_hospital.ui.data import dto_dataframe, executar_leitura, run_query


OPCOES = (
    "Tempo médio por residente",
    "Ranking de residentes",
    "Supervisão mensal",
    "Plantões por unidade",
    "Pacientes sem alto risco",
    "Pacientes internados",
    "Supervisão inadequada",
    "Estatísticas mensais",
    "Preceptores de pacientes flamenguistas",
    "Último atendimento por paciente",
    "Alto risco por residente",
    "Tempo médio de espera",
)

cabecalho_pagina(
    "Análises",
    "Consultas e estatísticas",
    "Execute as consultas SQL, views e consultas ORM previstas nas duas etapas.",
)
consulta = st.selectbox("Consulta", OPCOES, key="consulta_estatistica")
mes = None
if consulta in ("Supervisão mensal", "Plantões por unidade"):
    mes = st.date_input("Mês de referência", value=date.today()).replace(day=1)

try:
    if consulta == "Tempo médio por residente":
        dados = dto_dataframe(executar_leitura(calcular_tempo_medio_por_residente))
    elif consulta == "Ranking de residentes":
        dados = dto_dataframe(
            executar_leitura(ranking_residentes_por_atendimentos)
        )
    elif consulta == "Supervisão mensal":
        dados = dto_dataframe(
            executar_leitura(preceptores_com_mais_de_cinco_atendimentos, mes)
        )
    elif consulta == "Plantões por unidade":
        dados = dto_dataframe(
            executar_leitura(plantoes_por_unidade_e_residente, mes)
        )
    elif consulta == "Pacientes sem alto risco":
        dados = dto_dataframe(
            executar_leitura(pacientes_sem_procedimento_alto_risco)
        )
    elif consulta == "Pacientes internados":
        dados = run_query(
            "SELECT * FROM vw_pacientes_internados ORDER BY data_internacao DESC"
        )
    elif consulta == "Supervisão inadequada":
        dados = run_query(
            """
            SELECT * FROM vw_residentes_sem_supervisor
            ORDER BY data_plantao DESC, turno, residente
            """
        )
    elif consulta == "Estatísticas mensais":
        dados = run_query(
            """
            SELECT * FROM vw_estatisticas_atendimentos_mensal
            ORDER BY ano DESC, mes DESC, unidade
            """
        )
    elif consulta == "Preceptores de pacientes flamenguistas":
        dados = dto_dataframe(
            executar_leitura(preceptores_de_pacientes_flamenguistas)
        )
    elif consulta == "Último atendimento por paciente":
        dados = dto_dataframe(
            executar_leitura(ultimos_atendimentos_por_paciente)
        )
        if not dados.empty:
            dados["procedimentos"] = dados["procedimentos"].map(
                lambda itens: ", ".join(
                    f"{item['nome']} ({item['quantidade']}x)" for item in itens
                )
                or "Nenhum"
            )
    elif consulta == "Alto risco por residente":
        dados = dto_dataframe(
            executar_leitura(percentual_alto_risco_por_residente)
        )
    else:
        dados = dto_dataframe(executar_leitura(calcular_tempo_medio_espera))
except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
    mostrar_erro_banco(exc)
    st.stop()

if dados.empty:
    mostrar_estado_vazio("Sem resultados", "A consulta não retornou registros.")
else:
    mostrar_metricas([("Registros", len(dados), None)])
    colunas_publicas = [
        coluna for coluna in dados.columns if not str(coluna).startswith("id_")
    ]
    st.dataframe(
        dados.loc[:, colunas_publicas],
        hide_index=True,
        width="stretch",
        key="resultado_consulta_estatistica",
    )
