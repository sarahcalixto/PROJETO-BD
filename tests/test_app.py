"""Contratos essenciais da interface Streamlit consolidada."""

from datetime import date
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from projeto_hospital.services import (
    EscalaDTO,
    RegraNegocioViolada,
    ReajusteEscalaDTO,
)
from projeto_hospital.ui import data


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "frontend" / "app_pages"


def _escala_controlada() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 41,
                "id_atuacao_residente": 3,
                "residente": "Alphonse Elric",
                "data_plantao": date(2026, 10, 31),
                "turno": "noite",
                "unidade": "Enfermaria Central",
                "preceptor": "Bruno Bucciarati",
            }
        ]
    )


def _escalas_vazias() -> pd.DataFrame:
    return _escala_controlada().iloc[0:0]


def _unidades_controladas() -> pd.DataFrame:
    return pd.DataFrame(
        [{"id": 1, "nome": "Enfermaria Central", "tipo": "enfermaria"}]
    )


def _atuacoes_controladas(tipo: str, _data_referencia: date) -> pd.DataFrame:
    if tipo == "residente":
        registros = [{"id": 3, "nome": "Alphonse Elric", "crm": "CRM-R-3"}]
    else:
        registros = [{"id": 6, "nome": "Bruno Bucciarati", "crm": "CRM-P-6"}]
    return pd.DataFrame(registros)


def test_frontend_possui_somente_paginas_de_dominio() -> None:
    assert {item.name for item in PAGES.glob("*.py")} == {
        "atendimentos.py",
        "auditoria.py",
        "consultas_estatisticas.py",
        "escalas.py",
        "pacientes.py",
        "visao_geral.py",
    }


def test_paginas_sao_scripts_diretos_sem_wrappers() -> None:
    for caminho in PAGES.glob("*.py"):
        conteudo = caminho.read_text(encoding="utf-8")
        assert "executar_pagina" not in conteudo
        assert "def pagina_" not in conteudo
        assert "use_container_width" not in conteudo
        assert "unsafe_allow_html" not in conteudo


def test_navegacao_usa_nomes_de_dominio() -> None:
    conteudo = (ROOT / "frontend" / "app.py").read_text(encoding="utf-8")
    for titulo in (
        "Visão geral",
        "Atendimentos",
        "Pacientes",
        "Escalas",
        "Consultas e estatísticas",
        "Auditoria",
    ):
        assert titulo in conteudo
    assert '"Etapa 1"' not in conteudo
    assert '"Etapa 2"' not in conteudo
    assert "aplicar_estilos" not in conteudo


def test_consultas_obrigatorias_estao_acessiveis() -> None:
    conteudo = (PAGES / "consultas_estatisticas.py").read_text(encoding="utf-8")
    for simbolo in (
        "calcular_tempo_medio_por_residente",
        "ranking_residentes_por_atendimentos",
        "preceptores_com_mais_de_cinco_atendimentos",
        "plantoes_por_unidade_e_residente",
        "pacientes_sem_procedimento_alto_risco",
        "vw_pacientes_internados",
        "vw_residentes_sem_supervisor",
        "vw_estatisticas_atendimentos_mensal",
        "preceptores_de_pacientes_flamenguistas",
        "ultimos_atendimentos_por_paciente",
        "percentual_alto_risco_por_residente",
        "calcular_tempo_medio_espera",
    ):
        assert simbolo in conteudo


def test_auditoria_expoe_evidencias_tecnicas() -> None:
    conteudo = (PAGES / "auditoria.py").read_text(encoding="utf-8")
    for evidencia in (
        "trg_check_sobreposicao_escala",
        "trg_audita_atendimento",
        "trg_atualiza_media_procedimentos",
        "medir_lazy_e_eager",
        "demonstrar_concorrencia_escala",
    ):
        assert evidencia in conteudo


def test_visao_geral_renderiza_com_dados_controlados(monkeypatch) -> None:
    monkeypatch.setattr(
        data,
        "carregar_visao_geral",
        lambda: (
            pd.DataFrame(
                [{
                    "total_pacientes": 5,
                    "atendimentos_hoje": 2,
                    "total_unidades": 3,
                    "procedimentos_realizados": 10,
                }]
            ),
            pd.DataFrame(
                [{
                    "id_atendimento": 1,
                    "data_hora": pd.Timestamp("2026-08-02 10:00"),
                    "paciente": "Paciente teste",
                    "unidade": "UTI",
                    "duracao_minutos": 30,
                }]
            ),
        ),
    )
    app = AppTest.from_file(str(PAGES / "visao_geral.py")).run()
    assert not app.exception
    assert [item.value for item in app.metric] == ["5", "2", "3", "10"]


def test_reajuste_explicita_origem_destino_e_campos_mantidos(monkeypatch) -> None:
    monkeypatch.setattr(data, "listar_escalas_origem", _escala_controlada)

    app = AppTest.from_file(str(PAGES / "escalas.py"))
    app.session_state["operacao_escala"] = "Reajustar escala"
    app.run()

    assert not app.exception
    assert [item.label for item in app.selectbox] == [
        "Escala a reajustar",
        "Turno de destino",
    ]
    assert [item.value for item in app.subheader] == [
        "Escala atual",
        "Novo agendamento",
    ]
    textos = [item.value for item in app.caption]
    assert "Unidade mantida" in textos
    assert "Preceptor mantido" in textos
    assert app.checkbox[0].label == "Confirmo a alteração desta escala"
    assert "Selecione o turno de destino" in app.info[0].value


def test_reajuste_valida_confirmacao_e_envia_somente_contrato_oficial(
    monkeypatch,
) -> None:
    chamadas: list[dict[str, object]] = []

    def executar_controlado(_servico, **argumentos):
        chamadas.append(argumentos)
        return ReajusteEscalaDTO(
            **argumentos,
            quantidade_atualizada=1,
        )

    monkeypatch.setattr(data, "listar_escalas_origem", _escala_controlada)
    monkeypatch.setattr(data, "executar_escrita", executar_controlado)
    app = AppTest.from_file(str(PAGES / "escalas.py"))
    app.session_state["operacao_escala"] = "Reajustar escala"
    app.run()

    app.button[0].click().run()
    assert "Selecione o turno e confirme" in app.warning[0].value
    assert chamadas == []

    app.selectbox[1].select("tarde")
    app.date_input[0].set_value(date(2026, 11, 1))
    app.checkbox[0].check()
    app.button[0].click().run()

    assert not app.exception
    assert chamadas == [
        {
            "id_atuacao_residente": 3,
            "data_origem": date(2026, 10, 31),
            "turno_origem": "noite",
            "data_destino": date(2026, 11, 1),
            "turno_destino": "tarde",
        }
    ]
    assert "Unidade Enfermaria Central" in app.success[0].value
    assert "preceptor Bruno Bucciarati mantidos" in app.success[0].value


def test_nova_escala_mostra_ocupacao_e_cadastra(monkeypatch) -> None:
    chamadas: list[dict[str, object]] = []

    def executar_controlado(_servico, **argumentos):
        chamadas.append(argumentos)
        return EscalaDTO(id_escala=52, **argumentos)

    monkeypatch.setattr(data, "listar_escalas_origem", _escala_controlada)
    monkeypatch.setattr(data, "listar_unidades", _unidades_controladas)
    monkeypatch.setattr(data, "listar_atuacoes", _atuacoes_controladas)
    monkeypatch.setattr(data, "executar_escrita", executar_controlado)

    app = AppTest.from_file(str(PAGES / "escalas.py")).run()
    app.date_input[0].set_value(date(2026, 10, 31))
    app.segmented_control[1].select("noite").run()

    assert not app.exception
    assert [item.label for item in app.selectbox] == [
        "Unidade",
        "Residente",
        "Preceptor",
    ]
    assert len(app.dataframe) == 1
    assert app.dataframe[0].value.iloc[0].to_dict() == {
        "Residente": "Alphonse Elric",
        "Unidade": "Enfermaria Central",
        "Preceptor": "Bruno Bucciarati",
    }

    app.button[0].click().run()

    assert not app.exception
    assert chamadas == [
        {
            "id_unidade": 1,
            "data_plantao": date(2026, 10, 31),
            "turno": "noite",
            "id_atuacao_residente": 3,
            "id_atuacao_preceptor": 6,
        }
    ]
    assert "Escala 52 cadastrada" in app.success[0].value


def test_nova_escala_vazia_continua_disponivel_e_exibe_conflito(monkeypatch) -> None:
    def rejeitar_conflito(_servico, **_argumentos):
        raise RegraNegocioViolada(
            "Este residente já está escalado nesta data e turno."
        )

    monkeypatch.setattr(data, "listar_escalas_origem", _escalas_vazias)
    monkeypatch.setattr(data, "listar_unidades", _unidades_controladas)
    monkeypatch.setattr(data, "listar_atuacoes", _atuacoes_controladas)
    monkeypatch.setattr(data, "executar_escrita", rejeitar_conflito)

    app = AppTest.from_file(str(PAGES / "escalas.py")).run()

    assert not app.exception
    assert "Nenhuma escala cadastrada" in app.info[0].value
    assert app.button[0].label == "Cadastrar escala"

    app.button[0].click().run()

    assert not app.exception
    assert "Este residente já está escalado nesta data e turno." in app.error[0].value
