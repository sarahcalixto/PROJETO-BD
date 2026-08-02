"""Operações, consultas e evidências visuais da Etapa 2."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from math import isfinite

import pandas as pd
import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    AtendimentoCompletoInput,
    ProcedimentoCompletoInput,
    RegraNegocioViolada,
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
    mostrar_erro_banco,
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
) -> pd.DataFrame:
    opcoes = [f"{int(item.codigo)} — {item.nome}" for item in catalogo.itertuples()]
    inicial = pd.DataFrame({
        "Procedimento": pd.Series(dtype="string"),
        "Quantidade": pd.Series(dtype="Int64"),
        "Tempo real (min)": pd.Series(dtype="Int64"),
        "Início": pd.Series(dtype="datetime64[ns]"),
        "Observação": pd.Series(dtype="string"),
    })
    return st.data_editor(
        inicial,
        key="atendimento_completo_procedimentos",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "Procedimento": st.column_config.SelectboxColumn(
                "Procedimento *", options=opcoes, required=True
            ),
            "Quantidade": st.column_config.NumberColumn(
                "Quantidade *", min_value=1, max_value=9999, step=1, required=True
            ),
            "Tempo real (min)": st.column_config.NumberColumn(
                "Tempo real (min) *", min_value=1, max_value=1440, step=1, required=True
            ),
            "Início": st.column_config.DatetimeColumn(
                "Início *", format="DD/MM/YYYY HH:mm", required=True
            ),
            "Observação": st.column_config.TextColumn(
                "Observação (opcional)",
                help="Preencha somente quando houver intercorrência ou informação relevante.",
            ),
        },
    )


def _ausente(valor: object) -> bool:
    if valor is None:
        return True
    try:
        return bool(pd.isna(valor))
    except (TypeError, ValueError):
        return False


def _linha_vazia(row: pd.Series) -> bool:
    observacao = row.get("Observação")
    valores = (
        row.get("Procedimento"),
        row.get("Quantidade"),
        row.get("Tempo real (min)"),
        row.get("Início"),
    )
    return all(_ausente(valor) for valor in valores) and (
        _ausente(observacao) or not str(observacao).strip()
    )


def _inteiro_positivo(valor: object, campo: str, linha: int) -> int:
    if _ausente(valor):
        raise RegraNegocioViolada(f"Preencha {campo} na linha {linha}.")
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise RegraNegocioViolada(
            f"{campo.capitalize()} inválido na linha {linha}."
        ) from exc
    if not isfinite(numero) or not numero.is_integer() or numero <= 0:
        raise RegraNegocioViolada(
            f"{campo.capitalize()} deve ser um inteiro positivo na linha {linha}."
        )
    return int(numero)


def _preparar_procedimentos(
    procedimentos_df: pd.DataFrame,
    catalogo: pd.DataFrame,
    data_hora: datetime,
    duracao_minutos: int,
) -> tuple[ProcedimentoCompletoInput, ...]:
    linhas = [row for _, row in procedimentos_df.iterrows() if not _linha_vazia(row)]
    if not linhas:
        raise RegraNegocioViolada("Informe pelo menos um procedimento.")

    ids_por_rotulo = {
        f"{int(item.codigo)} — {item.nome}": int(item.id)
        for item in catalogo.itertuples()
    }
    itens: list[ProcedimentoCompletoInput] = []
    ids_informados: set[int] = set()
    fim_atendimento = data_hora + timedelta(minutes=duracao_minutos)

    for posicao, row in enumerate(linhas, start=1):
        rotulo = row.get("Procedimento")
        if _ausente(rotulo) or rotulo not in ids_por_rotulo:
            raise RegraNegocioViolada(
                f"Selecione um procedimento válido na linha {posicao}."
            )
        quantidade = _inteiro_positivo(row.get("Quantidade"), "a quantidade", posicao)
        tempo_real = _inteiro_positivo(
            row.get("Tempo real (min)"), "o tempo real", posicao
        )
        inicio_valor = row.get("Início")
        if _ausente(inicio_valor):
            raise RegraNegocioViolada(f"Preencha o início na linha {posicao}.")
        try:
            inicio = pd.Timestamp(inicio_valor).to_pydatetime()
        except (TypeError, ValueError) as exc:
            raise RegraNegocioViolada(
                f"Início inválido na linha {posicao}."
            ) from exc
        if inicio < data_hora:
            raise RegraNegocioViolada(
                f"O procedimento da linha {posicao} começa antes do atendimento."
            )
        if inicio + timedelta(minutes=tempo_real) > fim_atendimento:
            raise RegraNegocioViolada(
                f"O procedimento da linha {posicao} termina depois do atendimento."
            )

        id_procedimento = ids_por_rotulo[str(rotulo)]
        if id_procedimento in ids_informados:
            raise RegraNegocioViolada(
                f"O procedimento da linha {posicao} já foi informado."
            )
        ids_informados.add(id_procedimento)
        observacao_valor = row.get("Observação")
        observacao = (
            None
            if _ausente(observacao_valor) or not str(observacao_valor).strip()
            else str(observacao_valor).strip()
        )
        itens.append(
            ProcedimentoCompletoInput(
                id_procedimento=id_procedimento,
                quantidade=quantidade,
                tempo_real_minutos=tempo_real,
                data_hora_inicio=inicio,
                observacao=observacao,
                faturado=False,
            )
        )
    return tuple(itens)


def pagina_atendimento_completo() -> None:
    cabecalho_pagina(
        "Atendimentos",
        "Atendimento completo",
        "Registre atendimento e procedimentos em uma única transação atômica.",
    )
    agora = datetime.now().replace(second=0, microsecond=0)
    data_atendimento = st.date_input(
        "Data do atendimento *",
        value=agora.date(),
        help="A data define quais atuações profissionais estão vigentes.",
    )
    pacientes = listar_pacientes()
    residentes = listar_atuacoes("residente", data_atendimento)
    preceptores = listar_atuacoes("preceptor", data_atendimento)
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

    pacientes_por_id = {int(item.id): item for item in pacientes.itertuples()}
    residentes_por_id = {int(item.id): item for item in residentes.itertuples()}
    preceptores_por_id = {int(item.id): item for item in preceptores.itertuples()}
    unidades_por_id = {int(item.id): item for item in unidades.itertuples()}

    with st.form("form_atendimento_completo", border=True, clear_on_submit=True):
        with st.container(horizontal=True, gap="medium"):
            with st.container(width="stretch"):
                hora_atendimento = st.time_input("Hora *", value=agora.time())
                duracao = st.number_input(
                    "Duração em minutos *",
                    min_value=1,
                    max_value=1440,
                    value=None,
                    step=5,
                    placeholder="Informe a duração",
                )
                id_paciente = st.selectbox(
                    "Paciente *",
                    tuple(pacientes_por_id),
                    index=None,
                    placeholder="Selecione o paciente",
                    format_func=lambda identificador: (
                        f"{pacientes_por_id[identificador].nome} — convênio "
                        f"{pacientes_por_id[identificador].num_convenio or 'não informado'}"
                    ),
                )
            with st.container(width="stretch"):
                id_residente = st.selectbox(
                    "Residente (atuação) *",
                    tuple(residentes_por_id),
                    index=None,
                    placeholder="Selecione o residente",
                    format_func=lambda identificador: label_atuacao(
                        pd.Series(residentes_por_id[identificador]._asdict())
                    ),
                )
                id_preceptor = st.selectbox(
                    "Preceptor (atuação) *",
                    tuple(preceptores_por_id),
                    index=None,
                    placeholder="Selecione o preceptor",
                    format_func=lambda identificador: label_atuacao(
                        pd.Series(preceptores_por_id[identificador]._asdict())
                    ),
                )
                id_unidade = st.selectbox(
                    "Unidade *",
                    tuple(unidades_por_id),
                    index=None,
                    placeholder="Selecione a unidade",
                    format_func=lambda identificador: (
                        f"{unidades_por_id[identificador].nome} "
                        f"({unidades_por_id[identificador].tipo})"
                    ),
                )

        st.subheader("Procedimentos")
        st.caption(
            "Adicione pelo menos uma linha. Campos com * são obrigatórios e cada "
            "procedimento pode aparecer uma vez. Novos procedimentos começam não faturados."
        )
        procedimentos_df = _editor_procedimentos(catalogo)
        enviar = st.form_submit_button(
            "Registrar atendimento completo",
            type="primary",
            icon=":material/add_circle:",
            width="stretch",
        )

    if not enviar:
        return
    ausentes = [
        rotulo
        for rotulo, valor in (
            ("o paciente", id_paciente),
            ("o residente", id_residente),
            ("o preceptor", id_preceptor),
            ("a unidade", id_unidade),
            ("a duração", duracao),
        )
        if valor is None
    ]
    if ausentes:
        st.error(
            "Selecione ou informe " + ", ".join(ausentes) + ".",
            icon=":material/error:",
        )
        return
    data_hora = datetime.combine(data_atendimento, hora_atendimento)
    try:
        itens = _preparar_procedimentos(
            procedimentos_df, catalogo, data_hora, int(duracao)
        )
    except RegraNegocioViolada as exc:
        st.error(str(exc), icon=":material/error:")
        return
    entrada = AtendimentoCompletoInput(
        data_hora=data_hora,
        duracao_minutos=int(duracao),
        id_paciente=int(id_paciente),
        id_atuacao_residente=int(id_residente),
        id_atuacao_preceptor=int(id_preceptor),
        id_unidade=int(id_unidade),
        procedimentos=itens,
    )
    try:
        with st.spinner("Registrando transação completa...", show_time=True):
            id_criado = executar_escrita(registrar_atendimento_completo, entrada)
    except (psycopg.Error, SQLAlchemyError, RegraNegocioViolada) as exc:
        mostrar_erro_banco(exc, "Não foi possível registrar o atendimento.")
        return
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


def _mostrar_tabela(
    df: pd.DataFrame,
    titulo_vazio: str,
    *,
    exibir_ids_tecnicos: bool = False,
) -> None:
    if df.empty:
        mostrar_estado_vazio(titulo_vazio, "A consulta não retornou registros.")
    else:
        mostrar_metricas([("Registros", len(df), None)])
        visual = df
        if not exibir_ids_tecnicos:
            visual = df.loc[
                :,
                [not str(coluna).startswith("id_") for coluna in df.columns],
            ]
        st.dataframe(visual, hide_index=True, width="stretch")


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
        _mostrar_tabela(df, "Triggers não encontrados", exibir_ids_tecnicos=True)
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
        _mostrar_tabela(df, "Auditoria vazia", exibir_ids_tecnicos=True)
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
            format_func=lambda item: (
                f"{item.nome} — convênio {item.num_convenio or 'não informado'}"
            ),
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
