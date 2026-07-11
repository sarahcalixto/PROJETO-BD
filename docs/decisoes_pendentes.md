# Registro de decisões da modelagem

## Decisões resolvidas na versão 2.0

| Tema | Decisão | Justificativa |
|---|---|---|
| Endereço do paciente | Não incluir | O CRUD permite atualizar endereço **ou** convênio; `num_convenio` atende à operação solicitada sem inventar estrutura de endereço. |
| Faturamento | Incluir `faturado` em PROCEDIMENTO_REALIZADO | Permite impedir a remoção de um procedimento já faturado. |
| Nível de risco | Incluir `nivel_risco` em PROCEDIMENTO | Permite consultar pacientes sem procedimentos de risco ALTO. |
| Escala mensal | Incluir `data_plantao` em ESCALA | Permite filtrar e agregar plantões por mês. |
| Unidade do atendimento | Relacionar ATENDIMENTO a UNIDADE | Suporta estatísticas por unidade e os requisitos futuros. |
| Histórico profissional | Criar ATUACAO_PROFISSIONAL e suas especializações | Permite que um profissional mude de papel ao longo do tempo sem ocupar os dois papéis na mesma atuação. |

## Regras derivadas

- A especialização de PESSOA é parcial e sobreposta.
- A especialização de ATUACAO_PROFISSIONAL é total e disjunta.
- Atendimento e escala referenciam a atuação específica, e não somente o profissional.
- A combinação `(id_unidade, data_plantao, turno, id_atuacao_residente)` é única na escala.

## Pontos para a implementação física

Não são decisões conceituais pendentes, mas exigirão mecanismos no PostgreSQL:

- validar que `data_fim` não precede `data_inicio`;
- impedir sobreposição de atuações do mesmo profissional;
- assegurar que as atuações estejam vigentes no atendimento e no plantão;
- garantir que toda ATUACAO_PROFISSIONAL pertença a exatamente um subtipo.

Essas regras devem ser tratadas pelo integrante responsável pelo SQL, sem implementação nesta branch.
