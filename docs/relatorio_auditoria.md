# Relatório da auditoria e refatoração

## Fonte e método

A auditoria usou exclusivamente `requisitos.md`. Cada item mantido deve
implementar um requisito, permitir execução/teste ou compor uma entrega. O
worktree existente foi preservado e refatorado sem reset.

## Matriz de rastreabilidade dos requisitos

| Requisito oficial | Implementação | Teste ou evidência | Resultado |
|---|---|---|---|
| DER completo e justificativas | DER editável e PDF com entidades, cardinalidades e especializações | `pdfinfo`, `pdftotext` e conferência do arquivo Draw.io | Atendido |
| Modelo relacional e normalização até 3FN | Relações, chaves e justificativas de 1FN, 2FN e 3FN em `docs/modelagem/` | Revisão cruzada com `01_schema.sql` | Atendido |
| Schema com PK, FK, CHECK, NOT NULL e UNIQUE | Schema físico PostgreSQL 16 e garantias temporais complementares | `test_etapa2_base.py`, `test_triggers.py` | Atendido |
| Dados mínimos | Seed com 5 pacientes, 5 residentes, 5 preceptores, 3 unidades, 10 atendimentos e 10 procedimentos realizados | Consulta direta no banco recriado e suíte de integração | Atendido |
| Seis operações básicas em SQL puro | Funções e consultas de atendimento, histórico, procedimentos, convênio, remoção protegida e média por residente | `test_crud_consultas.py` | Atendido |
| Quatro consultas analíticas em SQL puro | Ranking, supervisão mensal, plantões mensais e pacientes sem alto risco | `test_consultas_analiticas.py` | Atendido |
| `sp_registrar_atendimento_completo` | Função armazenada com entrada JSONB e atomicidade na transação do chamador | Sucesso, JSON inválido e rollback em `test_procedures.py` | Atendido |
| `sp_calcular_tempo_medio_espera` | Função tabular para todas as unidades, inclusive média nula | Casos preenchidos, vazios e recomposição em `test_procedures.py` | Atendido |
| `sp_reajustar_escala` | Função com lock pessimista, validação de vigência e preservação de unidade/preceptor | Sucesso, conflitos e rollback em `test_procedures.py` | Atendido |
| `trg_check_sobreposicao_escala` | Trigger BEFORE INSERT/UPDATE e unicidade concorrente por residente/data/turno | INSERT e UPDATE entre unidades em `test_triggers.py` | Atendido |
| `trg_audita_atendimento` | Trigger AFTER INSERT/UPDATE/DELETE com imagens JSONB | Três operações e conteúdo exato em `test_triggers.py` | Atendido |
| `trg_atualiza_media_procedimentos` | Trigger que mantém a média após INSERT, UPDATE e DELETE | Inserção, alteração, remoção e rollback em `test_triggers.py` | Atendido |
| Três views oficiais | Internados, residentes sem supervisor doutor ativo e estatísticas mensais | Conteúdo, casos vazios e desempate em `test_views.py` | Atendido |
| Operações da Etapa 1 com ORM | Serviços SQLAlchemy 2 com DTOs e sessões transacionais, sem SQL textual | `test_orm_operacoes.py`, `test_orm_consultas.py` | Atendido |
| Relacionamentos lazy e eager | Medição reproduzível do número de consultas e eager loading seletivo | `test_orm_carregamento_transacoes.py` | Atendido |
| Três consultas ORM avançadas | Flamengo, último atendimento completo e percentual de alto risco | `test_orm_avancado.py` | Atendido |
| Concorrência com duas transações | Duas sessões disputam o mesmo destino, uma confirma, outra é rejeitada, e uma terceira confere o estado | `test_concorrencia.py` e script demonstrativo | Atendido |
| Aplicação demonstrável | Seis páginas Streamlit expõem operações, consultas, escalas e evidências técnicas | `test_app.py`, testes de serviços e smoke HTTP | Atendido |
| README e relatório técnico | Instalação, execução, demonstração e decisões de procedures, triggers e ORM | Links locais, comandos documentados e revisão do conteúdo | Atendido |
| Histórico Git separado por etapas | Commits existentes preservam a evolução e os novos commits são separados por responsabilidade | Revisão de `git log` antes da publicação | Atendido localmente |
| Apresentação, publicação e paginação final | Dependem da entrega fora do código | Não verificáveis no worktree | Atividades externas; não bloqueiam a conformidade técnica |

Não permaneceram requisitos funcionais ausentes. As únicas pendências são
entregas externas que não podem ser concluídas ou comprovadas pelo código.

## Problemas e soluções

| Problema encontrado | Requisito relacionado | Solução e validação |
|---|---|---|
| Um profissional podia possuir atuações simultâneas | histórico com um papel por instante | exclusion constraint temporal e teste de conflito |
| A especialização permitia atuação sem subtipo | residente/preceptor total e disjunto | constraint triggers diferidos e teste no commit |
| A trigger de escala tinha janela de corrida | conflito e concorrência | unicidade global por data/turno/residente, lock e teste com duas sessões |
| O frontend não permitia cadastrar escalas nem contextualizava conflitos | cadastro de escala e trigger de sobreposição | operação Nova escala, filtro de atuações vigentes, ocupação do turno e tradução segura da rejeição do PostgreSQL |
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
- `UV_CACHE_DIR=/tmp/projeto-bd-uv-cache uv run pytest -q`: **126 testes
  aprovados**, sem falhas e sem testes ignorados, com PostgreSQL disponível.
- `python -m compileall -q src frontend scripts tests`: concluído sem erros.
- `git diff --check`: concluído sem erros de whitespace.
- O PDF do DER foi conferido com `pdfinfo` e `pdftotext`: duas páginas A4 e
  presença das entidades Internação, Auditoria, Alergia e Escala.
- O smoke test da interface usa `streamlit.testing.v1.AppTest` na suíte; nenhum
  servidor persistente foi iniciado durante a auditoria.
