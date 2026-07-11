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

## Lacunas identificadas

O enunciado demanda informações que ainda não fazem parte do contrato inicial:

- endereço do paciente;
- estado de faturamento do procedimento realizado;
- nível de risco do procedimento;
- data ou vigência mensal da escala;
- unidade associada ao atendimento.

Esses pontos estão detalhados em `docs/decisoes_pendentes.md` e não devem ser adicionados ao modelo antes de aprovação do grupo.

## Limites desta branch

Esta branch organiza o repositório e a documentação sob responsabilidade da Sarah. Ela não implementa esquema SQL, dados de teste, CRUD, consultas básicas ou consultas analíticas, que pertencem aos demais integrantes.
