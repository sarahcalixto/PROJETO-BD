-- Dados de teste — Etapa 1
--
-- Cobre o minimo exigido pelo enunciado: 5 pacientes, 5 residentes,
-- 5 preceptores, 3 unidades, 10 atendimentos e 10 procedimentos realizados


BEGIN;

-- PESSOA -----------------------------------------------------------------
-- 1..5   -> pacientes
-- 6..10  -> residentes
-- 11..15 -> preceptores
-- 16..19 -> preceptores adicionais (equipe do projeto)

INSERT INTO pessoa (nome, cpf, data_nascimento, is_flamengo, telefone) VALUES
  ('Gon Freecss',          '10000000001', '1985-03-12', true,  '21988880001'),
  ('Edward Elric',         '10000000002', '1990-07-24', false, '21988880002'),
  ('Giorno Giovanna',      '10000000003', '1978-11-02', true,  '21988880003'),
  ('Killua Zoldyck',       '10000000004', '1995-01-30', false, '21988880004'),
  ('Winry Rockbell',       '10000000005', '1966-09-18', true,  '21988880005'),
  ('Narancia Ghirga',      '10000000006', '1996-04-09', true,  '21988880006'),
  ('Kurapika',             '10000000007', '1997-05-14', false, '21988880007'),
  ('Alphonse Elric',       '10000000008', '1995-12-20', true,  '21988880008'),
  ('Trish Una',            '10000000009', '1998-02-27', false, '21988880009'),
  ('Leorio Paradinight',   '10000000010', '1996-08-05', true,  '21988880010'),
  ('Bruno Bucciarati',     '10000000011', '1975-06-11', false, '21988880011'),
  ('Chrollo Lucilfer',     '10000000012', '1970-10-03', true,  '21988880012'),
  ('Roy Mustang',          '10000000013', '1980-01-22', false, '21988880013'),
  ('Leone Abbacchio',      '10000000014', '1968-03-15', true,  '21988880014'),
  ('Riza Hawkeye',         '10000000015', '1982-07-07', false, '21988880015'),
  ('Samuel Santos Ismael da Costa',    '10000000016', '2000-04-11', true,  '21988880016'),
  ('Ruan Campelo de Pontes',           '10000000017', '2000-06-23', true,  '21988880017'),
  ('Sarah Fernanda Calixto de Araujo', '10000000018', '2000-09-02', true,  '21988880018'),
  ('Ana Carolina de Sousa Camilo',     '10000000019', '2000-12-15', false, '21988880019');

-- PACIENTE -----------------------------------------------------------------

INSERT INTO paciente (id, num_convenio, grupo_sanguineo) VALUES
  (1, 'CONV-2026-001', 'O+'),
  (2, 'CONV-2026-002', 'A-'),
  (3, 'CONV-2026-003', 'B+'),
  (4, 'CONV-2026-004', 'AB+'),
  (5, 'CONV-2026-005', 'O-');

-- ALERGIA / PACIENTE_ALERGIA -------------------------------------------

INSERT INTO alergia (nome) VALUES
  ('Dipirona'),
  ('Penicilina'),
  ('Sulfa'),
  ('Frutos do Mar');

INSERT INTO paciente_alergia (id_paciente, id_alergia) VALUES
  (1, 1),
  (1, 3),
  (3, 2),
  (4, 4);

-- PROFISSIONAL ---------------------------------------------------------

INSERT INTO profissional (id, crm, data_admissao, especialidade) VALUES
  (6,  'CRM-RJ-100006', '2023-02-01', 'Clinica Medica'),
  (7,  'CRM-RJ-100007', '2023-02-01', 'Cirurgia Geral'),
  (8,  'CRM-RJ-100008', '2024-02-01', 'Pediatria'),
  (9,  'CRM-RJ-100009', '2024-02-01', 'Ortopedia'),
  (10, 'CRM-RJ-100010', '2025-02-01', 'Ginecologia'),
  (11, 'CRM-RJ-100011', '2015-03-01', 'Clinica Medica'),
  (12, 'CRM-RJ-100012', '2012-03-01', 'Cirurgia Geral'),
  (13, 'CRM-RJ-100013', '2018-03-01', 'Pediatria'),
  (14, 'CRM-RJ-100014', '2010-03-01', 'Ortopedia'),
  (15, 'CRM-RJ-100015', '2016-03-01', 'Ginecologia'),
  (16, 'CRM-RJ-100016', '2024-03-01', 'Cardiologia'),
  (17, 'CRM-RJ-100017', '2024-03-01', 'Neurologia'),
  (18, 'CRM-RJ-100018', '2024-03-01', 'Dermatologia'),
  (19, 'CRM-RJ-100019', '2024-03-01', 'Urologista');

-- ATUACAO_PROFISSIONAL ---------------------------------------------------
-- 1..5   -> atuacoes de residente
-- 6..10  -> atuacoes de preceptor
-- 11..14 -> atuacoes de preceptor
-- data_inicio fica no passado e data_fim NULL para garantir vigencia

INSERT INTO atuacao_profissional (id_profissional, tipo, data_inicio, data_fim) VALUES
  (6,  'residente', '2023-02-01', NULL),
  (7,  'residente', '2023-02-01', NULL),
  (8,  'residente', '2024-02-01', NULL),
  (9,  'residente', '2024-02-01', NULL),
  (10, 'residente', '2025-02-01', NULL),
  (11, 'preceptor', '2015-03-01', NULL),
  (12, 'preceptor', '2012-03-01', NULL),
  (13, 'preceptor', '2018-03-01', NULL),
  (14, 'preceptor', '2010-03-01', NULL),
  (15, 'preceptor', '2016-03-01', NULL),
  (16, 'preceptor', '2024-03-01', NULL),
  (17, 'preceptor', '2024-03-01', NULL),
  (18, 'preceptor', '2024-03-01', NULL),
  (19, 'preceptor', '2024-03-01', NULL);

INSERT INTO atuacao_residente (id, ano_residencia) VALUES
  (1, 'R3'),
  (2, 'R3'),
  (3, 'R2'),
  (4, 'R2'),
  (5, 'R1');

INSERT INTO atuacao_preceptor (id, titulacao) VALUES
  (6,  'doutor'),
  (7,  'doutor'),
  (8,  'mestre'),
  (9,  'doutor'),
  (10, 'mestre'),
  (11, 'doutor'),
  (12, 'doutor'),
  (13, 'doutor'),
  (14, 'doutor');

-- UNIDADE ------------------------------------------------------------------

INSERT INTO unidade (nome, tipo, capacidade_leitos) VALUES
  ('Enfermaria Central',      'enfermaria',     40),
  ('UTI Adulto',              'uti',            12),
  ('Pronto-Socorro Principal','pronto-socorro', 20);

-- PROCEDIMENTO ---------------------------------------------------------

INSERT INTO procedimento (codigo, nome, tempo_medio_minutos, nivel_risco) VALUES
  (1001, 'Sutura',                 20, 'baixo'),
  (1002, 'Coleta de sangue',       10, 'baixo'),
  (1003, 'Aplicacao de medicacao', 15, 'medio'),
  (1004, 'Intubacao orotraqueal',  45, 'alto'),
  (1005, 'Curativo complexo',      25, 'medio'),
  (1006, 'Drenagem toracica',      50, 'alto');

-- ATENDIMENTO ------------------------------------------------------------
-- Distribuicao pensada para as consultas analiticas:
--   * residente da atuacao 1 (Narancia Ghirga) fica em 1o lugar no
--     ranking de atendimentos (3 atendimentos)
--   * preceptor da atuacao 6 (Bruno Bucciarati) supervisiona 7
--     atendimentos no mes corrente (> 5), cobrindo a consulta de
--     preceptores com mais de 5 atendimentos no mes

INSERT INTO atendimento (
  data_hora, duracao_minutos,
  id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade
) VALUES
  (date_trunc('month', CURRENT_DATE) + interval '1 day 08:00', 30, 1, 1, 6, 1),
  (date_trunc('month', CURRENT_DATE) + interval '1 day 09:00', 45, 2, 1, 6, 1),
  (date_trunc('month', CURRENT_DATE) + interval '2 day 10:00', 20, 3, 1, 7, 2),
  (date_trunc('month', CURRENT_DATE) + interval '2 day 11:00', 60, 4, 2, 6, 2),
  (date_trunc('month', CURRENT_DATE) + interval '3 day 08:30', 25, 5, 2, 6, 3),
  (date_trunc('month', CURRENT_DATE) + interval '3 day 09:30', 40, 1, 3, 6, 3),
  (date_trunc('month', CURRENT_DATE) + interval '4 day 08:00', 35, 2, 3, 6, 1),
  (date_trunc('month', CURRENT_DATE) + interval '4 day 09:00', 50, 3, 4, 6, 2),
  (date_trunc('month', CURRENT_DATE) + interval '5 day 08:00', 15, 4, 5, 7, 3),
  (date_trunc('month', CURRENT_DATE) + interval '5 day 09:00', 55, 5, 5, 8, 1);

-- PROCEDIMENTO_REALIZADO ------------------------------------------------
-- Um procedimento por atendimento
-- Atendimentos 4 e 7 aplicam procedimentos de risco ALTO, 
-- de modo que os pacientes 2 e 4 fiquem de
-- fora da consulta "nunca realizou procedimento de risco ALTO"
-- (pacientes 1, 3 e 5 permanecem elegiveis)

INSERT INTO procedimento_realizado (
  id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao, faturado
) VALUES
  (1,  1, 1, 25, 'Sutura simples sem intercorrencias', true),
  (2,  2, 1, 10, 'Coleta de rotina',                   false),
  (3,  3, 2, 15, 'Duas doses aplicadas',               false),
  (4,  4, 1, 50, 'Intubacao em contexto de urgencia',  false),
  (5,  5, 1, 20, 'Curativo pos-cirurgico',             false),
  (6,  1, 1, 22, 'Sutura de retorno',                  false),
  (7,  6, 1, 45, 'Drenagem sem intercorrencias',       false),
  (8,  2, 1, 8,  'Coleta adicional para exame',        false),
  (9,  3, 1, 12, 'Aplicacao unica',                    false),
  (10, 5, 1, 18, 'Curativo de rotina',                 false);

-- ESCALA -------------------------------------------------------------------
-- residente da atuacao 1 com 2 plantoes na mesma unidade

INSERT INTO escala (
  id_unidade, data_plantao, turno, id_atuacao_residente, id_atuacao_preceptor
) VALUES
  (1, (date_trunc('month', CURRENT_DATE) + interval '1 day')::date, 'manha', 1, 6),
  (1, (date_trunc('month', CURRENT_DATE) + interval '2 day')::date, 'tarde', 1, 6),
  (2, (date_trunc('month', CURRENT_DATE) + interval '1 day')::date, 'noite', 2, 7),
  (2, (date_trunc('month', CURRENT_DATE) + interval '3 day')::date, 'manha', 3, 6),
  (3, (date_trunc('month', CURRENT_DATE) + interval '2 day')::date, 'tarde', 4, 8),
  (3, (date_trunc('month', CURRENT_DATE) + interval '4 day')::date, 'manha', 5, 7);

COMMIT;
