# Decisões pendentes da modelagem

Os itens abaixo evidenciam lacunas entre o enunciado e o contrato inicial. São propostas para discussão, não alterações autorizadas. Até aprovação explícita, nenhum atributo deve ser incorporado ao DER, ao modelo relacional ou ao SQL.

## 1. Endereço do paciente

O requisito prevê atualização de endereço, mas PACIENTE e PESSOA não possuem esse atributo.

**Decisão necessária:** definir se o endereço será um atributo simples, um conjunto de atributos ou uma relação própria, e se pertence a PESSOA ou apenas a PACIENTE.

## 2. Faturamento

A regra de remoção de procedimento depende de saber se o registro já foi faturado, informação ausente em PROCEDIMENTO_REALIZADO.

**Sugestão para avaliação:** `faturado BOOLEAN NOT NULL DEFAULT FALSE` em PROCEDIMENTO_REALIZADO.

## 3. Nível de risco

Uma consulta analítica exige identificar procedimentos com risco `ALTO`, mas PROCEDIMENTO não registra risco.

**Sugestão para avaliação:** atributo `nivel_risco` em PROCEDIMENTO, com domínio `BAIXO`, `MEDIO` e `ALTO`.

## 4. Escala por mês

A consulta mensal de escalas não pode ser respondida apenas com `dia_semana` e `turno`.

**Sugestões para avaliação:** adicionar `data_plantao` ou representar um período de vigência. O grupo deve escolher uma alternativa antes da implementação.

## 5. Atendimento por unidade

Consultas futuras demandam identificar em qual unidade ocorreu um atendimento, mas ATENDIMENTO não referencia UNIDADE.

**Sugestão para avaliação:** `id_unidade FK -> UNIDADE` em ATENDIMENTO.

## Registro de aprovação

Quando o grupo decidir cada ponto, registrar aqui a decisão, a justificativa, a data e os participantes; em seguida, atualizar de forma consistente o contrato, o DER, o modelo relacional e a normalização.
