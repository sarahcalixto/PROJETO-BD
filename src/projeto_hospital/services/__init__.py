"""API pública das operações e consultas ORM da aplicação."""

from projeto_hospital.services.consultas import (
    pacientes_sem_procedimento_alto_risco,
    plantoes_por_unidade_e_residente,
    preceptores_com_mais_de_cinco_atendimentos,
    ranking_residentes_por_atendimentos,
)
from projeto_hospital.services.dtos import (
    AtendimentoDTO,
    ConvenioPacienteDTO,
    MediaResidenteDTO,
    PacienteSemAltoRiscoDTO,
    PlantoesUnidadeDTO,
    ProcedimentoAtendimentoDTO,
    ProcedimentoRemovidoDTO,
    RankingResidenteDTO,
    SupervisaoPreceptorDTO,
)
from projeto_hospital.services.exceptions import (
    EntidadeNaoEncontrada,
    RegraNegocioViolada,
    ServicoORMError,
)
from projeto_hospital.services.operacoes import (
    atualizar_convenio_paciente,
    calcular_tempo_medio_por_residente,
    inserir_atendimento_validado,
    listar_atendimentos_paciente,
    listar_procedimentos_atendimento,
    remover_procedimento_nao_faturado,
)

__all__ = [
    "AtendimentoDTO",
    "ConvenioPacienteDTO",
    "EntidadeNaoEncontrada",
    "MediaResidenteDTO",
    "PacienteSemAltoRiscoDTO",
    "PlantoesUnidadeDTO",
    "ProcedimentoAtendimentoDTO",
    "ProcedimentoRemovidoDTO",
    "RankingResidenteDTO",
    "RegraNegocioViolada",
    "ServicoORMError",
    "SupervisaoPreceptorDTO",
    "atualizar_convenio_paciente",
    "calcular_tempo_medio_por_residente",
    "inserir_atendimento_validado",
    "listar_atendimentos_paciente",
    "listar_procedimentos_atendimento",
    "pacientes_sem_procedimento_alto_risco",
    "plantoes_por_unidade_e_residente",
    "preceptores_com_mais_de_cinco_atendimentos",
    "ranking_residentes_por_atendimentos",
    "remover_procedimento_nao_faturado",
]
