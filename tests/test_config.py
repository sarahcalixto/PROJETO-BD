"""Testes da configuração inicial do banco."""

import pytest

from projeto_hospital.config import load_database_config


VARIABLE_NAMES = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


def set_valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "projeto_hospital_teste",
        "DB_USER": "usuario_teste",
        "DB_PASSWORD": "segredo_teste",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_load_database_config_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)

    config = load_database_config(env_file=None)

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.name == "projeto_hospital_teste"
    assert config.connection_kwargs["dbname"] == "projeto_hospital_teste"


def test_load_database_config_reports_missing_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in VARIABLE_NAMES:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"):
        load_database_config(env_file=None)


@pytest.mark.parametrize("port", ["invalid", "0", "65536"])
def test_load_database_config_rejects_invalid_port(
    monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("DB_PORT", port)

    with pytest.raises(ValueError, match="DB_PORT"):
        load_database_config(env_file=None)
