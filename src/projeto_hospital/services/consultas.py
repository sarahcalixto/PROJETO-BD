"""Consultas analíticas implementadas com expressões SQLAlchemy."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from projeto_hospital.orm import (
    Atendimento,
    AtuacaoPreceptor,
    AtuacaoProfissional,
    AtuacaoResidente,
    Escala,
    Paciente,
    Pessoa,
    Procedimento,
    ProcedimentoRealizado,
    Unidade,
)
from projeto_hospital.services.dtos import (
    PacienteSemAltoRiscoDTO,
    PlantoesUnidadeDTO,
    RankingResidenteDTO,
    SupervisaoPreceptorDTO,
)


def _limites_mes(referencia: date) -> tuple[date, date]:
    inicio = referencia.replace(day=1)
    if inicio.month == 12:
        fim = date(inicio.year + 1, 1, 1)
    else:
        fim = date(inicio.year, inicio.month + 1, 1)

    return inicio, fim


def ranking_residentes_por_atendimentos(session: Session) -> list[RankingResidenteDTO]:
    total = func.count(Atendimento.id)

    statement = (
        select(Pessoa.nome, total.label("total_atendimentos"))
        .join(
            AtuacaoProfissional,
            Pessoa.id == AtuacaoProfissional.id_profissional,
        )
        .join(AtuacaoResidente, AtuacaoProfissional.id == AtuacaoResidente.id)
        .outerjoin(
            Atendimento,
            AtuacaoResidente.id == Atendimento.id_atuacao_residente,
        )
        .group_by(Pessoa.id, Pessoa.nome)
        .order_by(total.desc(), Pessoa.nome.asc())
    )

    return [
        RankingResidenteDTO(nome, total_atendimentos)
        for nome, total_atendimentos in session.execute(statement)
    ]


def preceptores_com_mais_de_cinco_atendimentos(session: Session, mes_referencia: date) -> list[SupervisaoPreceptorDTO]:
    inicio, fim = _limites_mes(mes_referencia)
    total = func.count(Atendimento.id)

    statement = (
        select(Pessoa.nome, total.label("total_supervisionado"))
        .join(
            AtuacaoProfissional,
            Pessoa.id == AtuacaoProfissional.id_profissional,
        )
        .join(AtuacaoPreceptor, AtuacaoProfissional.id == AtuacaoPreceptor.id)
        .join(
            Atendimento,
            AtuacaoPreceptor.id == Atendimento.id_atuacao_preceptor,
        )
        .where(Atendimento.data_hora >= inicio, Atendimento.data_hora < fim)
        .group_by(Pessoa.id, Pessoa.nome)
        .having(total > 5)
        .order_by(total.desc(), Pessoa.nome.asc())
    )

    return [
        SupervisaoPreceptorDTO(nome, total_supervisionado)
        for nome, total_supervisionado in session.execute(statement)
    ]


def plantoes_por_unidade_e_residente(session: Session, mes_referencia: date) -> list[PlantoesUnidadeDTO]:
    inicio, fim = _limites_mes(mes_referencia)
    quantidade = func.count(Escala.id)

    statement = (
        select(
            Unidade.nome,
            Pessoa.nome,
            quantidade.label("quantidade_plantoes"),
        )
        .outerjoin(
            Escala,
            and_(
                Unidade.id == Escala.id_unidade,
                Escala.data_plantao >= inicio,
                Escala.data_plantao < fim,
            ),
        )
        .outerjoin(
            AtuacaoResidente,
            Escala.id_atuacao_residente == AtuacaoResidente.id,
        )
        .outerjoin(
            AtuacaoProfissional,
            AtuacaoResidente.id == AtuacaoProfissional.id,
        )
        .outerjoin(Pessoa, AtuacaoProfissional.id_profissional == Pessoa.id)
        .group_by(Unidade.id, Unidade.nome, Pessoa.id, Pessoa.nome)
        .order_by(
            Unidade.nome.asc(),
            quantidade.desc(),
            Pessoa.nome.asc().nulls_last(),
        )
    )

    return [
        PlantoesUnidadeDTO(unidade, residente, quantidade_plantoes)
        for unidade, residente, quantidade_plantoes in session.execute(statement)
    ]


def pacientes_sem_procedimento_alto_risco(session: Session) -> list[PacienteSemAltoRiscoDTO]:
    realizou_alto_risco = (
        select(1)
        .select_from(Atendimento)
        .join(
            ProcedimentoRealizado,
            Atendimento.id == ProcedimentoRealizado.id_atendimento,
        )
        .join(
            Procedimento,
            ProcedimentoRealizado.id_procedimento == Procedimento.id,
        )
        .where(
            Atendimento.id_paciente == Paciente.id,
            Procedimento.nivel_risco == "alto",
        )
        .exists()
    )

    statement = (
        select(Pessoa.nome, Paciente.num_convenio)
        .join(Paciente, Pessoa.id == Paciente.id)
        .where(~realizou_alto_risco)
        .order_by(Pessoa.nome.asc())
    )

    return [
        PacienteSemAltoRiscoDTO(nome, num_convenio)
        for nome, num_convenio in session.execute(statement)
    ]
