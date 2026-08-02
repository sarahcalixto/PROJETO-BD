"""Serviços usados pelas novas páginas da Etapa 2."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session, sessionmaker

from projeto_hospital.services import (
    AtendimentoCompletoInput,
    ProcedimentoCompletoInput,
    RegraNegocioViolada,
    calcular_tempo_medio_espera,
    medir_lazy_e_eager,
    registrar_atendimento_completo,
)


def _entrada(*ids: int) -> AtendimentoCompletoInput:
    procedimentos = tuple(
        ProcedimentoCompletoInput(
            id_procedimento=id_procedimento,
            quantidade=1,
            tempo_real_minutos=20,
            data_hora_inicio=datetime(2026, 8, 20, 9, 5),
        )
        for id_procedimento in ids
    )
    return AtendimentoCompletoInput(
        data_hora=datetime(2026, 8, 20, 9),
        duracao_minutos=40,
        id_paciente=1,
        id_atuacao_residente=1,
        id_atuacao_preceptor=6,
        id_unidade=1,
        procedimentos=procedimentos,
    )


def test_registrar_atendimento_completo_via_sqlalchemy(orm_session: Session) -> None:
    id_atendimento = registrar_atendimento_completo(orm_session, _entrada(1, 2))
    assert id_atendimento > 0


@pytest.mark.parametrize("ids", [(), (1, 1)])
def test_atendimento_completo_valida_itens_antes_do_banco(
    orm_session: Session,
    ids: tuple[int, ...],
) -> None:
    with pytest.raises(RegraNegocioViolada):
        registrar_atendimento_completo(orm_session, _entrada(*ids))


def test_media_espera_e_medicao_de_loading(
    orm_session: Session,
    orm_session_factory: sessionmaker[Session],
) -> None:
    medias = calcular_tempo_medio_espera(orm_session)
    assert medias
    assert all(item.tempo_medio_espera_minutos >= Decimal("0") for item in medias)

    medicao = medir_lazy_e_eager(orm_session_factory, 1)
    assert medicao.consultas_lazy == 3
    assert medicao.consultas_eager == 1
    assert medicao.atendimentos_carregados == 2
