# Sistema de Gestão Hospitalar Dra. Yuska Maritan Brito

Projeto da disciplina de Banco de Dados para modelar e implementar, em PostgreSQL, a gestão de pessoas, pacientes, profissionais, unidades hospitalares, atendimentos, procedimentos e escalas de plantão.

## Stack

- Python 3.12 ou superior;
- PostgreSQL;
- `uv` para ambiente e dependências;
- `psycopg[binary]` para acesso ao banco;
- `python-dotenv` para configuração local;
- SQLAlchemy 2.x para o mapeamento objeto-relacional da Etapa 2;
- `pytest` para testes.

O acesso SQL puro da Etapa 1 permanece versionado. A Etapa 2 adiciona uma
camada SQLAlchemy sem remover os scripts originais.

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
docker compose up -d --wait
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
uv run pytest tests/test_app.py
uv run pytest tests/test_procedures.py tests/test_triggers.py tests/test_views.py
uv run pytest tests/test_orm_operacoes.py tests/test_orm_consultas.py tests/test_orm_avancado.py
uv run pytest tests/test_aceitacao_etapa2.py
uv run pytest
```

Os testes de integração recriam o schema a partir de `sql/01_schema.sql`,
carregam, nesta ordem, `02_dados_teste.sql`, `05_procedures.sql`,
`06_triggers.sql` e `07_views.sql`, e usam exclusivamente o banco
`projeto_hospital_teste`.
Eles são pulados automaticamente (`SKIPPED`) se esse banco não estiver
acessível. As fixtures compartilhadas de psycopg e SQLAlchemy ficam em
`tests/config.py`, registrado como plugin do pytest via `pyproject.toml`.

### Demonstração concorrente

Com o banco preparado pelos scripts, execute:

```bash
uv run python scripts/demonstrar_concorrencia.py
```

O programa abre duas sessões SQLAlchemy, faz as duas disputarem o lock do
mesmo residente e encerra com código zero somente quando uma transação confirma,
a outra é rejeitada e existe uma única escala no destino. Os logs mostram a
espera pelo lock pessimista.

### Ordem completa dos scripts SQL

1. `01_schema.sql`: tipos, tabelas, constraints e índices;
2. `02_dados_teste.sql`: massa mínima reproduzível;
3. `03_crud_consultas.sql`: operações SQL puro preservadas da Etapa 1;
4. `04_consultas_analiticas.sql`: consultas analíticas da Etapa 1;
5. `05_procedures.sql`: rotinas armazenadas e controle transacional;
6. `06_triggers.sql`: regras automáticas e auditoria;
7. `07_views.sql`: visões da Etapa 2.

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
│   ├── divisao_etapa_2.md
│   └── requisitos/
│       ├── requisitos_etapa_1.md
│       └── requisitos_etapa_2.md
├── frontend/
│   ├── app.py
│   ├── app_pages/
│   └── assets/
├── scripts/check_environment.py
├── scripts/demonstrar_concorrencia.py
├── sql/
│   ├── 01_schema.sql
│   ├── 02_dados_teste.sql
│   ├── 03_crud_consultas.sql
│   ├── 04_consultas_analiticas.sql
│   ├── 05_procedures.sql
│   ├── 06_triggers.sql
│   └── 07_views.sql
├── src/projeto_hospital/
│   ├── orm/
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── services/
│   └── ui/
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

A divisão detalhada da Etapa 2 está em
`docs/divisao_etapa_2.md`. Sarah entrega primeiro a base compartilhada; depois
Ruan assume procedures e concorrência, Carol assume triggers e views, e Samuel
assume operações e consultas ORM. Sarah realiza a integração e o front final.

## DER

O diagrama foi criado no diagrams.net e está versionado como `docs/modelagem/der_hospital.drawio`. A entrega `docs/modelagem/der_hospital.pdf` inclui o DER e as justificativas de cardinalidades e especializações. Os dois arquivos devem ser mantidos: o PDF não substitui a fonte editável.

## Branches e commits

- `main`: versão estável e integrada.
- `feature/etapa2-base`: infraestrutura compartilhada sob responsabilidade da Sarah.
- `feature/etapa2-procedures-concorrencia`: trabalho do Ruan.
- `feature/etapa2-triggers-views`: trabalho da Carol.
- `feature/etapa2-orm-operacoes`: trabalho do Samuel.
- Demais trabalhos devem usar branches de funcionalidade próprias e abrir integração somente após revisão.

Os commits devem seguir Conventional Commits, no formato `tipo(escopo opcional): descrição`, e conter uma única mudança lógica. Exemplos: `docs: add relational model template` e `test: add initial configuration test`.
