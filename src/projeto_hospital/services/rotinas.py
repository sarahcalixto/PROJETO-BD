"""Contratos SQLAlchemy para as rotinas armazenadas da Etapa 2."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import SmallInteger, bindparam, cast, func, literal, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from projeto_hospital.orm import Escala
from projeto_hospital.services.dtos import (
    AtendimentoCompletoInput,
    ReajusteEscalaDTO,
    TempoEsperaUnidadeDTO,
)
from projeto_hospital.services.exceptions import RegraNegocioViolada


TURNOS_VALIDOS = frozenset({"manha", "tarde", "noite"})


def _validar_identificador(valor: object, campo: str) -> int:
    """Rejeita IDs ausentes, booleanos e valores não positivos antes do banco."""
    if (
        not isinstance(valor, int)
        or isinstance(valor, bool)
        or valor <= 0
    ):
        raise RegraNegocioViolada(f"{campo} deve ser um identificador positivo")
    return valor


def registrar_atendimento_completo(
    session: Session,
    entrada: AtendimentoCompletoInput,
) -> int:
    if not isinstance(entrada.data_hora, datetime):
        raise RegraNegocioViolada("Informe uma data e hora válidas")
    if (
        not isinstance(entrada.duracao_minutos, int)
        or isinstance(entrada.duracao_minutos, bool)
        or not 1 <= entrada.duracao_minutos <= 1440
    ):
        raise RegraNegocioViolada("A duração deve estar entre 1 e 1440 minutos")
    if not entrada.procedimentos:
        raise RegraNegocioViolada("Informe pelo menos um procedimento")

    _validar_identificador(entrada.id_paciente, "Paciente")
    _validar_identificador(entrada.id_atuacao_residente, "Atuação residente")
    _validar_identificador(entrada.id_atuacao_preceptor, "Atuação preceptora")
    _validar_identificador(entrada.id_unidade, "Unidade")

    ids = [
        _validar_identificador(item.id_procedimento, f"Procedimento {posicao}")
        for posicao, item in enumerate(entrada.procedimentos, start=1)
    ]
    if len(ids) != len(set(ids)):
        raise RegraNegocioViolada("O mesmo procedimento não pode ser repetido")

    fim_atendimento = entrada.data_hora + timedelta(
        minutes=entrada.duracao_minutos
    )
    for posicao, item in enumerate(entrada.procedimentos, start=1):
        if (
            not isinstance(item.quantidade, int)
            or isinstance(item.quantidade, bool)
            or item.quantidade <= 0
        ):
            raise RegraNegocioViolada(
                f"A quantidade do procedimento {posicao} deve ser positiva"
            )
        if (
            not isinstance(item.tempo_real_minutos, int)
            or isinstance(item.tempo_real_minutos, bool)
            or item.tempo_real_minutos <= 0
        ):
            raise RegraNegocioViolada(
                f"O tempo real do procedimento {posicao} deve ser positivo"
            )
        if not isinstance(item.data_hora_inicio, datetime):
            raise RegraNegocioViolada(
                f"Informe um início válido para o procedimento {posicao}"
            )
        if item.data_hora_inicio < entrada.data_hora:
            raise RegraNegocioViolada(
                f"O procedimento {posicao} começa antes do atendimento"
            )
        if (
            item.data_hora_inicio
            + timedelta(minutes=item.tempo_real_minutos)
            > fim_atendimento
        ):
            raise RegraNegocioViolada(
                f"O procedimento {posicao} termina depois do atendimento"
            )
        if item.faturado is not False:
            raise RegraNegocioViolada(
                f"O procedimento {posicao} deve iniciar como não faturado"
            )
        if item.observacao is not None and not isinstance(item.observacao, str):
            raise RegraNegocioViolada(
                f"A observação do procedimento {posicao} deve ser textual"
            )

    procedimentos = [
        {
            "id_procedimento": item.id_procedimento,
            "quantidade": item.quantidade,
            "tempo_real_minutos": item.tempo_real_minutos,
            "data_hora_inicio": item.data_hora_inicio.isoformat(sep=" "),
            "observacao": (
                item.observacao.strip()
                if item.observacao is not None and item.observacao.strip()
                else None
            ),
            "faturado": item.faturado,
        }
        for item in entrada.procedimentos
    ]
    parametro_json = bindparam(
        "procedimentos",
        value=procedimentos,
        type_=JSONB,
    )
    id_atendimento = session.scalar(
        select(
            func.sp_registrar_atendimento_completo(
                entrada.data_hora,
                cast(literal(entrada.duracao_minutos), SmallInteger),
                entrada.id_paciente,
                entrada.id_atuacao_residente,
                entrada.id_atuacao_preceptor,
                entrada.id_unidade,
                parametro_json,
            )
        )
    )
    if id_atendimento is None:
        raise RegraNegocioViolada("A rotina não retornou o atendimento criado")
    return int(id_atendimento)


def calcular_tempo_medio_espera(
    session: Session,
) -> list[TempoEsperaUnidadeDTO]:
    rotina = func.sp_calcular_tempo_medio_espera().table_valued(
        "id_unidade",
        "unidade",
        "tempo_medio_espera_minutos",
    )
    statement = select(
        rotina.c.id_unidade,
        rotina.c.unidade,
        rotina.c.tempo_medio_espera_minutos,
    ).order_by(rotina.c.id_unidade)
    return [
        TempoEsperaUnidadeDTO(
            int(id_unidade),
            unidade,
            Decimal(tempo) if tempo is not None else None,
        )
        for id_unidade, unidade, tempo in session.execute(statement)
    ]


def reajustar_escala(
    session: Session,
    *,
    id_atuacao_residente: int,
    data_origem: date,
    turno_origem: str,
    data_destino: date,
    turno_destino: str,
) -> ReajusteEscalaDTO:
    _validar_identificador(id_atuacao_residente, "Atuação residente")
    if not isinstance(data_origem, date) or isinstance(data_origem, datetime):
        raise RegraNegocioViolada("Informe uma data de origem válida")
    if not isinstance(data_destino, date) or isinstance(data_destino, datetime):
        raise RegraNegocioViolada("Informe uma data de destino válida")
    if turno_origem not in TURNOS_VALIDOS:
        raise RegraNegocioViolada("Informe um turno de origem válido")
    if turno_destino not in TURNOS_VALIDOS:
        raise RegraNegocioViolada("Informe um turno de destino válido")
    if data_origem == data_destino and turno_origem == turno_destino:
        raise RegraNegocioViolada("Origem e destino da escala devem ser diferentes")

    quantidade = session.scalar(
        select(
            func.sp_reajustar_escala(
                id_atuacao_residente,
                data_origem,
                cast(literal(turno_origem), Escala.turno.type),
                data_destino,
                cast(literal(turno_destino), Escala.turno.type),
            )
        )
    )
    return ReajusteEscalaDTO(
        id_atuacao_residente=id_atuacao_residente,
        data_origem=data_origem,
        turno_origem=turno_origem,
        data_destino=data_destino,
        turno_destino=turno_destino,
        quantidade_atualizada=int(quantidade or 0),
    )
