# Requisitos da Etapa 1

## Contexto da aplicação

O Sistema de Gestão Hospitalar Dra. Yuska Maritan Brito deve apoiar o cadastro e o relacionamento de pessoas, pacientes, profissionais, residentes, preceptores, unidades hospitalares, atendimentos, procedimentos, procedimentos realizados e escalas de plantão.

## Requisitos de modelagem

- Elaborar um Diagrama Entidade-Relacionamento completo.
- Converter o DER em modelo relacional.
- Identificar chaves primárias, estrangeiras, compostas e demais restrições.
- Justificar cardinalidades e especializações.
- Demonstrar a normalização das relações até a Terceira Forma Normal (3FN).

## Requisitos de implementação

- Criar o banco no PostgreSQL a partir do modelo aprovado.
- Incluir restrições de integridade coerentes com o contrato do esquema.
- Preparar dados de teste representativos.
- Usar Python 3.12+, `uv` e acesso direto via `psycopg`, sem ORM nesta etapa.

## Requisitos de CRUD

- Implementar operações de criação, consulta, atualização e remoção solicitadas pelo enunciado.
- Respeitar as regras de integridade e faturamento durante alterações e exclusões.
- Manter as implementações no arquivo SQL reservado ao integrante responsável.

## Requisitos de consultas analíticas

- Produzir as consultas básicas e analíticas solicitadas para atendimentos, procedimentos e escalas.
- Incluir os recursos SQL requeridos pelo enunciado, como agregações, filtros de grupo e subconsultas.
- Manter as consultas no arquivo reservado ao integrante responsável.

## Evolução do modelo

A análise inicial identificou lacunas entre o esquema-base e as operações exigidas. As decisões aprovadas foram incorporadas ao modelo 2.0:

- `faturado` foi incluído em PROCEDIMENTO_REALIZADO para controlar sua remoção;
- `nivel_risco` foi incluído em PROCEDIMENTO para suportar a consulta de risco ALTO;
- `data_plantao` foi incluída em ESCALA para permitir consultas mensais;
- ATENDIMENTO passou a se relacionar com UNIDADE;
- ATUACAO_PROFISSIONAL, ATUACAO_RESIDENTE e ATUACAO_PRECEPTOR foram adotadas para preservar o histórico de papéis do profissional;
- `dia_semana` passou a ser derivado de `data_plantao`, evitando redundância no modelo normalizado.

O endereço do paciente não foi incluído, pois o requisito de atualização aceita endereço **ou** convênio e `num_convenio` já atende à operação solicitada.

## Fontes oficiais da modelagem

- `docs/contrato_modelo.md`: relações, atributos, chaves e regras aprovadas;
- `docs/modelagem/der_hospital.pdf`: modelo conceitual e justificativas de cardinalidades e especializações;
- `docs/modelagem/modelo_relacional.md`: tradução do DER para as 11 relações do modelo 2.0;
- `docs/modelagem/normalizacao.md`: evidência de normalização até 3FN;
- `docs/decisoes_pendentes.md`: registro das decisões resolvidas e regras destinadas à implementação física.

Os responsáveis pelo SQL devem implementar o modelo 2.0, e não o esquema-base apresentado originalmente no enunciado.

## Limites desta branch

Esta branch organiza o repositório e a documentação sob responsabilidade da Sarah. Ela não implementa esquema SQL, dados de teste, CRUD, consultas básicas ou consultas analíticas, que pertencem aos demais integrantes.
