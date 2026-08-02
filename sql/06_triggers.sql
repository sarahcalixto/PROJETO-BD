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




