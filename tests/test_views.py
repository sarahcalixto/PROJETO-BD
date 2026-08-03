"""Testes determinísticos das três views da Etapa 2."""

from datetime import date, datetime
from decimal import Decimal

import psycopg


def _ids(conn: psycopg.Connection) -> tuple[int, int, int, int]:
    paciente = conn.execute("SELECT id FROM paciente ORDER BY id LIMIT 1").fetchone()[0]
    residente = conn.execute("SELECT id FROM atuacao_residente ORDER BY id LIMIT 1").fetchone()[0]
    preceptor = conn.execute("SELECT id FROM atuacao_preceptor ORDER BY id LIMIT 1").fetchone()[0]
    unidade = conn.execute("SELECT id FROM unidade ORDER BY id LIMIT 1").fetchone()[0]
    return paciente, residente, preceptor, unidade


def test_pacientes_internados_considera_somente_internacao_mais_recente(
    conn: psycopg.Connection,
) -> None:
    paciente, _, _, unidade = _ids(conn)
    conn.execute("DELETE FROM internacao WHERE id_paciente = %s", (paciente,))
    conn.execute(
        """
        INSERT INTO internacao (
            id_paciente, id_unidade, data_hora_entrada, data_hora_saida
        ) VALUES
            (%s, %s, %s, NULL),
            (%s, %s, %s, %s)
        """,
        (
            paciente,
            unidade,
            datetime(2029, 1, 1, 8),
            paciente,
            unidade,
            datetime(2029, 2, 1, 8),
            datetime(2029, 2, 2, 8),
        ),
    )
    nome = conn.execute("SELECT nome FROM pessoa WHERE id = %s", (paciente,)).fetchone()[0]
    assert conn.execute(
        "SELECT COUNT(*) FROM vw_pacientes_internados WHERE paciente = %s",
        (nome,),
    ).fetchone()[0] == 0


def test_residentes_sem_supervisor_inclui_nao_doutor_e_doutor_inativo(
    conn: psycopg.Connection,
) -> None:
    _, residente, preceptor_doutor, unidade = _ids(conn)
    preceptor_nao_doutor = conn.execute(
        """
        SELECT id FROM atuacao_preceptor
        WHERE LOWER(titulacao) <> 'doutor'
        ORDER BY id LIMIT 1
        """
    ).fetchone()[0]
    conn.execute(
        "UPDATE atuacao_profissional SET data_fim = %s WHERE id = %s",
        (date(2029, 12, 31), preceptor_doutor),
    )
    conn.execute(
        """
        INSERT INTO escala (
            id_unidade, data_plantao, turno,
            id_atuacao_residente, id_atuacao_preceptor
        ) VALUES
            (%s, %s, 'manha', %s, %s),
            (%s, %s, 'tarde', %s, %s)
        """,
        (
            unidade,
            date(2030, 1, 2),
            residente,
            preceptor_doutor,
            unidade,
            date(2030, 1, 2),
            residente,
            preceptor_nao_doutor,
        ),
    )
    linhas = conn.execute(
        """
        SELECT id_atuacao_preceptor
        FROM escala e
        JOIN vw_residentes_sem_supervisor v
          ON v.data_plantao = e.data_plantao
         AND v.turno = e.turno
         AND v.unidade = (SELECT nome FROM unidade WHERE id = e.id_unidade)
        WHERE e.data_plantao = %s
        ORDER BY id_atuacao_preceptor
        """,
        (date(2030, 1, 2),),
    ).fetchall()
    assert [row[0] for row in linhas] == sorted(
        [preceptor_doutor, preceptor_nao_doutor]
    )


def test_estatisticas_mensais_calcula_valores_e_desempata_por_nome(
    conn: psycopg.Connection,
) -> None:
    paciente, residente, preceptor, unidade = _ids(conn)
    procedimentos = conn.execute(
        "SELECT id, nome FROM procedimento ORDER BY nome LIMIT 2"
    ).fetchall()
    ids_atendimentos = conn.execute(
        """
        INSERT INTO atendimento (
            data_hora, duracao_minutos, id_paciente,
            id_atuacao_residente, id_atuacao_preceptor, id_unidade
        ) VALUES
            (%s, 20, %s, %s, %s, %s),
            (%s, 40, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            datetime(2029, 11, 5, 10), paciente, residente, preceptor, unidade,
            datetime(2029, 11, 10, 14), paciente, residente, preceptor, unidade,
        ),
    ).fetchall()
    conn.execute(
        """
        INSERT INTO procedimento_realizado (
            id_atendimento, id_procedimento, quantidade,
            tempo_real_minutos, data_hora_inicio
            ) VALUES
                (%s, %s, 3, 15, %s),
                (%s, %s, 2, 10, %s),
                (%s, %s, 1, 35, %s)
        """,
        (
            ids_atendimentos[0][0], procedimentos[0][0], datetime(2029, 11, 5, 10, 5),
            ids_atendimentos[0][0], procedimentos[1][0], datetime(2029, 11, 5, 10, 10),
            ids_atendimentos[1][0], procedimentos[1][0], datetime(2029, 11, 10, 14, 5),
        ),
    )
    unidade_nome = conn.execute(
        "SELECT nome FROM unidade WHERE id = %s", (unidade,)
    ).fetchone()[0]
    resultado = conn.execute(
        """
        SELECT total_atendimentos, media_duracao_minutos,
               procedimento_mais_comum
        FROM vw_estatisticas_atendimentos_mensal
        WHERE unidade = %s AND ano = %s AND mes = %s
        """,
        (unidade_nome, 2029, 11),
    ).fetchone()
    assert resultado == (2, Decimal("30.00"), procedimentos[0][1])
