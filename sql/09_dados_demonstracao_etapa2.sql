-- Casos mínimos e idempotentes para demonstrar requisitos da Etapa 2.

INSERT INTO internacao (
    id_paciente, id_unidade, data_hora_entrada, data_hora_saida
)
SELECT p.id, u.id, CURRENT_TIMESTAMP - interval '2 days', NULL
FROM (SELECT id FROM paciente ORDER BY id LIMIT 1) AS p
CROSS JOIN (SELECT id FROM unidade ORDER BY id LIMIT 1) AS u
WHERE NOT EXISTS (
    SELECT 1 FROM internacao i
    WHERE i.id_paciente = p.id AND i.data_hora_saida IS NULL
);

INSERT INTO internacao (
    id_paciente, id_unidade, data_hora_entrada, data_hora_saida
)
SELECT p.id, u.id,
       CURRENT_TIMESTAMP - interval '10 days',
       CURRENT_TIMESTAMP - interval '7 days'
FROM (SELECT id FROM paciente ORDER BY id OFFSET 1 LIMIT 1) AS p
CROSS JOIN (SELECT id FROM unidade ORDER BY id LIMIT 1) AS u
WHERE NOT EXISTS (
    SELECT 1 FROM internacao i
    WHERE i.id_paciente = p.id AND i.data_hora_saida IS NOT NULL
);

-- Preceptor doutor cuja atuação terminou antes do plantão.
INSERT INTO pessoa (
    id, nome, cpf, data_nascimento, is_flamengo, telefone
) VALUES (
    900001, 'Preceptor inativo de demonstração', '90000000001',
    '1975-01-01', false, NULL
) ON CONFLICT (id) DO NOTHING;

INSERT INTO profissional (id, crm, data_admissao, especialidade)
VALUES (900001, 'CRM-DEMO-900001', '2020-01-01', 'Clínica Médica')
ON CONFLICT (id) DO NOTHING;

INSERT INTO atuacao_profissional (
    id, id_profissional, tipo, data_inicio, data_fim
) VALUES (
    900001, 900001, 'preceptor', '2020-01-01', CURRENT_DATE
) ON CONFLICT (id) DO NOTHING;

INSERT INTO atuacao_preceptor (id, tipo, titulacao)
VALUES (900001, 'preceptor', 'doutor')
ON CONFLICT (id) DO NOTHING;

INSERT INTO escala (
    id_unidade, data_plantao, turno,
    id_atuacao_residente, id_atuacao_preceptor
)
SELECT u.id, CURRENT_DATE + 90, 'noite', r.id, 900001
FROM (SELECT id FROM unidade ORDER BY id LIMIT 1) AS u
CROSS JOIN (SELECT id FROM atuacao_residente ORDER BY id LIMIT 1) AS r
WHERE NOT EXISTS (
    SELECT 1 FROM escala e
    WHERE e.id_atuacao_residente = r.id
      AND e.data_plantao = CURRENT_DATE + 90
      AND e.turno = 'noite'
);

-- Residente sem atendimentos para demonstrar percentuais iguais a zero.
INSERT INTO pessoa (
    id, nome, cpf, data_nascimento, is_flamengo, telefone
) VALUES (
    900002, 'Residente sem procedimentos', '90000000002',
    '2000-01-01', false, NULL
) ON CONFLICT (id) DO NOTHING;

INSERT INTO profissional (id, crm, data_admissao, especialidade)
VALUES (900002, 'CRM-DEMO-900002', CURRENT_DATE, 'Clínica Médica')
ON CONFLICT (id) DO NOTHING;

INSERT INTO atuacao_profissional (
    id, id_profissional, tipo, data_inicio, data_fim
) VALUES (
    900002, 900002, 'residente', CURRENT_DATE, NULL
) ON CONFLICT (id) DO NOTHING;

INSERT INTO atuacao_residente (id, tipo, ano_residencia)
VALUES (900002, 'residente', 'R1')
ON CONFLICT (id) DO NOTHING;

-- Evidência persistente das três operações do trigger de auditoria.
DO $$
DECLARE
    v_paciente int;
    v_residente int;
    v_preceptor int;
    v_unidade int;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM auditoria_atendimento
        WHERE id_atendimento = 900003
    ) THEN
        SELECT id INTO v_paciente FROM paciente ORDER BY id LIMIT 1;
        SELECT id INTO v_residente FROM atuacao_residente
            WHERE id <> 900002 ORDER BY id LIMIT 1;
        SELECT apre.id INTO v_preceptor
        FROM atuacao_preceptor apre
        JOIN atuacao_profissional ap ON ap.id = apre.id
        WHERE ap.data_inicio <= CURRENT_DATE
          AND (ap.data_fim IS NULL OR ap.data_fim >= CURRENT_DATE)
        ORDER BY apre.id LIMIT 1;
        SELECT id INTO v_unidade FROM unidade ORDER BY id LIMIT 1;

        INSERT INTO atendimento (
            id, data_hora, duracao_minutos, id_paciente,
            id_atuacao_residente, id_atuacao_preceptor, id_unidade
        ) VALUES (
            900003, CURRENT_TIMESTAMP, 30, v_paciente,
            v_residente, v_preceptor, v_unidade
        );
        UPDATE atendimento SET duracao_minutos = 35 WHERE id = 900003;
        DELETE FROM atendimento WHERE id = 900003;
    END IF;
END;
$$;
