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

-- LISTAGEM DE ATENDIMENTOS DE UM PACIENTE
-- Finalidade:
--   Listar todos os atendimentos de um paciente especifico em ordem
--   cronologica crescente.
--
-- Identificador esperado:
--   id_paciente, correspondente a PACIENTE(id_pessoa) e usado diretamente em
--   ATENDIMENTO.id_paciente.
--
-- Tabela principal:
--   ATENDIMENTO.
--
-- Chave usada no filtro:
--   ATENDIMENTO.id_paciente.
--
-- Coluna usada na ordenacao:
--   ATENDIMENTO.data_hora ASC.
--
-- Exemplo de execucao:
--   Substitua :id_paciente pelo identificador desejado ao executar no cliente
--   SQL, ou use o mecanismo de parametro equivalente.

SELECT
    id_atendimento,
    data_hora,
    duracao_minutos,
    id_paciente,
    id_atuacao_residente,
    id_atuacao_preceptor,
    id_unidade
FROM atendimento
WHERE id_paciente = :id_paciente
ORDER BY data_hora ASC;

-- LISTAGEM DE PROCEDIMENTOS DE UM ATENDIMENTO
-- Finalidade:
--   Listar os procedimentos realizados em um atendimento especifico,
--   exibindo o nome do procedimento, a quantidade e o tempo real gasto.
--
-- Identificador esperado:
--   id_atendimento, correspondente a ATENDIMENTO(id_atendimento) e usado
--   diretamente em PROCEDIMENTO_REALIZADO.id_atendimento.
--
-- Tabela principal:
--   PROCEDIMENTO_REALIZADO.
--
-- Chave usada no filtro:
--   PROCEDIMENTO_REALIZADO.id_atendimento.
--
-- Chave usada no JOIN:
--   PROCEDIMENTO.id_procedimento = PROCEDIMENTO_REALIZADO.id_procedimento.
--
-- Colunas retornadas:
--   PROCEDIMENTO_REALIZADO.id_procedimento, PROCEDIMENTO.nome,
--   PROCEDIMENTO_REALIZADO.quantidade e
--   PROCEDIMENTO_REALIZADO.tempo_real_minutos.
--
-- Exemplo de execucao:
--   Substitua :id_atendimento pelo identificador desejado ao executar no
--   cliente SQL, ou use o mecanismo de parametro equivalente.

SELECT
    pr.id_procedimento,
    p.nome,
    pr.quantidade,
    pr.tempo_real_minutos
FROM procedimento_realizado AS pr
JOIN procedimento AS p
    ON p.id_procedimento = pr.id_procedimento
WHERE pr.id_atendimento = :id_atendimento;

-- ATUALIZAÇÃO DOS DADOS DE UM PACIENTE
-- Finalidade:
--   Atualizar o numero do convenio de um paciente existente.
--
-- Parametros:
--   p_id_paciente: identificador do paciente, correspondente a
--   PACIENTE(id_pessoa).
--   p_num_convenio: novo valor para PACIENTE.num_convenio.
--
-- Tabela envolvida:
--   PACIENTE.
--
-- Campos permitidos:
--   PACIENTE.num_convenio. A documentacao confirma que PACIENTE tambem possui
--   alergias e grupo_sanguineo, mas nao define que esses campos devam ser
--   atualizados nesta operacao.
--
-- Validacoes:
--   A funcao localiza o paciente diretamente pela chave primaria e informa erro
--   quando o identificador nao existe. Restrições de nulidade, unicidade ou
--   dominio ficam a cargo do schema fisico oficial.
--
-- Retorno:
--   Retorna o identificador do paciente e o numero de convenio gravado.
--
-- Exemplo:
--   SELECT *
--   FROM atualizar_num_convenio_paciente(1, 'CONV-2026-001');

CREATE OR REPLACE FUNCTION atualizar_num_convenio_paciente(
    p_id_paciente paciente.id_pessoa%TYPE,
    p_num_convenio paciente.num_convenio%TYPE
)
RETURNS TABLE (
    id_paciente paciente.id_pessoa%TYPE,
    num_convenio paciente.num_convenio%TYPE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    UPDATE paciente
    SET num_convenio = p_num_convenio
    WHERE id_pessoa = p_id_paciente
    RETURNING paciente.id_pessoa, paciente.num_convenio;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Paciente nao encontrado: id_pessoa=%', p_id_paciente
            USING ERRCODE = 'no_data_found';
    END IF;
END;
$$;

-- REMOÇÃO DE PROCEDIMENTO REALIZADO NÃO FATURADO
-- Finalidade:
--   Remover um procedimento realizado somente quando ele ainda nao estiver
--   faturado.
--
-- Parametros:
--   p_id_atendimento: identificador do atendimento.
--   p_id_procedimento: identificador do procedimento.
--
-- Chave utilizada:
--   PROCEDIMENTO_REALIZADO possui chave primaria composta por
--   (id_atendimento, id_procedimento).
--
-- Regra de faturamento:
--   A remocao so ocorre quando PROCEDIMENTO_REALIZADO.faturado = FALSE. Essa
--   condicao faz parte do proprio DELETE.
--
-- Tratamento de registro inexistente:
--   Se a chave composta nao existir, a funcao emite erro claro.
--
-- Tratamento de registro faturado:
--   Se a chave composta existir, mas faturado for TRUE, a funcao bloqueia a
--   remocao e emite erro claro.
--
-- Retorno:
--   Retorna a chave composta removida e o valor de faturado removido, que sera
--   sempre FALSE quando a operacao for bem-sucedida.
--
-- Exemplo:
--   SELECT *
--   FROM remover_procedimento_realizado_nao_faturado(1, 2);

CREATE OR REPLACE FUNCTION remover_procedimento_realizado_nao_faturado(
    p_id_atendimento procedimento_realizado.id_atendimento%TYPE,
    p_id_procedimento procedimento_realizado.id_procedimento%TYPE
)
RETURNS TABLE (
    id_atendimento procedimento_realizado.id_atendimento%TYPE,
    id_procedimento procedimento_realizado.id_procedimento%TYPE,
    faturado procedimento_realizado.faturado%TYPE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    DELETE FROM procedimento_realizado AS pr
    WHERE pr.id_atendimento = p_id_atendimento
      AND pr.id_procedimento = p_id_procedimento
      AND pr.faturado = FALSE
    RETURNING pr.id_atendimento, pr.id_procedimento, pr.faturado;

    IF FOUND THEN
        RETURN;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM procedimento_realizado AS pr
        WHERE pr.id_atendimento = p_id_atendimento
          AND pr.id_procedimento = p_id_procedimento
    ) THEN
        RAISE EXCEPTION
            'Procedimento realizado ja faturado: id_atendimento=%, id_procedimento=%',
            p_id_atendimento,
            p_id_procedimento
            USING ERRCODE = 'check_violation';
    END IF;

    RAISE EXCEPTION
        'Procedimento realizado nao encontrado: id_atendimento=%, id_procedimento=%',
        p_id_atendimento,
        p_id_procedimento
        USING ERRCODE = 'no_data_found';
END;
$$;

-- ============================================================
-- TEMPO MÉDIO DOS ATENDIMENTOS POR ATUAÇÃO RESIDENTE
-- ============================================================

-- Finalidade:
--   Calcular o tempo medio de duracao dos atendimentos por atuacao residente
--   e exibir o nome do profissional associado a essa atuacao.
--
-- Tabelas utilizadas:
--   ATENDIMENTO, ATUACAO_RESIDENTE, ATUACAO_PROFISSIONAL, PROFISSIONAL e
--   PESSOA.
--
-- Caminho dos relacionamentos:
--   ATENDIMENTO.id_atuacao_residente -> ATUACAO_RESIDENTE.id_atuacao
--   ATUACAO_RESIDENTE.id_atuacao -> ATUACAO_PROFISSIONAL.id_atuacao
--   ATUACAO_PROFISSIONAL.id_profissional -> PROFISSIONAL.id_pessoa
--   PROFISSIONAL.id_pessoa -> PESSOA.id_pessoa
--
-- Campo usado para calcular a duracao:
--   ATENDIMENTO.duracao_minutos.
--
-- Unidade do resultado:
--   Minutos.
--
-- Tratamento de valores nulos:
--   Atendimentos com duracao_minutos nula nao entram na media.
--
-- Tratamento de atendimentos ainda em andamento:
--   O modelo armazena duracao_minutos e nao possui data/hora de termino; logo,
--   atendimentos sem duracao preenchida sao ignorados.
--
-- Estrategia de agregacao:
--   A media e calculada primeiro por id_atuacao_residente em uma subconsulta
--   derivada. Depois o resultado agregado e associado apenas as tabelas
--   necessarias para obter o nome do profissional, evitando multiplicar linhas
--   de atendimento antes da agregacao.
--
-- Exemplo de execucao:
--   Execute a consulta abaixo diretamente no cliente SQL.

SELECT
    medias.id_atuacao_residente,
    pessoa.nome AS nome_profissional,
    medias.tempo_medio_minutos
FROM (
    SELECT
        id_atuacao_residente,
        AVG(duracao_minutos) AS tempo_medio_minutos
    FROM atendimento
    WHERE duracao_minutos IS NOT NULL
      AND duracao_minutos > 0
    GROUP BY id_atuacao_residente
) AS medias
JOIN atuacao_residente
    ON atuacao_residente.id_atuacao = medias.id_atuacao_residente
JOIN atuacao_profissional
    ON atuacao_profissional.id_atuacao = atuacao_residente.id_atuacao
JOIN profissional
    ON profissional.id_pessoa = atuacao_profissional.id_profissional
JOIN pessoa
    ON pessoa.id_pessoa = profissional.id_pessoa
ORDER BY
    medias.tempo_medio_minutos DESC,
    pessoa.nome ASC;
