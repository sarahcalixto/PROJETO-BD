"""Consultas avançadas da Etapa 2, sem SQL textual."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, aliased, joinedload, selectinload

from projeto_hospital.orm import (
    Atendimento,
    AtuacaoPreceptor,
    AtuacaoProfissional,
    AtuacaoResidente,
    Paciente,
    Pessoa,
    Procedimento,
    ProcedimentoRealizado,
    Profissional,
)
from projeto_hospital.services.dtos import (
    PercentualAltoRiscoResidenteDTO,
    PreceptorFlamenguistaDTO,
    ProcedimentoResumoDTO,
    UltimoAtendimentoPacienteDTO,
)


def preceptores_de_pacientes_flamenguistas(
    session: Session,
) -> list[PreceptorFlamenguistaDTO]:
    """Lista preceptores que supervisionaram atendimento de flamenguistas."""

    pessoa_paciente = aliased(Pessoa)
    pessoa_preceptor = aliased(Pessoa)
    statement = (
        select(AtuacaoPreceptor.id, pessoa_preceptor.nome)
        .join(Atendimento, Atendimento.id_atuacao_preceptor == AtuacaoPreceptor.id)
        .join(Paciente, Paciente.id == Atendimento.id_paciente)
        .join(pessoa_paciente, pessoa_paciente.id == Paciente.id)
        .join(
            AtuacaoProfissional,
            AtuacaoProfissional.id == AtuacaoPreceptor.id,
        )
        .join(Profissional, Profissional.id == AtuacaoProfissional.id_profissional)
        .join(pessoa_preceptor, pessoa_preceptor.id == Profissional.id)
        .where(pessoa_paciente.is_flamengo.is_(True))
        .distinct()
        .order_by(pessoa_preceptor.nome, AtuacaoPreceptor.id)
    )
    return [PreceptorFlamenguistaDTO(*row) for row in session.execute(statement)]


def ultimos_atendimentos_por_paciente(
    session: Session,
) -> list[UltimoAtendimentoPacienteDTO]:
    """Retorna todos os pacientes e, quando existir, seu último atendimento."""

    pacientes = session.scalars(
        select(Paciente)
        .options(joinedload(Paciente.pessoa))
        .order_by(Paciente.id)
    ).all()

    ranking = (
        select(
            Atendimento.id.label("id_atendimento"),
            func.row_number()
            .over(
                partition_by=Atendimento.id_paciente,
                order_by=(Atendimento.data_hora.desc(), Atendimento.id.desc()),
            )
            .label("ordem"),
        )
        .subquery()
    )
    atendimentos = session.scalars(
        select(Atendimento)
        .join(ranking, ranking.c.id_atendimento == Atendimento.id)
        .where(ranking.c.ordem == 1)
        .options(
            joinedload(Atendimento.residente)
            .joinedload(AtuacaoResidente.atuacao)
            .joinedload(AtuacaoProfissional.profissional)
            .joinedload(Profissional.pessoa),
            joinedload(Atendimento.preceptor)
            .joinedload(AtuacaoPreceptor.atuacao)
            .joinedload(AtuacaoProfissional.profissional)
            .joinedload(Profissional.pessoa),
            selectinload(Atendimento.procedimentos).joinedload(
                ProcedimentoRealizado.procedimento
            ),
        )
    ).unique().all()
    por_paciente = {item.id_paciente: item for item in atendimentos}

    resultado: list[UltimoAtendimentoPacienteDTO] = []
    for paciente in pacientes:
        atendimento = por_paciente.get(paciente.id)
        if atendimento is None:
            resultado.append(
                UltimoAtendimentoPacienteDTO(
                    paciente.id,
                    paciente.pessoa.nome,
                    None,
                    None,
                    None,
                    None,
                    (),
                )
            )
            continue

        procedimentos = tuple(
            ProcedimentoResumoDTO(
                realizado.id_procedimento,
                realizado.procedimento.nome,
                realizado.quantidade,
            )
            for realizado in sorted(
                atendimento.procedimentos,
                key=lambda item: (item.procedimento.nome, item.id_procedimento),
            )
        )
        resultado.append(
            UltimoAtendimentoPacienteDTO(
                paciente.id,
                paciente.pessoa.nome,
                atendimento.id,
                atendimento.data_hora,
                atendimento.residente.atuacao.profissional.pessoa.nome,
                atendimento.preceptor.atuacao.profissional.pessoa.nome,
                procedimentos,
            )
        )

    return resultado


def percentual_alto_risco_por_residente(
    session: Session,
) -> list[PercentualAltoRiscoResidenteDTO]:
    """Calcula percentual por ocorrência e mantém residentes sem procedimentos."""

    total = func.count(ProcedimentoRealizado.id_procedimento)
    alto_risco = func.count(
        case((Procedimento.nivel_risco == "alto", ProcedimentoRealizado.id_procedimento))
    )
    statement = (
        select(AtuacaoResidente.id, Pessoa.nome, total, alto_risco)
        .join(AtuacaoProfissional, AtuacaoProfissional.id == AtuacaoResidente.id)
        .join(Pessoa, Pessoa.id == AtuacaoProfissional.id_profissional)
        .outerjoin(Atendimento, Atendimento.id_atuacao_residente == AtuacaoResidente.id)
        .outerjoin(
            ProcedimentoRealizado,
            ProcedimentoRealizado.id_atendimento == Atendimento.id,
        )
        .outerjoin(Procedimento, Procedimento.id == ProcedimentoRealizado.id_procedimento)
        .group_by(AtuacaoResidente.id, Pessoa.id, Pessoa.nome)
        .order_by(Pessoa.nome, AtuacaoResidente.id)
    )

    resultado = []
    for id_residente, nome, quantidade, quantidade_alto in session.execute(statement):
        percentual = (
            Decimal(quantidade_alto * 100) / Decimal(quantidade)
            if quantidade
            else Decimal("0")
        ).quantize(Decimal("0.01"))
        resultado.append(
            PercentualAltoRiscoResidenteDTO(
                id_residente,
                nome,
                quantidade,
                quantidade_alto,
                percentual,
            )
        )
    return resultado
