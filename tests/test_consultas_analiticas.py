from datetime import date, timedelta

import psycopg

from .utils import find_statement


def test_ranking_residentes_por_atendimentos(
    conn: psycopg.Connection, analiticas_statements: list[str]
) -> None:
    query = find_statement(analiticas_statements, "total_atendimentos")
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    assert rows[0] == ("Narancia Ghirga", 3)
    assert sum(total for _, total in rows) == 10


def test_preceptores_com_mais_de_5_atendimentos_no_mes(
    conn: psycopg.Connection, analiticas_statements: list[str]
) -> None:
    query = find_statement(analiticas_statements, "total_supervisionado")
    mes_atual = date.today().replace(day=1)
    with conn.cursor() as cur:
        cur.execute(query, {"mes_referencia": mes_atual})
        rows = cur.fetchall()

    assert rows == [("Bruno Bucciarati", 7)]


def test_preceptores_com_mais_de_5_atendimentos_nao_conta_outro_mes(
    conn: psycopg.Connection, analiticas_statements: list[str]
) -> None:
    query = find_statement(analiticas_statements, "total_supervisionado")
    mes_passado = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    with conn.cursor() as cur:
        cur.execute(query, {"mes_referencia": mes_passado})
        rows = cur.fetchall()

    assert rows == []


def test_plantoes_por_unidade_e_residente_no_mes_corrente(
    conn: psycopg.Connection, analiticas_statements: list[str]
) -> None:
    query = find_statement(analiticas_statements, "quantidade_plantoes")
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    assert ("Enfermaria Central", "Narancia Ghirga", 2) in rows
    assert sum(qtd for _, _, qtd in rows) == 6


def test_pacientes_sem_procedimento_de_risco_alto(
    conn: psycopg.Connection, analiticas_statements: list[str]
) -> None:
    query = find_statement(analiticas_statements,
                           "NOT EXISTS", "nivel_risco = 'alto'")
    with conn.cursor() as cur:
        cur.execute(query)
        nomes = {nome for nome, _ in cur.fetchall()}

    assert nomes == {"Gon Freecss",
                     "Giorno Giovanna", "Winry Rockbell"}
