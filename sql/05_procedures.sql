-- Procedures e controle de concorrencia
--
-- Registra um atendimento e seus procedimentos realizados em uma unica
-- operacao atomica
--
-- [
--   {
--     "id_procedimento": 1,
--     "quantidade": 1,
--     "tempo_real_minutos": 20,
--     "data_hora_inicio": "2026-08-02 09:15:00",
--     "observacao": "opcional",
--     "faturado": false
--   }
-- ]

CREATE OR REPLACE FUNCTION sp_registrar_atendimento_completo(
    p_data_hora atendimento.data_hora%TYPE,
    p_duracao_minutos atendimento.duracao_minutos%TYPE,
    p_id_paciente atendimento.id_paciente%TYPE,
    p_id_atuacao_residente atendimento.id_atuacao_residente%TYPE,
    p_id_atuacao_preceptor atendimento.id_atuacao_preceptor%TYPE,
    p_id_unidade atendimento.id_unidade%TYPE,
    p_procedimentos jsonb
)
RETURNS atendimento.id%TYPE
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_atendimento atendimento.id%TYPE;
    v_item jsonb;
    v_ordem bigint;
    v_id_procedimento procedimento_realizado.id_procedimento%TYPE;
    v_quantidade procedimento_realizado.quantidade%TYPE;
    v_tempo_real_minutos procedimento_realizado.tempo_real_minutos%TYPE;
    v_data_hora_inicio procedimento_realizado.data_hora_inicio%TYPE;
    v_observacao procedimento_realizado.observacao%TYPE;
    v_faturado procedimento_realizado.faturado%TYPE;
BEGIN
    IF p_data_hora IS NULL THEN
        RAISE EXCEPTION 'A data e hora do atendimento sao obrigatorias.'
            USING ERRCODE = 'not_null_violation';
    END IF;

    IF p_duracao_minutos IS NULL OR p_duracao_minutos <= 0 THEN
        RAISE EXCEPTION 'A duracao do atendimento deve ser positiva.'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM paciente
        WHERE id = p_id_paciente
    ) THEN
        RAISE EXCEPTION 'Paciente nao encontrado: id=%', p_id_paciente
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_residente
        WHERE id = p_id_atuacao_residente
    ) THEN
        RAISE EXCEPTION
            'Atuacao residente nao encontrada: id=%',
            p_id_atuacao_residente
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_preceptor
        WHERE id = p_id_atuacao_preceptor
    ) THEN
        RAISE EXCEPTION
            'Atuacao preceptora nao encontrada: id=%',
            p_id_atuacao_preceptor
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM unidade
        WHERE id = p_id_unidade
    ) THEN
        RAISE EXCEPTION 'Unidade nao encontrada: id=%', p_id_unidade
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_profissional AS ap
        JOIN atuacao_residente AS ar ON ar.id = ap.id
        WHERE ar.id = p_id_atuacao_residente
          AND ap.data_inicio <= p_data_hora::date
          AND (ap.data_fim IS NULL OR p_data_hora::date <= ap.data_fim)
    ) THEN
        RAISE EXCEPTION
            'Atuacao residente % nao esta vigente em %.',
            p_id_atuacao_residente,
            p_data_hora
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_profissional AS ap
        JOIN atuacao_preceptor AS apre ON apre.id = ap.id
        WHERE apre.id = p_id_atuacao_preceptor
          AND ap.data_inicio <= p_data_hora::date
          AND (ap.data_fim IS NULL OR p_data_hora::date <= ap.data_fim)
    ) THEN
        RAISE EXCEPTION
            'Atuacao preceptora % nao esta vigente em %.',
            p_id_atuacao_preceptor,
            p_data_hora
            USING ERRCODE = 'check_violation';
    END IF;

    IF p_procedimentos IS NULL
       OR jsonb_typeof(p_procedimentos) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION
            'Procedimentos deve ser um array JSONB nao vazio.'
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF jsonb_array_length(p_procedimentos) = 0 THEN
        RAISE EXCEPTION
            'A lista de procedimentos nao pode estar vazia.'
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM jsonb_array_elements(p_procedimentos) AS item(valor)
        WHERE jsonb_typeof(item.valor) IS DISTINCT FROM 'object'
    ) THEN
        RAISE EXCEPTION
            'Cada item de procedimentos deve ser um objeto JSON.'
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM jsonb_array_elements(p_procedimentos) AS item(valor)
        WHERE NOT item.valor ?& ARRAY[
                  'id_procedimento',
                  'quantidade',
                  'tempo_real_minutos',
                  'data_hora_inicio'
              ]
           OR item.valor -> 'id_procedimento' = 'null'::jsonb
           OR item.valor -> 'quantidade' = 'null'::jsonb
           OR item.valor -> 'tempo_real_minutos' = 'null'::jsonb
           OR item.valor -> 'data_hora_inicio' = 'null'::jsonb
    ) THEN
        RAISE EXCEPTION
            'Item de procedimento com campo obrigatorio ausente ou nulo.'
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    INSERT INTO atendimento (
        data_hora,
        duracao_minutos,
        id_paciente,
        id_atuacao_residente,
        id_atuacao_preceptor,
        id_unidade
    ) VALUES (
        p_data_hora,
        p_duracao_minutos,
        p_id_paciente,
        p_id_atuacao_residente,
        p_id_atuacao_preceptor,
        p_id_unidade
    )
    RETURNING id INTO v_id_atendimento;

    FOR v_item, v_ordem IN
        SELECT item.valor, item.ordem
        FROM jsonb_array_elements(p_procedimentos)
             WITH ORDINALITY AS item(valor, ordem)
        ORDER BY item.ordem
    LOOP
        BEGIN
            v_id_procedimento :=
                (v_item ->> 'id_procedimento')::integer;
            v_quantidade := (v_item ->> 'quantidade')::integer;
            v_tempo_real_minutos :=
                (v_item ->> 'tempo_real_minutos')::integer;
            v_data_hora_inicio :=
                (v_item ->> 'data_hora_inicio')::timestamp;
            v_observacao := v_item ->> 'observacao';
            v_faturado := CASE
                WHEN NOT v_item ? 'faturado'
                     OR v_item -> 'faturado' = 'null'::jsonb
                    THEN FALSE
                ELSE (v_item ->> 'faturado')::boolean
            END;
        EXCEPTION
            WHEN invalid_text_representation OR numeric_value_out_of_range THEN
                RAISE EXCEPTION
                    'Item % possui valor com tipo ou formato invalido.',
                    v_ordem
                    USING ERRCODE = 'invalid_parameter_value';
        END;

        IF NOT EXISTS (
            SELECT 1
            FROM procedimento
            WHERE id = v_id_procedimento
        ) THEN
            RAISE EXCEPTION
                'Procedimento nao encontrado no item %: id=%',
                v_ordem,
                v_id_procedimento
                USING ERRCODE = 'foreign_key_violation';
        END IF;

        IF v_quantidade <= 0 OR v_tempo_real_minutos <= 0 THEN
            RAISE EXCEPTION
                'Quantidade e tempo real devem ser positivos no item %.',
                v_ordem
                USING ERRCODE = 'check_violation';
        END IF;

        IF v_data_hora_inicio < p_data_hora THEN
            RAISE EXCEPTION
                'Inicio do procedimento no item % nao pode preceder o atendimento.',
                v_ordem
                USING ERRCODE = 'check_violation';
        END IF;

        INSERT INTO procedimento_realizado (
            id_atendimento,
            id_procedimento,
            quantidade,
            tempo_real_minutos,
            data_hora_inicio,
            observacao,
            faturado
        ) VALUES (
            v_id_atendimento,
            v_id_procedimento,
            v_quantidade,
            v_tempo_real_minutos,
            v_data_hora_inicio,
            v_observacao,
            v_faturado
        );
    END LOOP;

    RETURN v_id_atendimento;
END;
$$;
