# Divisão de tarefas da Etapa 2

## Fluxo de trabalho

1. Sarah entrega e integra `feature/etapa2-base`.
2. Os demais integrantes criam suas branches a partir da `main` atualizada.
3. Carol, Ruan e Samuel trabalham em paralelo e entregam testes junto ao código.
4. Sarah revisa e integra na ordem Carol, Ruan e Samuel.
5. Sarah adapta o front, fecha a documentação e valida a entrega completa.

## Sarah — base, ORM compartilhada e integração

### Entrega inicial

- Consolidar requisitos e contratos técnicos.
- Evoluir o esquema e os dados de teste.
- Adicionar SQLAlchemy, modelos, engine, sessões e fixtures compartilhadas.
- Atualizar README e convenções de colaboração.
- Integrar a base na `main` antes do início das outras branches.

Esta entrega já foi concluída na `main`.

### Complemento da base ORM

- Demonstrar explicitamente a diferença entre lazy loading e eager loading.
- Manter os testes compartilhados de sessão, commit e rollback.
- Testar o carregamento e a navegação dos relacionamentos entre as entidades.
- Deixar fixtures e exemplos reutilizáveis para os testes do Samuel.

### Entrega final

- Revisar e integrar as branches da Carol, do Ruan e do Samuel.
- Resolver incompatibilidades entre schema, objetos SQL, serviços ORM e front.
- Migrar os fluxos atuais do front de SQL puro para os serviços ORM.
- Adicionar ao front o registro de atendimento completo e o reajuste de escala.
- Adicionar telas de consulta para as views e consultas ORM avançadas.
- Manter auditoria e concorrência demonstradas por testes e logs, sem criar
  telas operacionais específicas para esses recursos.
- Atualizar os testes do front e executar a suíte completa com PostgreSQL.
- Atualizar o README com instalação, execução, ordem dos scripts e demonstração.
- Concluir o relatório, explicando procedures versus triggers, ORM e
  concorrência.
- Criar a tag da entrega somente depois da validação completa.

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
- Usar a infraestrutura de sessão, relacionamentos e carregamento preparada
  pela Sarah, sem criar uma segunda configuração ORM.
- Testar sucesso e falha das próprias operações, incluindo resultados vazios,
  entidades inexistentes e regras específicas de cada serviço.

## Regras de colaboração

- Criar a branch somente depois da integração de `feature/etapa2-base`.
- Não alterar arquivos de responsabilidade de outro integrante sem combinar.
- Usar Conventional Commits e uma mudança lógica por commit.
- Atualizar a branch com a `main` antes de abrir a integração.
- Toda entrega deve passar em `uv run pytest` com PostgreSQL disponível.
