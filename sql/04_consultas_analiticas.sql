-- Arquivo reservado para o integrante responsável.
-- Não implementar nesta branch.

-- Utilizando LEFT JOIN para incluir dados como residentes com 0 atendimentos realizados
-- e com 0 plantões 

-- As consultas levaram 0.06s a mais que a apenas utilizando JOINS

-- RANKING dos RESIDENTES por NÚMERO DE ATENDIMENTOS REALIZADOS (Mostrar nome e total)

SELECT 
    p.nome,
    COUNT(a.id) AS total_atendimentos
FROM pessoa p
JOIN atuacao_profissional ap ON p.id = ap.id_profissional
JOIN atuacao_residente ar ON ap.id = ar.id
LEFT JOIN atendimento a ON ar.id = a.id_atuacao_residente
GROUP BY 
    p.id, 
    p.nome
ORDER BY 
    total_atendimentos DESC;

-- PERCEPTORES que SUPERVISIONARAM mais de 5 ATENDIMENTOS em um determinado mês

SELECT 
    p.nome,
    COUNT(a.id) AS total_supervisionado
FROM pessoa p
JOIN atuacao_profissional ap ON p.id = ap.id_profissional
JOIN atuacao_preceptor apre ON ap.id = apre.id
JOIN atendimento a ON apre.id = a.id_atuacao_preceptor
WHERE
    a.data_hora >= %(mes_referencia)s
    AND a.data_hora < %(mes_referencia)s::date + interval '1 month'
GROUP BY p.id, p.nome
HAVING
    COUNT(a.id) > 5;

-- QUANTIDADE de PLANTÕES ESCALADOS por RESIDENTE no MÊS CORRENTE, por UNIDADE

SELECT 
    u.nome AS unidade,
    p.nome AS residente,
    COUNT(e.id) AS quantidade_plantoes
FROM unidade u
-- Mudamos o filtro de data para dentro do ON
LEFT JOIN escala e ON u.id = e.id_unidade
    AND e.data_plantao >= date_trunc('month', CURRENT_DATE)
    AND e.data_plantao < date_trunc('month', CURRENT_DATE) + interval '1 month'
-- Todos os joins seguintes precisam ser LEFT para não anular o primeiro
LEFT JOIN atuacao_residente ar ON e.id_atuacao_residente = ar.id
LEFT JOIN atuacao_profissional ap ON ar.id = ap.id
LEFT JOIN pessoa p ON ap.id_profissional = p.id
GROUP BY 
    u.id, 
    u.nome, 
    p.id, 
    p.nome
ORDER BY 
    u.nome ASC, 
    quantidade_plantoes DESC;

-- PACIENTE que NUNCA realizaram NENHUM procedimento de nível de RISCO ALTO

SELECT 
    pes.nome,
    pac.num_convenio
FROM pessoa pes
JOIN paciente pac ON pes.id = pac.id
WHERE NOT EXISTS (
    SELECT 1
    FROM atendimento a
    JOIN procedimento_realizado pr ON a.id = pr.id_atendimento
    JOIN procedimento proc ON pr.id_procedimento = proc.id
    WHERE 
        a.id_paciente = pac.id
        AND proc.nivel_risco = 'alto'
);


