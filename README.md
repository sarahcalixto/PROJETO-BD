# Sistema de Gestão Hospitalar Dra. Yuska Maritan Brito

Projeto da disciplina de Banco de Dados para modelar e implementar, em PostgreSQL, a gestão de pessoas, pacientes, profissionais, unidades hospitalares, atendimentos, procedimentos e escalas de plantão.

## Stack

- Python 3.12 ou superior;
- PostgreSQL;
- `uv` para ambiente e dependências;
- `psycopg[binary]` para acesso ao banco;
- `python-dotenv` para configuração local;
- `pytest` para testes.

O projeto não utiliza ORM, SQLAlchemy ou Alembic nesta etapa.

## Instalação

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>

uv sync
cp .env.example .env
uv run pytest
```

O `uv sync` cria e gerencia automaticamente o ambiente virtual `.venv` com a versão de Python fixada pelo projeto.

## Configuração do banco

Copie `.env.example` para `.env` e ajuste os valores para sua instalação local do PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projeto_hospital
DB_USER=postgres
DB_PASSWORD=postgres
```

O arquivo `.env` é ignorado pelo Git e nunca deve ser versionado. Para verificar a versão do Python e a presença das variáveis sem abrir uma conexão nem imprimir a senha, execute:

```bash
uv run python scripts/check_environment.py
```

## Testes

```bash
uv run pytest
```

Os testes iniciais validam apenas o carregamento seguro da configuração; não exigem um servidor PostgreSQL ativo.

## Estrutura

```text
.
├── docs/
│   ├── contrato_modelo.md
│   ├── decisoes_pendentes.md
│   ├── modelagem/
│   │   ├── README.md
│   │   ├── modelo_relacional.md
│   │   └── normalizacao.md
│   └── requisitos/requisitos_etapa_1.md
├── scripts/check_environment.py
├── sql/
│   ├── 01_schema.sql
│   ├── 02_dados_teste.sql
│   ├── 03_crud_consultas.sql
│   └── 04_consultas_analiticas.sql
├── src/projeto_hospital/
│   ├── __init__.py
│   ├── config.py
│   └── database.py
├── tests/
│   ├── __init__.py
│   └── test_config.py
├── .env.example
├── .python-version
├── pyproject.toml
└── uv.lock
```

Os arquivos SQL são apenas reservas nesta branch e devem ser preenchidos exclusivamente pelos responsáveis.

## Divisão da equipe

- Sarah: organização, convenções, contrato do esquema, DER, modelo relacional e normalização.
- Ruan: criação do esquema (`01_schema.sql`) e dados de teste (`02_dados_teste.sql`).
- Samuel: CRUD e consultas básicas (`03_crud_consultas.sql`).
- Carol: consultas analíticas (`04_consultas_analiticas.sql`).

## DER

O diagrama deve ser criado no diagrams.net. Salve o editável como `docs/modelagem/der_hospital.drawio` e exporte a entrega como `docs/modelagem/der_hospital.pdf`. Os dois arquivos devem ser mantidos: o PDF não substitui a fonte editável. Consulte `docs/modelagem/README.md` antes de versioná-los.

## Branches e commits

- `main`: versão estável e integrada.
- `feature/modelagem`: modelagem e documentação sob responsabilidade da Sarah.
- Demais trabalhos devem usar branches de funcionalidade próprias e abrir integração somente após revisão.

Os commits devem seguir Conventional Commits, no formato `tipo(escopo opcional): descrição`, e conter uma única mudança lógica. Exemplos: `docs: add relational model template` e `test: add initial configuration test`.
