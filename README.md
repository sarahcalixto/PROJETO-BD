# Sistema de Gestão Hospitalar — Etapa 2

Aplicação PostgreSQL + SQLAlchemy + Streamlit para atendimentos, pacientes,
procedimentos, internações e escalas do Hospital Dra. Yuska Maritan Brito.

O produto final implementa procedures, triggers, views, ORM, consultas
avançadas e controle de concorrência, incluindo evidências no front.

## Pré-requisitos

- Python 3.12 ou superior;
- `uv`;
- Docker com Docker Compose, ou PostgreSQL 16 local.

## Instalação rápida

```bash
git clone git@github.com:sarahcalixto/PROJETO-BD.git
cd PROJETO-BD
uv sync
cp .env.example .env
docker compose up -d --wait
uv run python scripts/preparar_banco.py
uv run streamlit run frontend/app.py
```

Acesse `http://localhost:8501`.

O comando de preparação é idempotente. Em um banco vazio, instala diretamente
o produto final da Etapa 2. Em um banco existente do projeto, adiciona os
objetos novos, faz o backfill necessário e preserva os dados atuais.

As variáveis padrão são:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projeto_hospital
DB_USER=postgres
DB_PASSWORD=postgres
```

O `.env` não deve ser versionado.

## Recursos disponíveis no front

- atendimento completo com múltiplos procedimentos e rollback integral;
- seleções obrigatórias sem valores presumidos e proteção contra reenvio;
- histórico, convênio, procedimentos e análises usando SQLAlchemy ORM;
- reajuste atômico de escala;
- três views e três consultas ORM avançadas;
- média de espera por unidade;
- auditoria, status dos triggers e médias dos procedimentos;
- comparação lazy/eager e concorrência com logs reais.

## Testes

Com o PostgreSQL saudável:

```bash
uv run pytest tests/test_app.py
uv run pytest tests/test_services_front_etapa2.py tests/test_migracao_etapa2.py
uv run pytest tests/test_aceitacao_etapa2.py
uv run pytest
```

Os testes de integração recriam somente `projeto_hospital_teste`; o banco
principal não é apagado.

Validações adicionais:

```bash
uv run python -m compileall -q src frontend scripts tests
git diff --check
```

## Estrutura essencial

```text
frontend/                       entrada e scripts das páginas Streamlit
src/projeto_hospital/orm/       entidades, engine e sessões SQLAlchemy
src/projeto_hospital/services/  operações, consultas e transações
src/projeto_hospital/ui/        componentes, dados e páginas reutilizáveis
sql/                            schema, migração, rotinas, triggers, views e dados
tests/                          testes unitários, integração, interface e aceitação
```

## Scripts SQL

Os scripts `01` e `02` descrevem a base final. O script `08` preserva e migra
uma base existente. O preparador aplica as rotinas `05`, os triggers `06`, as
views `07` e os dados demonstrativos `09`.

## Documentação

- [Requisitos da Etapa 2](docs/requisitos/requisitos_etapa_2.md)
- [Relatório técnico](docs/relatorio_etapa2.md)
- [Matriz de conformidade](docs/matriz_conformidade_etapa2.md)
- [Modelo e normalização](docs/modelagem/README.md)

## Demonstração concorrente pelo terminal

```bash
uv run python scripts/demonstrar_concorrencia.py
```

A mesma demonstração está disponível em **Evidências técnicas**. O resultado
esperado é uma transação confirmada, uma rejeitada e somente uma escala válida.
