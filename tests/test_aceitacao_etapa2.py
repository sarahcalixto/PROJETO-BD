"""Suíte de aceitação organizada pelos sete grupos do enunciado."""

from pathlib import Path

import psycopg
from sqlalchemy.orm import Session, sessionmaker

from projeto_hospital.orm import Atendimento, Paciente
from projeto_hospital.services import (
    demonstrar_concorrencia_escala,
    percentual_alto_risco_por_residente,
    preceptores_de_pacientes_flamenguistas,
    ultimos_atendimentos_por_paciente,
)


ROOT = Path(__file__).resolve().parents[1]


class TestGrupo1RotinasArmazenadas:
    def test_rotinas_e_parametro_jsonb_existem(self, conn: psycopg.Connection) -> None:
        linhas = conn.execute(
            """
            SELECT proname, prokind, pg_get_function_identity_arguments(oid)
            FROM pg_proc
            WHERE proname = ANY(%s)
            ORDER BY proname
            """,
            (
                [
                    "sp_calcular_tempo_medio_espera",
                    "sp_reajustar_escala",
                    "sp_registrar_atendimento_completo",
                ],
            ),
        ).fetchall()
        assert [linha[0] for linha in linhas] == [
            "sp_calcular_tempo_medio_espera",
            "sp_reajustar_escala",
            "sp_registrar_atendimento_completo",
        ]
        assert {linha[1] for linha in linhas} == {"f"}
        registrar = next(linha for linha in linhas if linha[0].startswith("sp_registrar"))
        assert "jsonb" in registrar[2]


class TestGrupo2Triggers:
    def test_tres_triggers_estao_ativos(self, conn: psycopg.Connection) -> None:
        nomes = conn.execute(
            """
            SELECT tgname
            FROM pg_trigger
            WHERE NOT tgisinternal AND tgname = ANY(%s)
            ORDER BY tgname
            """,
            (
                [
                    "trg_atualiza_media_procedimentos",
                    "trg_audita_atendimento",
                    "trg_check_sobreposicao_escala",
                ],
            ),
        ).fetchall()
        assert [item[0] for item in nomes] == [
            "trg_atualiza_media_procedimentos",
            "trg_audita_atendimento",
            "trg_check_sobreposicao_escala",
        ]


class TestGrupo3Views:
    def test_tres_views_publicas_existem(self, conn: psycopg.Connection) -> None:
        nomes = conn.execute(
            """
            SELECT viewname FROM pg_views
            WHERE schemaname = 'public' AND viewname = ANY(%s)
            ORDER BY viewname
            """,
            (
                [
                    "vw_estatisticas_atendimentos_mensal",
                    "vw_pacientes_internados",
                    "vw_residentes_sem_supervisor",
                ],
            ),
        ).fetchall()
        assert len(nomes) == 3


class TestGrupo4ORM:
    def test_mapeamentos_possuem_relacionamentos_lazy(self) -> None:
        assert Paciente.atendimentos.property.lazy == "select"
        assert Atendimento.procedimentos.property.lazy == "select"

    def test_servicos_avaliados_nao_usam_sql_textual(self) -> None:
        pasta = ROOT / "src" / "projeto_hospital" / "services"
        for caminho in (
            pasta / "operacoes.py",
            pasta / "consultas.py",
            pasta / "consultas_avancadas.py",
        ):
            conteudo = caminho.read_text(encoding="utf-8")
            assert "sqlalchemy import text" not in conteudo
            assert "text(" not in conteudo


class TestGrupo5ConsultasAvancadas:
    def test_as_tres_consultas_retornam_resultados_completos(
        self,
        orm_session: Session,
    ) -> None:
        assert preceptores_de_pacientes_flamenguistas(orm_session)
        ultimos = ultimos_atendimentos_por_paciente(orm_session)
        assert len(ultimos) == 5
        assert all(item.residente and item.preceptor for item in ultimos)
        percentuais = percentual_alto_risco_por_residente(orm_session)
        assert len(percentuais) == 5
        assert all(item.percentual_alto_risco >= 0 for item in percentuais)


class TestGrupo6Concorrencia:
    def test_duas_sessoes_mantem_apenas_uma_escala(
        self,
        orm_session_factory: sessionmaker[Session],
    ) -> None:
        resultado = demonstrar_concorrencia_escala(orm_session_factory)
        assert resultado.segunda_aguardou_lock is True
        assert (resultado.confirmadas, resultado.rejeitadas) == (1, 1)
        assert resultado.escalas_no_destino == 1
        assert "T2 aguardou o lock de T1" in resultado.logs


class TestGrupo7Entrega:
    def test_documentacao_obrigatoria_esta_versionavel(self) -> None:
        for relativo in (
            "README.md",
            "docs/relatorio_etapa2.md",
            "docs/matriz_conformidade_etapa2.md",
            "docs/roteiro_video_etapa2.md",
        ):
            assert (ROOT / relativo).is_file(), relativo
