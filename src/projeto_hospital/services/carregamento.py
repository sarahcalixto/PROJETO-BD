"""Medição executável de relacionamentos lazy e eager."""

from __future__ import annotations

from sqlalchemy import event, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from projeto_hospital.orm import Paciente
from projeto_hospital.services.dtos import MedicaoCarregamentoDTO
from projeto_hospital.services.exceptions import EntidadeNaoEncontrada


def medir_lazy_e_eager(
    factory: sessionmaker[Session],
    id_paciente: int,
) -> MedicaoCarregamentoDTO:
    engine = factory.kw["bind"]

    def executar(eager: bool) -> tuple[int, int]:
        comandos: list[str] = []

        def contar(*args: object) -> None:
            comandos.append(str(args[2]))

        event.listen(engine, "before_cursor_execute", contar)
        try:
            with factory() as session:
                if eager:
                    paciente = session.execute(
                        select(Paciente)
                        .where(Paciente.id == id_paciente)
                        .options(
                            joinedload(Paciente.pessoa),
                            joinedload(Paciente.atendimentos),
                        )
                    ).unique().scalar_one_or_none()
                else:
                    paciente = session.get(Paciente, id_paciente)
                if paciente is None:
                    raise EntidadeNaoEncontrada("Paciente", id_paciente)
                paciente.pessoa.nome
                quantidade = len(paciente.atendimentos)
        finally:
            event.remove(engine, "before_cursor_execute", contar)
        return len(comandos), quantidade

    consultas_lazy, quantidade = executar(False)
    consultas_eager, _ = executar(True)
    return MedicaoCarregamentoDTO(
        id_paciente=id_paciente,
        consultas_lazy=consultas_lazy,
        consultas_eager=consultas_eager,
        atendimentos_carregados=quantidade,
    )
