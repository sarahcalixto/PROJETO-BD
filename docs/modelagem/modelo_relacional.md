# Modelo relacional

| Relação | Atributos principais | Chaves e restrições |
|---|---|---|
| PESSOA | id, nome, cpf, data_nascimento, is_flamengo, telefone | PK id; UNIQUE cpf |
| PACIENTE | id, num_convenio, grupo_sanguineo | PK/FK id → PESSOA |
| ALERGIA | id, nome | PK id; UNIQUE nome |
| PACIENTE_ALERGIA | id_paciente, id_alergia | PK composta; FKs para PACIENTE e ALERGIA |
| PROFISSIONAL | id, crm, data_admissao, especialidade | PK/FK id → PESSOA; UNIQUE crm |
| ATUACAO_PROFISSIONAL | id, id_profissional, tipo, data_inicio, data_fim | PK id; FK profissional; período válido e não sobreposto |
| ATUACAO_RESIDENTE | id, tipo, ano_residencia | PK/FK composta para atuação; tipo residente |
| ATUACAO_PRECEPTOR | id, tipo, titulacao | PK/FK composta para atuação; tipo preceptor |
| UNIDADE | id, nome, tipo, capacidade_leitos | PK id; capacidade não negativa |
| ATENDIMENTO | id, data_hora, duracao_minutos, paciente, residente, preceptor, unidade | PK id; quatro FKs obrigatórias; duração positiva |
| PROCEDIMENTO | id, codigo, nome, tempo_medio_minutos, nivel_risco, media_tempo_procedimento | PK id; UNIQUE codigo; tempos positivos |
| PROCEDIMENTO_REALIZADO | id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio, observacao, faturado | PK composta; FKs; quantidade e tempo positivos |
| ESCALA | id, unidade, data_plantao, turno, residente, preceptor | PK id; FKs; duas chaves candidatas de residente/plantão |
| INTERNACAO | id, paciente, unidade, data_hora_entrada, data_hora_saida | PK id; FKs; período válido; uma internação ativa por paciente |
| AUDITORIA_ATENDIMENTO | id_auditoria, id_atendimento, operacao, usuario, data_hora, dados_antigos, dados_novos | PK id_auditoria; operação validada; referência lógica ao atendimento |

## Especializações

PESSOA possui especialização parcial e sobreposta em PACIENTE e PROFISSIONAL.
Uma pessoa pode não exercer nenhuma dessas classificações ou possuir ambas.

ATUACAO_PROFISSIONAL possui especialização total e disjunta. Cada período é
exatamente residente ou preceptor; o discriminador e as FKs compostas garantem
compatibilidade, triggers diferidos garantem totalidade e a exclusão temporal
impede que o mesmo profissional ocupe dois papéis no mesmo instante.

## Decisões derivadas dos requisitos

- `data_plantao` substitui o armazenamento de `dia_semana`; o dia é calculado.
- O vínculo de ATENDIMENTO com UNIDADE viabiliza as estatísticas mensais.
- `nivel_risco`, `faturado`, `data_hora_inicio` e a média observada existem
  porque são usados por consultas, procedures ou triggers oficiais.
- AUDITORIA_ATENDIMENTO não possui FK para preservar eventos de DELETE.
- A unicidade global de escala torna a regra da trigger segura sob concorrência.
