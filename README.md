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

Copie `.env.example` para `.env` e ajuste os valores se necessário:

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

### Subindo o PostgreSQL

Opção recomendada (não exige instalar PostgreSQL na máquina):

```bash
docker compose up -d
```

Isso sobe um PostgreSQL 16 em `localhost:5432` com usuário/senha `postgres`, já criando os bancos `projeto_hospital` e `projeto_hospital_teste` (este último usado pelos testes de integração).

Alternativa sem Docker (instalação local do PostgreSQL):

```bash
sudo pacman -S postgresql          # ou o gerenciador de pacotes da sua distro
sudo -iu postgres initdb -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
sudo -iu postgres psql \
  -c "ALTER ROLE postgres WITH PASSWORD 'postgres';" \
  -c "CREATE DATABASE projeto_hospital OWNER postgres;" \
  -c "CREATE DATABASE projeto_hospital_teste OWNER postgres;"
```

## Testes

```bash
uv run pytest
```

`test_crud_consultas.py` e `test_consultas_analiticas.py` são testes de integração: recriam o schema a partir de `sql/01_schema.sql`, carregam `sql/02_dados_teste.sql` e executam as funções/consultas de `sql/03_crud_consultas.sql` e `sql/04_consultas_analiticas.sql` contra o banco `projeto_hospital_teste`. Eles são pulados automaticamente (`SKIPPED`) se esse banco não estiver acessível. As fixtures usadas por esses testes ficam em `tests/config.py`, registrado como plugin do pytest via `addopts = "-p tests.config"` em `pyproject.toml` (em vez de um `conftest.py`).

## Estrutura

```text
.
├── docs/
│   ├── contrato_modelo.md
│   ├── decisoes_pendentes.md
│   ├── modelagem/
│   │   ├── README.md
│   │   ├── der_hospital.drawio
│   │   ├── der_hospital.pdf
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
│   ├── config.py
│   ├── utils.py
│   ├── test_crud_consultas.py
│   └── test_consultas_analiticas.py
├── .env.example
├── .python-version
├── docker-compose.yml
├── pyproject.toml
└── uv.lock
```

## Divisão da equipe

- Sarah: organização, convenções, contrato do esquema, DER, modelo relacional e normalização.
- Ruan: criação do esquema (`01_schema.sql`) e dados de teste (`02_dados_teste.sql`).
- Samuel: CRUD e consultas básicas (`03_crud_consultas.sql`).
- Carol: consultas analíticas (`04_consultas_analiticas.sql`).

## DER

O diagrama foi criado no diagrams.net e está versionado como `docs/modelagem/der_hospital.drawio`. A entrega `docs/modelagem/der_hospital.pdf` inclui o DER e as justificativas de cardinalidades e especializações. Os dois arquivos devem ser mantidos: o PDF não substitui a fonte editável.

## Branches e commits

- `main`: versão estável e integrada.
- `feature/modelagem`: modelagem e documentação sob responsabilidade da Sarah.
- Demais trabalhos devem usar branches de funcionalidade próprias e abrir integração somente após revisão.

Os commits devem seguir Conventional Commits, no formato `tipo(escopo opcional): descrição`, e conter uma única mudança lógica. Exemplos: `docs: add relational model template` e `test: add initial configuration test`.
