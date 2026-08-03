"""Aceitação da migração preservadora para a Etapa 2."""

import psycopg

from tests.utils import read_sql


def test_migracao_faz_backfill_e_e_idempotente(conn: psycopg.Connection) -> None:
    conn.execute("DROP VIEW IF EXISTS vw_pacientes_internados")
    conn.execute("DROP VIEW IF EXISTS vw_residentes_sem_supervisor")
    conn.execute("DROP VIEW IF EXISTS vw_estatisticas_atendimentos_mensal")
    conn.execute("DROP TABLE auditoria_atendimento CASCADE")
    conn.execute("DROP TABLE internacao CASCADE")
    conn.execute(
        "ALTER TABLE procedimento_realizado DROP COLUMN data_hora_inicio CASCADE"
    )
    conn.execute(
        "ALTER TABLE procedimento DROP COLUMN media_tempo_procedimento CASCADE"
    )

    scripts = (
        "08_migracao_etapa2.sql",
        "05_procedures.sql",
        "06_triggers.sql",
        "07_views.sql",
    )
    for _ in range(2):
        for nome in scripts:
            conn.execute(read_sql(nome))

    assert conn.execute(
        "SELECT COUNT(*) FROM procedimento_realizado WHERE data_hora_inicio IS NULL"
    ).fetchone()[0] == 0
    assert conn.execute("SELECT to_regclass('internacao')").fetchone()[0]
    assert conn.execute("SELECT to_regclass('auditoria_atendimento')").fetchone()[0]
    assert conn.execute(
        "SELECT to_regclass('vw_estatisticas_atendimentos_mensal')"
    ).fetchone()[0]
