# Matriz de conformidade — Etapa 2

Última validação: 2 de agosto de 2026. A suíte completa terminou com **97 testes
aprovados e nenhuma falha**. O vídeo e o ajuste do front são deliberadamente
posteriores e não são marcados como concluídos.

| Grupo | Requisito | Implementação | Evidência de teste | Resultado |
|---|---|---|---|---|
| 1 | Atendimento completo JSONB e rollback | `sql/05_procedures.sql` | `tests/test_procedures.py` | **Aprovado** |
| 1 | Média do primeiro procedimento | `sp_calcular_tempo_medio_espera` | `tests/test_procedures.py` | **Aprovado** |
| 1 | Reajuste integral e conflitos | `sp_reajustar_escala` | `tests/test_procedures.py` | **Aprovado** |
| 2 | Sobreposição em INSERT/UPDATE | `sql/06_triggers.sql` | `tests/test_triggers.py` | **Aprovado** |
| 2 | Auditoria INSERT/UPDATE/DELETE com JSON | `auditoria_atendimento` | `tests/test_triggers.py` | **Aprovado** |
| 2 | Média exata do procedimento | `media_tempo_procedimento` | `tests/test_triggers.py` | **Aprovado** |
| 3 | Internação ativa mais recente | `vw_pacientes_internados` | `tests/test_views.py` | **Aprovado** |
| 3 | Supervisor não doutor ou inativo | `vw_residentes_sem_supervisor` | `tests/test_views.py` | **Aprovado** |
| 3 | Estatística e desempate mensal | `vw_estatisticas_atendimentos_mensal` | `tests/test_views.py` | **Aprovado** |
| 4 | Operações e consultas da Etapa 1 via ORM | `src/projeto_hospital/services/` | `tests/test_orm_operacoes.py`, `tests/test_orm_consultas.py` | **Aprovado** |
| 4 | Sessão, commit, rollback, lazy/eager | `orm/session.py` e relacionamentos | `tests/test_orm_carregamento_transacoes.py` | **Aprovado** |
| 5 | Três consultas avançadas e casos zero | `consultas_avancadas.py` | `tests/test_orm_avancado.py` | **Aprovado** |
| 6 | Duas sessões e lock pessimista | `services/concorrencia.py` | `tests/test_aceitacao_etapa2.py` | **Aprovado** |
| 7 | README, relatório, matriz e roteiro | `README.md`, `docs/` | grupo 7 da suíte de aceitação | **Aprovado** |
| 7 | Vídeo de até 8 minutos | gravação manual | conferência manual | **Pendente** |
| Extra | Ajuste final do front | rodada posterior | regressão `tests/test_app.py` | **Pendente por escopo** |
