import os
from collections.abc import Iterator
from dataclasses import replace

import psycopg
import pytest

from projeto_hospital.config import DatabaseConfig, load_database_config

from .utils import read_sql, split_sql_statements


@pytest.fixture()
def conn(_prepared_database: DatabaseConfig) -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(**_prepared_database.connection_kwargs)
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture(scope="session")
def database_config() -> DatabaseConfig:
    try:
        config = load_database_config()
        test_name = os.environ.get("DB_NAME_TESTE", f"{config.name}_teste")
        return replace(config, name=test_name)
    except ValueError as error:
        pytest.skip(f"Configuracao do banco indisponivel: {error}")


@pytest.fixture(scope="session")
def _prepared_database(database_config: DatabaseConfig) -> Iterator[DatabaseConfig]:
    try:
        connection = psycopg.connect(
            **database_config.connection_kwargs, autocommit=True)
    except psycopg.OperationalError as error:
        pytest.skip(f"PostgreSQL indisponivel em {
                    database_config.host}:{database_config.port}: {error}")

    with connection:
        with connection.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            cur.execute(read_sql("01_schema.sql"))
            cur.execute(read_sql("02_dados_teste.sql"))

            crud_statements = split_sql_statements(
                read_sql("03_crud_consultas.sql"))
            for statement in crud_statements:
                if "CREATE OR REPLACE FUNCTION" in statement.upper():
                    cur.execute(statement)

    yield database_config


@pytest.fixture(scope="session")
def crud_statements() -> list[str]:
    return split_sql_statements(read_sql("03_crud_consultas.sql"))


@pytest.fixture(scope="session")
def analiticas_statements() -> list[str]:
    return split_sql_statements(read_sql("04_consultas_analiticas.sql"))
