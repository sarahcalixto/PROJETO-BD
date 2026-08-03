"""Evidências técnicas de integridade, ORM e concorrência."""

import psycopg
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from projeto_hospital.services import (
    ServicoORMError,
    demonstrar_concorrencia_escala,
    medir_lazy_e_eager,
)
from projeto_hospital.ui.components import (
    cabecalho_pagina,
    mostrar_erro_banco,
    mostrar_estado_vazio,
    mostrar_metricas,
)
from projeto_hospital.ui.data import (
    get_session_factory,
    listar_pacientes,
    run_query,
)


cabecalho_pagina(
    "Integridade",
    "Auditoria",
    "Inspecione auditoria, triggers, carregamento ORM e concorrência real.",
)
evidencia = st.selectbox(
    "Evidência",
    ("Auditoria de atendimentos", "Triggers", "Médias", "Lazy e eager", "Concorrência"),
    key="auditoria_evidencia",
)

try:
    if evidencia == "Auditoria de atendimentos":
        dados = run_query(
            """
            SELECT id_auditoria, id_atendimento, operacao, usuario,
                   data_hora, dados_antigos, dados_novos
            FROM auditoria_atendimento
            ORDER BY id_auditoria DESC
            LIMIT 100
            """
        )
        if dados.empty:
            mostrar_estado_vazio("Auditoria vazia", "Ainda não há eventos auditados.")
        else:
            st.dataframe(dados, hide_index=True, width="stretch")

    elif evidencia == "Triggers":
        dados = run_query(
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
        st.dataframe(dados, hide_index=True, width="stretch")

    elif evidencia == "Médias":
        dados = run_query(
            """
            SELECT codigo, nome, nivel_risco, tempo_medio_minutos,
                   media_tempo_procedimento
            FROM procedimento
            ORDER BY nome
            """
        )
        st.dataframe(dados, hide_index=True, width="stretch")

    elif evidencia == "Lazy e eager":
        pacientes = listar_pacientes()
        paciente = st.selectbox(
            "Paciente",
            pacientes.itertuples(),
            format_func=lambda item: item.nome,
        )
        resultado = medir_lazy_e_eager(get_session_factory(), int(paciente.id))
        mostrar_metricas(
            [
                ("Consultas lazy", resultado.consultas_lazy, None),
                ("Consultas eager", resultado.consultas_eager, None),
                ("Atendimentos", resultado.atendimentos_carregados, None),
            ]
        )
        st.caption(
            "O eager loading antecipa os relacionamentos; o lazy loading consulta "
            "cada relacionamento quando ele é acessado."
        )

    else:
        st.warning(
            "A demonstração cria duas escalas temporárias na mesma unidade, executa "
            "duas transações e remove somente os registros criados ao final.",
            icon=":material/warning:",
        )
        confirmar = st.checkbox("Confirmo a execução da demonstração concorrente")
        if st.button(
            "Executar concorrência",
            type="primary",
            icon=":material/lock_clock:",
            disabled=not confirmar,
        ):
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
except (psycopg.Error, SQLAlchemyError, ServicoORMError, RuntimeError) as exc:
    mostrar_erro_banco(exc, "Não foi possível carregar a evidência.")
