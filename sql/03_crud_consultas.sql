-- Arquivo reservado para o integrante responsável.
-- Não implementar nesta branch.

-- INSERÇÃO VALIDADA DE ATENDIMENTO
-- Finalidade:
--   Criar um atendimento somente quando as referencias obrigatorias existem
--   e as atuacoes de residente e preceptor estao vigentes na data informada.
--
-- Parametros:
--   p_id_atendimento: identificador do novo atendimento.
--   p_data_hora: data e hora do atendimento.
--   p_duracao_minutos: duracao positiva, em minutos.
--   p_id_paciente: paciente referenciado por ATENDIMENTO.id_paciente.
--   p_id_atuacao_residente: atuacao residente responsavel pelo atendimento.
--   p_id_atuacao_preceptor: atuacao preceptora supervisora do atendimento.
--   p_id_unidade: unidade em que o atendimento ocorreu.
--
-- Tabelas consultadas para validacao:
--   PACIENTE, ATUACAO_RESIDENTE, ATUACAO_PRECEPTOR,
--   ATUACAO_PROFISSIONAL e UNIDADE.
--
-- Tabela alterada:
--   ATENDIMENTO.
--
-- Exemplo:
--   SELECT inserir_atendimento_validado(
--       1,
--       TIMESTAMP '2026-07-13 09:00:00',
--       30,
--       1,
--       1,
--       2,
--       1
--   );

CREATE OR REPLACE FUNCTION inserir_atendimento_validado(
    p_id_atendimento atendimento.id_atendimento%TYPE,
    p_data_hora atendimento.data_hora%TYPE,
    p_duracao_minutos atendimento.duracao_minutos%TYPE,
    p_id_paciente atendimento.id_paciente%TYPE,
    p_id_atuacao_residente atendimento.id_atuacao_residente%TYPE,
    p_id_atuacao_preceptor atendimento.id_atuacao_preceptor%TYPE,
    p_id_unidade atendimento.id_unidade%TYPE
)
RETURNS atendimento.id_atendimento%TYPE
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_duracao_minutos IS NULL OR p_duracao_minutos <= 0 THEN
        RAISE EXCEPTION 'Duracao do atendimento deve ser positiva.'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM paciente
        WHERE id_pessoa = p_id_paciente
    ) THEN
        RAISE EXCEPTION 'Paciente nao encontrado: id_pessoa=%', p_id_paciente
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_residente
        WHERE id_atuacao = p_id_atuacao_residente
    ) THEN
        RAISE EXCEPTION 'Atuacao residente nao encontrada: id_atuacao=%', p_id_atuacao_residente
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_preceptor
        WHERE id_atuacao = p_id_atuacao_preceptor
    ) THEN
        RAISE EXCEPTION 'Atuacao preceptora nao encontrada: id_atuacao=%', p_id_atuacao_preceptor
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM unidade
        WHERE id_unidade = p_id_unidade
    ) THEN
        RAISE EXCEPTION 'Unidade nao encontrada: id_unidade=%', p_id_unidade
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_profissional
        WHERE id_atuacao = p_id_atuacao_residente
          AND data_inicio <= p_data_hora
          AND (data_fim IS NULL OR p_data_hora <= data_fim)
    ) THEN
        RAISE EXCEPTION
            'Atuacao residente % nao esta vigente em %.',
            p_id_atuacao_residente,
            p_data_hora
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_profissional
        WHERE id_atuacao = p_id_atuacao_preceptor
          AND data_inicio <= p_data_hora
          AND (data_fim IS NULL OR p_data_hora <= data_fim)
    ) THEN
        RAISE EXCEPTION
            'Atuacao preceptora % nao esta vigente em %.',
            p_id_atuacao_preceptor,
            p_data_hora
            USING ERRCODE = 'check_violation';
    END IF;

    INSERT INTO atendimento (
        id_atendimento,
        data_hora,
        duracao_minutos,
        id_paciente,
        id_atuacao_residente,
        id_atuacao_preceptor,
        id_unidade
    )
    VALUES (
        p_id_atendimento,
        p_data_hora,
        p_duracao_minutos,
        p_id_paciente,
        p_id_atuacao_residente,
        p_id_atuacao_preceptor,
        p_id_unidade
    );

    RETURN p_id_atendimento;
END;
$$;
