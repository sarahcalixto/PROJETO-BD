"""Testes isolados da interface Streamlit da Etapa 2."""

import pandas as pd
from streamlit.testing.v1 import AppTest


def render_visao_geral() -> None:
    from datetime import datetime

    import pandas as pd

    from projeto_hospital.ui import pages

    pages.carregar_visao_geral = lambda: (
        pd.DataFrame([{"total_pacientes": 12, "atendimentos_hoje": 3, "total_unidades": 4, "procedimentos_realizados": 18}]),
        pd.DataFrame([{"id_atendimento": 10, "data_hora": datetime(2026, 7, 25, 9, 30), "paciente": "Ana", "unidade": "Ambulatório", "duracao_minutos": 30}]),
    )
    pages.pagina_visao_geral()


def render_visao_vazia() -> None:
    import pandas as pd

    from projeto_hospital.ui import pages

    pages.carregar_visao_geral = lambda: (
        pd.DataFrame([{"total_pacientes": 0, "atendimentos_hoje": 0, "total_unidades": 0, "procedimentos_realizados": 0}]),
        pd.DataFrame(),
    )
    pages.pagina_visao_geral()


def render_historico() -> None:
    from datetime import date, datetime
    from types import SimpleNamespace

    import pandas as pd

    from projeto_hospital.ui import pages

    pages.listar_pacientes = lambda: pd.DataFrame(
        [{"id": 1, "nome": "Ana", "num_convenio": "C-1", "grupo_sanguineo": "A+"}]
    )
    pages.executar_leitura = lambda *args, **kwargs: [
        SimpleNamespace(id_atendimento=1, data_hora=datetime(2026, 7, 25, 9), duracao_minutos=30, id_paciente=1, id_atuacao_residente=2, id_atuacao_preceptor=3, id_unidade=4),
        SimpleNamespace(id_atendimento=2, data_hora=datetime(2026, 7, 25, 10), duracao_minutos=60, id_paciente=1, id_atuacao_residente=2, id_atuacao_preceptor=3, id_unidade=4),
    ]
    pages.dto_dataframe = lambda items: pd.DataFrame([vars(item) for item in items])
    pages.pagina_atendimentos_paciente()


def render_navegacao() -> None:
    import pandas as pd

    from projeto_hospital.ui import pages

    pages.carregar_visao_geral = lambda: (
        pd.DataFrame([{"total_pacientes": 0, "atendimentos_hoje": 0, "total_unidades": 0, "procedimentos_realizados": 0}]),
        pd.DataFrame(),
    )
    pages.criar_navegacao().run()


def render_atendimento_completo() -> None:
    from datetime import date

    import pandas as pd

    from projeto_hospital.ui import stage2

    stage2.listar_pacientes = lambda: pd.DataFrame(
        [{"id": 1, "nome": "Ana", "num_convenio": "C-1", "grupo_sanguineo": "A+"}]
    )
    stage2.listar_atuacoes = lambda tipo: pd.DataFrame(
        [{
            "id": 1 if tipo == "residente" else 6,
            "nome": tipo.title(),
            "data_inicio": date(2020, 1, 1),
            "data_fim": None,
        }]
    )
    stage2.listar_unidades = lambda: pd.DataFrame([{"id": 1, "nome": "UTI", "tipo": "uti"}])
    stage2.listar_procedimentos_catalogo = lambda: pd.DataFrame([{"id": 1, "nome": "Sutura", "nivel_risco": "baixo", "tempo_medio_minutos": 20}])
    stage2.executar_escrita = lambda *args, **kwargs: 42
    stage2.pagina_atendimento_completo()


def render_reajuste() -> None:
    from datetime import date
    from types import SimpleNamespace

    import pandas as pd

    from projeto_hospital.ui import stage2

    stage2.listar_escalas_origem = lambda: pd.DataFrame([{
        "id": 1, "id_atuacao_residente": 1, "residente": "Rita",
        "data_plantao": date(2026, 8, 3), "turno": "manha",
        "unidade": "UTI", "preceptor": "Paulo",
    }])
    stage2.executar_escrita = lambda *args, **kwargs: SimpleNamespace(quantidade_atualizada=1)
    stage2.pagina_reajustar_escala()


def render_painel() -> None:
    from datetime import datetime

    import pandas as pd

    from projeto_hospital.ui import stage2

    chamadas: list[str] = []

    def query(sql: str, params=None) -> pd.DataFrame:
        del params
        chamadas.append(sql)
        if "vw_pacientes_internados" not in sql:
            raise AssertionError("Uma consulta oculta foi executada")
        return pd.DataFrame([{"paciente": "Ana", "num_convenio": "C-1", "data_internacao": datetime(2026, 8, 1)}])

    stage2.run_query = query
    stage2.pagina_painel_etapa2()
    assert len(chamadas) == 1


def render_painel_orm() -> None:
    from datetime import datetime
    from types import SimpleNamespace

    import pandas as pd

    from projeto_hospital.ui import stage2

    chamadas: list[str] = []
    stage2.run_query = lambda *args, **kwargs: pd.DataFrame(
        [{"paciente": "Ana", "data_internacao": datetime(2026, 8, 1)}]
    )

    def leitura(servico, *args, **kwargs):
        del args, kwargs
        chamadas.append(servico.__name__)
        return [SimpleNamespace(id_atuacao_preceptor=6, nome="Paulo")]

    stage2.executar_leitura = leitura
    stage2.dto_dataframe = lambda items: pd.DataFrame([vars(item) for item in items])
    stage2.pagina_painel_etapa2()
    if st := __import__("streamlit"):
        st.session_state["_chamadas_orm"] = chamadas


def render_evidencia_concorrencia() -> None:
    from types import SimpleNamespace

    import pandas as pd
    import streamlit as st
    from projeto_hospital.ui import stage2

    st.session_state.setdefault("execucoes_concorrencia", 0)

    def demonstrar(factory):
        del factory
        st.session_state["execucoes_concorrencia"] += 1
        return SimpleNamespace(
            logs=("T1 manteve lock", "T2 aguardou", "T1 confirmou", "T2 rejeitada"),
            confirmadas=1,
            rejeitadas=1,
            escalas_no_destino=1,
        )

    stage2.demonstrar_concorrencia_escala = demonstrar
    stage2.get_session_factory = lambda: object()
    stage2.run_query = lambda *args, **kwargs: pd.DataFrame(
        [{"trigger": "trg_audita_atendimento", "tabela": "atendimento", "ativo": True}]
    )
    stage2.pagina_evidencias_tecnicas()


def render_erro() -> None:
    import psycopg
    from projeto_hospital.ui.components import executar_pagina

    def falhar() -> None:
        raise psycopg.OperationalError("conexão interrompida")

    executar_pagina(falhar)


def test_visao_geral_e_estado_vazio() -> None:
    preenchida = AppTest.from_function(render_visao_geral).run()
    assert not preenchida.exception
    assert [item.value for item in preenchida.metric] == ["12", "3", "4", "18"]
    assert len(preenchida.dataframe) == 1

    vazia = AppTest.from_function(render_visao_vazia).run()
    assert not vazia.exception
    assert any("Nenhum atendimento" in item.value for item in vazia.info)


def test_historico_usa_resultados_orm() -> None:
    app = AppTest.from_function(render_historico).run()
    assert not app.exception
    assert [item.value for item in app.metric] == ["2", "90 min", "45.0 min"]


def test_navegacao_abre_visao_geral_e_inclui_etapa2() -> None:
    app = AppTest.from_function(render_navegacao).run()
    assert not app.exception
    assert app.title[0].value == "Painel hospitalar"
    assert [item.value for item in app.metric] == ["0", "0", "0", "0"]


def test_atendimento_completo_exibe_editor_e_registra() -> None:
    app = AppTest.from_function(render_atendimento_completo).run()
    assert not app.exception
    botao = next(item for item in app.button if item.label == "Registrar atendimento completo")
    app = botao.click().run()
    assert not app.exception
    assert any("Atendimento 42" in item.value for item in app.success)


def test_reajuste_exige_confirmacao_e_confirma_transacao() -> None:
    app = AppTest.from_function(render_reajuste).run()
    botao = next(item for item in app.button if item.label == "Reajustar escala")
    app = botao.click().run()
    assert any("Confirme" in item.value for item in app.warning)
    app.checkbox[0].check()
    botao = next(item for item in app.button if item.label == "Reajustar escala")
    app = botao.click().run()
    assert any("1 escala" in item.value for item in app.success)


def test_painel_executa_somente_consulta_aberta() -> None:
    app = AppTest.from_function(render_painel).run()
    assert not app.exception
    assert len(app.dataframe) == 1


def test_painel_orm_nao_executa_view_oculta() -> None:
    app = AppTest.from_function(render_painel_orm).run()
    app.selectbox[0].select("Preceptores e flamenguistas")
    app = app.run()
    assert not app.exception
    assert app.session_state["_chamadas_orm"] == ["preceptores_de_pacientes_flamenguistas"]


def test_concorrencia_so_executa_apos_clique_confirmado() -> None:
    app = AppTest.from_function(render_evidencia_concorrencia).run()
    app.selectbox[0].select("Concorrência")
    app = app.run()
    assert app.session_state["execucoes_concorrencia"] == 0
    app.checkbox[0].check()
    app = app.run()
    botao = next(item for item in app.button if item.label == "Executar concorrência")
    app = botao.click().run()
    assert app.session_state["execucoes_concorrencia"] == 1
    assert [item.value for item in app.metric] == ["1", "1", "1"]


def test_erro_de_banco_tem_mensagem_amigavel() -> None:
    app = AppTest.from_function(render_erro).run()
    assert not app.exception
    assert "Não foi possível carregar" in app.error[0].value
