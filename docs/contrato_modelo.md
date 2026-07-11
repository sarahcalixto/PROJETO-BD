# Contrato inicial do modelo

**Versão:** 1.0
**Estado:** base estável para a modelagem, sujeita apenas às decisões pendentes documentadas separadamente.

## Convenções

- Nomes oficiais de relações e atributos são apresentados em maiúsculas para leitura do modelo.
- `PK` identifica chave primária; `FK`, chave estrangeira; e `UQ`, restrição de unicidade.
- Especializações usam a chave da relação-pai simultaneamente como PK e FK.
- Tipos físicos, nulabilidade e regras não expressamente aprovadas serão definidos na implementação SQL pelo responsável.

## Relações oficiais

### PESSOA

| Atributo | Chave | Referência |
|---|---|---|
| id_pessoa | PK | — |
| nome | — | — |
| cpf | — | — |
| data_nascimento | — | — |
| is_flamengo | — | — |
| telefone | — | — |

### PACIENTE

| Atributo | Chave | Referência |
|---|---|---|
| id_pessoa | PK, FK | PESSOA(id_pessoa) |
| num_convenio | — | — |
| alergias | — | — |
| grupo_sanguineo | — | — |

### PROFISSIONAL

| Atributo | Chave | Referência |
|---|---|---|
| id_pessoa | PK, FK | PESSOA(id_pessoa) |
| crm | — | — |
| data_admissao | — | — |
| especialidade | — | — |

### PRECEPTOR

| Atributo | Chave | Referência |
|---|---|---|
| id_profissional | PK, FK | PROFISSIONAL(id_pessoa) |
| titulacao | — | — |

### RESIDENTE

| Atributo | Chave | Referência |
|---|---|---|
| id_profissional | PK, FK | PROFISSIONAL(id_pessoa) |
| ano_residencia | — | — |

### UNIDADE

| Atributo | Chave | Referência |
|---|---|---|
| id_unidade | PK | — |
| nome | — | — |
| tipo | — | — |
| capacidade_leitos | — | — |

### ATENDIMENTO

| Atributo | Chave | Referência |
|---|---|---|
| id_atendimento | PK | — |
| data_hora | — | — |
| duracao_minutos | — | — |
| id_paciente | FK | PACIENTE(id_pessoa) |
| id_residente | FK | RESIDENTE(id_profissional) |
| id_preceptor | FK | PRECEPTOR(id_profissional) |

### PROCEDIMENTO

| Atributo | Chave | Referência |
|---|---|---|
| id_procedimento | PK | — |
| codigo | — | — |
| nome | — | — |
| tempo_medio_minutos | — | — |

### PROCEDIMENTO_REALIZADO

| Atributo | Chave | Referência |
|---|---|---|
| id_atendimento | PK, FK | ATENDIMENTO(id_atendimento) |
| id_procedimento | PK, FK | PROCEDIMENTO(id_procedimento) |
| quantidade | — | — |
| tempo_real_minutos | — | — |
| observacao | — | — |

A chave primária é composta por `(id_atendimento, id_procedimento)`.

### ESCALA

| Atributo | Chave | Referência |
|---|---|---|
| id_escala | PK | — |
| id_unidade | FK | UNIDADE(id_unidade) |
| dia_semana | — | — |
| turno | — | — |
| id_residente | FK | RESIDENTE(id_profissional) |
| id_preceptor | FK | PRECEPTOR(id_profissional) |

Restrição aprovada: `UQ (id_unidade, dia_semana, turno, id_residente)`.

## Decisões aprovadas

- PACIENTE e PROFISSIONAL especializam PESSOA por meio de PK compartilhada.
- PRECEPTOR e RESIDENTE especializam PROFISSIONAL por meio de PK compartilhada.
- PROCEDIMENTO_REALIZADO representa a associação entre ATENDIMENTO e PROCEDIMENTO e possui chave primária composta.
- ESCALA referencia uma unidade, um residente e um preceptor e impede a repetição da combinação aprovada.

## Decisões pendentes

Endereço, faturamento, nível de risco, dimensão temporal mensal da escala e unidade do atendimento não integram esta versão. As alternativas estão registradas em `docs/decisoes_pendentes.md` e exigem autorização antes de alterar este contrato.
