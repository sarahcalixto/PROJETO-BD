-- Arquivo reservado para o integrante responsável.
-- Não implementar nesta branch.

-- RANKING dos RESIDENTES por NÚMERO DE ATENDIMENTOS REALIZADOS (Mostrar nome e total)

SELECT 
    p.nome,
    COUNT(a.id_atendimento) AS total_atendimentos 
FROM PESSOA p 
JOIN ATUACAO_PROFISSIONAL ap ON p.id_pessoa = ap.id_profissional
JOIN ATUACAO_RESIDENTE ar ON ap.id_atuacao = ar.id_atuacao
JOIN ATENDIMENTO a ON ar.id_atuacao = a.id_atuacao_residente
GROUP BY 
        p.id_pessoa,
        p.nome
ORDER BY
        total_atendimentos DESC;

-- PERCEPTORES que SUPERVISIONARAM mais de 5 ATENDIMENTOS em um determinado mês

SELECT 
    p.nome,
    COUNT(a.id_atendimento) AS total_supervisionado
FROM PESSOA p
JOIN ATUACAO_PROFISSIONAL ap ON p.id_pessoa = ap.id_profissional
JOIN ATUACAO_PRECEPTOR apre ON ap.id_atuacao = apre.id_atuacao
JOIN ATENDIMENTO a ON apre.id_atuacao = a.id_atuacao_preceptor
WHERE 
    EXTRACT(MONTH FROM a.data_hora) = 7 
    AND EXTRACT(YEAR FROM a.data_hora) = 2026
GROUP BY 
        p.id_pessoa, 
        p.nome
HAVING 
    COUNT(a.id_atendimento) > 5;

-- QUANTIDADE de PLANTÕES ESCALADOS por RESIDENTE no MÊS CORRENTE, por UNIDADE

SELECT 
    u.nome AS unidade,
    p.nome AS residente,
    COUNT(e.id_escala) AS quantidade_plantoes
FROM UNIDADE u
JOIN ESCALA e ON u.id_unidade = e.id_unidade
JOIN ATUACAO_RESIDENTE ar ON e.id_atuacao_residente = ar.id_atuacao
JOIN ATUACAO_PROFISSIONAL ap ON ar.id_atuacao = ap.id_atuacao
JOIN PESSOA p ON ap.id_profissional = p.id_pessoa
WHERE 
    EXTRACT(MONTH FROM e.data_plantao) = EXTRACT(MONTH FROM CURRENT_DATE)
    AND EXTRACT(YEAR FROM e.data_plantao) = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY 
    u.id_unidade, 
    u.nome, 
    p.id_pessoa, 
    p.nome
ORDER BY 
    u.nome ASC, 
    quantidade_plantoes DESC;

-- PACIENTE que NUNCA realizaram NENHUM procedimento de nível de RISCO ALTO

SELECT 
    pes.nome,
    pac.num_convenio
FROM PESSOA pes
JOIN PACIENTE pac ON pes.id_pessoa = pac.id_pessoa
WHERE NOT EXISTS (
    SELECT 1
    FROM ATENDIMENTO a
    JOIN PROCEDIMENTO_REALIZADO pr ON a.id_atendimento = pr.id_atendimento
    JOIN PROCEDIMENTO proc ON pr.id_procedimento = proc.id_procedimento
    WHERE 
        a.id_paciente = pac.id_pessoa
        AND proc.nivel_risco = 'ALTO'
);


