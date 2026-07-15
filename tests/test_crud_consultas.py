from datetime import datetime

import psycopg
import pytest

from .utils import find_statement


def test_inserir_atendimento_validado_com_sucesso(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT inserir_atendimento_validado(%s, %s, %s, %s, %s, %s, %s);",
            (100, datetime.now(), 30, 1, 1, 6, 1),
        )
        (novo_id,) = cur.fetchone()
        assert novo_id == 100

        cur.execute("SELECT id_paciente FROM atendimento WHERE id = 100;")
        assert cur.fetchone() == (1,)


def test_inserir_atendimento_validado_paciente_inexistente(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur, pytest.raises(psycopg.errors.ForeignKeyViolation):
        cur.execute(
            "SELECT inserir_atendimento_validado(%s, %s, %s, %s, %s, %s, %s);",
            (101, datetime.now(), 30, 9999, 1, 6, 1),
        )


def test_inserir_atendimento_validado_atuacao_nao_vigente(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur, pytest.raises(psycopg.errors.CheckViolation):
        cur.execute(
            "SELECT inserir_atendimento_validado(%s, %s, %s, %s, %s, %s, %s);",
            (102, datetime(2000, 1, 1, 8, 0), 30, 1, 1, 6, 1),
        )


def test_listar_atendimentos_de_um_paciente(
    conn: psycopg.Connection, crud_statements: list[str]
) -> None:
    query = find_statement(crud_statements, "FROM atendimento", "id_paciente")
    with conn.cursor() as cur:
        cur.execute(query, {"id_paciente": 1})
        rows = cur.fetchall()

    atendimento_ids = [row[0] for row in rows]
    assert atendimento_ids == [1, 6]


def test_listar_procedimentos_de_um_atendimento(
    conn: psycopg.Connection, crud_statements: list[str]
) -> None:
    query = find_statement(crud_statements, "pr.tempo_real_minutos")
    with conn.cursor() as cur:
        cur.execute(query, {"id_atendimento": 3})
        rows = cur.fetchall()

    assert rows == [(3, "Aplicacao de medicacao", 2, 15)]


def test_atualizar_num_convenio_paciente(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM atualizar_num_convenio_paciente(%s, %s);",
            (1, "CONV-NOVO-001"),
        )
        assert cur.fetchone() == (1, "CONV-NOVO-001")

        cur.execute("SELECT num_convenio FROM paciente WHERE id = 1;")
        assert cur.fetchone() == ("CONV-NOVO-001",)


def test_atualizar_num_convenio_paciente_inexistente(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur, pytest.raises(psycopg.Error) as exc_info:
        cur.execute(
            "SELECT * FROM atualizar_num_convenio_paciente(%s, %s);",
            (9999, "X"),
        )
    assert exc_info.value.sqlstate == "P0002"


def test_remover_procedimento_realizado_faturado_e_bloqueado(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur, pytest.raises(psycopg.errors.CheckViolation):
        cur.execute(
            "SELECT * FROM remover_procedimento_realizado_nao_faturado(%s, %s);",
            (1, 1),
        )


def test_remover_procedimento_realizado_nao_faturado(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM remover_procedimento_realizado_nao_faturado(%s, %s);",
            (2, 2),
        )
        assert cur.fetchone() == (2, 2, False)

        cur.execute(
            "SELECT 1 FROM procedimento_realizado WHERE id_atendimento = 2 AND id_procedimento = 2;"
        )
        assert cur.fetchone() is None


def test_tempo_medio_duracao_por_atuacao_residente(
    conn: psycopg.Connection, crud_statements: list[str]
) -> None:
    query = find_statement(crud_statements, "AVG(duracao_minutos)")
    with conn.cursor() as cur:
        cur.execute(query)
        resultados = {
            atuacao_id: float(media) for atuacao_id, _, media in cur.fetchall()
        }

    assert resultados[1] == pytest.approx(95 / 3)
    assert resultados[2] == pytest.approx(42.5)
    assert resultados[3] == pytest.approx(37.5)
    assert resultados[4] == pytest.approx(50)
    assert resultados[5] == pytest.approx(35)
