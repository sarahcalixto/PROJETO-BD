"""Testes de integração dos três triggers da Etapa 2."""

from datetime import date, datetime
from decimal import Decimal

import psycopg
import pytest


def _ids(conn: psycopg.Connection) -> tuple[int, int, int, int, int]:
    residente = conn.execute("SELECT id FROM atuacao_residente ORDER BY id LIMIT 1").fetchone()[0]
    preceptor = conn.execute("SELECT id FROM atuacao_preceptor ORDER BY id LIMIT 1").fetchone()[0]
    unidades = conn.execute("SELECT id FROM unidade ORDER BY id LIMIT 2").fetchall()
    paciente = conn.execute("SELECT id FROM paciente ORDER BY id LIMIT 1").fetchone()[0]
    return residente, preceptor, unidades[0][0], unidades[1][0], paciente


@pytest.mark.parametrize("operacao", ["INSERT", "UPDATE"])
def test_sobreposicao_bloqueia_insert_e_update(
    conn: psycopg.Connection,
    operacao: str,
) -> None:
    residente, preceptor, unidade_1, unidade_2, _ = _ids(conn)
    data_plantao = date(2029, 10, 10)
    conn.execute(
        """
        INSERT INTO escala (
            id_unidade, data_plantao, turno,
            id_atuacao_residente, id_atuacao_preceptor
        ) VALUES (%s, %s, 'manha', %s, %s)
        """,
        (unidade_1, data_plantao, residente, preceptor),
    )

    with pytest.raises(psycopg.errors.CheckViolation):
        if operacao == "INSERT":
            conn.execute(
                """
                INSERT INTO escala (
                    id_unidade, data_plantao, turno,
                    id_atuacao_residente, id_atuacao_preceptor
                ) VALUES (%s, %s, 'manha', %s, %s)
                """,
                (unidade_2, data_plantao, residente, preceptor),
            )
        else:
            id_escala = conn.execute(
                """
                INSERT INTO escala (
                    id_unidade, data_plantao, turno,
                    id_atuacao_residente, id_atuacao_preceptor
                ) VALUES (%s, %s, 'tarde', %s, %s)
                RETURNING id
                """,
                (unidade_2, data_plantao, residente, preceptor),
            ).fetchone()[0]
            conn.execute(
                "UPDATE escala SET turno = 'manha' WHERE id = %s",
                (id_escala,),
            )


def test_auditoria_registra_json_exato_das_tres_operacoes(
    conn: psycopg.Connection,
) -> None:
    residente, preceptor, unidade, _, paciente = _ids(conn)
    id_atendimento = 9999
    conn.execute(
        """
        INSERT INTO atendimento (
            id, data_hora, duracao_minutos, id_paciente,
            id_atuacao_residente, id_atuacao_preceptor, id_unidade
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            id_atendimento,
            datetime(2029, 10, 10, 10),
            30,
            paciente,
            residente,
            preceptor,
            unidade,
        ),
    )
    conn.execute(
        "UPDATE atendimento SET duracao_minutos = %s WHERE id = %s",
        (45, id_atendimento),
    )
    conn.execute("DELETE FROM atendimento WHERE id = %s", (id_atendimento,))

    logs = conn.execute(
        """
        SELECT operacao, dados_antigos, dados_novos
        FROM auditoria_atendimento
        WHERE id_atendimento = %s
        ORDER BY id_auditoria
        """,
        (id_atendimento,),
    ).fetchall()

    assert [log[0] for log in logs] == ["INSERT", "UPDATE", "DELETE"]
    assert logs[0][1] is None
    assert logs[0][2]["duracao_minutos"] == 30
    assert logs[1][1]["duracao_minutos"] == 30
    assert logs[1][2]["duracao_minutos"] == 45
    assert logs[2][1]["duracao_minutos"] == 45
    assert logs[2][2] is None


def test_media_do_procedimento_e_calculada_exatamente(
    conn: psycopg.Connection,
) -> None:
    residente, preceptor, unidade, _, paciente = _ids(conn)
    procedimento = conn.execute(
        "SELECT id FROM procedimento ORDER BY id LIMIT 1"
    ).fetchone()[0]
    id_atendimento = conn.execute(
        """
        INSERT INTO atendimento (
            data_hora, duracao_minutos, id_paciente,
            id_atuacao_residente, id_atuacao_preceptor, id_unidade
        ) VALUES (%s, 30, %s, %s, %s, %s)
        RETURNING id
        """,
        (datetime(2029, 11, 10, 10), paciente, residente, preceptor, unidade),
    ).fetchone()[0]
    tempos_anteriores = [
        row[0]
        for row in conn.execute(
            """
            SELECT tempo_real_minutos
            FROM procedimento_realizado
            WHERE id_procedimento = %s
            """,
            (procedimento,),
        ).fetchall()
    ]
    conn.execute(
        """
        INSERT INTO procedimento_realizado (
            id_atendimento, id_procedimento, quantidade,
            tempo_real_minutos, data_hora_inicio
        ) VALUES (%s, %s, 1, 10, %s)
        """,
        (id_atendimento, procedimento, datetime(2029, 11, 10, 10, 5)),
    )
    media = conn.execute(
        "SELECT media_tempo_procedimento FROM procedimento WHERE id = %s",
        (procedimento,),
    ).fetchone()[0]
    esperada = (
        Decimal(sum(tempos_anteriores) + 10)
        / Decimal(len(tempos_anteriores) + 1)
    ).quantize(Decimal("0.01"))
    assert media == esperada


def test_media_do_procedimento_permanece_consistente_em_update_e_delete(
    conn: psycopg.Connection,
) -> None:
    residente, preceptor, unidade, _, paciente = _ids(conn)
    procedimento = conn.execute(
        "SELECT id FROM procedimento ORDER BY id LIMIT 1"
    ).fetchone()[0]
    inicio = datetime(2029, 12, 10, 10)
    id_atendimento = conn.execute(
        """
        INSERT INTO atendimento (
            data_hora, duracao_minutos, id_paciente,
            id_atuacao_residente, id_atuacao_preceptor, id_unidade
        ) VALUES (%s, 60, %s, %s, %s, %s)
        RETURNING id
        """,
        (inicio, paciente, residente, preceptor, unidade),
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO procedimento_realizado (
            id_atendimento, id_procedimento, quantidade,
            tempo_real_minutos, data_hora_inicio
        ) VALUES (%s, %s, 1, 10, %s)
        """,
        (id_atendimento, procedimento, inicio),
    )
    conn.execute(
        """
        UPDATE procedimento_realizado
        SET tempo_real_minutos = 20
        WHERE id_atendimento = %s AND id_procedimento = %s
        """,
        (id_atendimento, procedimento),
    )
    conn.execute(
        """
        DELETE FROM procedimento_realizado
        WHERE id_atendimento = %s AND id_procedimento = %s
        """,
        (id_atendimento, procedimento),
    )

    media = conn.execute(
        """
        SELECT media_tempo_procedimento
        FROM procedimento
        WHERE id = %s
        """,
        (procedimento,),
    ).fetchone()[0]
    esperada = conn.execute(
        """
        SELECT ROUND(AVG(tempo_real_minutos), 2)
        FROM procedimento_realizado
        WHERE id_procedimento = %s
        """,
        (procedimento,),
    ).fetchone()[0]
    assert media == esperada


@pytest.mark.parametrize(
    ("inicio_procedimento", "tempo_real"),
    [
        (datetime(2029, 12, 11, 9, 59), 10),
        (datetime(2029, 12, 11, 10, 20), 20),
    ],
    ids=["antes-do-atendimento", "termino-apos-atendimento"],
)
def test_procedimento_direto_respeita_janela_do_atendimento(
    conn: psycopg.Connection,
    inicio_procedimento: datetime,
    tempo_real: int,
) -> None:
    residente, preceptor, unidade, _, paciente = _ids(conn)
    procedimento = conn.execute(
        "SELECT id FROM procedimento ORDER BY id LIMIT 1"
    ).fetchone()[0]
    id_atendimento = conn.execute(
        """
        INSERT INTO atendimento (
            data_hora, duracao_minutos, id_paciente,
            id_atuacao_residente, id_atuacao_preceptor, id_unidade
        ) VALUES ('2029-12-11 10:00', 30, %s, %s, %s, %s)
        RETURNING id
        """,
        (paciente, residente, preceptor, unidade),
    ).fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            """
            INSERT INTO procedimento_realizado (
                id_atendimento, id_procedimento, quantidade,
                tempo_real_minutos, data_hora_inicio
            ) VALUES (%s, %s, 1, %s, %s)
            """,
            (id_atendimento, procedimento, tempo_real, inicio_procedimento),
        )
