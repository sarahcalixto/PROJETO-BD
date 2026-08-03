# Relatório da auditoria e refatoração

## Fonte e método

A auditoria usou exclusivamente `requisitos.md`. Cada item mantido deve
implementar um requisito, permitir execução/teste ou compor uma entrega. O
worktree existente foi preservado e refatorado sem reset.

## Cobertura dos requisitos

| Grupo | Situação após a refatoração | Evidência principal |
|---|---|---|
| DER, modelo relacional e 3FN | Atendido | `docs/modelagem/` |
| Schema, constraints e dados mínimos | Atendido | `sql/01_schema.sql`, `02_dados_teste.sql` |
| CRUD e consultas SQL puro | Atendido | `03_crud_consultas.sql`, `04_consultas_analiticas.sql` |
| Três rotinas armazenadas | Atendido | `05_procedures.sql` |
| Três triggers obrigatórios | Atendido | `06_triggers.sql` |
| Três views | Atendido | `07_views.sql` |
| Operações e consultas ORM | Atendido | `src/projeto_hospital/services/` |
| Lazy/eager e transações | Atendido | serviço de carregamento e testes |
| Concorrência com duas transações e logs | Atendido | serviço e script de concorrência |
| Interface de demonstração | Atendido | seis páginas Streamlit de domínio |
| README e relatório técnico | Atendido | README e `relatorio_etapa2.md` |
| Apresentação, publicação e paginação | Não verificável localmente | atividades manuais externas |

Não permaneceram requisitos funcionais ausentes. As únicas pendências são
entregas externas que não podem ser concluídas ou comprovadas pelo código.

## Problemas e soluções

| Problema encontrado | Requisito relacionado | Solução e validação |
|---|---|---|
| Um profissional podia possuir atuações simultâneas | histórico com um papel por instante | exclusion constraint temporal e teste de conflito |
| A especialização permitia atuação sem subtipo | residente/preceptor total e disjunto | constraint triggers diferidos e teste no commit |
| A trigger de escala tinha janela de corrida | conflito e concorrência | unicidade global por data/turno/residente, lock e teste com duas sessões |
| Média de espera omitiria unidades vazias | cálculo para cada unidade | LEFT JOIN e retorno nulo testado |
| Procedimento mais comum ignorava quantidade | estatística mensal | ranking por `SUM(quantidade)` e desempate alfabético |
| Seed continha pessoas e evidências técnicas extras | dados mínimos de teste | cinco pacientes, residentes e preceptores; evidências criadas pelos testes |
| Script demonstrativo persistia dados artificiais | repositório enxuto | remoção de `09_dados_demonstracao_etapa2.sql` |
| Concorrência usava unidades diferentes e removia por datas | mesma combinação e preservação de dados | mesma unidade e limpeza somente pelos IDs temporários |
| Interface tinha onze wrappers e módulos de 600–750 linhas | frontend objetivo | seis scripts diretos com navegação por domínio |
| CSS dependia de seletores internos do Streamlit | manutenção da interface | remoção do CSS; uso do tema e APIs nativas |
| Documentos descreviam vídeo e requisitos não oficiais | fonte de verdade única | remoção e consolidação nos quatro documentos finais |
| DER não mostrava entidades da Etapa 2 | DER completo | inclusão de Internação, Auditoria e atributos derivados |

## Arquivos removidos ou consolidados

- Removidos: Gherkin, especificação funcional intermediária, revisão de QA,
  divisão de equipe, decisões encerradas, roteiro de vídeo, requisitos
  duplicados, matriz antiga e contrato duplicado do modelo.
- Consolidados: documentação normativa em `requisitos.md`; esquema lógico em
  `modelo_relacional.md`; decisões técnicas em `relatorio_etapa2.md`; cobertura
  e alterações neste relatório.
- Código removido: `database.py`, `ui/pages.py`, `ui/stage2.py`, onze wrappers
  antigos e o seed demonstrativo persistente.
- Mantidos: scripts SQL da Etapa 1, migração, mapeamentos, serviços, testes por
  requisito, DER editável/PDF e script de concorrência.

## Inconsistências do enunciado e decisões

- ESCALA é apresentada com `dia_semana`, mas uma consulta exige contagem no mês.
  O modelo armazena `data_plantao` e deriva o dia.
- A descrição de unicidade menciona o preceptor, mas o exemplo e a tabela
  sugerida exigem um único supervisor por residente. A chave não inclui o
  preceptor e a regra global impede duas unidades no mesmo turno.
- “Procedimento mais comum” não define o critério. Foi usada a soma de
  `quantidade`, com desempate alfabético determinístico.
- “Percentual de procedimentos” pode significar linhas ou quantidade. A ORM
  conta ocorrências de PROCEDIMENTO_REALIZADO, conforme a entidade associativa.
- PostgreSQL distingue procedure de função. As rotinas com retorno são funções
  armazenadas e mantêm os nomes `sp_*` oficiais.

## Validação

- Schema novo, migração idempotente e dados mínimos são recriados no banco
  isolado `projeto_hospital_teste`.
- A suíte cobre CRUD, consultas, rollback, triggers, views, ORM, loading,
  concorrência e contratos da interface.
- `UV_CACHE_DIR=/tmp/projeto-bd-uv-cache uv run pytest -q`: **115 testes
  aprovados**, sem falhas e sem testes ignorados, com PostgreSQL disponível.
- `python -m compileall -q src frontend scripts tests`: concluído sem erros.
- `git diff --check`: concluído sem erros de whitespace.
- O PDF do DER foi conferido com `pdfinfo` e `pdftotext`: duas páginas A4 e
  presença das entidades Internação, Auditoria, Alergia e Escala.
- O smoke test da interface usa `streamlit.testing.v1.AppTest` na suíte; nenhum
  servidor persistente foi iniciado durante a auditoria.
