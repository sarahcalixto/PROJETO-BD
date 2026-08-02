# Roteiro do vídeo da Etapa 2 — até 8 minutos

## 0:00–0:40 — Contexto e arquitetura

- Apresentar rapidamente o hospital e os sete grupos de requisitos.
- Mostrar a árvore `sql/`, `src/projeto_hospital/` e `tests/`.
- Explicar que PostgreSQL protege regras e SQLAlchemy atende a aplicação.

## 0:40–2:10 — Rotinas armazenadas

- Abrir `05_procedures.sql` e explicar por que são functions armazenadas com
  retorno, mantendo atomicidade transacional.
- Executar o caso feliz do atendimento JSONB.
- Executar um procedimento inválido e provar que atendimento e itens foram
  revertidos.
- Mostrar resumidamente média de espera e reajuste de escala.

## 2:10–3:25 — Triggers e views

- Demonstrar bloqueio de sobreposição em escala.
- Inserir, alterar e excluir um atendimento; consultar auditoria em ordem de ID.
- Mostrar a média atualizada e as três views, destacando supervisor inativo e
  desempate alfabético.

## 3:25–5:15 — ORM e consultas avançadas

- Mostrar entidades, relacionamentos e `session_scope`.
- Executar uma operação da Etapa 1 e um rollback.
- Comparar a contagem mensurável de queries lazy (3) e eager (1).
- Exibir os DTOs das três consultas: preceptores de flamenguistas, último
  atendimento completo e percentual de alto risco, incluindo zero.

## 5:15–6:25 — Concorrência

- Executar `uv run python scripts/demonstrar_concorrencia.py`.
- Narrar: T1 mantém lock, T2 espera, T1 confirma, T2 é rejeitada.
- Mostrar no resultado que existe somente uma escala no destino.

## 6:25–7:30 — Testes e conformidade

- Executar a suíte de aceitação e, se couber, a suíte completa.
- Abrir `docs/matriz_conformidade_etapa2.md` e relacionar requisitos, código e
  testes.

## 7:30–8:00 — Encerramento

- Resumir decisões e resultados.
- Informar que a gravação valida a entrega e que o ajuste visual do front será
  feito depois, sem ter alterado a interface nesta integração.

## Checklist antes de gravar

- [ ] Banco saudável e scripts aplicados.
- [ ] Suíte completa verde.
- [ ] Terminal com fonte legível e sem credenciais expostas.
- [ ] Cronômetro abaixo de oito minutos.
- [ ] Link do vídeo adicionado à entrega.
