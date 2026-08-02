"""Executa a demonstração de concorrência da Etapa 2."""

from __future__ import annotations

import logging

from projeto_hospital.orm import create_database_engine, create_session_factory
from projeto_hospital.services.concorrencia import demonstrar_concorrencia_escala


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = create_database_engine()
    try:
        resultado = demonstrar_concorrencia_escala(create_session_factory(engine))
    finally:
        engine.dispose()

    print(resultado)
    sucesso = (
        resultado.segunda_aguardou_lock
        and resultado.confirmadas == 1
        and resultado.rejeitadas == 1
        and resultado.escalas_no_destino == 1
    )
    return 0 if sucesso else 1


if __name__ == "__main__":
    raise SystemExit(main())
