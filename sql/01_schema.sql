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
