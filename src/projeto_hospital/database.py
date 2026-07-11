"""Acesso inicial ao PostgreSQL sem camada ORM."""

from psycopg import Connection, connect

from projeto_hospital.config import DatabaseConfig


def open_connection(config: DatabaseConfig) -> Connection:
    """Abre uma conexão usando a configuração validada."""

    return connect(**config.connection_kwargs)
