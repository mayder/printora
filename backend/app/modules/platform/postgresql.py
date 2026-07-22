from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

import psycopg
from psycopg.rows import dict_row


INSERT_TABLE = re.compile(
    r"^\s*INSERT\s+INTO\s+[\"']?([a-zA-Z0-9_]+)[\"']?",
    re.IGNORECASE,
)
INSERT_OR_IGNORE = re.compile(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\s+", re.IGNORECASE)
DATETIME_WITH_MODIFIER = re.compile(
    r"datetime\(\s*(?:'now'|CURRENT_TIMESTAMP)\s*,\s*(%s|'[^']+')\s*\)",
    re.IGNORECASE,
)
DATETIME_NOW = re.compile(r"datetime\(\s*'now'\s*\)", re.IGNORECASE)
GROUP_CONCAT_DISTINCT = re.compile(r"GROUP_CONCAT\(DISTINCT\s+([^\)]+)\)", re.IGNORECASE)
GROUP_CONCAT = re.compile(r"GROUP_CONCAT\(\s*([^\)]+)\s*\)", re.IGNORECASE)
CURRENT_TIMESTAMP_TOKEN = re.compile(r"\bCURRENT_TIMESTAMP\b", re.IGNORECASE)
CURRENT_TIMESTAMP_SENTINEL = "__PRINTORA_POSTGRESQL_CURRENT_TIMESTAMP__"


class PostgreSQLCursor:
    def __init__(self, cursor: psycopg.Cursor[Any], *, lastrowid: int | None = None) -> None:
        self._cursor = cursor
        self.lastrowid = lastrowid

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def fetchone(self) -> dict[str, Any] | None:
        return self._cursor.fetchone()

    def fetchall(self) -> list[dict[str, Any]]:
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor)


class PostgreSQLConnection:
    def __init__(self, database_url: str) -> None:
        self._connection = psycopg.connect(database_url, row_factory=dict_row)
        self._tables_with_id = self._load_tables_with_id()

    def execute(
        self,
        statement: str,
        parameters: Sequence[object] | None = None,
    ) -> PostgreSQLCursor:
        translated = translate_sql(statement)
        table = _insert_table(translated)
        automatic_returning = bool(
            table
            and table in self._tables_with_id
            and " RETURNING " not in f" {translated.upper()} "
        )
        if automatic_returning:
            translated = translated.rstrip().rstrip(";") + " RETURNING id"
        cursor = self._connection.cursor(row_factory=dict_row)
        cursor.execute(translated, tuple(parameters or ()))
        lastrowid = None
        if automatic_returning:
            row = cursor.fetchone()
            if row is not None and row.get("id") is not None:
                lastrowid = int(row["id"])
        return PostgreSQLCursor(cursor, lastrowid=lastrowid)

    def executemany(
        self,
        statement: str,
        parameters: Iterable[Sequence[object]],
    ) -> PostgreSQLCursor:
        cursor = self._connection.cursor(row_factory=dict_row)
        cursor.executemany(translate_sql(statement), parameters)
        return PostgreSQLCursor(cursor)

    def execute_script(self, script: str) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(script)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def _load_tables_with_id(self) -> set[str]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.columns
                WHERE table_schema = current_schema() AND column_name = 'id'
                """
            )
            return {str(row["table_name"]) for row in cursor.fetchall()}


def translate_sql(statement: str) -> str:
    translated = _replace_qmark_placeholders(statement)
    ignore_conflicts = bool(INSERT_OR_IGNORE.match(translated))
    if ignore_conflicts:
        translated = INSERT_OR_IGNORE.sub("INSERT INTO ", translated, count=1)
    translated = DATETIME_WITH_MODIFIER.sub(_postgresql_datetime, translated)
    translated = DATETIME_NOW.sub(
        f"CAST({CURRENT_TIMESTAMP_SENTINEL} AS TEXT)",
        translated,
    )
    translated = CURRENT_TIMESTAMP_TOKEN.sub("CAST(CURRENT_TIMESTAMP AS TEXT)", translated)
    translated = translated.replace(CURRENT_TIMESTAMP_SENTINEL, "CURRENT_TIMESTAMP")
    translated = GROUP_CONCAT_DISTINCT.sub(r"STRING_AGG(DISTINCT \1, ',')", translated)
    translated = GROUP_CONCAT.sub(r"STRING_AGG(\1, ',')", translated)
    if ignore_conflicts:
        translated = translated.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    return translated


def _postgresql_datetime(match: re.Match[str]) -> str:
    modifier = match.group(1)
    if modifier == "%s":
        return f"CAST({CURRENT_TIMESTAMP_SENTINEL} + (%s)::interval AS TEXT)"
    return f"CAST({CURRENT_TIMESTAMP_SENTINEL} + INTERVAL {modifier} AS TEXT)"


def _replace_qmark_placeholders(statement: str) -> str:
    output: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(statement):
        character = statement[index]
        if quote is not None:
            output.append(character)
            if character == quote:
                if index + 1 < len(statement) and statement[index + 1] == quote:
                    output.append(statement[index + 1])
                    index += 1
                else:
                    quote = None
        elif character in {"'", '"'}:
            quote = character
            output.append(character)
        elif character == "?":
            output.append("%s")
        else:
            output.append(character)
        index += 1
    return "".join(output)


def _insert_table(statement: str) -> str | None:
    match = INSERT_TABLE.match(statement)
    return match.group(1).lower() if match else None
