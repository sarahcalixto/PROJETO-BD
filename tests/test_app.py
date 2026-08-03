"""Contratos essenciais da interface Streamlit consolidada."""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from projeto_hospital.ui import data


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "frontend" / "app_pages"


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
