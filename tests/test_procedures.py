from datetime import datetime
import psycopg
import pytest
from psycopg.types.json import Jsonb
from .utils import read_sql


ATENDIMENTO_PADRAO = (
    datetime(2026, 8, 10, 9, 0),
    45,
    1,
    1,
    6,
    1,
)


def procedimento_json(
    id_procedimento: int = 1,
    *,
    inicio: datetime = datetime(2026, 8, 10, 9, 5),
) -> dict[str, object]:
    return {
        "id_procedimento": id_procedimento,
        "quantidade": 1,
        "tempo_real_minutos": 20,
        "data_hora_inicio": inicio.isoformat(sep=" "),
        "observacao": "Procedimento de teste",
        "faturado": False,
    }


def registrar_atendimento(
    conn: psycopg.Connection,
    procedimentos: object,
    atendimento: tuple[object, ...] = ATENDIMENTO_PADRAO,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sp_registrar_atendimento_completo(
                %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (*atendimento, Jsonb(procedimentos)),
        )
        row = cur.fetchone()

    assert row is not None
    return row[0]


def test_script_de_procedures_e_reexecutavel(conn: psycopg.Connection) -> None:
    script = read_sql("05_procedures.sql")

    with conn.cursor() as cur:
        cur.execute(script)
        cur.execute(script)


def test_registrar_atendimento_completo_com_sucesso(
    conn: psycopg.Connection,
) -> None:
    procedimentos = [
        procedimento_json(1),
        procedimento_json(
            2,
            inicio=datetime(2026, 8, 10, 9, 20),
        ),
    ]

    id_atendimento = registrar_atendimento(conn, procedimentos)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT data_hora, duracao_minutos, id_paciente,
                   id_atuacao_residente, id_atuacao_preceptor, id_unidade
            FROM atendimento
            WHERE id = %s
            """,
            (id_atendimento,),
        )
        assert cur.fetchone() == ATENDIMENTO_PADRAO

        cur.execute(
            """
            SELECT id_procedimento, quantidade, tempo_real_minutos,
                   data_hora_inicio, observacao, faturado
            FROM procedimento_realizado
            WHERE id_atendimento = %s
            ORDER BY id_procedimento
            """,
            (id_atendimento,),
        )
        assert cur.fetchall() == [
            (
                1,
                1,
                20,
                datetime(2026, 8, 10, 9, 5),
                "Procedimento de teste",
                False,
            ),
            (
                2,
                1,
                20,
                datetime(2026, 8, 10, 9, 20),
                "Procedimento de teste",
                False,
            ),
        ]


@pytest.mark.parametrize(
    ("indice_parametro", "valor_inexistente"),
    [
        (2, 999_901),
        (3, 999_902),
        (4, 999_903),
        (5, 999_904),
    ],
    ids=["paciente", "residente", "preceptor", "unidade"],
)
def test_registrar_atendimento_rejeita_referencia_inexistente(
    conn: psycopg.Connection,
    indice_parametro: int,
    valor_inexistente: int,
) -> None:
    atendimento = list(ATENDIMENTO_PADRAO)
    atendimento[indice_parametro] = valor_inexistente

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        registrar_atendimento(conn, [procedimento_json()], tuple(atendimento))


@pytest.mark.parametrize("id_atuacao", [1, 6], ids=["residente", "preceptor"])
def test_registrar_atendimento_rejeita_atuacao_fora_da_vigencia(
    conn: psycopg.Connection,
    id_atuacao: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE atuacao_profissional SET data_fim = %s WHERE id = %s",
            (datetime(2026, 8, 9).date(), id_atuacao),
        )

    with pytest.raises(psycopg.errors.CheckViolation):
        registrar_atendimento(conn, [procedimento_json()])


def test_registrar_atendimento_rejeita_json_malformado(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM atendimento")
        quantidade_antes = cur.fetchone()[0]

    with conn.cursor() as cur, pytest.raises(psycopg.errors.InvalidTextRepresentation):
        cur.execute(
            """
            SELECT sp_registrar_atendimento_completo(
                %s, %s, %s, %s, %s, %s, %s::jsonb
            )
            """,
            (*ATENDIMENTO_PADRAO, '[{"id_procedimento": 1'),
        )

    conn.rollback()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM atendimento")
        assert cur.fetchone()[0] == quantidade_antes


@pytest.mark.parametrize(
    "procedimentos",
    [None, {}, [], [1], [{"id_procedimento": 1}]],
    ids=["null", "objeto", "vazio", "item-nao-objeto", "item-incompleto"],
)
def test_registrar_atendimento_rejeita_estrutura_json_invalida(
    conn: psycopg.Connection,
    procedimentos: object,
) -> None:
    with pytest.raises(psycopg.errors.InvalidParameterValue):
        registrar_atendimento(conn, procedimentos)


def test_falha_em_procedimento_reverte_atendimento_e_itens_anteriores(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM atendimento")
        atendimentos_antes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM procedimento_realizado")
        itens_antes = cur.fetchone()[0]

    procedimentos = [procedimento_json(1), procedimento_json(999_999)]

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        registrar_atendimento(conn, procedimentos)

    conn.rollback()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM atendimento")
        assert cur.fetchone()[0] == atendimentos_antes
        cur.execute("SELECT COUNT(*) FROM procedimento_realizado")
        assert cur.fetchone()[0] == itens_antes


def test_registrar_atendimento_rejeita_procedimento_antes_do_atendimento(
    conn: psycopg.Connection,
) -> None:
    procedimento = procedimento_json(
        inicio=datetime(2026, 8, 10, 8, 59),
    )

    with pytest.raises(psycopg.errors.CheckViolation):
        registrar_atendimento(conn, [procedimento])
