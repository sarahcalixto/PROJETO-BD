# Normalização até a Terceira Forma Normal

Esta análise considera o modelo relacional 3.0 e as regras de negócio registradas no contrato. Uma seta `X → Y` indica que X determina funcionalmente Y.

## Dependências funcionais

| Relação | Dependências funcionais relevantes |
|---|---|
| PESSOA | `id_pessoa → nome, cpf, data_nascimento, is_flamengo, telefone`; `cpf → id_pessoa, nome, data_nascimento, is_flamengo, telefone` |
| PACIENTE | `id_pessoa → num_convenio, alergias, grupo_sanguineo` |
| PROFISSIONAL | `id_pessoa → crm, data_admissao, especialidade`; `crm → id_pessoa, data_admissao, especialidade` |
| ATUACAO_PROFISSIONAL | `id_atuacao → id_profissional, data_inicio, data_fim` |
| ATUACAO_RESIDENTE | `id_atuacao → ano_residencia` |
| ATUACAO_PRECEPTOR | `id_atuacao → titulacao` |
| UNIDADE | `id_unidade → nome, tipo, capacidade_leitos` |
| ATENDIMENTO | `id_atendimento → data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade` |
| PROCEDIMENTO | `id_procedimento → codigo, nome, tempo_medio_minutos, nivel_risco, media_tempo_procedimento`; `codigo →` os mesmos atributos |
| PROCEDIMENTO_REALIZADO | `(id_atendimento, id_procedimento) → quantidade, tempo_real_minutos, data_hora_inicio, observacao, faturado` |
| ESCALA | `id_escala → id_unidade, turno, data_plantao, id_atuacao_residente, id_atuacao_preceptor`; `(id_unidade, data_plantao, turno, id_atuacao_residente) → id_escala, id_atuacao_preceptor` |
| INTERNACAO | `id_internacao → id_paciente, id_unidade, data_hora_entrada, data_hora_saida` |
| AUDITORIA_ATENDIMENTO | `id_auditoria → id_atendimento, operacao, usuario, data_hora, dados_antigos, dados_novos` |

CPF, CRM, código do procedimento e a combinação única da escala são chaves candidatas conforme as restrições aprovadas. Como `data_plantao → dia_semana`, o dia da semana é derivado em consultas e não é armazenado em ESCALA; isso elimina a dependência transitiva que surgiria ao manter os dois valores.

## Primeira Forma Normal (1FN)

Todas as relações possuem chave identificadora e não contêm grupos repetitivos. IDs, datas, indicadores, quantidades e descrições são tratados como valores escalares.

`alergias`, `telefone` e `observacao` são considerados campos textuais atômicos no escopo da Etapa 1. Se o sistema futuramente precisar pesquisar alergias ou manter vários telefones individualmente, esses atributos deverão ser decompostos em relações próprias; essa necessidade não está no enunciado atual.

PROCEDIMENTO_REALIZADO elimina o grupo repetitivo de procedimentos dentro de ATENDIMENTO: cada tipo realizado ocupa uma tupla identificada pelo par atendimento–procedimento.

## Segunda Forma Normal (2FN)

Apenas PROCEDIMENTO_REALIZADO possui chave primária composta. `quantidade`, `tempo_real_minutos`, `observacao` e `faturado` descrevem a ocorrência de um procedimento específico em um atendimento específico e, portanto, dependem do par completo. Nenhum deles é propriedade isolada de ATENDIMENTO ou PROCEDIMENTO.

As demais relações têm chave primária simples; logo, não podem apresentar dependência parcial da chave primária. A chave candidata composta de ESCALA também determina a tupla completa e não produz dependência parcial declarada.

Consequentemente, todas as relações satisfazem a 2FN.

## Terceira Forma Normal (3FN)

Os dados descritivos das entidades referenciadas não são repetidos nas relações dependentes: ATENDIMENTO mantém apenas IDs de paciente, atuações e unidade; ESCALA mantém apenas IDs das atuações e unidade; PROCEDIMENTO_REALIZADO mantém apenas os IDs do atendimento e procedimento. Nome do paciente, dados profissionais, nome da unidade e descrição do procedimento permanecem em suas relações próprias.

As especializações também evitam dependências transitivas: atributos gerais ficam em PESSOA ou PROFISSIONAL; datas do papel ficam em ATUACAO_PROFISSIONAL; `ano_residencia` e `titulacao` ficam somente nos subtipos correspondentes.

`media_tempo_procedimento` é uma redundância derivada e controlada exigida pela
Etapa 2. Ela é mantida exclusivamente por trigger e não deve ser editada pela
aplicação. As demais dependências mantêm as relações em 3FN; a tabela de
auditoria é um registro histórico imutável.

## Justificativa por relação

| Relação | 1FN | 2FN | 3FN |
|---|---|---|---|
| PESSOA | Atributos escalares; PK definida | Chave simples | Dados pessoais dependem somente de id_pessoa ou da chave candidata cpf |
| PACIENTE | Atributos escalares; PK definida | Chave simples | Dados clínicos/cadastrais dependem somente de id_pessoa |
| PROFISSIONAL | Atributos escalares; PK definida | Chave simples | Dados profissionais dependem somente de id_pessoa ou crm |
| ATUACAO_PROFISSIONAL | Uma tupla por período de atuação | Chave simples | Profissional e vigência dependem somente de id_atuacao |
| ATUACAO_RESIDENTE | Uma tupla por atuação residente | Chave simples | Ano depende somente de id_atuacao |
| ATUACAO_PRECEPTOR | Uma tupla por atuação preceptora | Chave simples | Titulação depende somente de id_atuacao |
| UNIDADE | Atributos escalares; PK definida | Chave simples | Dados da unidade dependem somente de id_unidade |
| ATENDIMENTO | Uma tupla por atendimento | Chave simples | Não replica atributos das entidades referenciadas |
| PROCEDIMENTO | Atributos escalares; PK definida | Chave simples | Dados dependem somente de id_procedimento ou codigo |
| PROCEDIMENTO_REALIZADO | Uma tupla por par atendimento–procedimento | Todos os atributos não-chave dependem da chave completa | Não replica dados de atendimento ou procedimento |
| ESCALA | Uma tupla por alocação de plantão | Chave primária simples e chave candidata composta completas | Supervisor e demais dados são determinados pelas chaves candidatas |
| INTERNACAO | Uma tupla por período de internação | Chave simples | Paciente, unidade e período dependem somente de id_internacao |
| AUDITORIA_ATENDIMENTO | Uma tupla por evento auditado | Chave simples | Metadados e imagens dependem somente de id_auditoria |

## Integridade sem alteração da normalização

- A totalidade e disjunção de ATUACAO_PROFISSIONAL são restrições entre relações, não dependências que exijam nova decomposição.
- Vigência e não sobreposição de períodos são regras temporais e não alteram a forma normal.
- `dia_semana` deve ser calculado a partir de `data_plantao`; armazená-lo como coluna independente reintroduziria redundância e anomalia de atualização.
- Campos de domínio (`nivel_risco`, `ano_residencia`, `turno`, `tipo`) requerem CHECKs, mas continuam atômicos.
