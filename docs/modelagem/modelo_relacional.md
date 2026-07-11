# Modelo relacional — versão 2.0

O modelo abaixo traduz o DER ampliado para relações. Tipos físicos e sintaxe SQL pertencem à etapa de implementação.

| Relação | Atributos | Chave primária | Chaves estrangeiras | Restrições principais |
|---|---|---|---|---|
| PESSOA | id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone | id_pessoa | — | cpf único |
| PACIENTE | id_pessoa, num_convenio, alergias, grupo_sanguineo | id_pessoa | id_pessoa → PESSOA(id_pessoa) | PK compartilhada com PESSOA |
| PROFISSIONAL | id_pessoa, crm, data_admissao, especialidade | id_pessoa | id_pessoa → PESSOA(id_pessoa) | crm único; PK compartilhada com PESSOA |
| ATUACAO_PROFISSIONAL | id_atuacao, id_profissional, data_inicio, data_fim | id_atuacao | id_profissional → PROFISSIONAL(id_pessoa) | data_fim ausente ou posterior/igual a data_inicio; períodos do mesmo profissional não se sobrepõem |
| ATUACAO_RESIDENTE | id_atuacao, ano_residencia | id_atuacao | id_atuacao → ATUACAO_PROFISSIONAL(id_atuacao) | ano_residencia em R1, R2 ou R3; PK compartilhada |
| ATUACAO_PRECEPTOR | id_atuacao, titulacao | id_atuacao | id_atuacao → ATUACAO_PROFISSIONAL(id_atuacao) | PK compartilhada |
| UNIDADE | id_unidade, nome, tipo, capacidade_leitos | id_unidade | — | tipo no domínio aprovado; capacidade_leitos não negativa |
| ATENDIMENTO | id_atendimento, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade | id_atendimento | id_paciente → PACIENTE(id_pessoa); id_atuacao_residente → ATUACAO_RESIDENTE(id_atuacao); id_atuacao_preceptor → ATUACAO_PRECEPTOR(id_atuacao); id_unidade → UNIDADE(id_unidade) | duração positiva; FKs obrigatórias; atuações vigentes em data_hora |
| PROCEDIMENTO | id_procedimento, codigo, nome, tempo_medio_minutos, nivel_risco | id_procedimento | — | codigo único; tempo médio positivo; risco em BAIXO, MEDIO ou ALTO |
| PROCEDIMENTO_REALIZADO | id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao, faturado | (id_atendimento, id_procedimento) | id_atendimento → ATENDIMENTO(id_atendimento); id_procedimento → PROCEDIMENTO(id_procedimento) | quantidade e tempo real positivos; faturado padrão falso |
| ESCALA | id_escala, id_unidade, dia_semana, turno, data_plantao, id_atuacao_residente, id_atuacao_preceptor | id_escala | id_unidade → UNIDADE(id_unidade); id_atuacao_residente → ATUACAO_RESIDENTE(id_atuacao); id_atuacao_preceptor → ATUACAO_PRECEPTOR(id_atuacao) | UNIQUE(id_unidade, data_plantao, turno, id_atuacao_residente); domínios de dia e turno; atuações vigentes na data |

## Mapeamento das especializações

PACIENTE e PROFISSIONAL usam a chave de PESSOA como PK e FK. Como a especialização é parcial e sobreposta, uma PESSOA pode não aparecer em nenhuma dessas relações ou aparecer nas duas.

ATUACAO_RESIDENTE e ATUACAO_PRECEPTOR usam a chave de ATUACAO_PROFISSIONAL como PK e FK. A especialização é total e disjunta: cada atuação deve aparecer em exatamente uma das duas relações.

## Mapeamento dos relacionamentos

- RECEBE é materializado por `id_paciente` em ATENDIMENTO.
- REALIZA e SUPERVISIONA são materializados pelas FKs de atuação em ATENDIMENTO.
- OCORRE_EM é materializado por `id_unidade` em ATENDIMENTO.
- PROCEDIMENTO_REALIZADO materializa o relacionamento N:N entre ATENDIMENTO e PROCEDIMENTO e mantém seus atributos próprios.
- ACONTECE_EM, ESCALADO_EM e SUPERVISIONA_PLANTAO são materializados pelas três FKs de ESCALA.

## Regras que excedem constraints simples

A especialização total/disjunta, a ausência de sobreposição de atuações e a vigência da atuação nas datas referenciadas exigem validação transacional, trigger ou mecanismo equivalente na implementação física. Este documento apenas formaliza essas regras.
