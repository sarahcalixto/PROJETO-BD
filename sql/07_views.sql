-- implementação das views da etapa2 do projeto de banco de dados --
-- não serão usadas views materializada principalmente pela necessidade de dados em tempo real --


-- view vw_pacientes_internados: pacientes que estão atualmente internados --
CREATE OR REPLACE VIEW vw_pacientes_internados AS
SELECT 
    pes.nome AS paciente,
    pac.num_convenio,
    i.data_hora_entrada AS data_internacao
FROM internacao i 
JOIN paciente pac ON i.id_paciente = pac.id
JOIN pessoa pes ON pac.id = pes.id 
-- como foi criado um índice no schema, basta adicionar esse filtro:
WHERE i.data_hora_saida IS NULL;

-- view vw_residentes_sem_supervisor -- 
CREATE OR REPLACE VIEW vw_residentes_sem_supervisor AS
SELECT DISTINCT
    e.data_plantao,
    e.turno,
    u.nome AS unidade,
    pres.nome AS residente,
    pprec.nome AS preceptor_alocado,
    aprec.titulacao
FROM escala e
JOIN unidade u ON e.id_unidade = u.id
JOIN atuacao_residente ar ON e.id_atuacao_residente = ar.id
JOIN atuacao_profissional aprof_res ON ar.id = aprof_res.id
JOIN pessoa pres ON aprof_res.id_profissional = pres.id
JOIN atuacao_preceptor aprec ON e.id_atuacao_preceptor = aprec.id
JOIN atuacao_profissional aprof_prec ON aprec.id = aprof_prec.id
JOIN pessoa pprec ON aprof_prec.id_profissional = pprec.id
WHERE LOWER(aprec.titulacao) <> 'doutor'; -- verifica se a titulação é diferente de doutor

-- view vw_estatisticas_atendimentos_mensal --
-- agregação por mês e por unidade: total
-- de atendimentos, média de duração, procedimentos mais comuns.
-- nessa situação poderia ser utilizada view materializada porém apenas se tivessemos milhões de dados
-- pois relatórios mensais não precisam ser atualizados constantemente
-- mas como se trata de um escopo de dados pequeno escolhemos a view normal

CREATE OR REPLACE VIEW vw_estatisticas_atendimentos_mensal AS

WITH BaseAtendimentos AS (
    SELECT 
        a.id AS id_atendimento,
        a.id_unidade,
        u.nome AS unidade,
        EXTRACT(YEAR FROM a.data_hora) AS ano,
        EXTRACT(MONTH FROM a.data_hora) AS mes,
        a.duracao_minutos
    FROM atendimento a
    JOIN unidade u ON a.id_unidade = u.id
),
EstatisticasGerais AS (
    SELECT 
        ano,
        mes,
        id_unidade,
        unidade,
        COUNT(id_atendimento) AS total_atendimentos,
        ROUND(AVG(duracao_minutos), 2) AS media_duracao_minutos
    FROM BaseAtendimentos
    GROUP BY ano, mes, id_unidade, unidade
),
ContagemProcedimentos AS (
    SELECT 
        b.ano,
        b.mes,
        b.id_unidade,
        p.nome AS procedimento,
        COUNT(pr.id_procedimento) AS qtd_realizado
    FROM BaseAtendimentos b
    JOIN procedimento_realizado pr ON b.id_atendimento = pr.id_atendimento
    JOIN procedimento p ON pr.id_procedimento = p.id
    GROUP BY b.ano, b.mes, b.id_unidade, p.nome
),
RankingProcedimentos AS (
    SELECT 
        ano,
        mes,
        id_unidade,
        procedimento,
        ROW_NUMBER() OVER(
            PARTITION BY ano, mes, id_unidade 
            ORDER BY qtd_realizado DESC, procedimento ASC
        ) AS rn
    FROM ContagemProcedimentos
)
SELECT 
    eg.ano,
    eg.mes,
    eg.unidade,
    eg.total_atendimentos,
    eg.media_duracao_minutos,
    rp.procedimento AS procedimento_mais_comum
FROM EstatisticasGerais eg
LEFT JOIN RankingProcedimentos rp 
    ON eg.ano = rp.ano 
   AND eg.mes = rp.mes 
   AND eg.id_unidade = rp.id_unidade 
   AND rp.rn = 1;



