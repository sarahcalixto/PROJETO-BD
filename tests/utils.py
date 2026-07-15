from pathlib import Path

import sqlparse

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def read_sql(filename: str) -> str:
    return (SQL_DIR / filename).read_text(encoding="utf-8")


def split_sql_statements(text: str) -> list[str]:
    return [s.strip() for s in sqlparse.split(text) if s.strip()]


def find_statement(statements: list[str], *needles: str) -> str:
    matches = [s for s in statements if all(n in s for n in needles)]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one file containing {needles!r}, but  found {len(matches)}"
        )
    return matches[0]
