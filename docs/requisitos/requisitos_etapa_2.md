# Requisitos da Etapa 2

## Objetivo

Evoluir o sistema hospitalar com regras de negócio no PostgreSQL, persistência
com SQLAlchemy 2.x, consultas avançadas e controle explícito de concorrência.

## Contrato de dados da base

- `INTERNACAO` registra paciente, unidade, entrada e saída. Apenas uma
  internação sem alta é permitida por paciente.
- `PROCEDIMENTO_REALIZADO.data_hora_inicio` registra o início efetivo do
  procedimento e deve ser igual ou posterior ao atendimento correspondente.
- `PROCEDIMENTO.media_tempo_procedimento` armazena a média dos tempos reais e
  permanece nula enquanto não houver ocorrências.
- `AUDITORIA_ATENDIMENTO` preserva o identificador do atendimento mesmo após
  exclusão; por isso, `id_atendimento` não possui chave estrangeira.

## Stored procedures

### `sp_registrar_atendimento_completo`

Recebe os dados do atendimento e uma lista JSONB de procedimentos. Deve validar
as referências, inserir o atendimento e todos os procedimentos na mesma
transação e propagar qualquer erro para que o chamador faça rollback integral.

### `sp_calcular_tempo_medio_espera`

Calcula por unidade a média entre `ATENDIMENTO.data_hora` e o primeiro
`PROCEDIMENTO_REALIZADO.data_hora_inicio`. Atendimentos sem procedimento não
participam da média.

### `sp_reajustar_escala`

Move todas as escalas de um residente de uma data/turno de origem para outra
data/turno. A operação deve validar o conjunto completo antes de alterar dados e
falhar integralmente se houver conflito.

## Triggers

- `trg_check_sobreposicao_escala`: bloqueia o mesmo residente em mais de uma
  unidade na mesma data e turno, em `INSERT` e `UPDATE`.
- `trg_audita_atendimento`: registra `INSERT`, `UPDATE` e `DELETE`, incluindo
  usuário, instante e imagens JSONB anterior/nova.
- `trg_atualiza_media_procedimentos`: recalcula a média do procedimento após
  inserção de uma ocorrência.

## Views

- `vw_pacientes_internados`: uma linha por paciente atualmente internado.
- `vw_residentes_sem_supervisor`: escalas cujo preceptor não é doutor ou cuja
  atuação não está vigente na data do plantão.
- `vw_estatisticas_atendimentos_mensal`: total, duração média e procedimento
  mais comum por mês e unidade. Empates são resolvidos por nome do procedimento
  em ordem alfabética.

## ORM e concorrência

- Todas as operações da Etapa 1 devem ser reimplementadas com a DSL do
  SQLAlchemy, sem SQL textual.
- Os relacionamentos usam carregamento lazy por padrão; consultas de telas ou
  relatórios devem aplicar eager loading explicitamente quando necessário.
- O cenário concorrente usa duas sessões e bloqueio pessimista para serializar
  a escala do mesmo residente/data/turno. Ao final, somente uma escala pode ser
  confirmada.

## Entrega

- Commits e branches separados por bloco de responsabilidade.
- Testes de sucesso, falha e rollback para cada requisito.
- README atualizado, relatório breve e matriz de conformidade.
