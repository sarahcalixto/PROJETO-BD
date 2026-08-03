"""Cadastro e reajuste transacional das escalas de plantão."""

from datetime import date, timedelta

import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    ServicoORMError,
    criar_escala,
    reajustar_escala,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
)
from projeto_hospital.ui.data import (
    executar_escrita,
    listar_atuacoes,
    listar_escalas_origem,
    listar_unidades,
)


TURNOS = ("manha", "tarde", "noite")
ROTULOS = {"manha": "Manhã", "tarde": "Tarde", "noite": "Noite"}

cabecalho_pagina(
    "Escalas",
    "Escalas",
    "Cadastre um plantão ou reagende uma escala existente. Conflitos do "
    "residente são bloqueados pelo PostgreSQL.",
)

mensagem_sucesso = st.session_state.pop("escala_criada_sucesso", None)
if mensagem_sucesso:
    st.success(mensagem_sucesso)

operacao = st.segmented_control(
    "Operação",
    ("Nova escala", "Reajustar escala"),
    default="Nova escala",
    required=True,
    key="operacao_escala",
)
escalas = listar_escalas_origem()

if operacao == "Nova escala":
    data_plantao = st.date_input(
        "Data do plantão",
        value=date.today(),
        key="nova_escala_data",
    )
    turno = st.segmented_control(
        "Turno",
        TURNOS,
        default="manha",
        required=True,
        format_func=ROTULOS.get,
        key="nova_escala_turno",
    )

    with st.container(border=True):
        st.subheader("Ocupação do turno")
        st.caption(
            "Consulte as escalas existentes antes de selecionar o residente."
        )
        ocupadas = escalas.loc[
            (escalas["data_plantao"] == data_plantao)
            & (escalas["turno"] == turno),
            ["residente", "unidade", "preceptor"],
        ]
        if ocupadas.empty:
            st.info(
                "Nenhuma escala cadastrada nesta data e turno.",
                icon=":material/event_available:",
            )
        else:
            st.dataframe(
                ocupadas.rename(
                    columns={
                        "residente": "Residente",
                        "unidade": "Unidade",
                        "preceptor": "Preceptor",
                    }
                ),
                hide_index=True,
                width="stretch",
                key="ocupacao_nova_escala",
            )

    unidades = listar_unidades()
    residentes = listar_atuacoes("residente", data_plantao)
    preceptores = listar_atuacoes("preceptor", data_plantao)
    if unidades.empty or residentes.empty or preceptores.empty:
        mostrar_estado_vazio(
            "Cadastro indisponível",
            "Não há unidade, residente ou preceptor vigente na data selecionada.",
        )
        st.stop()

    with st.form("criar_escala", border=True):
        unidade = st.selectbox(
            "Unidade",
            unidades.itertuples(),
            format_func=lambda item: f"{item.nome} — {item.tipo}",
        )
        residente = st.selectbox(
            "Residente",
            residentes.itertuples(),
            format_func=lambda item: f"{item.nome} — {item.crm}",
        )
        preceptor = st.selectbox(
            "Preceptor",
            preceptores.itertuples(),
            format_func=lambda item: f"{item.nome} — {item.crm}",
        )
        cadastrar = st.form_submit_button(
            "Cadastrar escala",
            type="primary",
            icon=":material/event_available:",
        )

    if cadastrar:
        try:
            resultado = executar_escrita(
                criar_escala,
                id_unidade=int(unidade.id),
                data_plantao=data_plantao,
                turno=turno,
                id_atuacao_residente=int(residente.id),
                id_atuacao_preceptor=int(preceptor.id),
            )
            st.session_state["escala_criada_sucesso"] = (
                f"Escala {resultado.id_escala} cadastrada para {residente.nome} "
                f"em {data_plantao:%d/%m/%Y} — {ROTULOS[turno]}, na unidade "
                f"{unidade.nome}, com {preceptor.nome}."
            )
            st.rerun()
        except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
            mostrar_erro_banco(exc, "Não foi possível cadastrar a escala.")

else:
    if escalas.empty:
        mostrar_estado_vazio("Nenhuma escala", "Não existem escalas para reajustar.")
        st.stop()

    origem = st.selectbox(
        "Escala a reajustar",
        escalas.itertuples(),
        format_func=lambda item: (
            f"{item.residente} — {item.data_plantao} — "
            f"{ROTULOS[item.turno]} — {item.unidade}"
        ),
    )

    coluna_atual, coluna_destino = st.columns(2)
    with coluna_atual.container(border=True, height="stretch"):
        st.subheader("Escala atual")
        st.caption("Residente")
        st.write(origem.residente)
        st.caption("Unidade")
        st.write(origem.unidade)
        st.caption("Preceptor")
        st.write(origem.preceptor)
        st.caption("Data e turno")
        st.write(f"{origem.data_plantao:%d/%m/%Y} — {ROTULOS[origem.turno]}")

    with coluna_destino.container(border=True, height="stretch"):
        st.subheader("Novo agendamento")
        st.caption("Residente, unidade e preceptor permanecem iguais.")
        st.caption("Unidade mantida")
        st.write(origem.unidade)
        st.caption("Preceptor mantido")
        st.write(origem.preceptor)
        data_destino = st.date_input(
            "Data de destino",
            value=max(date.today(), origem.data_plantao) + timedelta(days=1),
            key=f"data_destino_escala_{origem.id}",
        )
        turno_destino = st.selectbox(
            "Turno de destino",
            TURNOS,
            index=None,
            format_func=ROTULOS.get,
            key=f"turno_destino_escala_{origem.id}",
        )

    if turno_destino is None:
        st.info(
            "Selecione o turno de destino para conferir o resumo da alteração.",
            icon=":material/info:",
        )
    else:
        st.info(
            f"{origem.residente} permanecerá na unidade {origem.unidade}, "
            f"com {origem.preceptor}. A escala de "
            f"{origem.data_plantao:%d/%m/%Y} — {ROTULOS[origem.turno]} será "
            f"reagendada para {data_destino:%d/%m/%Y} — "
            f"{ROTULOS[turno_destino]}.",
            icon=":material/event_repeat:",
        )

    st.caption(
        "Conflitos do residente e a vigência das atuações do residente e do "
        "preceptor são verificados automaticamente antes da confirmação."
    )

    with st.form("reajustar_escala", border=False):
        confirmar = st.checkbox("Confirmo a alteração desta escala")
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
                    f"Escala de {origem.residente} reajustada de "
                    f"{origem.data_plantao:%d/%m/%Y} — {ROTULOS[origem.turno]} "
                    f"para {data_destino:%d/%m/%Y} — {ROTULOS[turno_destino]}. "
                    f"Unidade {origem.unidade} e preceptor {origem.preceptor} "
                    f"mantidos. {resultado.quantidade_atualizada} escala(s) "
                    "atualizada(s)."
                )
            except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
                mostrar_erro_banco(exc, "Não foi possível reajustar a escala.")
