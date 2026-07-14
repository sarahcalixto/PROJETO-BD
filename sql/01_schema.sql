--- 

create type grupo_sanguineo as enum ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-');
create type turno as enum ('manha', 'tarde', 'noite');
create type risco as enum ('baixo', 'medio', 'alto');
create type ano_residencia as enum ('R1', 'R2', 'R3');
create type tipo_unidade as enum ('enfermaria', 'uti','ambulatorio');
create type tipo_atuacao as enum ('residente', 'preceptor');

---

create table pessoa (
  id serial primary key,
  nome varchar(255) not null,
  cpf varchar(11) unique not null,
  data_nascimento date not null,
  is_flamengo boolean not null default true,
  telefone text,
);

create table paciente (
  id int primary key references pessoa(id) on delete cascade,
  num_convenio text,
  alergias text, -- TODO: maybe we can model this better(?)
  grupo_sanguineo grupo_sanguineo,
);

create table profissional (
  id int primary key references pessoa(id) on delete cascade,
  crm text not null unique,
  data_admissao date not null,
  especialidade text not null,
);

---

/*
* Um profissional pode atuar como preceptor em um determinado período
* e como residente em outro (histórico),
* mas em um dado momento ele ocupa apenas um papel no sistema
* TODO: so we need to make id be disjunt from atuacao
*/

create table atuacao_profissional (
  id serial primary key,
  id_profissional int references profissional(id) on delete cascade,
  tipo tipo_atuacao not null,
  data_inicio date not null,
  data_fim date,

  -- FIXME: can data_fim be null? dunno
  constraint atuacao_periodo_valido check (data_fim is null or data_fim >= data_inicio),
);

create table atuacao_residente (
  id int primary key references atuacao_profissional(id) on delete cascade,
  ano_residencia ano_residencia
);

create table atuacao_preceptor (
  id int primary key references atuacao_profissional(id) on delete cascade,
  titulacao text,
);

---

create table unidade (
  id serial primary key,
  nome varchar(255),
  tipo tipo_unidade,
  capacidade_leitos int check (capacidade_leitos >= 0)
);

create table atendimento (
  id serial primary key,
  duracao_minutos smallint, -- TODO: we surely can make this better
  id_paciente int references paciente(id) on delete cascade,
  id_atuacao_residente int references atuacao_residente(id) on delete cascade,
  id_atuacao_preceptor int references atuacao_preceptor(id) on delete cascade,
  id_unidade int references unidade(id) on delete cascade,
);

create table procedimento (
  id serial primary key,
  codigo int unique not null,
  nome varchar(255) not null,
  tempo_medio_minutos int check (tempo_medio_minutos >= 0),
  nivel_risco risco not null,
);

create table procedimento_realizado (
  id_atendimento int references atendimento(id),
  id_procedimento int references procedimento(id),
  quantidade int check (quantidade >= 0),
  tempo_real_minutos int check (tempo_medio_minutos >= 0),
  observacao text,
  faturado boolean default false,

  primary key (id_atendimento, id_procedimento)
);

create table escala (
  id serial primary key,
  id_unidade int references unidade(id),
  data_plantao date not null,
  turno turno not null,
  id_atuacao_residente int references atuacao_residente(id),
  id_atuacao_preceptor int references atuacao_preceptor(id),
);
