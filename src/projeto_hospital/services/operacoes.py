"""Operações da Etapa 1 reimplementadas com a DSL do SQLAlchemy."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from projeto_hospital.orm import (
    Atendimento,
    AtuacaoPreceptor,
    AtuacaoProfissional,
    AtuacaoResidente,
    Paciente,
    Pessoa,
    ProcedimentoRealizado,
    Profissional,
    Unidade,
)
from projeto_hospital.services.dtos import (
    AtendimentoDTO,
    ConvenioPacienteDTO,
    MediaResidenteDTO,
    ProcedimentoAtendimentoDTO,
    ProcedimentoRemovidoDTO,
)
from projeto_hospital.services.exceptions import (
    EntidadeNaoEncontrada,
    RegraNegocioViolada,
)


def _atendimento_dto(atendimento: Atendimento) -> AtendimentoDTO:
    return AtendimentoDTO(
        id_atendimento=atendimento.id,
        data_hora=atendimento.data_hora,
        duracao_minutos=atendimento.duracao_minutos,
        id_paciente=atendimento.id_paciente,
        id_atuacao_residente=atendimento.id_atuacao_residente,
        id_atuacao_preceptor=atendimento.id_atuacao_preceptor,
        id_unidade=atendimento.id_unidade,
    )


def _validar_vigencia(atuacao: AtuacaoProfissional, data_hora: datetime, papel: str) -> None:
    data_referencia = data_hora.date()

    vigente = atuacao.data_inicio <= data_referencia and (
        atuacao.data_fim is None or data_referencia <= atuacao.data_fim
    )

    if not vigente:
        raise RegraNegocioViolada(f"Atuação {papel} {atuacao.id} não está vigente em {data_referencia}")


def inserir_atendimento_validado(session: Session, *, id_atendimento: int, data_hora: datetime, duracao_minutos: int, id_paciente: int, id_atuacao_residente: int, id_atuacao_preceptor: int, id_unidade: int) -> AtendimentoDTO:
    """Insere um atendimento após validar referências e vigência das atuações."""

    if duracao_minutos <= 0:
        raise RegraNegocioViolada("A duração do atendimento deve ser positiva")

    if session.get(Paciente, id_paciente) is None:
        raise EntidadeNaoEncontrada("Paciente", id_paciente)

    residente = session.get(AtuacaoResidente, id_atuacao_residente)
    if residente is None:
        raise EntidadeNaoEncontrada("Atuação residente", id_atuacao_residente)

    preceptor = session.get(AtuacaoPreceptor, id_atuacao_preceptor)
    if preceptor is None:
        raise EntidadeNaoEncontrada("Atuação preceptora", id_atuacao_preceptor)

    if session.get(Unidade, id_unidade) is None:
        raise EntidadeNaoEncontrada("Unidade", id_unidade)

    _validar_vigencia(residente.atuacao, data_hora, "residente")
    _validar_vigencia(preceptor.atuacao, data_hora, "preceptora")

    atendimento = Atendimento(
        id=id_atendimento,
        data_hora=data_hora,
        duracao_minutos=duracao_minutos,
        id_paciente=id_paciente,
        id_atuacao_residente=id_atuacao_residente,
        id_atuacao_preceptor=id_atuacao_preceptor,
        id_unidade=id_unidade,
    )

    session.add(atendimento)
    session.flush()
    return _atendimento_dto(atendimento)


def listar_atendimentos_paciente(session: Session, id_paciente: int) -> list[AtendimentoDTO]:
    """Lista cronologicamente os atendimentos de um paciente existente."""

    if session.get(Paciente, id_paciente) is None:
        raise EntidadeNaoEncontrada("Paciente", id_paciente)

    atendimentos = session.scalars(
        select(Atendimento)
        .where(Atendimento.id_paciente == id_paciente)
        .order_by(Atendimento.data_hora, Atendimento.id)
    ).all()

    return [_atendimento_dto(atendimento) for atendimento in atendimentos]


def listar_procedimentos_atendimento(session: Session, id_atendimento: int) -> list[ProcedimentoAtendimentoDTO]:
    """Lista procedimentos usando eager loading explícito dos relacionamentos."""

    atendimento = session.scalar(
        select(Atendimento)
        .where(Atendimento.id == id_atendimento)
        .options(
            selectinload(Atendimento.procedimentos).selectinload(
                ProcedimentoRealizado.procedimento
            )
        )
    )

    if atendimento is None:
        raise EntidadeNaoEncontrada("Atendimento", id_atendimento)

    realizacoes = sorted(
        atendimento.procedimentos,
        key=lambda realizacao: realizacao.id_procedimento,
    )

    return [
        ProcedimentoAtendimentoDTO(
            id_procedimento=realizacao.id_procedimento,
            nome=realizacao.procedimento.nome,
            quantidade=realizacao.quantidade,
            tempo_real_minutos=realizacao.tempo_real_minutos,
            data_hora_inicio=realizacao.data_hora_inicio,
            observacao=realizacao.observacao,
            faturado=realizacao.faturado,
        )
        for realizacao in realizacoes
    ]


def atualizar_convenio_paciente(session: Session, id_paciente: int, num_convenio: str | None) -> ConvenioPacienteDTO:
    paciente = session.get(Paciente, id_paciente)
    if paciente is None:
        raise EntidadeNaoEncontrada("Paciente", id_paciente)

    paciente.num_convenio = num_convenio
    session.flush()

    return ConvenioPacienteDTO(paciente.id, paciente.num_convenio)


def remover_procedimento_nao_faturado(session: Session, id_atendimento: int, id_procedimento: int) -> ProcedimentoRemovidoDTO:
    chave = (id_atendimento, id_procedimento)

    realizacao = session.get(ProcedimentoRealizado, chave)
    if realizacao is None:
        raise EntidadeNaoEncontrada("Procedimento realizado", chave)

    if realizacao.faturado:
        raise RegraNegocioViolada("Procedimento realizado já está faturado")

    resultado = ProcedimentoRemovidoDTO(
        id_atendimento=realizacao.id_atendimento,
        id_procedimento=realizacao.id_procedimento,
        faturado=realizacao.faturado,
    )

    session.delete(realizacao)
    session.flush()

    return resultado


def calcular_tempo_medio_por_residente(session: Session) -> list[MediaResidenteDTO]:
    media = func.avg(Atendimento.duracao_minutos)
    statement = (
        select(
            Atendimento.id_atuacao_residente,
            Pessoa.nome,
            media.label("tempo_medio_minutos"),
        )
        .join(
            AtuacaoResidente,
            AtuacaoResidente.id == Atendimento.id_atuacao_residente,
        )
        .join(
            AtuacaoProfissional,
            AtuacaoProfissional.id == AtuacaoResidente.id,
        )
        .join(
            Profissional,
            Profissional.id == AtuacaoProfissional.id_profissional,
        )
        .join(Pessoa, Pessoa.id == Profissional.id)
        .where(Atendimento.duracao_minutos > 0)
        .group_by(Atendimento.id_atuacao_residente, Pessoa.nome)
        .order_by(media.desc(), Pessoa.nome.asc())
    )

    return [
        MediaResidenteDTO(id_atuacao, nome, Decimal(valor))
        for id_atuacao, nome, valor in session.execute(statement)
    ]
