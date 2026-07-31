"""Infraestrutura pública de persistência SQLAlchemy."""

from projeto_hospital.orm.base import Base
from projeto_hospital.orm.models import (
    Alergia,
    Atendimento,
    AtuacaoPreceptor,
    AtuacaoProfissional,
    AtuacaoResidente,
    AuditoriaAtendimento,
    Escala,
    Internacao,
    Paciente,
    Pessoa,
    Procedimento,
    ProcedimentoRealizado,
    Profissional,
    Unidade,
)
from projeto_hospital.orm.session import (
    create_database_engine,
    create_session_factory,
    session_scope,
)

__all__ = [
    "Alergia",
    "Atendimento",
    "AtuacaoPreceptor",
    "AtuacaoProfissional",
    "AtuacaoResidente",
    "AuditoriaAtendimento",
    "Base",
    "Escala",
    "Internacao",
    "Paciente",
    "Pessoa",
    "Procedimento",
    "ProcedimentoRealizado",
    "Profissional",
    "Unidade",
    "create_database_engine",
    "create_session_factory",
    "session_scope",
]
