"""Operações de atendimento e procedimentos realizados."""

from datetime import datetime, timedelta

import pandas as pd
import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    AtendimentoCompletoInput,
    ProcedimentoCompletoInput,
    ServicoORMError,
    listar_atendimentos_paciente,
    listar_procedimentos_atendimento,
    registrar_atendimento_completo,
    remover_procedimento_nao_faturado,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
)
from projeto_hospital.ui.data import (
    dto_dataframe,
    executar_escrita,
    executar_leitura,
    listar_atendimentos_ids,
    listar_atuacoes,
    listar_pacientes,
    listar_procedimentos_catalogo,
    listar_unidades,
)


def _rotulo_atuacao(item: object) -> str:
    fim = getattr(item, "data_fim", None) or "atual"
    return (
        f"{getattr(item, 'nome')} — {getattr(item, 'crm')} "
        f"({getattr(item, 'data_inicio')} a {fim})"
    )


def _procedimentos_do_editor(
    tabela: pd.DataFrame,
    catalogo: pd.DataFrame,
    inicio_atendimento: datetime,
    duracao: int,
) -> tuple[ProcedimentoCompletoInput, ...]:
    ids = {
        f"{int(item.codigo)} — {item.nome}": int(item.id)
        for item in catalogo.itertuples()
    }
    fim_atendimento = inicio_atendimento + timedelta(minutes=duracao)
    resultado: list[ProcedimentoCompletoInput] = []
    informados: set[int] = set()
    for posicao, linha in tabela.dropna(how="all").iterrows():
        numero_linha = int(posicao) + 1
        rotulo = linha.get("Procedimento")
        if rotulo not in ids:
            raise ValueError(f"Selecione o procedimento da linha {numero_linha}.")
        try:
            quantidade = int(linha.get("Quantidade"))
            tempo = int(linha.get("Tempo real (min)"))
            inicio = pd.Timestamp(linha.get("Início")).to_pydatetime()
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Complete os valores da linha {numero_linha}."
            ) from exc
        if quantidade <= 0 or tempo <= 0:
            raise ValueError("Quantidade e tempo real devem ser positivos.")
        if inicio < inicio_atendimento or inicio + timedelta(minutes=tempo) > fim_atendimento:
            raise ValueError(
                f"O procedimento da linha {numero_linha} deve caber no atendimento."
            )
        identificador = ids[str(rotulo)]
        if identificador in informados:
            raise ValueError("O mesmo procedimento não pode ser repetido.")
        informados.add(identificador)
        observacao = linha.get("Observação")
        resultado.append(
            ProcedimentoCompletoInput(
                id_procedimento=identificador,
                quantidade=quantidade,
                tempo_real_minutos=tempo,
                data_hora_inicio=inicio,
                observacao=(
                    str(observacao).strip()
                    if pd.notna(observacao) and str(observacao).strip()
                    else None
                ),
            )
        )
    if not resultado:
        raise ValueError("Informe pelo menos um procedimento.")
    return tuple(resultado)


cabecalho_pagina(
    "Atendimentos",
    "Atendimentos",
    "Registre atendimentos e consulte ou remova procedimentos realizados.",
)
operacao = st.segmented_control(
    "Operação",
    ("Registrar", "Histórico", "Procedimentos", "Remover procedimento"),
    default="Registrar",
    key="atendimentos_operacao",
)

if operacao == "Registrar":
    agora = datetime.now().replace(second=0, microsecond=0)
    with st.container(horizontal=True):
        data_atendimento = st.date_input("Data", value=agora.date())
        hora_atendimento = st.time_input("Hora", value=agora.time(), step=60)
    data_hora = datetime.combine(data_atendimento, hora_atendimento)
    pacientes = listar_pacientes()
    residentes = listar_atuacoes("residente", data_atendimento)
    preceptores = listar_atuacoes("preceptor", data_atendimento)
    unidades = listar_unidades()
    catalogo = listar_procedimentos_catalogo()
    if any(df.empty for df in (pacientes, residentes, preceptores, unidades, catalogo)):
        mostrar_estado_vazio(
            "Cadastros incompletos",
            "São necessários pacientes, profissionais, unidades e procedimentos.",
        )
        st.stop()

    pacientes_por_id = {int(item.id): item for item in pacientes.itertuples()}
    residentes_por_id = {int(item.id): item for item in residentes.itertuples()}
    preceptores_por_id = {int(item.id): item for item in preceptores.itertuples()}
    unidades_por_id = {int(item.id): item for item in unidades.itertuples()}
    procedimentos_opcoes = [
        f"{int(item.codigo)} — {item.nome}" for item in catalogo.itertuples()
    ]
    tabela_inicial = pd.DataFrame(
        columns=(
            "Procedimento",
            "Quantidade",
            "Tempo real (min)",
            "Início",
            "Observação",
        )
    )
    with st.form("registrar_atendimento", border=True):
        with st.container(horizontal=True):
            duracao = st.number_input(
                "Duração em minutos", min_value=1, max_value=1440, value=None
            )
            paciente = st.selectbox(
                "Paciente",
                tuple(pacientes_por_id),
                index=None,
                format_func=lambda item: pacientes_por_id[item].nome,
            )
            unidade = st.selectbox(
                "Unidade",
                tuple(unidades_por_id),
                index=None,
                format_func=lambda item: unidades_por_id[item].nome,
            )
        with st.container(horizontal=True):
            residente = st.selectbox(
                "Residente",
                tuple(residentes_por_id),
                index=None,
                format_func=lambda item: _rotulo_atuacao(residentes_por_id[item]),
            )
            preceptor = st.selectbox(
                "Preceptor",
                tuple(preceptores_por_id),
                index=None,
                format_func=lambda item: _rotulo_atuacao(preceptores_por_id[item]),
            )
        st.subheader("Procedimentos")
        tabela = st.data_editor(
            tabela_inicial,
            key="atendimentos_procedimentos",
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "Procedimento": st.column_config.SelectboxColumn(
                    "Procedimento", options=procedimentos_opcoes, required=True
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "Quantidade", min_value=1, step=1, required=True
                ),
                "Tempo real (min)": st.column_config.NumberColumn(
                    "Tempo real (min)", min_value=1, step=1, required=True
                ),
                "Início": st.column_config.DatetimeColumn(
                    "Início",
                    default=data_hora,
                    min_value=data_hora,
                    format="DD/MM/YYYY HH:mm",
                    required=True,
                ),
                "Observação": st.column_config.TextColumn("Observação"),
            },
        )
        enviar = st.form_submit_button(
            "Registrar atendimento",
            type="primary",
            icon=":material/add_circle:",
        )
    if enviar:
        if None in (duracao, paciente, residente, preceptor, unidade):
            st.error("Preencha todos os campos obrigatórios.")
        else:
            try:
                itens = _procedimentos_do_editor(
                    tabela, catalogo, data_hora, int(duracao)
                )
                id_criado = executar_escrita(
                    registrar_atendimento_completo,
                    AtendimentoCompletoInput(
                        data_hora=data_hora,
                        duracao_minutos=int(duracao),
                        id_paciente=int(paciente),
                        id_atuacao_residente=int(residente),
                        id_atuacao_preceptor=int(preceptor),
                        id_unidade=int(unidade),
                        procedimentos=itens,
                    ),
                )
                st.success(f"Atendimento {id_criado} registrado com sucesso.")
            except ValueError as exc:
                st.error(str(exc))
            except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
                mostrar_erro_banco(exc, "Não foi possível registrar o atendimento.")

elif operacao == "Histórico":
    pacientes = listar_pacientes()
    paciente = st.selectbox(
        "Paciente",
        pacientes.itertuples(),
        index=None,
        format_func=lambda item: item.nome,
    )
    if paciente is not None:
        try:
            dados = dto_dataframe(
                executar_leitura(listar_atendimentos_paciente, int(paciente.id))
            )
            if dados.empty:
                mostrar_estado_vazio("Sem histórico", "O paciente não possui atendimentos.")
            else:
                st.dataframe(dados, hide_index=True, width="stretch")
        except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
            mostrar_erro_banco(exc)

elif operacao == "Procedimentos":
    atendimentos = listar_atendimentos_ids()
    atendimento = st.selectbox(
        "Atendimento",
        atendimentos.itertuples(),
        index=None,
        format_func=lambda item: (
            f"Atendimento {item.id} — {item.paciente} — {item.data_hora}"
        ),
    )
    if atendimento is not None:
        try:
            dados = dto_dataframe(
                executar_leitura(listar_procedimentos_atendimento, int(atendimento.id))
            )
            if dados.empty:
                mostrar_estado_vazio("Sem procedimentos", "Nenhum procedimento registrado.")
            else:
                st.dataframe(dados, hide_index=True, width="stretch")
        except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
            mostrar_erro_banco(exc)

else:
    atendimentos = listar_atendimentos_ids()
    atendimento = st.selectbox(
        "Atendimento",
        atendimentos.itertuples(),
        index=None,
        format_func=lambda item: f"Atendimento {item.id} — {item.paciente}",
    )
    if atendimento is not None:
        try:
            procedimentos = executar_leitura(
                listar_procedimentos_atendimento, int(atendimento.id)
            )
        except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
            mostrar_erro_banco(exc)
            st.stop()
        removiveis = [item for item in procedimentos if not item.faturado]
        if not removiveis:
            mostrar_estado_vazio(
                "Nenhum item removível",
                "O atendimento não possui procedimentos não faturados.",
            )
        else:
            with st.form("remover_procedimento", border=True):
                procedimento = st.selectbox(
                    "Procedimento não faturado",
                    removiveis,
                    format_func=lambda item: f"{item.codigo} — {item.nome}",
                )
                confirmar = st.checkbox("Confirmo a remoção")
                remover = st.form_submit_button(
                    "Remover procedimento",
                    type="primary",
                    icon=":material/delete:",
                )
            if remover:
                if not confirmar:
                    st.warning("Confirme a remoção antes de continuar.")
                else:
                    try:
                        executar_escrita(
                            remover_procedimento_nao_faturado,
                            int(atendimento.id),
                            int(procedimento.id_procedimento),
                        )
                        st.success("Procedimento removido com sucesso.")
                    except (psycopg.Error, SQLAlchemyError, ServicoORMError) as exc:
                        mostrar_erro_banco(exc, "Não foi possível remover o procedimento.")
