-- implementação dos triggers da etapa2 do projeto de banco de dados --

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
    WHERE id_procedimento = NEW.id_procedimento;

    -- atualiza a tabela procedimento respeitando o check (is null or > 0)
    UPDATE procedimento
    SET media_tempo_procedimento = v_media
    WHERE id = NEW.id_procedimento;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualiza_media_procedimentos ON procedimento_realizado;
CREATE TRIGGER trg_atualiza_media_procedimentos
AFTER INSERT ON procedimento_realizado
-- foi usado novamente o trigger do tipo de linha por motivos de:
-- o código precisa saber exatamente qual procedimento teve uma nova ocorrência inserida

FOR EACH ROW EXECUTE FUNCTION atualiza_media_procedimentos();
