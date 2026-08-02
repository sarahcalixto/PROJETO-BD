# Relatório técnico — Etapa 2

## Visão geral

A Etapa 2 mantém o modelo normalizado e o SQL puro da primeira entrega, mas
adiciona regras no PostgreSQL, uma camada SQLAlchemy 2.x e uma demonstração de
concorrência. A separação foi intencional: constraints e triggers protegem os
dados independentemente do cliente; rotinas armazenadas concentram operações
atômicas; serviços ORM oferecem contratos Python testáveis sem SQL textual.

O schema ganhou internações, horário efetivo de início dos procedimentos, média
observada por procedimento e auditoria de atendimentos. A massa de teste cobre
internações abertas/encerradas, diferentes titulações, conflitos de escala e
procedimentos com riscos distintos.

## Rotinas, triggers e atomicidade

As três rotinas solicitadas são implementadas com `CREATE FUNCTION`. No
PostgreSQL, functions e procedures são rotinas armazenadas; a escolha por
functions foi necessária porque os contratos retornam, respectivamente, o ID
criado, uma tabela de médias e a quantidade de escalas movidas. Uma procedure
chamada com `CALL` não oferece esses retornos da mesma maneira. A decisão não
reduz a atomicidade: cada chamada participa da transação do chamador e qualquer
exceção reverte todas as alterações feitas pela rotina.

`sp_registrar_atendimento_completo` valida referências e vigência, exige um
array JSONB não vazio, cria o atendimento e percorre os procedimentos na ordem
recebida. Um item inválido interrompe a instrução e nenhum registro parcial
permanece. `sp_calcular_tempo_medio_espera` usa o primeiro início por
atendimento. `sp_reajustar_escala` bloqueia a atuação do residente com
`FOR UPDATE`, valida todo o destino e só então altera o conjunto.

Os triggers têm responsabilidades diferentes. O trigger de sobreposição atua
antes de `INSERT` e `UPDATE`; o de auditoria registra imagens JSONB anterior e
nova após as três operações; o de média recalcula o valor exato depois de cada
nova realização. As views mantêm consultas reutilizáveis: a internação mais
recente, supervisão inadequada por titulação ou vigência e estatísticas mensais
com desempate alfabético determinístico.

## SQLAlchemy e consultas

Todas as tabelas são mapeadas com entidades e relacionamentos. A fábrica de
sessões usa transações explícitas e `session_scope` confirma no sucesso ou faz
rollback diante de qualquer erro. As seis operações e as quatro consultas da
Etapa 1 foram reimplementadas com `select`, joins e funções da DSL, sem SQL cru.

As três consultas avançadas possuem DTOs imutáveis. A primeira encontra os
preceptores de atendimentos de pacientes flamenguistas; a segunda usa uma
função de janela para escolher, com desempate por ID, o último atendimento de
cada paciente e carrega profissionais e procedimentos; a terceira usa
`OUTER JOIN` para preservar residentes sem procedimentos e calcula o percentual
de alto risco com duas casas decimais.

O carregamento lazy permanece como padrão dos mapeamentos. Um teste instrumenta
o engine e demonstra três comandos quando pessoa e atendimentos são acessados
sob demanda. A variante eager usa `joinedload` e executa um único comando, sem
consultas adicionais ao navegar pelos mesmos relacionamentos.

## Concorrência, testes e limitações atuais

A demonstração concorrente abre duas sessões SQLAlchemy. A primeira reajusta a
escala e mantém o lock; a segunda inicia o mesmo destino e fica bloqueada. Após
o commit da primeira, a segunda reavalia o estado e é rejeitada. O teste exige
uma confirmação, uma rejeição, uma única escala final e os logs da espera.

A suíte é dividida por procedures, triggers, views, operações ORM, consultas
avançadas, concorrência e entrega. Ela também verifica rollback, resultados
vazios, entidades ausentes, JSON inválido, valores exatos e objetos instalados
no catálogo do PostgreSQL. A interface atual é executada apenas como teste de
regressão nesta rodada.

Ainda faltam duas atividades manuais: gravar o vídeo de até oito minutos e,
depois da validação da equipe, adaptar o front aos novos fluxos ORM. Por isso a
Etapa 2 não recebe tag final neste momento.
