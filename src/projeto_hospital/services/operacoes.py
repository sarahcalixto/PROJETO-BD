"""Operações da Etapa 1 reimplementadas com a DSL do SQLAlchemy."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload

from projeto_hospital.orm import (
    Atendimento,
    AtuacaoPreceptor,
    AtuacaoProfissional,
    AtuacaoResidente,
    Escala,
    Paciente,
    Pessoa,
    ProcedimentoRealizado,
    Profissional,
    Unidade,
)
from projeto_hospital.services.dtos import (
    AtendimentoDTO,
    AtendimentoHistoricoDTO,
    ConvenioPacienteDTO,
    EscalaDTO,
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


def _validar_vigencia(
    atuacao: AtuacaoProfissional,
    referencia: date | datetime,
    papel: str,
) -> None:
    data_referencia = (
        referencia.date() if isinstance(referencia, datetime) else referencia
    )

    vigente = atuacao.data_inicio <= data_referencia and (
        atuacao.data_fim is None or data_referencia <= atuacao.data_fim
    )

    if not vigente:
        raise RegraNegocioViolada(f"Atuação {papel} {atuacao.id} não está vigente em {data_referencia}")


def criar_escala(
    session: Session,
    *,
    id_unidade: int,
    data_plantao: date,
    turno: str,
    id_atuacao_residente: int,
    id_atuacao_preceptor: int,
) -> EscalaDTO:
    """Cria uma escala e deixa conflitos concorrentes para o PostgreSQL."""

    identificadores = (
        (id_unidade, "Unidade"),
        (id_atuacao_residente, "Atuação residente"),
        (id_atuacao_preceptor, "Atuação preceptora"),
    )
    for identificador, campo in identificadores:
        if (
            not isinstance(identificador, int)
            or isinstance(identificador, bool)
            or identificador <= 0
        ):
            raise RegraNegocioViolada(f"{campo} deve ser um identificador positivo")
    if not isinstance(data_plantao, date) or isinstance(data_plantao, datetime):
        raise RegraNegocioViolada("Informe uma data de plantão válida")
    if turno not in {"manha", "tarde", "noite"}:
        raise RegraNegocioViolada("Informe um turno válido")

    if session.get(Unidade, id_unidade) is None:
        raise EntidadeNaoEncontrada("Unidade", id_unidade)
    residente = session.get(AtuacaoResidente, id_atuacao_residente)
    if residente is None:
        raise EntidadeNaoEncontrada("Atuação residente", id_atuacao_residente)
    preceptor = session.get(AtuacaoPreceptor, id_atuacao_preceptor)
    if preceptor is None:
        raise EntidadeNaoEncontrada("Atuação preceptora", id_atuacao_preceptor)

    _validar_vigencia(residente.atuacao, data_plantao, "residente")
    _validar_vigencia(preceptor.atuacao, data_plantao, "preceptora")

    escala = Escala(
        id_unidade=id_unidade,
        data_plantao=data_plantao,
        turno=turno,
        id_atuacao_residente=id_atuacao_residente,
        id_atuacao_preceptor=id_atuacao_preceptor,
    )
    session.add(escala)
    try:
        session.flush()
    except IntegrityError as error:
        origem = error.orig
        diagnostico = getattr(origem, "diag", None)
        sqlstate = getattr(origem, "sqlstate", None)
        constraint = getattr(diagnostico, "constraint_name", None)
        mensagem = getattr(diagnostico, "message_primary", "")
        conflito_de_escala = constraint in {
            "escala_unidade_residente_uq",
            "escala_residente_turno_uq",
        } or (sqlstate == "23514" and mensagem.startswith("Conflito de escala"))
        if conflito_de_escala:
            raise RegraNegocioViolada(
                "Este residente já está escalado nesta data e turno."
            ) from error
        raise

    return EscalaDTO(
        id_escala=escala.id,
        id_unidade=escala.id_unidade,
        data_plantao=escala.data_plantao,
        turno=escala.turno,
        id_atuacao_residente=escala.id_atuacao_residente,
        id_atuacao_preceptor=escala.id_atuacao_preceptor,
    )


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


def listar_atendimentos_paciente(
    session: Session,
    id_paciente: int,
) -> list[AtendimentoHistoricoDTO]:
    """Lista cronologicamente os atendimentos de um paciente existente."""

    if session.get(Paciente, id_paciente) is None:
        raise EntidadeNaoEncontrada("Paciente", id_paciente)

    pessoa_residente = aliased(Pessoa)
    pessoa_preceptor = aliased(Pessoa)
    atuacao_residente = aliased(AtuacaoProfissional)
    atuacao_preceptor = aliased(AtuacaoProfissional)
    rows = session.execute(
        select(
            Atendimento.id,
            Atendimento.data_hora,
            Atendimento.duracao_minutos,
            pessoa_residente.nome,
            pessoa_preceptor.nome,
            Unidade.nome,
        )
        .join(AtuacaoResidente, AtuacaoResidente.id == Atendimento.id_atuacao_residente)
        .join(atuacao_residente, atuacao_residente.id == AtuacaoResidente.id)
        .join(
            pessoa_residente,
            pessoa_residente.id == atuacao_residente.id_profissional,
        )
        .join(AtuacaoPreceptor, AtuacaoPreceptor.id == Atendimento.id_atuacao_preceptor)
        .join(atuacao_preceptor, atuacao_preceptor.id == AtuacaoPreceptor.id)
        .join(
            pessoa_preceptor,
            pessoa_preceptor.id == atuacao_preceptor.id_profissional,
        )
        .join(Unidade, Unidade.id == Atendimento.id_unidade)
        .where(Atendimento.id_paciente == id_paciente)
        .order_by(Atendimento.data_hora, Atendimento.id)
    ).all()

    return [AtendimentoHistoricoDTO(*row) for row in rows]


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
            codigo=realizacao.procedimento.codigo,
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
    if num_convenio is not None and not isinstance(num_convenio, str):
        raise RegraNegocioViolada("O número de convênio deve ser textual")

    convenio_normalizado = (
        num_convenio.strip()
        if isinstance(num_convenio, str) and num_convenio.strip()
        else None
    )
    paciente.num_convenio = convenio_normalizado
    session.flush()

    return ConvenioPacienteDTO(paciente.id, paciente.num_convenio)


def remover_procedimento_nao_faturado(session: Session, id_atendimento: int, id_procedimento: int) -> ProcedimentoRemovidoDTO:
    chave = (id_atendimento, id_procedimento)

    realizacao = session.scalar(
        select(ProcedimentoRealizado)
        .where(
            ProcedimentoRealizado.id_atendimento == id_atendimento,
            ProcedimentoRealizado.id_procedimento == id_procedimento,
        )
        .with_for_update()
    )
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
