"""Configuração da conexão com o banco de dados."""

from dataclasses import dataclass
from os import environ
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class DatabaseConfig:
    """Parâmetros necessários para conectar ao PostgreSQL."""

    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def connection_kwargs(self) -> dict[str, str | int]:
        """Retorna argumentos compatíveis com ``psycopg.connect``."""

        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.name,
            "user": self.user,
            "password": self.password,
        }


def load_database_config(env_file: str | Path | None = ".env") -> DatabaseConfig:
    """Carrega e valida a configuração a partir do ambiente."""

    if env_file is not None:
        load_dotenv(dotenv_path=env_file, override=False)

    variable_names = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [name for name in variable_names if not environ.get(name)]
    if missing:
        raise ValueError(
            "Variáveis de ambiente obrigatórias ausentes: " + ", ".join(missing)
        )

    try:
        port = int(environ["DB_PORT"])
    except ValueError as error:
        raise ValueError("DB_PORT deve ser um número inteiro.") from error

    if not 1 <= port <= 65535:
        raise ValueError("DB_PORT deve estar entre 1 e 65535.")

    return DatabaseConfig(
        host=environ["DB_HOST"],
        port=port,
        name=environ["DB_NAME"],
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
    )
