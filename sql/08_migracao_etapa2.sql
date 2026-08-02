-- Migração idempotente do schema da Etapa 1 para o produto final da Etapa 2.
-- Este arquivo preserva os registros existentes; os objetos programáveis são
-- atualizados pelos scripts 05, 06 e 07 após esta migração estrutural.

ALTER TABLE procedimento
    ADD COLUMN IF NOT EXISTS media_tempo_procedimento numeric(10, 2);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'procedimento_media_tempo_positivo'
    ) THEN
        ALTER TABLE procedimento
            ADD CONSTRAINT procedimento_media_tempo_positivo
            CHECK (
                media_tempo_procedimento IS NULL
                OR media_tempo_procedimento > 0
            );
    END IF;
END;
$$;

ALTER TABLE procedimento_realizado
    ADD COLUMN IF NOT EXISTS data_hora_inicio timestamp;

UPDATE procedimento_realizado AS pr
SET data_hora_inicio = a.data_hora
FROM atendimento AS a
WHERE a.id = pr.id_atendimento
  AND pr.data_hora_inicio IS NULL;

ALTER TABLE procedimento_realizado
    ALTER COLUMN data_hora_inicio SET NOT NULL;

CREATE TABLE IF NOT EXISTS internacao (
    id serial PRIMARY KEY,
    id_paciente int NOT NULL REFERENCES paciente(id),
    id_unidade int NOT NULL REFERENCES unidade(id),
    data_hora_entrada timestamp NOT NULL,
    data_hora_saida timestamp,
    CONSTRAINT internacao_periodo_valido CHECK (
        data_hora_saida IS NULL
        OR data_hora_saida >= data_hora_entrada
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS internacao_paciente_ativa_uq
    ON internacao (id_paciente)
    WHERE data_hora_saida IS NULL;

CREATE TABLE IF NOT EXISTS auditoria_atendimento (
    id_auditoria bigserial PRIMARY KEY,
    id_atendimento int NOT NULL,
    operacao varchar(6) NOT NULL
        CHECK (operacao IN ('INSERT', 'UPDATE', 'DELETE')),
    usuario text NOT NULL,
    data_hora timestamp with time zone NOT NULL DEFAULT current_timestamp,
    dados_antigos jsonb,
    dados_novos jsonb
);

UPDATE procedimento AS p
SET media_tempo_procedimento = medias.valor
FROM (
    SELECT id_procedimento, ROUND(AVG(tempo_real_minutos), 2) AS valor
    FROM procedimento_realizado
    GROUP BY id_procedimento
) AS medias
WHERE medias.id_procedimento = p.id;
