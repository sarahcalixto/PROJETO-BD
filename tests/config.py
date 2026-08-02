import os
from collections.abc import Iterator
from dataclasses import replace

import psycopg
import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from projeto_hospital.config import DatabaseConfig, load_database_config
from projeto_hospital.orm import create_database_engine, create_session_factory

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
def orm_engine(_prepared_database: DatabaseConfig) -> Iterator[Engine]:
    """Engine SQLAlchemy conectado ao banco de teste já preparado."""
    engine = create_database_engine(_prepared_database)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def orm_session_factory(
    orm_engine: Engine,
) -> sessionmaker[Session]:
    return create_session_factory(orm_engine)


@pytest.fixture()
def orm_session(
    orm_session_factory: sessionmaker[Session],
) -> Iterator[Session]:
    session = orm_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


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
        pytest.skip(
            "PostgreSQL indisponivel em "
            f"{database_config.host}:{database_config.port}: {error}"
        )

    with connection:
        with connection.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            cur.execute(read_sql("01_schema.sql"))
            cur.execute(read_sql("02_dados_teste.sql"))
            cur.execute(read_sql("05_procedures.sql"))
            cur.execute(read_sql("06_triggers.sql"))
            cur.execute(read_sql("07_views.sql"))
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
