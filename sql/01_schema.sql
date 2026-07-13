create table pessoa (
  id serial primary key,
  nome varchar(255) not null,
  cpf varchar(11) unique not null,
  data_nascimento date,
  is_flamengo boolean default true,
  telefone varchar(20),
);

create table paciente (
  id int primary key references pessoa(id) on delete cascade,
  num_convenio varchar(50),
  alergias text, -- TODO: maybe we can model this better
  grupo_sanguineo varchar(3),
);

create table profissional (
  id int primary key references pessoa(id) on delete cascade,
  crm varchar(20) unique,
  data_admissao date,
  especialidade text,
);

---

create table atuacao_profissional (
  id serial primary key,
  id_profissional int references profissional(id) on delete cascade,
  data_inicio date,
  data_fim date,
);

create table atuacao_residente (
  id int primary key references atuacao_profissional(id) on delete cascade,
  ano_residencia text -- TODO: how can we model this better?
);

create table atuacao_preceptor (
  id int primary key references atuacao_profissional(id) on delete cascade,
  titulacao text,
);

---

create table unidade (
  id serial primary key,
  nome varchar(255),
  tipo text, -- TODO: what does this represents? :/
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

create type risco as enum ('baixo', 'medio', 'alto');

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

create type turno as enum ('manha', 'tarde', 'noite');

create table escala (
  id serial primary key,
  id_unidade int references unidade(id),
  data_plantao date not null,
  turno turno not null,
  id_atuacao_residente int references atuacao_residente(id),
  id_atuacao_preceptor int references atuacao_preceptor(id),
)
