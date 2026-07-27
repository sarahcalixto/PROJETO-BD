"""Painel Streamlit do Sistema de Gestão Hospitalar."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import psycopg
import streamlit as st
from psycopg.rows import dict_row

# Permite importar o pacote existente em src/projeto_hospital.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from projeto_hospital.config import load_database_config  # noqa: E402

st.set_page_config(
    page_title="Hospital Dra. Yuska Maritan Brito",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Identidade visual e componentes compartilhados
# ---------------------------------------------------------------------------


def aplicar_estilos() -> None:
    """Aplica somente ajustes que complementam o tema nativo do Streamlit."""
    st.html(
        """
        <style>
        [data-testid="stMainBlockContainer"] {
            max-width: 1480px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(15, 118, 110, 0.14);
        }

        [data-testid="stSidebar"][aria-expanded="true"] [data-testid="stLogoLink"] {
            height: 4.5rem;
            align-items: center;
        }

        [data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarLogo"] {
            width: 15rem !important;
            height: auto !important;
            max-width: 100% !important;
            max-height: 3.75rem !important;
        }

        div[data-testid="stForm"],
        div[data-testid="stExpander"] {
            border-color: rgba(15, 118, 110, 0.16);
        }

        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.25rem;
            }

            [data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarLogo"] {
                width: 13.5rem !important;
            }
        }
        </style>
        """
    )


def cabecalho_pagina(categoria: str, titulo: str, descricao: str) -> None:
    """Renderiza um cabeçalho consistente para todas as páginas."""
    st.badge(categoria, color="primary")
    st.title(titulo)
    st.caption(descricao)


def mostrar_metricas(metricas: Sequence[tuple[str, str | int, str | None]]) -> None:
    """Mostra métricas em uma faixa que quebra linha em telas estreitas."""
    with st.container(horizontal=True, gap="small"):
        for rotulo, valor, ajuda in metricas:
            st.metric(rotulo, valor, help=ajuda, border=True, width="stretch")


def mostrar_estado_vazio(titulo: str, descricao: str) -> None:
    """Padroniza mensagens de ausência de resultados."""
    with st.container(border=True):
        st.info(
            f"**{titulo}**\n\n{descricao}",
            icon=":material/info:",
        )


def mostrar_erro_banco(
    exc: Exception,
    mensagem: str = "Não foi possível carregar os dados desta página.",
) -> None:
    """Apresenta uma mensagem amigável e mantém o detalhe técnico acessível."""
    st.error(mensagem, icon=":material/error:")
    with st.expander("Ver detalhes técnicos", icon=":material/code:"):
        st.code(str(exc), language=None)


def executar_pagina(pagina: Callable[[], None]) -> None:
    """Isola erros de leitura sem esconder falhas de programação."""
    try:
        pagina()
    except psycopg.Error as exc:
        mostrar_erro_banco(exc)


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def get_connection() -> psycopg.Connection:
    config = load_database_config()
    return psycopg.connect(row_factory=dict_row, **config.connection_kwargs)


def run_query(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
    """Executa SELECT e devolve o resultado como DataFrame."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except psycopg.Error:
        conn.rollback()
        raise


def run_command(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
    """Executa comando de escrita via função armazenada e confirma a transação."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall() if cur.description else []
        conn.commit()
        return pd.DataFrame(rows)
    except psycopg.Error:
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# Helpers de domínio
# ---------------------------------------------------------------------------


def listar_pacientes() -> pd.DataFrame:
    return run_query(
        """
        SELECT pac.id, pes.nome, pac.num_convenio, pac.grupo_sanguineo
        FROM paciente pac
        JOIN pessoa pes ON pes.id = pac.id
        ORDER BY pes.nome
        """
    )


def listar_atuacoes(tipo: str) -> pd.DataFrame:
    tabela = "atuacao_residente" if tipo == "residente" else "atuacao_preceptor"
    return run_query(
        f"""
        SELECT
            t.id,
            pes.nome,
            ap.data_inicio,
            ap.data_fim
        FROM {tabela} t
        JOIN atuacao_profissional ap ON ap.id = t.id
        JOIN profissional prof ON prof.id = ap.id_profissional
        JOIN pessoa pes ON pes.id = prof.id
        ORDER BY pes.nome
        """
    )


def listar_unidades() -> pd.DataFrame:
    return run_query("SELECT id, nome, tipo FROM unidade ORDER BY nome")


def listar_atendimentos_ids() -> pd.DataFrame:
    return run_query(
        """
        SELECT a.id, pes.nome AS paciente, a.data_hora
        FROM atendimento a
        JOIN paciente pac ON pac.id = a.id_paciente
        JOIN pessoa pes ON pes.id = pac.id
        ORDER BY a.data_hora DESC
        """
    )


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
        indicadores = run_query(
            """
            SELECT
                (SELECT COUNT(*) FROM paciente) AS total_pacientes,
                (SELECT COUNT(*) FROM atendimento
                 WHERE data_hora::date = CURRENT_DATE) AS atendimentos_hoje,
                (SELECT COUNT(*) FROM unidade) AS total_unidades,
                (SELECT COUNT(*) FROM procedimento_realizado) AS procedimentos_realizados
            """
        )
        recentes = run_query(
            """
            SELECT
                a.id AS id_atendimento,
                a.data_hora,
                pes.nome AS paciente,
                u.nome AS unidade,
                a.duracao_minutos
            FROM atendimento a
            JOIN paciente pac ON pac.id = a.id_paciente
            JOIN pessoa pes ON pes.id = pac.id
            JOIN unidade u ON u.id = a.id_unidade
            ORDER BY a.data_hora DESC
            LIMIT 8
            """
        )

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


def pagina_inserir_atendimento() -> None:
    cabecalho_pagina(
        "Atendimentos",
        "Inserir novo atendimento",
        "Registre o paciente, a equipe responsável, a unidade e os dados de duração.",
    )

    with st.spinner("Carregando opções do atendimento...", show_time=True):
        pacientes = listar_pacientes()
        residentes = listar_atuacoes("residente")
        preceptores = listar_atuacoes("preceptor")
        unidades = listar_unidades()

    if pacientes.empty or residentes.empty or preceptores.empty or unidades.empty:
        mostrar_estado_vazio(
            "Pré-requisitos incompletos",
            "Cadastre pacientes, profissionais com atuação e unidades antes de inserir "
            "um atendimento.",
        )
        return

    proximo = run_query("SELECT COALESCE(MAX(id), 0) + 1 AS proximo FROM atendimento")
    proximo_id = int(proximo.iloc[0]["proximo"])

    with st.form("form_inserir_atendimento", border=True):
        st.subheader("Dados do atendimento")
        with st.container(horizontal=True, gap="medium"):
            with st.container(width="stretch"):
                st.caption("Identificação e horário")
                id_atendimento = st.number_input(
                    "ID do atendimento", min_value=1, value=proximo_id, step=1
                )
                data_atendimento = st.date_input("Data", value=date.today())
                hora = st.time_input(
                    "Hora", value=datetime.now().time().replace(microsecond=0)
                )
                duracao = st.number_input(
                    "Duração em minutos", min_value=1, value=30, step=5
                )

            with st.container(width="stretch"):
                st.caption("Paciente, equipe e local")
                paciente = st.selectbox(
                    "Paciente",
                    pacientes.itertuples(),
                    format_func=lambda r: f"{r.nome} (id {r.id})",
                )
                residente = st.selectbox(
                    "Residente (atuação)",
                    residentes.itertuples(),
                    format_func=lambda r: label_atuacao(pd.Series(r._asdict())),
                )
                preceptor = st.selectbox(
                    "Preceptor (atuação)",
                    preceptores.itertuples(),
                    format_func=lambda r: label_atuacao(pd.Series(r._asdict())),
                )
                unidade = st.selectbox(
                    "Unidade",
                    unidades.itertuples(),
                    format_func=lambda r: f"{r.nome} ({r.tipo})",
                )

        enviado = st.form_submit_button(
            "Inserir atendimento",
            type="primary",
            icon=":material/add_circle:",
            width="stretch",
        )

    if enviado:
        data_hora = datetime.combine(data_atendimento, hora)
        try:
            with st.spinner("Registrando atendimento...", show_time=True):
                resultado = run_command(
                    "SELECT inserir_atendimento_validado(%s, %s, %s, %s, %s, %s, %s) AS id_criado",
                    (
                        int(id_atendimento),
                        data_hora,
                        int(duracao),
                        int(paciente.id),
                        int(residente.id),
                        int(preceptor.id),
                        int(unidade.id),
                    ),
                )
            st.success(
                f"Atendimento inserido com sucesso — ID "
                f"{int(resultado.iloc[0]['id_criado'])}.",
                icon=":material/check_circle:",
            )
        except psycopg.Error as exc:
            mostrar_erro_banco(exc, "Não foi possível inserir o atendimento.")


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
        df = run_query(
            """
            SELECT id AS id_atendimento, data_hora, duracao_minutos,
                   id_atuacao_residente, id_atuacao_preceptor, id_unidade
            FROM atendimento
            WHERE id_paciente = %(id_paciente)s
            ORDER BY data_hora ASC
            """,
            {"id_paciente": int(paciente.id)},
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
        df = run_query(
            """
            SELECT
                pr.id_procedimento,
                p.nome,
                pr.quantidade,
                pr.tempo_real_minutos,
                pr.faturado,
                pr.observacao
            FROM procedimento_realizado AS pr
            JOIN procedimento AS p ON p.id = pr.id_procedimento
            WHERE pr.id_atendimento = %(id_atendimento)s
            """,
            {"id_atendimento": int(atendimento.id)},
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
                resultado = run_command(
                    "SELECT * FROM atualizar_num_convenio_paciente(%s, %s)",
                    (int(paciente.id), novo_convenio),
                )
            st.success(
                f"Convênio atualizado para “{resultado.iloc[0]['num_convenio']}”.",
                icon=":material/check_circle:",
            )
        except psycopg.Error as exc:
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
                    resultado = run_command(
                        "SELECT * FROM remover_procedimento_realizado_nao_faturado(%s, %s)",
                        (atendimento_id, procedimento_id),
                    )
                if resultado.empty:
                    st.warning("Nenhum registro foi removido.")
                else:
                    st.session_state["mensagem_remocao"] = (
                        "Procedimento removido com sucesso."
                    )
                    st.rerun()
            except psycopg.Error as exc:
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
            procedimentos = run_query(
                """
                SELECT pr.id_procedimento, p.nome, pr.faturado
                FROM procedimento_realizado pr
                JOIN procedimento p ON p.id = pr.id_procedimento
                WHERE pr.id_atendimento = %(id_atendimento)s
                """,
                {"id_atendimento": int(atendimento.id)},
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
        df = run_query(
            """
            SELECT
                medias.id_atuacao_residente,
                pessoa.nome AS nome_profissional,
                medias.tempo_medio_minutos
            FROM (
                SELECT id_atuacao_residente, AVG(duracao_minutos) AS tempo_medio_minutos
                FROM atendimento
                WHERE duracao_minutos IS NOT NULL AND duracao_minutos > 0
                GROUP BY id_atuacao_residente
            ) AS medias
            JOIN atuacao_residente ON atuacao_residente.id = medias.id_atuacao_residente
            JOIN atuacao_profissional ON atuacao_profissional.id = atuacao_residente.id
            JOIN profissional ON profissional.id = atuacao_profissional.id_profissional
            JOIN pessoa ON pessoa.id = profissional.id
            ORDER BY medias.tempo_medio_minutos DESC, pessoa.nome ASC
            """
        )

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
        df = run_query(
            """
            SELECT p.nome, COUNT(a.id) AS total_atendimentos
            FROM pessoa p
            JOIN atuacao_profissional ap ON p.id = ap.id_profissional
            JOIN atuacao_residente ar ON ap.id = ar.id
            LEFT JOIN atendimento a ON ar.id = a.id_atuacao_residente
            GROUP BY p.id, p.nome
            ORDER BY total_atendimentos DESC
            """
        )
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
        df = run_query(
            """
            SELECT p.nome, COUNT(a.id) AS total_supervisionado
            FROM pessoa p
            JOIN atuacao_profissional ap ON p.id = ap.id_profissional
            JOIN atuacao_preceptor apre ON ap.id = apre.id
            JOIN atendimento a ON apre.id = a.id_atuacao_preceptor
            WHERE a.data_hora >= %(mes_referencia)s
              AND a.data_hora < %(mes_referencia)s::date + interval '1 month'
            GROUP BY p.id, p.nome
            HAVING COUNT(a.id) > 5
            """,
            {"mes_referencia": mes_referencia},
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
        df = run_query(
            """
            SELECT u.nome AS unidade, p.nome AS residente, COUNT(e.id) AS quantidade_plantoes
            FROM unidade u
            LEFT JOIN escala e ON u.id = e.id_unidade
                AND e.data_plantao >= date_trunc('month', CURRENT_DATE)
                AND e.data_plantao < date_trunc('month', CURRENT_DATE) + interval '1 month'
            LEFT JOIN atuacao_residente ar ON e.id_atuacao_residente = ar.id
            LEFT JOIN atuacao_profissional ap ON ar.id = ap.id
            LEFT JOIN pessoa p ON ap.id_profissional = p.id
            GROUP BY u.id, u.nome, p.id, p.nome
            ORDER BY u.nome ASC, quantidade_plantoes DESC
            """
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
        df = run_query(
            """
            SELECT pes.nome, pac.num_convenio
            FROM pessoa pes
            JOIN paciente pac ON pes.id = pac.id
            WHERE NOT EXISTS (
                SELECT 1
                FROM atendimento a
                JOIN procedimento_realizado pr ON a.id = pr.id_atendimento
                JOIN procedimento proc ON pr.id_procedimento = proc.id
                WHERE a.id_paciente = pac.id AND proc.nivel_risco = 'alto'
            )
            """
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
    """Cria a navegação agrupada usando páginas baseadas em funções."""
    paginas = {
        "Início": [
            st.Page(
                lambda: executar_pagina(pagina_visao_geral),
                title="Visão geral",
                icon=":material/dashboard:",
                url_path="inicio",
                default=True,
            )
        ],
        "Atendimentos": [
            st.Page(
                lambda: executar_pagina(pagina_inserir_atendimento),
                title="Novo atendimento",
                icon=":material/add_circle:",
                url_path="novo-atendimento",
            ),
            st.Page(
                lambda: executar_pagina(pagina_atendimentos_paciente),
                title="Histórico do paciente",
                icon=":material/clinical_notes:",
                url_path="historico-paciente",
            ),
            st.Page(
                lambda: executar_pagina(pagina_procedimentos_atendimento),
                title="Procedimentos",
                icon=":material/medical_services:",
                url_path="procedimentos",
            ),
        ],
        "Pacientes": [
            st.Page(
                lambda: executar_pagina(pagina_atualizar_paciente),
                title="Atualizar convênio",
                icon=":material/edit:",
                url_path="atualizar-convenio",
            )
        ],
        "Análises": [
            st.Page(
                lambda: executar_pagina(pagina_tempo_medio_residente),
                title="Tempo por residente",
                icon=":material/timer:",
                url_path="tempo-residente",
            ),
            st.Page(
                lambda: executar_pagina(pagina_consultas_analiticas),
                title="Consultas analíticas",
                icon=":material/monitoring:",
                url_path="consultas-analiticas",
            ),
        ],
        "Administração": [
            st.Page(
                lambda: executar_pagina(pagina_remover_procedimento),
                title="Remover procedimento",
                icon=":material/delete:",
                url_path="remover-procedimento",
            )
        ],
    }
    return st.navigation(paginas, position="sidebar", expanded=True)


def main() -> None:
    aplicar_estilos()
    st.logo(
        Path(__file__).parent / "assets" / "hospital-logo.svg",
        size="large",
        icon_image=":material/local_hospital:",
    )

    try:
        get_connection()
    except Exception as exc:  # noqa: BLE001
        with st.sidebar:
            st.badge(
                "Banco desconectado",
                icon=":material/database_off:",
                color="red",
            )
        cabecalho_pagina(
            "Conexão",
            "Banco de dados indisponível",
            "O painel não conseguiu acessar o PostgreSQL configurado.",
        )
        st.error(
            "Verifique se o serviço está ativo e se as variáveis do arquivo `.env` "
            "estão corretas.",
            icon=":material/error:",
        )
        with st.expander("Ver detalhes técnicos", icon=":material/code:"):
            st.code(str(exc), language=None)
        st.stop()

    with st.sidebar:
        st.badge(
            "Banco conectado",
            icon=":material/database:",
            color="green",
        )
        st.caption("Gestão hospitalar · SQL puro")

    pagina = criar_navegacao()
    pagina.run()


if __name__ == "__main__":
    main()
