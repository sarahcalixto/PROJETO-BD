# Sistema de Gestão Hospitalar Dra. Yuska Maritan Brito

Projeto acadêmico em PostgreSQL 16, SQLAlchemy 2 e Streamlit para gerenciar
atendimentos, pacientes, profissionais, procedimentos, internações e escalas.
O repositório preserva as operações em SQL puro da Etapa 1 e apresenta sua
reimplementação por ORM, além das rotinas, triggers, views e concorrência da
Etapa 2.

## Pré-requisitos

- Python 3.12 ou superior;
- [`uv`](https://docs.astral.sh/uv/);
- Docker com Docker Compose, ou PostgreSQL 16 local.

## Instalação

```bash
git clone git@github.com:sarahcalixto/PROJETO-BD.git
cd PROJETO-BD
uv sync
cp .env.example .env
docker compose up -d --wait
uv run python scripts/preparar_banco.py
uv run streamlit run frontend/app.py
```

A aplicação fica disponível em `http://localhost:8501`. O preparador é
idempotente: cria uma base vazia pelo schema final ou migra uma base existente
antes de instalar as rotinas, triggers e views.

Variáveis padrão:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projeto_hospital
DB_USER=postgres
DB_PASSWORD=postgres
```

O arquivo `.env` é local e não deve ser versionado.

## Funcionalidades demonstráveis

- registro atômico de atendimento com múltiplos procedimentos;
- histórico do paciente, listagem e remoção protegida por faturamento;
- atualização de convênio e tempo médio por residente;
- consultas analíticas da Etapa 1;
- cadastro de escalas com atuações vigentes e visualização da ocupação do turno;
- reajuste transacional de data e turno da escala, mantendo residente, unidade
  e preceptor;
- três views e três consultas ORM avançadas;
- tempo médio de espera, auditoria e média real dos procedimentos;
- comparação lazy/eager e concorrência pessimista com logs.

A navegação usa somente conceitos do domínio: Visão geral, Atendimentos,
Pacientes, Escalas, Consultas e estatísticas e Auditoria.

## Como demonstrar

Para cadastrar, abra **Escalas**, mantenha **Nova escala**, informe data e
turno e selecione unidade, residente e preceptor. A página mostra a ocupação
existente; se o residente já estiver escalado naquele dia e turno, o PostgreSQL
rejeita a operação e a interface apresenta o conflito sem alterar os registros.

Para apresentar o reajuste, abra **Escalas**, escolha a escala, compare a
situação atual com o novo agendamento, informe data e turno e confirme. A
operação mantém residente, unidade e preceptor e verifica automaticamente
conflitos e vigência das atuações.

Para demonstrar concorrência pela interface, abra **Auditoria**, selecione
**Concorrência**, confirme a execução e use **Executar concorrência**. A mesma
demonstração pode ser executada no terminal:

```bash
uv run python scripts/demonstrar_concorrencia.py
```

O resultado esperado é: T1 obtém o lock e confirma; T2 aguarda e é rejeitada
com SQLSTATE `23505`; uma única escala permanece no destino; e os registros
temporários são removidos. O lock pessimista é adquirido pela função armazenada
e a constraint de unicidade do PostgreSQL garante o estado final.

## Scripts SQL

| Script | Finalidade |
|---|---|
| `01_schema.sql` | Schema físico completo e constraints |
| `02_dados_teste.sql` | Dados mínimos determinísticos |
| `03_crud_consultas.sql` | CRUD e consultas básicas em SQL puro |
| `04_consultas_analiticas.sql` | Consultas analíticas em SQL puro |
| `05_procedures.sql` | Três rotinas armazenadas |
| `06_triggers.sql` | Triggers obrigatórios e integridade temporal |
| `07_views.sql` | Três views obrigatórias |
| `08_migracao_etapa2.sql` | Migração estrutural idempotente |

As rotinas com retorno são funções armazenadas do PostgreSQL. Elas mantêm os
nomes `sp_*` pedidos no enunciado e são chamadas dentro de transações explícitas.

## Testes

Com o PostgreSQL saudável, a suíte recria apenas o schema `public` de
`projeto_hospital_teste`; o banco principal não é apagado.

```bash
uv run pytest
uv run pytest -q tests/test_servico_escalas.py
uv run pytest -q tests/test_concorrencia.py
uv run python -m compileall -q src frontend scripts tests
git diff --check
```

A última validação completa, com PostgreSQL disponível, resultou em **126 testes
aprovados**, sem falhas e sem testes ignorados.

## Estrutura

```text
frontend/                     aplicação e páginas Streamlit
src/projeto_hospital/orm/     mapeamentos e sessões SQLAlchemy
src/projeto_hospital/services operações, consultas e transações
src/projeto_hospital/ui/      componentes e acesso compartilhado a dados
sql/                          schema, dados, consultas e objetos programáveis
tests/                        validação SQL, ORM, concorrência e interface
docs/modelagem/               DER, modelo relacional e normalização
```

## Documentação

- [Requisitos oficiais](requisitos.md)
- [Artefatos de modelagem](docs/modelagem/README.md)
- [Relatório técnico da Etapa 2](docs/relatorio_etapa2.md)
- [Relatório da auditoria](docs/relatorio_auditoria.md)


