"""Erros de domínio produzidos pelos serviços ORM."""

from __future__ import annotations

from typing import Any


class ServicoORMError(Exception):
    """Classe-base para falhas esperadas da camada de serviços."""


class EntidadeNaoEncontrada(ServicoORMError):
    def __init__(self, entidade: str, identificador: Any) -> None:
        self.entidade = entidade
        self.identificador = identificador
        super().__init__(f"{entidade} não encontrado(a): {identificador}")


class RegraNegocioViolada(ServicoORMError):
    """Indica que uma operação válida tecnicamente viola o domínio."""
