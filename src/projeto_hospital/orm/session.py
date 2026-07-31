"""Configuração de engine e sessões transacionais SQLAlchemy."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from projeto_hospital.config import DatabaseConfig, load_database_config


def create_database_engine(
    config: DatabaseConfig | None = None,
    *,
    echo: bool = False,
) -> Engine:
    """Cria um engine sem interpolar credenciais manualmente na URL."""
    database = config or load_database_config()
    url = URL.create(
        drivername="postgresql+psycopg",
        username=database.user,
        password=database.password,
        host=database.host,
        port=database.port,
        database=database.name,
    )
    return create_engine(url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Cria a fábrica de sessões usada pelos serviços da aplicação."""
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Confirma a transação no sucesso e executa rollback em qualquer falha."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
