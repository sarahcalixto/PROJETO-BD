# Relatório técnico — Etapa 2

## Evolução do banco

A Etapa 2 mantém o modelo da Etapa 1 e acrescenta os dados necessários às
rotinas e análises avançadas: início efetivo do procedimento, média observada
do procedimento, internações e auditoria de atendimentos. O atendimento também
se relaciona com uma unidade e a escala armazena `data_plantao`; o dia da semana
é derivado dessa data para evitar redundância.

O histórico de papéis profissionais é representado por
`ATUACAO_PROFISSIONAL`, com subtipos residente e preceptor. Uma constraint de
exclusão impede períodos sobrepostos para o mesmo profissional. Triggers de
constraint diferidos permitem inserir pai e subtipo na mesma transação e, no
commit, exigem exatamente um subtipo compatível com o discriminador.

A escala preserva a chave candidata pedida no enunciado e também possui uma
unicidade global por data, turno e residente. A segunda garantia torna a regra
segura diante de duas inserções concorrentes em unidades diferentes; a trigger
obrigatória continua oferecendo a mensagem de domínio antes da gravação.

## Procedures e triggers

As rotinas com retorno foram implementadas como funções armazenadas do
PostgreSQL, mantendo os nomes `sp_*` oficiais. Essa forma permite retornar o
identificador criado, tabelas calculadas e quantidades alteradas sem abrir mão
da execução transacional.

`sp_registrar_atendimento_completo` recebe um array JSONB, valida referências e
insere o atendimento e seus procedimentos na transação do chamador. Qualquer
erro é propagado e o `session_scope` do SQLAlchemy executa rollback integral.
`sp_calcular_tempo_medio_espera` encontra o primeiro procedimento de cada
atendimento e calcula a média por unidade; unidades sem ocorrência permanecem
no resultado com valor nulo. `sp_reajustar_escala` bloqueia a atuação residente,
valida origem, destino e vigência e só então atualiza o conjunto completo.

Triggers foram escolhidos para invariantes que precisam valer em qualquer
caminho de escrita. `trg_check_sobreposicao_escala` rejeita o residente em duas
unidades no mesmo plantão. `trg_audita_atendimento` registra as imagens JSONB
anterior e nova em INSERT, UPDATE e DELETE. A auditoria mantém uma referência
lógica, sem chave estrangeira, para sobreviver à exclusão do atendimento.
`trg_atualiza_media_procedimentos` mantém a média observada; embora o requisito
mínimo cite INSERT, UPDATE e DELETE também são tratados para que a coluna não
fique obsoleta após a operação de remoção exigida na Etapa 1.

## Views e ORM

As três views são comuns, não materializadas, pois o volume acadêmico é baixo e
as telas devem refletir o estado atual. `vw_pacientes_internados` considera a
internação mais recente. `vw_residentes_sem_supervisor` identifica titulação
diferente de doutor ou atuação preceptora fora da vigência. A view mensal agrega
por ano, mês e unidade; o procedimento mais comum é o de maior soma da
quantidade executada e empates são resolvidos pelo nome em ordem alfabética.

O SQLAlchemy 2 mapeia todas as relações e reimplementa as operações da Etapa 1
com `select`, joins, agregações, subconsultas correlacionadas e transações, sem
SQL textual. As consultas de leitura retornam dataclasses imutáveis para que a
interface não dependa de entidades ligadas a uma sessão já encerrada.
Relacionamentos permanecem lazy por padrão. Nos relatórios que percorrem
coleções são aplicados `selectinload` ou `joinedload`; a medição disponível na
página Auditoria registra a diferença no número de consultas.

As consultas avançadas retornam preceptores ligados a atendimentos de pacientes
flamenguistas, o atendimento mais recente de cada paciente com profissionais e
procedimentos e o percentual de registros de procedimentos de alto risco por
residente. O percentual usa linhas de `PROCEDIMENTO_REALIZADO`, e não o campo
`quantidade`, por tratar cada linha como a ocorrência associativa avaliada.

## Concorrência e interface

A demonstração cria duas escalas temporárias do mesmo residente e unidade em
datas de origem diferentes. Duas sessões tentam movê-las para a mesma data e
turno. A primeira mantém o lock pessimista sobre a atuação; a segunda aguarda,
reavalia o destino depois do commit e é rejeitada. Uma terceira sessão confirma
uma única escala final, e a limpeza remove somente os IDs criados pela própria
demonstração.

O Streamlit foi organizado em seis páginas de domínio. A interface faz
validações de preenchimento para melhorar a experiência, mas referências,
vigência, atomicidade, faturamento e conflitos permanecem protegidos nos
serviços e no PostgreSQL. Consultas e evidências são executadas somente quando
selecionadas, reduzindo reruns e trabalho oculto.
