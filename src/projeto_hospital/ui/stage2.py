"""Operações, consultas e evidências visuais da Etapa 2."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from projeto_hospital.services import (
    AtendimentoCompletoInput,
    ProcedimentoCompletoInput,
    calcular_tempo_medio_espera,
    demonstrar_concorrencia_escala,
    medir_lazy_e_eager,
    percentual_alto_risco_por_residente,
    preceptores_de_pacientes_flamenguistas,
    reajustar_escala,
    registrar_atendimento_completo,
    ultimos_atendimentos_por_paciente,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_estado_vazio,
    mostrar_metricas,
)
from projeto_hospital.ui.data import (
    dto_dataframe,
    executar_escrita,
    executar_leitura,
    get_session_factory,
    listar_atuacoes,
    listar_escalas_origem,
    listar_pacientes,
    listar_procedimentos_catalogo,
    listar_unidades,
    run_query,
)
from projeto_hospital.ui.pages import label_atuacao


TURNOS = ("manha", "tarde", "noite")
ROTULOS_TURNO = {"manha": "Manhã", "tarde": "Tarde", "noite": "Noite"}


def _editor_procedimentos(
    catalogo: pd.DataFrame,
    inicio_padrao: datetime,
) -> pd.DataFrame:
    nomes = catalogo["nome"].tolist()
    inicial = pd.DataFrame(
        {
            "Procedimento": pd.Series([nomes[0]], dtype="string"),
            "Quantidade": pd.Series([1], dtype="int64"),
            "Tempo real (min)": pd.Series(
                [int(catalogo.iloc[0]["tempo_medio_minutos"])], dtype="int64"
            ),
            "Início": pd.Series([inicio_padrao], dtype="datetime64[ns]"),
            "Observação": pd.Series([""], dtype="string"),
            "Faturado": pd.Series([False], dtype="bool"),
        }
    )
    return st.data_editor(
        inicial,
        key="atendimento_completo_procedimentos",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "Procedimento": st.column_config.SelectboxColumn(
                "Procedimento", options=nomes, required=True
            ),
            "Quantidade": st.column_config.NumberColumn(
                "Quantidade", min_value=1, step=1, required=True
            ),
            "Tempo real (min)": st.column_config.NumberColumn(
                "Tempo real (min)", min_value=1, step=1, required=True
            ),
            "Início": st.column_config.DatetimeColumn(
                "Início", format="DD/MM/YYYY HH:mm", required=True
            ),
            "Observação": st.column_config.TextColumn("Observação"),
            "Faturado": st.column_config.CheckboxColumn("Faturado"),
        },
    )


def pagina_atendimento_completo() -> None:
    cabecalho_pagina(
        "Atendimentos",
        "Atendimento completo",
        "Registre atendimento e procedimentos em uma única transação atômica.",
    )
    pacientes = listar_pacientes()
    residentes = listar_atuacoes("residente")
    preceptores = listar_atuacoes("preceptor")
    unidades = listar_unidades()
    catalogo = listar_procedimentos_catalogo()
    if any(
        item.empty
        for item in (pacientes, residentes, preceptores, unidades, catalogo)
    ):
        mostrar_estado_vazio(
            "Pré-requisitos incompletos",
            "São necessários pacientes, profissionais, unidades e procedimentos.",
        )
        return

    agora = datetime.now().replace(second=0, microsecond=0)
    with st.form("form_atendimento_completo", border=True):
        with st.container(horizontal=True, gap="medium"):
            with st.container(width="stretch"):
                data_atendimento = st.date_input("Data", value=agora.date())
                hora_atendimento = st.time_input("Hora", value=agora.time())
                duracao = st.number_input(
                    "Duração em minutos", min_value=1, value=30, step=5
                )
                paciente = st.selectbox(
                    "Paciente",
                    pacientes.itertuples(),
                    format_func=lambda item: f"{item.nome} (id {item.id})",
                )
            with st.container(width="stretch"):
                residente = st.selectbox(
                    "Residente (atuação)",
                    residentes.itertuples(),
                    format_func=lambda item: label_atuacao(
                        pd.Series(item._asdict())
                    ),
                )
                preceptor = st.selectbox(
                    "Preceptor (atuação)",
                    preceptores.itertuples(),
                    format_func=lambda item: label_atuacao(
                        pd.Series(item._asdict())
                    ),
                )
                unidade = st.selectbox(
                    "Unidade",
                    unidades.itertuples(),
                    format_func=lambda item: f"{item.nome} ({item.tipo})",
                )

        st.subheader("Procedimentos")
        st.caption("Adicione ou remova linhas. Cada procedimento pode aparecer uma vez.")
        procedimentos_df = _editor_procedimentos(catalogo, agora)
        enviar = st.form_submit_button(
            "Registrar atendimento completo",
            type="primary",
            icon=":material/add_circle:",
            width="stretch",
        )

    if not enviar:
        return
    data_hora = datetime.combine(data_atendimento, hora_atendimento)
    linhas = procedimentos_df.dropna(subset=["Procedimento"])
    if linhas.empty:
        st.error("Informe pelo menos um procedimento.", icon=":material/error:")
        return
    if linhas["Procedimento"].duplicated().any():
        st.error("Remova procedimentos duplicados.", icon=":material/error:")
        return
    if linhas["Início"].isna().any() or any(
        pd.Timestamp(valor).to_pydatetime() < data_hora for valor in linhas["Início"]
    ):
        st.error(
            "O início de cada procedimento deve ser igual ou posterior ao atendimento.",
            icon=":material/error:",
        )
        return

    ids_por_nome = dict(zip(catalogo["nome"], catalogo["id"], strict=True))
    itens = tuple(
        ProcedimentoCompletoInput(
            id_procedimento=int(ids_por_nome[row["Procedimento"]]),
            quantidade=int(row["Quantidade"]),
            tempo_real_minutos=int(row["Tempo real (min)"]),
            data_hora_inicio=pd.Timestamp(row["Início"]).to_pydatetime(),
            observacao=str(row["Observação"]).strip() or None,
            faturado=bool(row["Faturado"]),
        )
        for _, row in linhas.iterrows()
    )
    entrada = AtendimentoCompletoInput(
        data_hora=data_hora,
        duracao_minutos=int(duracao),
        id_paciente=int(paciente.id),
        id_atuacao_residente=int(residente.id),
        id_atuacao_preceptor=int(preceptor.id),
        id_unidade=int(unidade.id),
        procedimentos=itens,
    )
    with st.spinner("Registrando transação completa...", show_time=True):
        id_criado = executar_escrita(registrar_atendimento_completo, entrada)
    st.success(
        f"Atendimento {id_criado} e {len(itens)} procedimento(s) registrados.",
        icon=":material/check_circle:",
    )


def pagina_reajustar_escala() -> None:
    cabecalho_pagina(
        "Operações da Etapa 2",
        "Reajustar escala",
        "Mova todas as escalas de uma origem para um destino validado atomicamente.",
    )
    escalas = listar_escalas_origem()
    if escalas.empty:
        mostrar_estado_vazio("Nenhuma escala", "Não existem escalas para reajustar.")
        return
    origem = st.selectbox(
        "Escala de origem",
        escalas.itertuples(),
        format_func=lambda item: (
            f"{item.residente} · {item.data_plantao} · "
            f"{ROTULOS_TURNO[item.turno]} · {item.unidade}"
        ),
    )
    with st.form("form_reajustar_escala", border=True):
        data_destino = st.date_input(
            "Data de destino", value=max(date.today(), origem.data_plantao) + timedelta(days=1)
        )
        turno_destino = st.selectbox(
            "Turno de destino", TURNOS, format_func=ROTULOS_TURNO.get
        )
        confirmar = st.checkbox(
            "Confirmo o reajuste de todas as escalas desta origem"
        )
        executar = st.form_submit_button(
            "Reajustar escala",
            type="primary",
            icon=":material/event_repeat:",
        )
    if executar:
        if not confirmar:
            st.warning("Confirme o reajuste antes de continuar.")
            return
        resultado = executar_escrita(
            reajustar_escala,
            id_atuacao_residente=int(origem.id_atuacao_residente),
            data_origem=origem.data_plantao,
            turno_origem=origem.turno,
            data_destino=data_destino,
            turno_destino=turno_destino,
        )
        st.success(
            f"{resultado.quantidade_atualizada} escala(s) reajustada(s).",
            icon=":material/check_circle:",
        )


def _mostrar_tabela(df: pd.DataFrame, titulo_vazio: str) -> None:
    if df.empty:
        mostrar_estado_vazio(titulo_vazio, "A consulta não retornou registros.")
    else:
        mostrar_metricas([("Registros", len(df), None)])
        st.dataframe(df, hide_index=True, width="stretch")


def pagina_painel_etapa2() -> None:
    cabecalho_pagina(
        "Consultas da Etapa 2",
        "Painel da Etapa 2",
        "Cada opção executa somente a consulta atualmente selecionada.",
    )
    opcoes = (
        "Pacientes internados",
        "Supervisão inadequada",
        "Estatísticas mensais",
        "Preceptores e flamenguistas",
        "Últimos atendimentos",
        "Alto risco por residente",
        "Média de espera",
    )
    escolha = st.selectbox("Consulta", opcoes, key="painel_etapa2_consulta")

    if escolha == "Pacientes internados":
        df = run_query(
            "SELECT * FROM vw_pacientes_internados ORDER BY data_internacao DESC"
        )
    elif escolha == "Supervisão inadequada":
        df = run_query(
            """
            SELECT * FROM vw_residentes_sem_supervisor
            ORDER BY data_plantao DESC, turno, residente
            """
        )
    elif escolha == "Estatísticas mensais":
        df = run_query(
            """
            SELECT * FROM vw_estatisticas_atendimentos_mensal
            ORDER BY ano DESC, mes DESC, unidade
            """
        )
    elif escolha == "Preceptores e flamenguistas":
        df = dto_dataframe(
            executar_leitura(preceptores_de_pacientes_flamenguistas)
        )
    elif escolha == "Últimos atendimentos":
        df = dto_dataframe(executar_leitura(ultimos_atendimentos_por_paciente))
        if not df.empty:
            df["procedimentos"] = df["procedimentos"].map(
                lambda itens: ", ".join(
                    f"{item['nome']} ({item['quantidade']}x)" for item in itens
                ) or "Nenhum"
            )
    elif escolha == "Alto risco por residente":
        df = dto_dataframe(
            executar_leitura(percentual_alto_risco_por_residente)
        )
    else:
        df = dto_dataframe(executar_leitura(calcular_tempo_medio_espera))
    _mostrar_tabela(df, "Sem dados para esta consulta")


def pagina_evidencias_tecnicas() -> None:
    cabecalho_pagina(
        "Demonstração",
        "Evidências técnicas",
        "Inspecione triggers, auditoria, loading ORM e concorrência com dados reais.",
    )
    escolha = st.selectbox(
        "Evidência",
        ("Triggers", "Auditoria", "Médias", "Lazy e eager", "Concorrência"),
        key="evidencias_tipo",
    )
    if escolha == "Triggers":
        df = run_query(
            """
            SELECT tgname AS trigger, relname AS tabela, tgenabled = 'O' AS ativo
            FROM pg_trigger
            JOIN pg_class ON pg_class.oid = pg_trigger.tgrelid
            WHERE NOT tgisinternal
              AND tgname IN (
                  'trg_check_sobreposicao_escala',
                  'trg_audita_atendimento',
                  'trg_atualiza_media_procedimentos'
              )
            ORDER BY tgname
            """
        )
        _mostrar_tabela(df, "Triggers não encontrados")
    elif escolha == "Auditoria":
        df = run_query(
            """
            SELECT id_auditoria, id_atendimento, operacao, usuario,
                   data_hora, dados_antigos, dados_novos
            FROM auditoria_atendimento
            ORDER BY id_auditoria DESC
            LIMIT 100
            """
        )
        _mostrar_tabela(df, "Auditoria vazia")
    elif escolha == "Médias":
        df = run_query(
            """
            SELECT codigo, nome, nivel_risco, tempo_medio_minutos,
                   media_tempo_procedimento
            FROM procedimento
            ORDER BY nome
            """
        )
        _mostrar_tabela(df, "Procedimentos não encontrados")
    elif escolha == "Lazy e eager":
        pacientes = listar_pacientes()
        paciente = st.selectbox(
            "Paciente para medição",
            pacientes.itertuples(),
            format_func=lambda item: f"{item.nome} (id {item.id})",
        )
        resultado = medir_lazy_e_eager(
            get_session_factory(), int(paciente.id)
        )
        mostrar_metricas(
            [
                ("Consultas lazy", resultado.consultas_lazy, None),
                ("Consultas eager", resultado.consultas_eager, None),
                ("Atendimentos", resultado.atendimentos_carregados, None),
            ]
        )
        st.info(
            "O eager loading carrega pessoa e atendimentos em uma consulta; "
            "o lazy loading busca os relacionamentos quando acessados.",
            icon=":material/info:",
        )
    else:
        st.warning(
            "A demonstração cria escalas temporárias, executa duas transações "
            "e remove os registros auxiliares ao final.",
            icon=":material/warning:",
        )
        confirmar = st.checkbox("Confirmo a execução da demonstração concorrente")
        executar = st.button(
            "Executar concorrência",
            type="primary",
            icon=":material/lock_clock:",
            disabled=not confirmar,
        )
        if executar:
            with st.status("Executando duas transações...", expanded=True) as status:
                resultado = demonstrar_concorrencia_escala(get_session_factory())
                for mensagem in resultado.logs:
                    st.write(mensagem)
                status.update(label="Demonstração concluída", state="complete")
            mostrar_metricas(
                [
                    ("Confirmadas", resultado.confirmadas, None),
                    ("Rejeitadas", resultado.rejeitadas, None),
                    ("Escalas no destino", resultado.escalas_no_destino, None),
                ]
            )
            st.success(
                "A segunda sessão aguardou o lock e somente uma operação confirmou.",
                icon=":material/check_circle:",
            )
