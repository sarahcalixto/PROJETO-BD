"""Contratos SQLAlchemy para as rotinas armazenadas da Etapa 2."""

from __future__ import annotations

from datetime import date
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


def registrar_atendimento_completo(
    session: Session,
    entrada: AtendimentoCompletoInput,
) -> int:
    if not entrada.procedimentos:
        raise RegraNegocioViolada("Informe pelo menos um procedimento")

    ids = [item.id_procedimento for item in entrada.procedimentos]
    if len(ids) != len(set(ids)):
        raise RegraNegocioViolada("O mesmo procedimento não pode ser repetido")

    procedimentos = [
        {
            "id_procedimento": item.id_procedimento,
            "quantidade": item.quantidade,
            "tempo_real_minutos": item.tempo_real_minutos,
            "data_hora_inicio": item.data_hora_inicio.isoformat(sep=" "),
            "observacao": item.observacao,
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
        TempoEsperaUnidadeDTO(int(id_unidade), unidade, Decimal(tempo))
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
