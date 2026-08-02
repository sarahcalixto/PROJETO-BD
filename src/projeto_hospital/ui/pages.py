"""Páginas e navegação do painel Streamlit."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    atualizar_convenio_paciente,
    calcular_tempo_medio_por_residente,
    listar_atendimentos_paciente,
    listar_procedimentos_atendimento,
    pacientes_sem_procedimento_alto_risco,
    plantoes_por_unidade_e_residente,
    preceptores_com_mais_de_cinco_atendimentos,
    ranking_residentes_por_atendimentos,
    remover_procedimento_nao_faturado,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    executar_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
    mostrar_metricas,
)
from projeto_hospital.ui.data import (
    carregar_visao_geral,
    dto_dataframe,
    executar_escrita,
    executar_leitura,
    listar_atendimentos_ids,
    listar_pacientes,
)

PAGES_DIR = Path(__file__).parents[3] / "frontend" / "app_pages"


def label_atuacao(row: pd.Series) -> str:
    fim = row["data_fim"] if row["data_fim"] is not None else "atual"
    return f"{row['nome']} (id {row['id']}, {row['data_inicio']} → {fim})"


def formatar_inteiro(valor: object) -> str:
    """Formata contagens vindas do PostgreSQL sem expor casas decimais."""
    return f"{int(valor):,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------


def pagina_visao_geral() -> None:
    cabecalho_pagina(
        "Visão geral",
        "Painel hospitalar",
        "Acompanhe os principais números operacionais e os atendimentos mais recentes.",
    )

    with st.spinner("Atualizando indicadores...", show_time=True):
        indicadores, recentes = carregar_visao_geral()

    resumo = indicadores.iloc[0]
    mostrar_metricas(
        [
            ("Pacientes", formatar_inteiro(resumo["total_pacientes"]), "Pacientes cadastrados"),
            (
                "Atendimentos hoje",
                formatar_inteiro(resumo["atendimentos_hoje"]),
                "Atendimentos na data atual",
            ),
            ("Unidades", formatar_inteiro(resumo["total_unidades"]), "Unidades cadastradas"),
            (
                "Procedimentos",
                formatar_inteiro(resumo["procedimentos_realizados"]),
                "Procedimentos realizados registrados",
            ),
        ]
    )

    st.subheader("Atendimentos recentes")
    st.caption("Últimos oito registros, ordenados da ocorrência mais recente para a mais antiga.")
    if recentes.empty:
        mostrar_estado_vazio(
            "Nenhum atendimento registrado",
            "Os atendimentos inseridos aparecerão aqui automaticamente.",
        )
        return

    st.dataframe(
        recentes,
        hide_index=True,
        width="stretch",
        column_order=[
            "id_atendimento",
            "data_hora",
            "paciente",
            "unidade",
            "duracao_minutos",
        ],
        column_config={
            "id_atendimento": st.column_config.NumberColumn("ID", format="%d"),
            "data_hora": st.column_config.DatetimeColumn(
                "Data e hora", format="DD/MM/YYYY HH:mm"
            ),
            "paciente": st.column_config.TextColumn("Paciente"),
            "unidade": st.column_config.TextColumn("Unidade"),
            "duracao_minutos": st.column_config.NumberColumn(
                "Duração", format="%d min"
            ),
        },
    )


def pagina_atendimentos_paciente() -> None:
    cabecalho_pagina(
        "Consultas",
        "Atendimentos por paciente",
        "Selecione um paciente para consultar seu histórico de atendimentos.",
    )

    with st.spinner("Carregando pacientes...", show_time=True):
        pacientes = listar_pacientes()
    if pacientes.empty:
        mostrar_estado_vazio(
            "Nenhum paciente cadastrado",
            "Cadastre um paciente para consultar seu histórico.",
        )
        return

    with st.container(border=True):
        paciente = st.selectbox(
            "Paciente",
            pacientes.itertuples(),
            format_func=lambda r: f"{r.nome} (id {r.id})",
        )

    with st.spinner("Buscando atendimentos...", show_time=True):
        df = dto_dataframe(
            executar_leitura(listar_atendimentos_paciente, int(paciente.id))
        )

    if df.empty:
        mostrar_estado_vazio(
            "Histórico vazio",
            "Este paciente ainda não possui atendimentos registrados.",
        )
        return

    mostrar_metricas(
        [
            ("Atendimentos", len(df), "Total encontrado para o paciente"),
            (
                "Tempo total",
                f"{int(df['duracao_minutos'].sum())} min",
                "Soma das durações",
            ),
            (
                "Duração média",
                f"{df['duracao_minutos'].mean():.1f} min",
                "Média das durações registradas",
            ),
        ]
    )
    st.subheader("Histórico")
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "id_atendimento": st.column_config.NumberColumn("Atendimento", format="%d"),
            "data_hora": st.column_config.DatetimeColumn(
                "Data e hora", format="DD/MM/YYYY HH:mm"
            ),
            "duracao_minutos": st.column_config.NumberColumn(
                "Duração", format="%d min"
            ),
            "id_atuacao_residente": st.column_config.NumberColumn(
                "Atuação residente", format="%d"
            ),
            "id_atuacao_preceptor": st.column_config.NumberColumn(
                "Atuação preceptora", format="%d"
            ),
            "id_unidade": st.column_config.NumberColumn("Unidade", format="%d"),
        },
    )


def pagina_procedimentos_atendimento() -> None:
    cabecalho_pagina(
        "Consultas",
        "Procedimentos por atendimento",
        "Consulte procedimentos, quantidades, tempos registrados e situação de faturamento.",
    )

    with st.spinner("Carregando atendimentos...", show_time=True):
        atendimentos = listar_atendimentos_ids()
    if atendimentos.empty:
        mostrar_estado_vazio(
            "Nenhum atendimento cadastrado",
            "Registre um atendimento antes de consultar procedimentos.",
        )
        return

    with st.container(border=True):
        atendimento = st.selectbox(
            "Atendimento",
            atendimentos.itertuples(),
            format_func=lambda r: f"id {r.id} — {r.paciente} — {r.data_hora}",
        )

    with st.spinner("Buscando procedimentos...", show_time=True):
        df = dto_dataframe(
            executar_leitura(
                listar_procedimentos_atendimento,
                int(atendimento.id),
            )
        )

    if df.empty:
        mostrar_estado_vazio(
            "Nenhum procedimento encontrado",
            "Este atendimento não possui procedimentos registrados.",
        )
        return

    mostrar_metricas(
        [
            ("Tipos de procedimento", len(df), None),
            ("Quantidade total", int(df["quantidade"].sum()), None),
            ("Tempo registrado", f"{int(df['tempo_real_minutos'].sum())} min", None),
        ]
    )
    st.subheader("Procedimentos realizados")
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "id_procedimento": st.column_config.NumberColumn("ID", format="%d"),
            "nome": st.column_config.TextColumn("Procedimento"),
            "quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
            "tempo_real_minutos": st.column_config.NumberColumn(
                "Tempo real", format="%d min"
            ),
            "faturado": st.column_config.CheckboxColumn(
                "Faturado", disabled=True
            ),
            "observacao": st.column_config.TextColumn("Observação"),
        },
    )


def pagina_atualizar_paciente() -> None:
    cabecalho_pagina(
        "Pacientes",
        "Atualizar convênio",
        "Altere o número de convênio associado a um paciente cadastrado.",
    )

    with st.spinner("Carregando pacientes...", show_time=True):
        pacientes = listar_pacientes()
    if pacientes.empty:
        mostrar_estado_vazio(
            "Nenhum paciente cadastrado",
            "Cadastre um paciente antes de atualizar o convênio.",
        )
        return

    paciente = st.selectbox(
        "Paciente",
        pacientes.itertuples(),
        format_func=lambda r: f"{r.nome} (convênio atual: {r.num_convenio or '—'})",
    )

    with st.form("form_atualizar_convenio", border=True):
        st.caption(f"Paciente selecionado: **{paciente.nome}**")
        novo_convenio = st.text_input(
            "Novo número de convênio",
            value=paciente.num_convenio or "",
            placeholder="Informe o identificador do convênio",
        )
        atualizar = st.form_submit_button(
            "Salvar alteração",
            type="primary",
            icon=":material/save:",
        )

    if atualizar:
        try:
            with st.spinner("Atualizando convênio...", show_time=True):
                resultado = executar_escrita(
                    atualizar_convenio_paciente,
                    int(paciente.id),
                    novo_convenio or None,
                )
            st.success(
                f"Convênio atualizado para “{resultado.num_convenio or 'não informado'}”.",
                icon=":material/check_circle:",
            )
        except (psycopg.Error, SQLAlchemyError) as exc:
            mostrar_erro_banco(exc, "Não foi possível atualizar o convênio.")


def _confirmar_remocao(atendimento_id: int, procedimento_id: int, nome: str) -> None:
    @st.dialog("Confirmar remoção", icon=":material/delete:")
    def dialogo() -> None:
        st.warning(
            "Esta ação remove definitivamente o vínculo do procedimento com o atendimento.",
            icon=":material/warning:",
        )
        st.write(f"**Atendimento:** {atendimento_id}")
        st.write(f"**Procedimento:** {nome}")
        with st.container(
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
        ):
            cancelar = st.button("Cancelar", width="stretch")
            confirmar = st.button(
                "Confirmar remoção",
                type="primary",
                icon=":material/delete_forever:",
                width="stretch",
            )
        if confirmar:
            try:
                with st.spinner("Removendo procedimento...", show_time=True):
                    resultado = executar_escrita(
                        remover_procedimento_nao_faturado,
                        atendimento_id,
                        procedimento_id,
                    )
                st.session_state["mensagem_remocao"] = (
                    f"Procedimento {resultado.id_procedimento} removido com sucesso."
                )
                st.rerun()
            except (psycopg.Error, SQLAlchemyError) as exc:
                mostrar_erro_banco(exc, "Não foi possível remover o procedimento.")
        if cancelar:
            st.rerun()

    dialogo()


def pagina_remover_procedimento() -> None:
    cabecalho_pagina(
        "Administração",
        "Remover procedimento",
        "Remova apenas procedimentos ainda não faturados, com confirmação explícita.",
    )

    if mensagem := st.session_state.pop("mensagem_remocao", None):
        st.success(mensagem, icon=":material/check_circle:")

    with st.spinner("Carregando atendimentos...", show_time=True):
        atendimentos = listar_atendimentos_ids()
    if atendimentos.empty:
        mostrar_estado_vazio(
            "Nenhum atendimento cadastrado",
            "Não há procedimentos disponíveis para remoção.",
        )
        return

    with st.container(border=True):
        atendimento = st.selectbox(
            "Atendimento",
            atendimentos.itertuples(),
            format_func=lambda r: f"id {r.id} — {r.paciente} — {r.data_hora}",
            key="atendimento_remover",
        )

        with st.spinner("Carregando procedimentos...", show_time=True):
            procedimentos = dto_dataframe(
                executar_leitura(
                    listar_procedimentos_atendimento,
                    int(atendimento.id),
                )
            )

        if procedimentos.empty:
            mostrar_estado_vazio(
                "Nenhum procedimento registrado",
                "Este atendimento não possui procedimentos para remover.",
            )
            return

        procedimento = st.selectbox(
            "Procedimento",
            procedimentos.itertuples(),
            format_func=lambda r: (
                f"{r.nome} — {'faturado' if r.faturado else 'não faturado'}"
            ),
        )

        if procedimento.faturado:
            st.warning(
                "Este procedimento já foi faturado e não pode ser removido.",
                icon=":material/lock:",
            )
        remover = st.button(
            "Revisar e remover",
            type="primary",
            icon=":material/delete:",
            disabled=bool(procedimento.faturado),
        )

    if remover:
        _confirmar_remocao(
            int(atendimento.id),
            int(procedimento.id_procedimento),
            procedimento.nome,
        )


def pagina_tempo_medio_residente() -> None:
    cabecalho_pagina(
        "Análises",
        "Tempo médio por residente",
        "Compare a duração média dos atendimentos realizados por cada residente.",
    )

    with st.spinner("Calculando tempos médios...", show_time=True):
        df = dto_dataframe(executar_leitura(calcular_tempo_medio_por_residente))

    if df.empty:
        mostrar_estado_vazio(
            "Dados insuficientes",
            "Ainda não há atendimentos válidos para calcular as médias.",
        )
        return

    df["tempo_medio_minutos"] = df["tempo_medio_minutos"].astype(float)
    mostrar_metricas(
        [
            ("Residentes analisados", len(df), None),
            (
                "Média geral",
                f"{df['tempo_medio_minutos'].mean():.1f} min",
                "Média dos resultados por residente",
            ),
            (
                "Maior média",
                f"{df['tempo_medio_minutos'].max():.1f} min",
                None,
            ),
        ]
    )

    with st.container(horizontal=True, gap="medium"):
        with st.container(border=True, width="stretch"):
            st.subheader("Comparativo")
            st.bar_chart(
                df,
                x="nome_profissional",
                y="tempo_medio_minutos",
                x_label="Residente",
                y_label="Minutos",
                color="#0f766e",
                horizontal=True,
                height=380,
            )
        with st.container(border=True, width="stretch"):
            st.subheader("Detalhamento")
            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config={
                    "id_atuacao_residente": st.column_config.NumberColumn(
                        "Atuação", format="%d"
                    ),
                    "nome_profissional": st.column_config.TextColumn("Residente"),
                    "tempo_medio_minutos": st.column_config.NumberColumn(
                        "Tempo médio", format="%.1f min"
                    ),
                },
            )


def mostrar_ranking_residentes() -> None:
    with st.spinner("Montando ranking...", show_time=True):
        df = dto_dataframe(executar_leitura(ranking_residentes_por_atendimentos))
    if df.empty:
        mostrar_estado_vazio(
            "Ranking indisponível",
            "Nenhum residente foi encontrado para compor o ranking.",
        )
        return

    mostrar_metricas(
        [
            ("Residentes", len(df), None),
            (
                "Atendimentos contabilizados",
                int(df["total_atendimentos"].sum()),
                None,
            ),
        ]
    )
    with st.container(horizontal=True, gap="medium"):
        with st.container(border=True, width="stretch"):
            st.bar_chart(
                df,
                x="nome",
                y="total_atendimentos",
                x_label="Residente",
                y_label="Atendimentos",
                color="#0f766e",
                horizontal=True,
                height=360,
            )
        with st.container(border=True, width="stretch"):
            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config={
                    "nome": st.column_config.TextColumn("Residente"),
                    "total_atendimentos": st.column_config.NumberColumn(
                        "Atendimentos", format="%d"
                    ),
                },
            )


def mostrar_supervisao_mensal() -> None:
    with st.container(border=True):
        mes_referencia = st.date_input(
            "Mês de referência",
            value=date.today().replace(day=1),
            key="mes_preceptores",
            help="A consulta considera o mês correspondente à data escolhida.",
        )
    with st.spinner("Consultando supervisões...", show_time=True):
        df = dto_dataframe(
            executar_leitura(
                preceptores_com_mais_de_cinco_atendimentos,
                mes_referencia,
            )
        )
    if df.empty:
        mostrar_estado_vazio(
            "Nenhum resultado para o período",
            "Nenhum preceptor supervisionou mais de cinco atendimentos nesse mês.",
        )
        return

    mostrar_metricas(
        [
            ("Preceptores encontrados", len(df), None),
            (
                "Supervisões contabilizadas",
                int(df["total_supervisionado"].sum()),
                None,
            ),
        ]
    )
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "nome": st.column_config.TextColumn("Preceptor"),
            "total_supervisionado": st.column_config.NumberColumn(
                "Atendimentos supervisionados", format="%d"
            ),
        },
    )


def mostrar_plantoes_unidade() -> None:
    with st.spinner("Consultando escalas...", show_time=True):
        df = dto_dataframe(
            executar_leitura(plantoes_por_unidade_e_residente, date.today())
        )
    if df.empty:
        mostrar_estado_vazio(
            "Nenhuma escala encontrada",
            "Não há unidades ou plantões disponíveis para o mês corrente.",
        )
        return

    mostrar_metricas(
        [
            ("Unidades", df["unidade"].nunique(), None),
            ("Plantões no mês", int(df["quantidade_plantoes"].sum()), None),
        ]
    )
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "unidade": st.column_config.TextColumn("Unidade"),
            "residente": st.column_config.TextColumn(
                "Residente", default="Sem escala"
            ),
            "quantidade_plantoes": st.column_config.NumberColumn(
                "Plantões", format="%d"
            ),
        },
    )


def mostrar_pacientes_sem_alto_risco() -> None:
    with st.spinner("Analisando histórico de risco...", show_time=True):
        df = dto_dataframe(
            executar_leitura(pacientes_sem_procedimento_alto_risco)
        )
    if df.empty:
        mostrar_estado_vazio(
            "Nenhum paciente encontrado",
            "Todos os pacientes possuem ao menos um procedimento de alto risco.",
        )
        return

    mostrar_metricas(
        [("Pacientes sem procedimento de alto risco", len(df), None)]
    )
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "nome": st.column_config.TextColumn("Paciente"),
            "num_convenio": st.column_config.TextColumn(
                "Convênio", default="Não informado"
            ),
        },
    )


def pagina_consultas_analiticas() -> None:
    cabecalho_pagina(
        "Análises",
        "Consultas analíticas",
        "Explore rankings, supervisões, plantões e indicadores de risco em quatro perspectivas.",
    )

    tabs = st.tabs(
        ["Ranking", "Supervisão", "Plantões", "Risco"],
        key="consultas_analiticas_tabs",
        on_change="rerun",
    )
    renderizadores = (
        mostrar_ranking_residentes,
        mostrar_supervisao_mensal,
        mostrar_plantoes_unidade,
        mostrar_pacientes_sem_alto_risco,
    )
    for tab, renderizar in zip(tabs, renderizadores, strict=True):
        if tab.open:
            with tab:
                renderizar()


# ---------------------------------------------------------------------------
# Navegação
# ---------------------------------------------------------------------------


def criar_navegacao() -> st.navigation:
    """Cria a navegação agrupada usando scripts de página Streamlit."""
    paginas = {
        "Início": [
            st.Page(
                str(PAGES_DIR / "visao_geral.py"),
                title="Visão geral",
                icon=":material/dashboard:",
                url_path="inicio",
                default=True,
            )
        ],
        "Atendimentos": [
            st.Page(
                str(PAGES_DIR / "novo_atendimento.py"),
                title="Atendimento completo",
                icon=":material/add_circle:",
                url_path="atendimento-completo",
            ),
            st.Page(
                str(PAGES_DIR / "historico_paciente.py"),
                title="Histórico do paciente",
                icon=":material/clinical_notes:",
                url_path="historico-paciente",
            ),
            st.Page(
                str(PAGES_DIR / "procedimentos.py"),
                title="Procedimentos",
                icon=":material/medical_services:",
                url_path="procedimentos",
            ),
        ],
        "Pacientes": [
            st.Page(
                str(PAGES_DIR / "atualizar_convenio.py"),
                title="Atualizar convênio",
                icon=":material/edit:",
                url_path="atualizar-convenio",
            )
        ],
        "Análises": [
            st.Page(
                str(PAGES_DIR / "tempo_residente.py"),
                title="Tempo por residente",
                icon=":material/timer:",
                url_path="tempo-residente",
            ),
            st.Page(
                str(PAGES_DIR / "consultas_analiticas.py"),
                title="Consultas analíticas",
                icon=":material/monitoring:",
                url_path="consultas-analiticas",
            ),
        ],
        "Etapa 2": [
            st.Page(
                str(PAGES_DIR / "reajustar_escala.py"),
                title="Reajustar escala",
                icon=":material/calendar_month:",
                url_path="reajustar-escala",
            ),
            st.Page(
                str(PAGES_DIR / "painel_etapa2.py"),
                title="Painel da Etapa 2",
                icon=":material/query_stats:",
                url_path="painel-etapa2",
            ),
            st.Page(
                str(PAGES_DIR / "evidencias_tecnicas.py"),
                title="Evidências técnicas",
                icon=":material/fact_check:",
                url_path="evidencias-tecnicas",
            ),
        ],
        "Administração": [
            st.Page(
                str(PAGES_DIR / "remover_procedimento.py"),
                title="Remover procedimento",
                icon=":material/delete:",
                url_path="remover-procedimento",
            )
        ],
    }
    return st.navigation(paginas, position="sidebar", expanded=True)
