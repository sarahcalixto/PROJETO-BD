"""Contratos de entrada e saída da camada de serviços ORM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class AtendimentoDTO:
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    id_paciente: int
    id_atuacao_residente: int
    id_atuacao_preceptor: int
    id_unidade: int


@dataclass(frozen=True, slots=True)
class ProcedimentoAtendimentoDTO:
    id_procedimento: int
    nome: str
    quantidade: int
    tempo_real_minutos: int
    data_hora_inicio: datetime
    observacao: str | None
    faturado: bool


@dataclass(frozen=True, slots=True)
class ConvenioPacienteDTO:
    id_paciente: int
    num_convenio: str | None


@dataclass(frozen=True, slots=True)
class ProcedimentoRemovidoDTO:
    id_atendimento: int
    id_procedimento: int
    faturado: bool


@dataclass(frozen=True, slots=True)
class MediaResidenteDTO:
    id_atuacao_residente: int
    nome_profissional: str
    tempo_medio_minutos: Decimal


@dataclass(frozen=True, slots=True)
class RankingResidenteDTO:
    nome: str
    total_atendimentos: int


@dataclass(frozen=True, slots=True)
class SupervisaoPreceptorDTO:
    nome: str
    total_supervisionado: int


@dataclass(frozen=True, slots=True)
class PlantoesUnidadeDTO:
    unidade: str
    residente: str | None
    quantidade_plantoes: int


@dataclass(frozen=True, slots=True)
class PacienteSemAltoRiscoDTO:
    nome: str
    num_convenio: str | None
