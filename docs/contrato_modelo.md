# Contrato do modelo

**Versão:** 2.0

**Estado:** modelo ampliado aprovado para a Etapa 1 e alinhado ao DER.

## Convenções

- `PK` identifica chave primária; `FK`, chave estrangeira; e `UQ`, unicidade.
- Toda atuação pertence a um profissional e assume exatamente um papel: residente ou preceptor.
- ATENDIMENTO e ESCALA referenciam atuações, preservando o papel exercido no período.
- Tipos físicos e ações referenciais serão definidos no script SQL pelo integrante responsável.

## Relações oficiais

### PESSOA

| Atributo | Chave | Regra |
|---|---|---|
| id_pessoa | PK | Identificador da pessoa |
| nome | — | Nome da pessoa |
| cpf | UQ | CPF não se repete |
| data_nascimento | — | Data de nascimento |
| is_flamengo | — | Indicador booleano |
| telefone | — | Telefone de contato |

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
| crm | UQ | — |
| data_admissao | — | — |
| especialidade | — | — |

### ATUACAO_PROFISSIONAL

| Atributo | Chave | Referência |
|---|---|---|
| id_atuacao | PK | — |
| id_profissional | FK | PROFISSIONAL(id_pessoa) |
| data_inicio | — | Início da vigência |
| data_fim | — | Fim opcional da vigência |

Cada atuação deve ser classificada em exatamente uma das especializações abaixo. Os períodos de atuação de um mesmo profissional não devem se sobrepor.

### ATUACAO_RESIDENTE

| Atributo | Chave | Referência |
|---|---|---|
| id_atuacao | PK, FK | ATUACAO_PROFISSIONAL(id_atuacao) |
| ano_residencia | — | Domínio previsto: R1, R2 ou R3 |

### ATUACAO_PRECEPTOR

| Atributo | Chave | Referência |
|---|---|---|
| id_atuacao | PK, FK | ATUACAO_PROFISSIONAL(id_atuacao) |
| titulacao | — | Titulação durante a atuação |

### UNIDADE

| Atributo | Chave | Regra |
|---|---|---|
| id_unidade | PK | Identificador da unidade |
| nome | — | Nome da unidade |
| tipo | — | Enfermaria, UTI, Pronto-Socorro ou Ambulatório |
| capacidade_leitos | — | Valor não negativo |

### ATENDIMENTO

| Atributo | Chave | Referência |
|---|---|---|
| id_atendimento | PK | — |
| data_hora | — | — |
| duracao_minutos | — | Valor positivo |
| id_paciente | FK | PACIENTE(id_pessoa) |
| id_atuacao_residente | FK | ATUACAO_RESIDENTE(id_atuacao) |
| id_atuacao_preceptor | FK | ATUACAO_PRECEPTOR(id_atuacao) |
| id_unidade | FK | UNIDADE(id_unidade) |

As atuações referenciadas devem estar vigentes na data e hora do atendimento.

### PROCEDIMENTO

| Atributo | Chave | Regra |
|---|---|---|
| id_procedimento | PK | — |
| codigo | UQ | Código do procedimento |
| nome | — | — |
| tempo_medio_minutos | — | Valor positivo |
| nivel_risco | — | Domínio: BAIXO, MEDIO ou ALTO |

### PROCEDIMENTO_REALIZADO

| Atributo | Chave | Referência/regra |
|---|---|---|
| id_atendimento | PK, FK | ATENDIMENTO(id_atendimento) |
| id_procedimento | PK, FK | PROCEDIMENTO(id_procedimento) |
| quantidade | — | Valor positivo |
| tempo_real_minutos | — | Valor positivo |
| observacao | — | — |
| faturado | — | Booleano, padrão falso |

A chave primária é composta por `(id_atendimento, id_procedimento)`.

### ESCALA

| Atributo | Chave | Referência |
|---|---|---|
| id_escala | PK | — |
| id_unidade | FK | UNIDADE(id_unidade) |
| dia_semana | — | Segunda a domingo |
| turno | — | Manhã, tarde ou noite |
| data_plantao | — | Data que permite consultas mensais |
| id_atuacao_residente | FK | ATUACAO_RESIDENTE(id_atuacao) |
| id_atuacao_preceptor | FK | ATUACAO_PRECEPTOR(id_atuacao) |

Restrição aprovada: `UQ (id_unidade, data_plantao, turno, id_atuacao_residente)`. As atuações devem estar vigentes em `data_plantao`.

## Especializações e cardinalidades

- PESSOA possui especialização parcial e sobreposta: nem toda pessoa precisa ter subtipo, e uma pessoa pode ser paciente e profissional.
- ATUACAO_PROFISSIONAL possui especialização total e disjunta: toda atuação é residente ou preceptor, nunca ambas simultaneamente.
- Um atendimento possui exatamente um paciente, uma atuação residente, uma atuação preceptora e uma unidade; cada participante pode aparecer em vários atendimentos.
- Um atendimento possui um ou mais procedimentos realizados; um tipo de procedimento pode não ter sido realizado ou aparecer em vários atendimentos.
- Uma escala possui exatamente uma unidade, uma atuação residente e uma atuação preceptora; cada um deles pode participar de várias escalas.

## Limite do contrato

Este documento define o esquema lógico aprovado, mas não implementa SQL. Regras temporais que dependam da comparação entre datas devem ser tratadas pelo responsável pela implementação.
