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
from projeto_hospital.services.carregamento import medir_lazy_e_eager
from projeto_hospital.services.dtos import (
    AtendimentoDTO,
    AtendimentoHistoricoDTO,
    AtendimentoCompletoInput,
    ConvenioPacienteDTO,
    MediaResidenteDTO,
    MedicaoCarregamentoDTO,
    PacienteSemAltoRiscoDTO,
    PercentualAltoRiscoResidenteDTO,
    PlantoesUnidadeDTO,
    PreceptorFlamenguistaDTO,
    ProcedimentoAtendimentoDTO,
    ProcedimentoCompletoInput,
    ProcedimentoRemovidoDTO,
    ProcedimentoResumoDTO,
    RankingResidenteDTO,
    ReajusteEscalaDTO,
    SupervisaoPreceptorDTO,
    TempoEsperaUnidadeDTO,
    UltimoAtendimentoPacienteDTO,
)
from projeto_hospital.services.rotinas import (
    calcular_tempo_medio_espera,
    reajustar_escala,
    registrar_atendimento_completo,
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
    "AtendimentoHistoricoDTO",
    "AtendimentoCompletoInput",
    "ConvenioPacienteDTO",
    "EntidadeNaoEncontrada",
    "MediaResidenteDTO",
    "MedicaoCarregamentoDTO",
    "PacienteSemAltoRiscoDTO",
    "PercentualAltoRiscoResidenteDTO",
    "PlantoesUnidadeDTO",
    "ProcedimentoAtendimentoDTO",
    "ProcedimentoCompletoInput",
    "ProcedimentoRemovidoDTO",
    "ProcedimentoResumoDTO",
    "PreceptorFlamenguistaDTO",
    "RankingResidenteDTO",
    "ReajusteEscalaDTO",
    "ResultadoConcorrencia",
    "RegraNegocioViolada",
    "ServicoORMError",
    "SupervisaoPreceptorDTO",
    "TempoEsperaUnidadeDTO",
    "UltimoAtendimentoPacienteDTO",
    "atualizar_convenio_paciente",
    "calcular_tempo_medio_por_residente",
    "calcular_tempo_medio_espera",
    "demonstrar_concorrencia_escala",
    "inserir_atendimento_validado",
    "listar_atendimentos_paciente",
    "listar_procedimentos_atendimento",
    "medir_lazy_e_eager",
    "pacientes_sem_procedimento_alto_risco",
    "percentual_alto_risco_por_residente",
    "plantoes_por_unidade_e_residente",
    "preceptores_com_mais_de_cinco_atendimentos",
    "preceptores_de_pacientes_flamenguistas",
    "ranking_residentes_por_atendimentos",
    "reajustar_escala",
    "registrar_atendimento_completo",
    "remover_procedimento_nao_faturado",
    "ultimos_atendimentos_por_paciente",
]
