"""Contratos de entrada e saída da camada de serviços ORM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
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
class AtendimentoHistoricoDTO:
    id_atendimento: int
    data_hora: datetime
    duracao_minutos: int
    residente: str
    preceptor: str
    unidade: str


@dataclass(frozen=True, slots=True)
class ProcedimentoAtendimentoDTO:
    id_procedimento: int
    codigo: int
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


@dataclass(frozen=True, slots=True)
class PreceptorFlamenguistaDTO:
    id_atuacao_preceptor: int
    nome: str


@dataclass(frozen=True, slots=True)
class ProcedimentoResumoDTO:
    id_procedimento: int
    nome: str
    quantidade: int


@dataclass(frozen=True, slots=True)
class UltimoAtendimentoPacienteDTO:
    id_paciente: int
    paciente: str
    id_atendimento: int | None
    data_hora: datetime | None
    residente: str | None
    preceptor: str | None
    procedimentos: tuple[ProcedimentoResumoDTO, ...]


@dataclass(frozen=True, slots=True)
class PercentualAltoRiscoResidenteDTO:
    id_atuacao_residente: int
    residente: str
    total_procedimentos: int
    procedimentos_alto_risco: int
    percentual_alto_risco: Decimal


@dataclass(frozen=True, slots=True)
class ProcedimentoCompletoInput:
    id_procedimento: int
    quantidade: int
    tempo_real_minutos: int
    data_hora_inicio: datetime
    observacao: str | None = None
    faturado: bool = False


@dataclass(frozen=True, slots=True)
class AtendimentoCompletoInput:
    data_hora: datetime
    duracao_minutos: int
    id_paciente: int
    id_atuacao_residente: int
    id_atuacao_preceptor: int
    id_unidade: int
    procedimentos: tuple[ProcedimentoCompletoInput, ...]


@dataclass(frozen=True, slots=True)
class TempoEsperaUnidadeDTO:
    id_unidade: int
    unidade: str
    tempo_medio_espera_minutos: Decimal | None


@dataclass(frozen=True, slots=True)
class ReajusteEscalaDTO:
    id_atuacao_residente: int
    data_origem: date
    turno_origem: str
    data_destino: date
    turno_destino: str
    quantidade_atualizada: int


@dataclass(frozen=True, slots=True)
class EscalaDTO:
    id_escala: int
    id_unidade: int
    data_plantao: date
    turno: str
    id_atuacao_residente: int
    id_atuacao_preceptor: int


@dataclass(frozen=True, slots=True)
class MedicaoCarregamentoDTO:
    id_paciente: int
    consultas_lazy: int
    consultas_eager: int
    atendimentos_carregados: int
