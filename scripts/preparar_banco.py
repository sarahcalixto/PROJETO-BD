"""Migra com segurança o banco configurado para o produto final da Etapa 2."""

from __future__ import annotations

from pathlib import Path

import psycopg

from projeto_hospital.config import load_database_config


ROOT = Path(__file__).resolve().parents[1]
OBJETOS_ETAPA_2 = (
    "05_procedures.sql",
    "06_triggers.sql",
    "07_views.sql",
)


def preparar_banco() -> None:
    config = load_database_config()
    with psycopg.connect(**config.connection_kwargs) as conn:
        existe_schema = conn.execute(
            "SELECT to_regclass('public.pessoa') IS NOT NULL"
        ).fetchone()[0]
        scripts_estruturais = (
            ("08_migracao_etapa2.sql",)
            if existe_schema
            else ("01_schema.sql", "02_dados_teste.sql")
        )
        for nome in (*scripts_estruturais, *OBJETOS_ETAPA_2):
            conn.execute((ROOT / "sql" / nome).read_text(encoding="utf-8"))


def main() -> int:
    preparar_banco()
    print("Banco preparado no estado final da Etapa 2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
