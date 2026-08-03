"""Mapeamentos SQLAlchemy das relações do sistema hospitalar."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    literal_column,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from projeto_hospital.orm.base import Base


grupo_sanguineo_type = ENUM(
    "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
    name="grupo_sanguineo",
    create_type=False,
)
turno_type = ENUM("manha", "tarde", "noite", name="turno", create_type=False)
risco_type = ENUM("baixo", "medio", "alto", name="risco", create_type=False)
ano_residencia_type = ENUM("R1", "R2", "R3", name="ano_residencia", create_type=False)
tipo_unidade_type = ENUM(
    "enfermaria", "uti", "pronto-socorro", "ambulatorio",
    name="tipo_unidade",
    create_type=False,
)
tipo_atuacao_type = ENUM(
    "residente", "preceptor", name="tipo_atuacao", create_type=False
)


paciente_alergia = Table(
    "paciente_alergia",
    Base.metadata,
    Column("id_paciente", ForeignKey("paciente.id", ondelete="CASCADE"), primary_key=True),
    Column("id_alergia", ForeignKey("alergia.id"), primary_key=True),
)


class Pessoa(Base):
    __tablename__ = "pessoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    data_nascimento: Mapped[date] = mapped_column(Date)
    is_flamengo: Mapped[bool] = mapped_column(Boolean, default=True)
    telefone: Mapped[str | None] = mapped_column(Text)

    paciente: Mapped[Paciente | None] = relationship(back_populates="pessoa")
    profissional: Mapped[Profissional | None] = relationship(back_populates="pessoa")


class Alergia(Base):
    __tablename__ = "alergia"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), unique=True)

    pacientes: Mapped[list[Paciente]] = relationship(
        secondary=paciente_alergia,
        back_populates="alergias",
    )


class Paciente(Base):
    __tablename__ = "paciente"

    id: Mapped[int] = mapped_column(ForeignKey("pessoa.id", ondelete="CASCADE"), primary_key=True)
    num_convenio: Mapped[str | None] = mapped_column(Text)
    grupo_sanguineo: Mapped[str | None] = mapped_column(grupo_sanguineo_type)

    pessoa: Mapped[Pessoa] = relationship(back_populates="paciente")
    alergias: Mapped[list[Alergia]] = relationship(
        secondary=paciente_alergia,
        back_populates="pacientes",
    )
    atendimentos: Mapped[list[Atendimento]] = relationship(back_populates="paciente")
    internacoes: Mapped[list[Internacao]] = relationship(back_populates="paciente")


class Profissional(Base):
    __tablename__ = "profissional"

    id: Mapped[int] = mapped_column(ForeignKey("pessoa.id", ondelete="CASCADE"), primary_key=True)
    crm: Mapped[str] = mapped_column(Text, unique=True)
    data_admissao: Mapped[date] = mapped_column(Date)
    especialidade: Mapped[str] = mapped_column(Text)

    pessoa: Mapped[Pessoa] = relationship(back_populates="profissional")
    atuacoes: Mapped[list[AtuacaoProfissional]] = relationship(back_populates="profissional")


class AtuacaoProfissional(Base):
    __tablename__ = "atuacao_profissional"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_profissional: Mapped[int] = mapped_column(ForeignKey("profissional.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(tipo_atuacao_type)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)

    profissional: Mapped[Profissional] = relationship(back_populates="atuacoes")
    residente: Mapped[AtuacaoResidente | None] = relationship(back_populates="atuacao")
    preceptor: Mapped[AtuacaoPreceptor | None] = relationship(back_populates="atuacao")

    __table_args__ = (
        CheckConstraint(
            "data_fim is null or data_fim >= data_inicio",
            name="atuacao_periodo_valido",
        ),
        UniqueConstraint("id", "tipo", name="atuacao_id_tipo_uq"),
        ExcludeConstraint(
            (id_profissional, "="),
            (
                func.daterange(
                    data_inicio,
                    func.coalesce(data_fim, literal_column("'infinity'::date")),
                    "[]",
                ),
                "&&",
            ),
            name="atuacao_profissional_periodo_excl",
            using="gist",
        ),
    )


class AtuacaoResidente(Base):
    __tablename__ = "atuacao_residente"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id", "tipo"],
            ["atuacao_profissional.id", "atuacao_profissional.tipo"],
            ondelete="CASCADE",
        ),
        CheckConstraint("tipo = 'residente'"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(tipo_atuacao_type, default="residente")
    ano_residencia: Mapped[str] = mapped_column(ano_residencia_type)

    atuacao: Mapped[AtuacaoProfissional] = relationship(back_populates="residente")
    atendimentos: Mapped[list[Atendimento]] = relationship(back_populates="residente")
    escalas: Mapped[list[Escala]] = relationship(back_populates="residente")


class AtuacaoPreceptor(Base):
    __tablename__ = "atuacao_preceptor"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id", "tipo"],
            ["atuacao_profissional.id", "atuacao_profissional.tipo"],
            ondelete="CASCADE",
        ),
        CheckConstraint("tipo = 'preceptor'"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(tipo_atuacao_type, default="preceptor")
    titulacao: Mapped[str] = mapped_column(Text)

    atuacao: Mapped[AtuacaoProfissional] = relationship(back_populates="preceptor")
    atendimentos: Mapped[list[Atendimento]] = relationship(back_populates="preceptor")
    escalas: Mapped[list[Escala]] = relationship(back_populates="preceptor")


class Unidade(Base):
    __tablename__ = "unidade"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[str] = mapped_column(tipo_unidade_type)
    capacidade_leitos: Mapped[int | None] = mapped_column(Integer)

    atendimentos: Mapped[list[Atendimento]] = relationship(back_populates="unidade")
    escalas: Mapped[list[Escala]] = relationship(back_populates="unidade")
    internacoes: Mapped[list[Internacao]] = relationship(back_populates="unidade")


class Atendimento(Base):
    __tablename__ = "atendimento"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime)
    duracao_minutos: Mapped[int] = mapped_column(SmallInteger)
    id_paciente: Mapped[int] = mapped_column(ForeignKey("paciente.id", ondelete="CASCADE"))
    id_atuacao_residente: Mapped[int] = mapped_column(ForeignKey("atuacao_residente.id", ondelete="CASCADE"))
    id_atuacao_preceptor: Mapped[int] = mapped_column(ForeignKey("atuacao_preceptor.id", ondelete="CASCADE"))
    id_unidade: Mapped[int] = mapped_column(ForeignKey("unidade.id", ondelete="CASCADE"))

    paciente: Mapped[Paciente] = relationship(back_populates="atendimentos")
    residente: Mapped[AtuacaoResidente] = relationship(back_populates="atendimentos")
    preceptor: Mapped[AtuacaoPreceptor] = relationship(back_populates="atendimentos")
    unidade: Mapped[Unidade] = relationship(back_populates="atendimentos")
    procedimentos: Mapped[list[ProcedimentoRealizado]] = relationship(
        back_populates="atendimento",
        cascade="all, delete-orphan",
    )


class Procedimento(Base):
    __tablename__ = "procedimento"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[int] = mapped_column(Integer, unique=True)
    nome: Mapped[str] = mapped_column(String(255))
    tempo_medio_minutos: Mapped[int] = mapped_column(Integer)
    nivel_risco: Mapped[str] = mapped_column(risco_type)
    media_tempo_procedimento: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    realizacoes: Mapped[list[ProcedimentoRealizado]] = relationship(back_populates="procedimento")


class ProcedimentoRealizado(Base):
    __tablename__ = "procedimento_realizado"

    id_atendimento: Mapped[int] = mapped_column(ForeignKey("atendimento.id"), primary_key=True)
    id_procedimento: Mapped[int] = mapped_column(ForeignKey("procedimento.id"), primary_key=True)
    quantidade: Mapped[int] = mapped_column(Integer)
    tempo_real_minutos: Mapped[int] = mapped_column(Integer)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime)
    observacao: Mapped[str | None] = mapped_column(Text)
    faturado: Mapped[bool] = mapped_column(Boolean, default=False)

    atendimento: Mapped[Atendimento] = relationship(back_populates="procedimentos")
    procedimento: Mapped[Procedimento] = relationship(back_populates="realizacoes")


class Escala(Base):
    __tablename__ = "escala"
    __table_args__ = (
        UniqueConstraint(
            "id_unidade",
            "data_plantao",
            "turno",
            "id_atuacao_residente",
            name="escala_unidade_residente_uq",
        ),
        UniqueConstraint(
            "data_plantao",
            "turno",
            "id_atuacao_residente",
            name="escala_residente_turno_uq",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_unidade: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    data_plantao: Mapped[date] = mapped_column(Date)
    turno: Mapped[str] = mapped_column(turno_type)
    id_atuacao_residente: Mapped[int] = mapped_column(ForeignKey("atuacao_residente.id"))
    id_atuacao_preceptor: Mapped[int] = mapped_column(ForeignKey("atuacao_preceptor.id"))

    unidade: Mapped[Unidade] = relationship(back_populates="escalas")
    residente: Mapped[AtuacaoResidente] = relationship(back_populates="escalas")
    preceptor: Mapped[AtuacaoPreceptor] = relationship(back_populates="escalas")


class Internacao(Base):
    __tablename__ = "internacao"
    __table_args__ = (
        CheckConstraint(
            "data_hora_saida is null or data_hora_saida >= data_hora_entrada",
            name="internacao_periodo_valido",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_paciente: Mapped[int] = mapped_column(ForeignKey("paciente.id"))
    id_unidade: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    data_hora_entrada: Mapped[datetime] = mapped_column(DateTime)
    data_hora_saida: Mapped[datetime | None] = mapped_column(DateTime)

    paciente: Mapped[Paciente] = relationship(back_populates="internacoes")
    unidade: Mapped[Unidade] = relationship(back_populates="internacoes")


class AuditoriaAtendimento(Base):
    __tablename__ = "auditoria_atendimento"

    id_auditoria: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_atendimento: Mapped[int] = mapped_column(Integer)
    operacao: Mapped[str] = mapped_column(String(6))
    usuario: Mapped[str] = mapped_column(Text)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dados_antigos: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    dados_novos: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
