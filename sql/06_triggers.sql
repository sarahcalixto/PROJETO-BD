-- Integridade da especialização de atuação profissional. A validação é
-- diferida para permitir inserir a atuação-pai e seu subtipo na mesma transação.
CREATE OR REPLACE FUNCTION valida_especializacao_atuacao()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id integer := COALESCE(NEW.id, OLD.id);
    v_tipo tipo_atuacao;
    v_residente boolean;
    v_preceptor boolean;
BEGIN
    SELECT tipo INTO v_tipo
    FROM atuacao_profissional
    WHERE id = v_id;

    IF NOT FOUND THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    SELECT
        EXISTS (SELECT 1 FROM atuacao_residente WHERE id = v_id),
        EXISTS (SELECT 1 FROM atuacao_preceptor WHERE id = v_id)
    INTO v_residente, v_preceptor;

    IF v_residente = v_preceptor
       OR (v_tipo = 'residente' AND NOT v_residente)
       OR (v_tipo = 'preceptor' AND NOT v_preceptor) THEN
        RAISE EXCEPTION
            'A atuação % deve possuir exatamente um subtipo compatível com %.',
            v_id, v_tipo
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_valida_especializacao_atuacao
ON atuacao_profissional;
CREATE CONSTRAINT TRIGGER trg_valida_especializacao_atuacao
AFTER INSERT OR UPDATE ON atuacao_profissional
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION valida_especializacao_atuacao();

DROP TRIGGER IF EXISTS trg_valida_especializacao_residente
ON atuacao_residente;
CREATE CONSTRAINT TRIGGER trg_valida_especializacao_residente
AFTER INSERT OR UPDATE OR DELETE ON atuacao_residente
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION valida_especializacao_atuacao();

DROP TRIGGER IF EXISTS trg_valida_especializacao_preceptor
ON atuacao_preceptor;
CREATE CONSTRAINT TRIGGER trg_valida_especializacao_preceptor
AFTER INSERT OR UPDATE OR DELETE ON atuacao_preceptor
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION valida_especializacao_atuacao();

DO $$
DECLARE
    v_atuacao atuacao_profissional%ROWTYPE;
    v_residente boolean;
    v_preceptor boolean;
BEGIN
    FOR v_atuacao IN SELECT * FROM atuacao_profissional LOOP
        SELECT
            EXISTS (SELECT 1 FROM atuacao_residente WHERE id = v_atuacao.id),
            EXISTS (SELECT 1 FROM atuacao_preceptor WHERE id = v_atuacao.id)
        INTO v_residente, v_preceptor;

        IF v_residente = v_preceptor
           OR (v_atuacao.tipo = 'residente' AND NOT v_residente)
           OR (v_atuacao.tipo = 'preceptor' AND NOT v_preceptor) THEN
            RAISE EXCEPTION 'Atuação % possui especialização inválida.', v_atuacao.id
                USING ERRCODE = 'check_violation';
        END IF;
    END LOOP;
END;
$$;

-- Triggers exigidos e garantias temporais complementares.

-- função que vai verificar se está ocorrendo a sobreposição de horário do residente em outras unidades --
CREATE OR REPLACE FUNCTION check_sobreposicao_escala()
RETURNS TRIGGER
AS $$ -- a função retorna o trigger
BEGIN
    -- verifica se o residente já possui plantão na mesma data e turno em outra unidade
    IF EXISTS(
        SELECT 1
        FROM escala
        WHERE data_plantao = NEW.data_plantao
         AND turno = NEW.turno
         AND id_atuacao_residente = NEW.id_atuacao_residente
         AND id_unidade <> NEW.id_unidade -- <> esse símbolo indica "diferente de" basicamente verificando a diferença entre as unidades
         AND id <> COALESCE(NEW.id, -1) -- aqui temos a função COALESCE que retorna o primeiro valor NÃO nulo em uma lista de expressões
         -- ela garante que em caso de UPDATE a linha não se compare consigo mesma
         ) THEN
            RAISE EXCEPTION 'Conflito de escala: O residente (ID atuação %) já está escalado no dia % no turno % em outra unidade',
                NEW.id_atuacao_residente, NEW.data_plantao, NEW.turno
                USING ERRCODE = 'check_violation'; -- deixando como erro padronizado
        END IF;

        RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- criação do trigger trg_check_sobreposicao_escala para INSERT e UPDATE --
DROP TRIGGER IF EXISTS trg_check_sobreposicao_escala ON escala; -- como não existe CREATE OR REPLACE TRIGGER no PostgreSQL

CREATE TRIGGER trg_check_sobreposicao_escala
BEFORE INSERT OR UPDATE ON escala
FOR EACH ROW EXECUTE FUNCTION check_sobreposicao_escala(); -- trigger do tipo linha pois é preciso validar dados específicos

-- função do trigger trg_audita_atendimento --
CREATE OR REPLACE FUNCTION audita_atendimento()
RETURNS TRIGGER
AS $$
DECLARE
v_old JSONB := NULL; -- dados antigos
v_new JSONB := NULL; -- dados novos
v_id_atendimento INT; -- garantir que o ID seja adquirido corretamente

BEGIN
    -- captura os estados da linha dependendo da operação
    IF(TG_OP = 'DELETE') THEN
        v_old := to_jsonb(OLD);
        v_id_atendimento := OLD.id;
    ELSIF(TG_OP = 'UPDATE') THEN
        v_old := to_jsonb(OLD);
        v_new := to_jsonb(NEW);
        v_id_atendimento := NEW.id;
    ELSIF (TG_OP = 'INSERT') THEN
        v_new := to_jsonb(NEW);
        v_id_atendimento := NEW.id;
    END IF;

    -- o campo data_hora foi omitido para apoveitar o DEFAULT do schema
    INSERT INTO auditoria_atendimento (
        id_atendimento, operacao, usuario, dados_antigos, dados_novos
    ) VALUES (
        v_id_atendimento, TG_OP, current_user, v_old, v_new
    );

    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audita_atendimento ON atendimento;
CREATE TRIGGER trg_audita_atendimento
AFTER INSERT OR UPDATE OR DELETE ON atendimento
-- se foi usado um trigger do tipo linha novamente pelos motivos de:
-- acesso aos dados individuais que é necessário para estabelecer os dados antigos e o depois de cada linha
-- caso alguém execute um comando para remover 50 atendimentos de uma vez com trigger de comando o histórico seria perdido

FOR EACH ROW EXECUTE FUNCTION audita_atendimento();

-- Protege as regras temporais do atendimento mesmo quando a escrita não passa
-- pela rotina de cadastro completo.
CREATE OR REPLACE FUNCTION valida_atendimento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_profissional ap
        JOIN atuacao_residente ar ON ar.id = ap.id
        WHERE ar.id = NEW.id_atuacao_residente
          AND ap.data_inicio <= NEW.data_hora::date
          AND (ap.data_fim IS NULL OR NEW.data_hora::date <= ap.data_fim)
    ) THEN
        RAISE EXCEPTION 'A atuacao residente nao esta vigente na data do atendimento.'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM atuacao_profissional ap
        JOIN atuacao_preceptor apre ON apre.id = ap.id
        WHERE apre.id = NEW.id_atuacao_preceptor
          AND ap.data_inicio <= NEW.data_hora::date
          AND (ap.data_fim IS NULL OR NEW.data_hora::date <= ap.data_fim)
    ) THEN
        RAISE EXCEPTION 'A atuacao preceptora nao esta vigente na data do atendimento.'
            USING ERRCODE = 'check_violation';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM atuacao_profissional residente
        JOIN atuacao_profissional preceptor
          ON preceptor.id = NEW.id_atuacao_preceptor
        WHERE residente.id = NEW.id_atuacao_residente
          AND residente.id_profissional = preceptor.id_profissional
    ) THEN
        RAISE EXCEPTION 'Residente e preceptor devem ser profissionais diferentes.'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_valida_atendimento ON atendimento;
CREATE TRIGGER trg_valida_atendimento
BEFORE INSERT OR UPDATE OF data_hora, id_atuacao_residente, id_atuacao_preceptor
ON atendimento
FOR EACH ROW EXECUTE FUNCTION valida_atendimento();

-- A chave estrangeira garante a existência do atendimento; este trigger
-- garante a janela temporal definida pelo contrato do domínio.
CREATE OR REPLACE FUNCTION valida_procedimento_realizado()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_inicio_atendimento timestamp;
    v_fim_atendimento timestamp;
BEGIN
    SELECT a.data_hora,
           a.data_hora + make_interval(mins => a.duracao_minutos)
    INTO v_inicio_atendimento, v_fim_atendimento
    FROM atendimento a
    WHERE a.id = NEW.id_atendimento;

    IF NEW.data_hora_inicio < v_inicio_atendimento THEN
        RAISE EXCEPTION 'O procedimento nao pode iniciar antes do atendimento.'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.data_hora_inicio + make_interval(mins => NEW.tempo_real_minutos)
       > v_fim_atendimento THEN
        RAISE EXCEPTION 'O procedimento nao pode terminar depois do atendimento.'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_valida_procedimento_realizado
ON procedimento_realizado;
CREATE TRIGGER trg_valida_procedimento_realizado
BEFORE INSERT OR UPDATE OF id_atendimento, data_hora_inicio, tempo_real_minutos
ON procedimento_realizado
FOR EACH ROW EXECUTE FUNCTION valida_procedimento_realizado();

-- função do trigger trg_atualiza_media_procedimentos --
CREATE OR REPLACE FUNCTION atualiza_media_procedimentos()
RETURNS TRIGGER
AS $$
DECLARE
    -- usando a mesma tipagem do schema
    v_media NUMERIC(10,2);
BEGIN
    -- calcula a media e força o arredondamento para 2 casas decimais
    SELECT ROUND(AVG(tempo_real_minutos), 2)
    INTO v_media
    FROM procedimento_realizado
    WHERE id_procedimento = COALESCE(NEW.id_procedimento, OLD.id_procedimento);

    -- atualiza a tabela procedimento respeitando o check (is null or > 0)
    UPDATE procedimento
    SET media_tempo_procedimento = v_media
    WHERE id = COALESCE(NEW.id_procedimento, OLD.id_procedimento);

    -- Em uma alteração da chave, o procedimento anterior também precisa ser
    -- recalculado. A média volta a NULL quando não restam ocorrências.
    IF TG_OP = 'UPDATE' AND OLD.id_procedimento <> NEW.id_procedimento THEN
        SELECT ROUND(AVG(tempo_real_minutos), 2)
        INTO v_media
        FROM procedimento_realizado
        WHERE id_procedimento = OLD.id_procedimento;

        UPDATE procedimento
        SET media_tempo_procedimento = v_media
        WHERE id = OLD.id_procedimento;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualiza_media_procedimentos ON procedimento_realizado;
CREATE TRIGGER trg_atualiza_media_procedimentos
AFTER INSERT OR UPDATE OF id_procedimento, tempo_real_minutos OR DELETE
ON procedimento_realizado
-- foi usado novamente o trigger do tipo de linha por motivos de:
-- o código precisa saber exatamente qual procedimento teve uma nova ocorrência inserida

FOR EACH ROW EXECUTE FUNCTION atualiza_media_procedimentos();

-- Ao instalar os triggers sobre uma base já preenchida, estabelece o valor
-- derivado imediatamente, inclusive no caminho de instalação de banco vazio.
UPDATE procedimento AS p
SET media_tempo_procedimento = medias.valor
FROM (
    SELECT id_procedimento, ROUND(AVG(tempo_real_minutos), 2) AS valor
    FROM procedimento_realizado
    GROUP BY id_procedimento
) AS medias
WHERE medias.id_procedimento = p.id;

UPDATE procedimento AS p
SET media_tempo_procedimento = NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM procedimento_realizado pr
    WHERE pr.id_procedimento = p.id
);
