from streamlit.testing.v1 import AppTest


def render_visao_geral_preenchida() -> None:
    from datetime import datetime

    import pandas as pd

    import app

    def consulta(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
        del params
        if "total_pacientes" in sql:
            return pd.DataFrame(
                [
                    {
                        "total_pacientes": 12,
                        "atendimentos_hoje": 3,
                        "total_unidades": 4,
                        "procedimentos_realizados": 18,
                    }
                ]
            )
        return pd.DataFrame(
            [
                {
                    "id_atendimento": 10,
                    "data_hora": datetime(2026, 7, 25, 9, 30),
                    "paciente": "Ana Silva",
                    "unidade": "Ambulatório",
                    "duracao_minutos": 30,
                }
            ]
        )

    app.run_query = consulta
    app.pagina_visao_geral()


def render_visao_geral_vazia() -> None:
    import pandas as pd

    import app

    def consulta(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
        del params
        if "total_pacientes" in sql:
            return pd.DataFrame(
                [
                    {
                        "total_pacientes": 0,
                        "atendimentos_hoje": 0,
                        "total_unidades": 0,
                        "procedimentos_realizados": 0,
                    }
                ]
            )
        return pd.DataFrame()

    app.run_query = consulta
    app.pagina_visao_geral()


def render_navegacao() -> None:
    import pandas as pd

    import app

    def consulta(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
        del params
        if "total_pacientes" in sql:
            return pd.DataFrame(
                [
                    {
                        "total_pacientes": 0,
                        "atendimentos_hoje": 0,
                        "total_unidades": 0,
                        "procedimentos_realizados": 0,
                    }
                ]
            )
        return pd.DataFrame()

    app.run_query = consulta
    pagina = app.criar_navegacao()
    pagina.run()


def render_historico_paciente() -> None:
    from datetime import datetime

    import pandas as pd

    import app

    app.listar_pacientes = lambda: pd.DataFrame(
        [
            {
                "id": 1,
                "nome": "Ana Silva",
                "num_convenio": "CONV-01",
                "grupo_sanguineo": "A+",
            }
        ]
    )
    app.run_query = lambda sql, params=None: pd.DataFrame(
        [
            {
                "id_atendimento": 1,
                "data_hora": datetime(2026, 7, 25, 9, 0),
                "duracao_minutos": 30,
                "id_atuacao_residente": 2,
                "id_atuacao_preceptor": 3,
                "id_unidade": 4,
            },
            {
                "id_atendimento": 2,
                "data_hora": datetime(2026, 7, 25, 10, 0),
                "duracao_minutos": 60,
                "id_atuacao_residente": 2,
                "id_atuacao_preceptor": 3,
                "id_unidade": 4,
            },
        ]
    )
    app.pagina_atendimentos_paciente()


def render_erro_consulta() -> None:
    import psycopg

    import app

    def pagina_com_erro() -> None:
        raise psycopg.OperationalError("conexão interrompida")

    app.executar_pagina(pagina_com_erro)


def render_remocao_nao_faturada() -> None:
    from datetime import datetime

    import pandas as pd

    import app

    app.listar_atendimentos_ids = lambda: pd.DataFrame(
        [
            {
                "id": 1,
                "paciente": "Ana Silva",
                "data_hora": datetime(2026, 7, 25, 9, 0),
            }
        ]
    )
    app.run_query = lambda sql, params=None: pd.DataFrame(
        [{"id_procedimento": 7, "nome": "Curativo", "faturado": False}]
    )
    app.pagina_remover_procedimento()


def render_consultas_analiticas() -> None:
    import pandas as pd

    import app

    def consulta(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
        del params
        if "total_atendimentos" not in sql:
            raise AssertionError("Uma aba analítica oculta executou sua consulta")
        return pd.DataFrame(
            [
                {"nome": "Ana Residente", "total_atendimentos": 5},
                {"nome": "Bia Residente", "total_atendimentos": 3},
            ]
        )

    app.run_query = consulta
    app.pagina_consultas_analiticas()


def test_visao_geral_exibe_metricas_e_atividade_recente() -> None:
    app_test = AppTest.from_function(render_visao_geral_preenchida).run()

    assert not app_test.exception
    assert [metrica.label for metrica in app_test.metric] == [
        "Pacientes",
        "Atendimentos hoje",
        "Unidades",
        "Procedimentos",
    ]
    assert [metrica.value for metrica in app_test.metric] == ["12", "3", "4", "18"]
    assert len(app_test.dataframe) == 1


def test_visao_geral_exibe_estado_vazio() -> None:
    app_test = AppTest.from_function(render_visao_geral_vazia).run()

    assert not app_test.exception
    assert any(
        "Nenhum atendimento registrado" in mensagem.value
        for mensagem in app_test.info
    )


def test_navegacao_abre_visao_geral_por_padrao() -> None:
    app_test = AppTest.from_function(render_navegacao).run()

    assert not app_test.exception
    assert app_test.title[0].value == "Painel hospitalar"
    assert [metrica.value for metrica in app_test.metric] == ["0", "0", "0", "0"]


def test_historico_exibe_resumo_e_tabela() -> None:
    app_test = AppTest.from_function(render_historico_paciente).run()

    assert not app_test.exception
    assert [metrica.value for metrica in app_test.metric] == [
        "2",
        "90 min",
        "45.0 min",
    ]
    assert len(app_test.dataframe) == 1


def test_erro_de_banco_tem_mensagem_amigavel() -> None:
    app_test = AppTest.from_function(render_erro_consulta).run()

    assert not app_test.exception
    assert "Não foi possível carregar os dados" in app_test.error[0].value
    assert len(app_test.status) == 1


def test_remocao_exige_confirmacao() -> None:
    app_test = AppTest.from_function(render_remocao_nao_faturada).run()

    assert not app_test.exception
    revisar = next(
        botao for botao in app_test.button if botao.label == "Revisar e remover"
    )
    revisar.click().run()

    assert any(
        botao.label == "Confirmar remoção" for botao in app_test.button
    )
    assert any(botao.label == "Cancelar" for botao in app_test.button)


def test_consultas_analiticas_executam_apenas_aba_ativa() -> None:
    app_test = AppTest.from_function(render_consultas_analiticas).run()

    assert not app_test.exception
    assert [metrica.value for metrica in app_test.metric] == ["2", "8"]
