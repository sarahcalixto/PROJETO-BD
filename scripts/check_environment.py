"""Verifica os pré-requisitos locais sem abrir conexão ou expor segredos."""

import sys

from projeto_hospital.config import load_database_config


def main() -> int:
    """Retorna zero quando Python e configuração atendem aos requisitos."""

    if sys.version_info < (3, 12):
        print("Erro: Python 3.12 ou superior é necessário.")
        return 1

    try:
        config = load_database_config()
    except ValueError as error:
        print(f"Erro de configuração: {error}")
        return 1

    print(f"Python: {sys.version.split()[0]}")
    print(f"Banco configurado: {config.host}:{config.port}/{config.name}")
    print("Credenciais: definidas (valor oculto)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
