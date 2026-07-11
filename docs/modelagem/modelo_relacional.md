# Modelo relacional

Este documento organiza a tradução do DER aprovado para relações. Ele descreve a modelagem, não contém comandos SQL.

| Tabela | Atributos | PK | FKs | Constraints | Observações |
|---|---|---|---|---|---|
| PESSOA | id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone | id_pessoa | — | A definir | Supertipo de paciente e profissional |
| PACIENTE | id_pessoa, num_convenio, alergias, grupo_sanguineo | id_pessoa | id_pessoa → PESSOA(id_pessoa) | A definir | Especialização com PK compartilhada |
| PROFISSIONAL | id_pessoa, crm, data_admissao, especialidade | id_pessoa | id_pessoa → PESSOA(id_pessoa) | A definir | Supertipo de residente e preceptor |
| PRECEPTOR | id_profissional, titulacao | id_profissional | id_profissional → PROFISSIONAL(id_pessoa) | A definir | Especialização com PK compartilhada |
| RESIDENTE | id_profissional, ano_residencia | id_profissional | id_profissional → PROFISSIONAL(id_pessoa) | A definir | Especialização com PK compartilhada |
| UNIDADE | id_unidade, nome, tipo, capacidade_leitos | id_unidade | — | A definir | Unidade hospitalar |
| ATENDIMENTO | id_atendimento, data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor | id_atendimento | id_paciente → PACIENTE; id_residente → RESIDENTE; id_preceptor → PRECEPTOR | A definir | Associação com unidade ainda pendente |
| PROCEDIMENTO | id_procedimento, codigo, nome, tempo_medio_minutos | id_procedimento | — | A definir | Nível de risco ainda pendente |
| PROCEDIMENTO_REALIZADO | id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao | (id_atendimento, id_procedimento) | id_atendimento → ATENDIMENTO; id_procedimento → PROCEDIMENTO | PK composta | Faturamento ainda pendente |
| ESCALA | id_escala, id_unidade, dia_semana, turno, id_residente, id_preceptor | id_escala | id_unidade → UNIDADE; id_residente → RESIDENTE; id_preceptor → PRECEPTOR | UNIQUE(id_unidade, dia_semana, turno, id_residente) | Data ou vigência ainda pendente |

## Revisões necessárias antes da implementação

- Confirmar tipos, nulabilidade, domínios e regras de exclusão/atualização das FKs.
- Resolver os itens de `docs/decisoes_pendentes.md`.
- Conferir a correspondência entre este documento, o DER e o contrato do modelo.
- Registrar justificativas de cardinalidade e especialização junto ao DER aprovado.
