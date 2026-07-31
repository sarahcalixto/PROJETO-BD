# Divisão de tarefas da Etapa 2

## Fluxo de trabalho

1. Sarah entrega e integra `feature/etapa2-base`.
2. Os demais integrantes criam suas branches a partir da `main` atualizada.
3. Carol, Ruan e Samuel trabalham em paralelo e entregam testes junto ao código.
4. Sarah revisa e integra na ordem Carol, Ruan e Samuel.
5. Sarah adapta o front, fecha a documentação e valida a entrega completa.

## Sarah — base e integração

### Entrega inicial

- Consolidar requisitos e contratos técnicos.
- Evoluir o esquema e os dados de teste.
- Adicionar SQLAlchemy, modelos, engine, sessões e fixtures compartilhadas.
- Atualizar README e convenções de colaboração.
- Integrar a base na `main` antes do início das outras branches.

### Entrega final

- Migrar o front para os serviços ORM.
- Expor procedures, views e consultas avançadas voltadas ao usuário.
- Integrar branches, executar a suíte completa e concluir relatório e vídeo.

## Ruan — procedures e concorrência

Branch: `feature/etapa2-procedures-concorrencia`

- Implementar as três stored procedures em `sql/05_procedures.sql`.
- Implementar a simulação concorrente e o bloqueio pessimista.
- Testar sucesso, rollback, JSON inválido, conflitos e duas transações.

## Carol — triggers e views

Branch: `feature/etapa2-triggers-views`

- Implementar triggers em `sql/06_triggers.sql`.
- Implementar views em `sql/07_views.sql`.
- Testar auditoria, sobreposição, médias e resultados determinísticos das views.

## Samuel — operações ORM

Branch: `feature/etapa2-orm-operacoes`

- Reimplementar todas as operações da Etapa 1 com SQLAlchemy.
- Implementar as três consultas ORM avançadas.
- Demonstrar lazy e eager loading.
- Testar transações, relacionamentos, resultados vazios e entidades ausentes.

## Regras de colaboração

- Criar a branch somente depois da integração de `feature/etapa2-base`.
- Não alterar arquivos de responsabilidade de outro integrante sem combinar.
- Usar Conventional Commits e uma mudança lógica por commit.
- Atualizar a branch com a `main` antes de abrir a integração.
- Toda entrega deve passar em `uv run pytest` com PostgreSQL disponível.
