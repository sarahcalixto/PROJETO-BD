"""API pública das operações e consultas ORM da aplicação."""

from projeto_hospital.services.consultas import (
    pacientes_sem_procedimento_alto_risco,
    plantoes_por_unidade_e_residente,
    preceptores_com_mais_de_cinco_atendimentos,
    ranking_residentes_por_atendimentos,
)
from projeto_hospital.services.consultas_avancadas import (
    percentual_alto_risco_por_residente,
    preceptores_de_pacientes_flamenguistas,
    ultimos_atendimentos_por_paciente,
)
from projeto_hospital.services.concorrencia import (
    ResultadoConcorrencia,
    demonstrar_concorrencia_escala,
)
from projeto_hospital.services.dtos import (
    AtendimentoDTO,
    ConvenioPacienteDTO,
    MediaResidenteDTO,
    PacienteSemAltoRiscoDTO,
    PercentualAltoRiscoResidenteDTO,
    PlantoesUnidadeDTO,
    PreceptorFlamenguistaDTO,
    ProcedimentoAtendimentoDTO,
    ProcedimentoRemovidoDTO,
    ProcedimentoResumoDTO,
    RankingResidenteDTO,
    SupervisaoPreceptorDTO,
    UltimoAtendimentoPacienteDTO,
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
    "PercentualAltoRiscoResidenteDTO",
    "PlantoesUnidadeDTO",
    "ProcedimentoAtendimentoDTO",
    "ProcedimentoRemovidoDTO",
    "ProcedimentoResumoDTO",
    "PreceptorFlamenguistaDTO",
    "RankingResidenteDTO",
    "ResultadoConcorrencia",
    "RegraNegocioViolada",
    "ServicoORMError",
    "SupervisaoPreceptorDTO",
    "UltimoAtendimentoPacienteDTO",
    "atualizar_convenio_paciente",
    "calcular_tempo_medio_por_residente",
    "demonstrar_concorrencia_escala",
    "inserir_atendimento_validado",
    "listar_atendimentos_paciente",
    "listar_procedimentos_atendimento",
    "pacientes_sem_procedimento_alto_risco",
    "percentual_alto_risco_por_residente",
    "plantoes_por_unidade_e_residente",
    "preceptores_com_mais_de_cinco_atendimentos",
    "preceptores_de_pacientes_flamenguistas",
    "ranking_residentes_por_atendimentos",
    "remover_procedimento_nao_faturado",
    "ultimos_atendimentos_por_paciente",
]
