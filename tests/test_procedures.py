from datetime import date, datetime
from decimal import Decimal
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


def test_registrar_atendimento_rejeita_duracao_acima_do_limite(
    conn: psycopg.Connection,
) -> None:
    atendimento = list(ATENDIMENTO_PADRAO)
    atendimento[1] = 1441
    with pytest.raises(psycopg.errors.CheckViolation):
        registrar_atendimento(conn, [procedimento_json()], tuple(atendimento))


def test_registrar_atendimento_rejeita_procedimento_que_termina_depois(
    conn: psycopg.Connection,
) -> None:
    procedimento = procedimento_json(
        inicio=datetime(2026, 8, 10, 9, 40),
    )

    with pytest.raises(psycopg.errors.CheckViolation):
        registrar_atendimento(conn, [procedimento])


def test_registrar_atendimento_rejeita_procedimento_inicialmente_faturado(
    conn: psycopg.Connection,
) -> None:
    procedimento = procedimento_json()
    procedimento["faturado"] = True

    with pytest.raises(psycopg.errors.CheckViolation):
        registrar_atendimento(conn, [procedimento])


def test_registrar_atendimento_rejeita_reenvio_exatamente_duplicado(
    conn: psycopg.Connection,
) -> None:
    registrar_atendimento(conn, [procedimento_json()])
    with conn.cursor() as cur:
        cur.execute("SAVEPOINT antes_do_reenvio")

    with pytest.raises(psycopg.errors.UniqueViolation):
        registrar_atendimento(conn, [procedimento_json()])

    with conn.cursor() as cur:
        cur.execute("ROLLBACK TO SAVEPOINT antes_do_reenvio")
        cur.execute(
            """
            SELECT COUNT(*)
            FROM atendimento
            WHERE data_hora = %s
              AND duracao_minutos = %s
              AND id_paciente = %s
              AND id_atuacao_residente = %s
              AND id_atuacao_preceptor = %s
              AND id_unidade = %s
            """,
            ATENDIMENTO_PADRAO,
        )
        assert cur.fetchone()[0] == 1


def test_tempo_medio_espera_usa_primeiro_procedimento_e_ignora_sem_procedimento(
    conn: psycopg.Connection,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO unidade (nome, tipo, capacidade_leitos)
            VALUES ('Unidade teste da media', 'ambulatorio', 10)
            RETURNING id
            """
        )
        id_unidade = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO unidade (nome, tipo, capacidade_leitos)
            VALUES ('Unidade sem procedimento', 'ambulatorio', 10)
            RETURNING id
            """
        )
        id_unidade_sem_procedimento = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO atendimento (
                data_hora, duracao_minutos, id_paciente,
                id_atuacao_residente, id_atuacao_preceptor, id_unidade
            ) VALUES
                ('2026-09-01 10:00:00', 60, 1, 1, 6, %s),
                ('2026-09-01 11:00:00', 30, 2, 1, 6, %s),
                ('2026-09-01 12:00:00', 20, 3, 1, 6, %s),
                ('2026-09-01 13:00:00', 20, 4, 1, 6, %s)
            RETURNING id
            """,
            (
                id_unidade,
                id_unidade,
                id_unidade,
                id_unidade_sem_procedimento,
            ),
        )
        ids_atendimentos = [row[0] for row in cur.fetchall()]

        cur.execute(
            """
            INSERT INTO procedimento_realizado (
                id_atendimento, id_procedimento, quantidade,
                tempo_real_minutos, data_hora_inicio
            ) VALUES
                    (%s, 1, 1, 10, '2026-09-01 10:50:00'),
                (%s, 2, 1, 20, '2026-09-01 10:20:00'),
                (%s, 1, 1, 10, '2026-09-01 11:10:00')
            """,
            (
                ids_atendimentos[0],
                ids_atendimentos[0],
                ids_atendimentos[1],
            ),
        )

        cur.execute(
            """
            SELECT id_unidade, unidade, tempo_medio_espera_minutos
            FROM sp_calcular_tempo_medio_espera()
            """
        )
        resultados = {row[0]: row[1:] for row in cur.fetchall()}

    assert resultados[id_unidade] == (
        "Unidade teste da media",
        Decimal("15.00"),
    )
    assert resultados[id_unidade_sem_procedimento] == (
        "Unidade sem procedimento",
        None,
    )


def inserir_escala(
    conn: psycopg.Connection,
    *,
    residente: int = 1,
    unidade: int = 1,
    data_plantao: date,
    turno: str,
    preceptor: int = 6,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO escala (
                id_unidade, data_plantao, turno,
                id_atuacao_residente, id_atuacao_preceptor
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (unidade, data_plantao, turno, residente, preceptor),
        )
        row = cur.fetchone()

    assert row is not None
    return row[0]


def reajustar_escala(
    conn: psycopg.Connection,
    *,
    residente: int = 1,
    data_origem: date,
    turno_origem: str,
    data_destino: date,
    turno_destino: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sp_reajustar_escala(%s, %s, %s, %s, %s)
            """,
            (
                residente,
                data_origem,
                turno_origem,
                data_destino,
                turno_destino,
            ),
        )
        row = cur.fetchone()

    assert row is not None
    return row[0]


def test_reajustar_escala_move_origem_e_preserva_demais_escalas(
    conn: psycopg.Connection,
) -> None:
    data_origem = date(2027, 1, 10)
    data_destino = date(2027, 1, 12)
    id_movido = inserir_escala(
        conn,
        data_plantao=data_origem,
        turno="manha",
    )
    id_preservado = inserir_escala(
        conn,
        data_plantao=date(2027, 1, 11),
        turno="tarde",
    )

    quantidade = reajustar_escala(
        conn,
        data_origem=data_origem,
        turno_origem="manha",
        data_destino=data_destino,
        turno_destino="noite",
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, data_plantao, turno::text
            FROM escala
            WHERE id IN (%s, %s)
            ORDER BY id
            """,
            (id_movido, id_preservado),
        )
        escalas = {row[0]: row[1:] for row in cur.fetchall()}

    assert quantidade == 1
    assert escalas[id_movido] == (data_destino, "noite")
    assert escalas[id_preservado] == (date(2027, 1, 11), "tarde")


def test_reajustar_multiplas_escalas_na_mesma_transacao(
    conn: psycopg.Connection,
) -> None:
    data_origem = date(2027, 1, 20)
    data_destino = date(2027, 1, 21)
    inserir_escala(
        conn,
        residente=1,
        unidade=1,
        data_plantao=data_origem,
        turno="manha",
        preceptor=6,
    )
    inserir_escala(
        conn,
        residente=2,
        unidade=2,
        data_plantao=data_origem,
        turno="manha",
        preceptor=7,
    )

    quantidades = [
        reajustar_escala(
            conn,
            residente=residente,
            data_origem=data_origem,
            turno_origem="manha",
            data_destino=data_destino,
            turno_destino="tarde",
        )
        for residente in (1, 2)
    ]

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id_atuacao_residente
            FROM escala
            WHERE id_atuacao_residente IN (1, 2)
              AND data_plantao = %s
              AND turno = 'tarde'
            ORDER BY id_atuacao_residente
            """,
            (data_destino,),
        )
        residentes_reajustados = [row[0] for row in cur.fetchall()]

    assert quantidades == [1, 1]
    assert residentes_reajustados == [1, 2]


def test_reajustar_escala_rejeita_residente_inexistente(
    conn: psycopg.Connection,
) -> None:
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        reajustar_escala(
            conn,
            residente=999_999,
            data_origem=date(2027, 2, 1),
            turno_origem="manha",
            data_destino=date(2027, 2, 2),
            turno_destino="tarde",
        )


def test_reajustar_escala_rejeita_origem_sem_escalas(
    conn: psycopg.Connection,
) -> None:
    with pytest.raises(psycopg.errors.NoDataFound):
        reajustar_escala(
            conn,
            data_origem=date(2027, 2, 1),
            turno_origem="manha",
            data_destino=date(2027, 2, 2),
            turno_destino="tarde",
        )


def test_reajustar_escala_rejeita_origem_igual_ao_destino(
    conn: psycopg.Connection,
) -> None:
    data_plantao = date(2027, 3, 1)
    inserir_escala(
        conn,
        data_plantao=data_plantao,
        turno="manha",
    )

    with pytest.raises(psycopg.errors.CheckViolation):
        reajustar_escala(
            conn,
            data_origem=data_plantao,
            turno_origem="manha",
            data_destino=data_plantao,
            turno_destino="manha",
        )


@pytest.mark.parametrize("id_atuacao", [1, 6], ids=["residente", "preceptor"])
def test_reajustar_escala_rejeita_atuacao_fora_da_vigencia_no_destino(
    conn: psycopg.Connection,
    id_atuacao: int,
) -> None:
    data_origem = date(2027, 4, 1)
    data_destino = date(2027, 4, 3)
    id_escala = inserir_escala(
        conn,
        data_plantao=data_origem,
        turno="manha",
    )
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE atuacao_profissional SET data_fim = %s WHERE id = %s",
            (date(2027, 4, 2), id_atuacao),
        )
        cur.execute("SAVEPOINT antes_do_reajuste")

    with pytest.raises(psycopg.errors.CheckViolation):
        reajustar_escala(
            conn,
            data_origem=data_origem,
            turno_origem="manha",
            data_destino=data_destino,
            turno_destino="tarde",
        )

    with conn.cursor() as cur:
        cur.execute("ROLLBACK TO SAVEPOINT antes_do_reajuste")
        cur.execute(
            "SELECT data_plantao, turno::text FROM escala WHERE id = %s",
            (id_escala,),
        )
        assert cur.fetchone() == (data_origem, "manha")


def test_conflito_no_destino_nao_atualiza_escala_de_origem(
    conn: psycopg.Connection,
) -> None:
    data_origem = date(2027, 5, 1)
    data_destino = date(2027, 5, 2)
    id_origem = inserir_escala(
        conn,
        unidade=1,
        data_plantao=data_origem,
        turno="manha",
    )
    id_destino = inserir_escala(
        conn,
        unidade=2,
        data_plantao=data_destino,
        turno="tarde",
    )
    with conn.cursor() as cur:
        cur.execute("SAVEPOINT antes_do_reajuste")

    with pytest.raises(psycopg.errors.UniqueViolation):
        reajustar_escala(
            conn,
            data_origem=data_origem,
            turno_origem="manha",
            data_destino=data_destino,
            turno_destino="tarde",
        )

    with conn.cursor() as cur:
        cur.execute("ROLLBACK TO SAVEPOINT antes_do_reajuste")
        cur.execute(
            """
            SELECT id, id_unidade, data_plantao, turno::text
            FROM escala
            WHERE id IN (%s, %s)
            ORDER BY id
            """,
            (id_origem, id_destino),
        )
        assert cur.fetchall() == [
            (id_origem, 1, data_origem, "manha"),
            (id_destino, 2, data_destino, "tarde"),
        ]
