# Normalização até a Terceira Forma Normal

Este documento é o roteiro da análise formal. As justificativas devem ser completadas com base no DER aprovado, nas regras de negócio confirmadas e nas dependências funcionais identificadas pelo grupo.

## Dependências funcionais

Para cada relação, registrar no formato `determinante → atributos determinados`:

| Relação | Dependências funcionais | Fonte/regra de negócio |
|---|---|---|
| PESSOA | A preencher | A preencher |
| PACIENTE | A preencher | A preencher |
| PROFISSIONAL | A preencher | A preencher |
| PRECEPTOR | A preencher | A preencher |
| RESIDENTE | A preencher | A preencher |
| UNIDADE | A preencher | A preencher |
| ATENDIMENTO | A preencher | A preencher |
| PROCEDIMENTO | A preencher | A preencher |
| PROCEDIMENTO_REALIZADO | A preencher | A preencher |
| ESCALA | A preencher | A preencher |

## Primeira Forma Normal (1FN)

Documentar, para cada relação:

- a atomicidade dos atributos;
- a ausência de grupos repetitivos;
- o identificador da tupla;
- eventuais atributos multivalorados que exijam revisão.

## Segunda Forma Normal (2FN)

Documentar:

- quais relações possuem chave composta;
- se todo atributo não-chave depende da chave completa;
- qualquer dependência parcial encontrada e sua decomposição proposta.

## Terceira Forma Normal (3FN)

Documentar:

- dependências transitivas entre atributos não-chave;
- decomposições necessárias;
- preservação das dependências e junção sem perda;
- justificativa final de 3FN para cada relação.

## Análise de PROCEDIMENTO_REALIZADO

A relação possui a chave composta `(id_atendimento, id_procedimento)`. A análise deve demonstrar, usando regras de negócio confirmadas, se `quantidade`, `tempo_real_minutos` e `observacao` dependem da chave completa e se existem dependências parciais ou transitivas. Não presumir a resposta sem validar a semântica desses atributos.

## Justificativas por relação

| Relação | 1FN | 2FN | 3FN | Ajuste necessário |
|---|---|---|---|---|
| PESSOA | A preencher | A preencher | A preencher | A preencher |
| PACIENTE | A preencher | A preencher | A preencher | A preencher |
| PROFISSIONAL | A preencher | A preencher | A preencher | A preencher |
| PRECEPTOR | A preencher | A preencher | A preencher | A preencher |
| RESIDENTE | A preencher | A preencher | A preencher | A preencher |
| UNIDADE | A preencher | A preencher | A preencher | A preencher |
| ATENDIMENTO | A preencher | A preencher | A preencher | A preencher |
| PROCEDIMENTO | A preencher | A preencher | A preencher | A preencher |
| PROCEDIMENTO_REALIZADO | A preencher | A preencher | A preencher | A preencher |
| ESCALA | A preencher | A preencher | A preencher | A preencher |

## Observações sobre chaves compostas

- Identificar atributos primos e não-primos.
- Verificar dependências parciais antes de afirmar conformidade com a 2FN.
- Documentar a finalidade de cada chave candidata e restrição de unicidade.
- Não tratar automaticamente a restrição única de ESCALA como sua chave primária.
