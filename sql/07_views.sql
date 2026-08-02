-- implementação das views da etapa2 do projeto de banco de dados --

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



