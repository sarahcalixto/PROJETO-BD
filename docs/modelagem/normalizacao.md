# Normalização até a Terceira Forma Normal

## Primeira Forma Normal

Todas as relações possuem chave e atributos escalares. Alergias são
multivaloradas no domínio e, por isso, foram decompostas em ALERGIA e
PACIENTE_ALERGIA. Da mesma forma, PROCEDIMENTO_REALIZADO materializa a relação
N:N entre atendimento e procedimento sem armazenar uma lista em uma coluna.

## Segunda Forma Normal

As relações com chave composta são PACIENTE_ALERGIA e PROCEDIMENTO_REALIZADO.
Na primeira não existem atributos não chave. Na segunda, quantidade, tempo real,
início, observação e faturamento descrevem a combinação completa de atendimento
e procedimento. Logo, não existem dependências parciais.

## Terceira Forma Normal

Dados descritivos permanecem em suas próprias entidades: atendimentos e escalas
guardam somente as FKs; nomes de pessoas, unidades e procedimentos não são
repetidos. A hierarquia PESSOA → PROFISSIONAL → ATUACAO_PROFISSIONAL separa
atributos gerais, profissionais e temporais, enquanto ano de residência e
titulação ficam exclusivamente nos subtipos correspondentes.

As chaves alternativas CPF, CRM, código do procedimento, nome da alergia e as
combinações únicas da escala determinam suas tuplas completas. `dia_semana` não
é armazenado porque é determinado por `data_plantao`.

`media_tempo_procedimento` é a única redundância derivada intencional. Ela é
exigida na Etapa 2 e mantida exclusivamente por trigger após mudanças nas
ocorrências. AUDITORIA_ATENDIMENTO é um registro histórico imutável, não uma
duplicação editável do atendimento atual.

Assim, as relações estão em 3FN. A ausência de sobreposição de atuações, a
especialização total/disjunta, a vigência temporal e a unicidade concorrente de
escalas são restrições de integridade e não exigem nova decomposição.
