#!/usr/bin/env python3
"""Compara snapshot SQLite e PostgreSQL sem escrever em nenhum dos bancos."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


SQLITE_EXCLUDED_TABLES = {"sqlite_sequence", "postgresql_transition_outbox"}
POSTGRESQL_EXCLUDED_TABLES = {"printora_transition_replication_state"}


def sqlite_tables(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_schema
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]) not in SQLITE_EXCLUDED_TABLES]


def postgresql_tables(connection: psycopg.Connection[Any]) -> list[str]:
    rows = connection.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    ).fetchall()
    return [
        str(row["table_name"])
        for row in rows
        if str(row["table_name"]) not in POSTGRESQL_EXCLUDED_TABLES
    ]


def sqlite_foreign_key_violations(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("PRAGMA foreign_key_check").fetchall()
    return [
        {
            "table": row[0],
            "rowid": row[1],
            "parent": row[2],
            "foreign_key_id": row[3],
        }
        for row in rows[:100]
    ]


def postgresql_foreign_keys(connection: psycopg.Connection[Any]) -> dict[str, int]:
    row = connection.execute(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE constraint_definition.convalidated) AS validated
        FROM pg_constraint constraint_definition
        JOIN pg_namespace namespace
          ON namespace.oid = constraint_definition.connamespace
        WHERE namespace.nspname = current_schema()
          AND constraint_definition.contype = 'f'
        """
    ).fetchone()
    return {"total": int(row["total"]), "validated": int(row["validated"])}


def postgresql_sequences(connection: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT table_name,
               column_name,
               pg_get_serial_sequence(
                   quote_ident(table_schema) || '.' || quote_ident(table_name),
                   column_name
               ) AS sequence_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
        ORDER BY table_name, ordinal_position
        """
    ).fetchall()
    report: list[dict[str, Any]] = []
    for row in rows:
        sequence_name = row["sequence_name"]
        if not sequence_name:
            continue
        maximum = connection.execute(
            sql.SQL("SELECT MAX({}) AS maximum FROM {}").format(
                sql.Identifier(str(row["column_name"])),
                sql.Identifier(str(row["table_name"])),
            )
        ).fetchone()["maximum"]
        sequence = connection.execute(
            sql.SQL("SELECT last_value, is_called FROM {}").format(
                sql.Identifier(*str(sequence_name).split(".", 1))
            )
        ).fetchone()
        safe = (
            maximum is None and not bool(sequence["is_called"])
        ) or (
            maximum is not None
            and bool(sequence["is_called"])
            and int(sequence["last_value"]) >= int(maximum)
        )
        report.append(
            {
                "table": row["table_name"],
                "column": row["column_name"],
                "sequence": sequence_name,
                "last_value": sequence["last_value"],
                "is_called": sequence["is_called"],
                "table_maximum": maximum,
                "safe": safe,
            }
        )
    return report


def sqlite_columns(connection: sqlite3.Connection, table: str) -> tuple[list[str], list[str]]:
    rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    columns = [str(row[1]) for row in rows]
    primary = [str(row[1]) for row in sorted(rows, key=lambda row: int(row[5])) if int(row[5])]
    return columns, primary


def postgresql_columns(
    connection: psycopg.Connection[Any],
    table: str,
) -> tuple[list[str], list[str]]:
    columns = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    ).fetchall()
    primary = connection.execute(
        """
        SELECT attribute.attname AS column_name
        FROM pg_index index_definition
        JOIN pg_class table_definition ON table_definition.oid = index_definition.indrelid
        JOIN pg_attribute attribute
          ON attribute.attrelid = table_definition.oid
         AND attribute.attnum = ANY(index_definition.indkey)
        WHERE table_definition.relname = %s AND index_definition.indisprimary
        ORDER BY array_position(index_definition.indkey, attribute.attnum)
        """,
        (table,),
    ).fetchall()
    return (
        [str(row["column_name"]) for row in columns],
        [str(row["column_name"]) for row in primary],
    )


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def digest_rows(rows: Iterable[Any], columns: list[str]) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        payload = [_canonical(row[column]) for column in columns]
        digest.update(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()


def _canonical(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat(sep=" ")
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    return str(value)


def table_report(
    sqlite_connection: sqlite3.Connection,
    postgresql_connection: psycopg.Connection[Any],
    table: str,
) -> dict[str, Any]:
    sqlite_column_names, sqlite_primary = sqlite_columns(sqlite_connection, table)
    postgresql_column_names, postgresql_primary = postgresql_columns(postgresql_connection, table)
    common_columns = [column for column in sqlite_column_names if column in postgresql_column_names]
    order_columns = sqlite_primary or (["id"] if "id" in common_columns else common_columns)
    projection = ", ".join(quote(column) for column in common_columns)
    ordering = ", ".join(quote(column) for column in order_columns)
    sqlite_cursor = sqlite_connection.execute(
        f"SELECT {projection} FROM {quote(table)} ORDER BY {ordering}"
    )
    postgresql_cursor = postgresql_connection.execute(
        f"SELECT {projection} FROM {quote(table)} ORDER BY {ordering}"
    )
    sqlite_count, sqlite_digest = digest_rows(sqlite_cursor, common_columns)
    postgresql_count, postgresql_digest = digest_rows(postgresql_cursor, common_columns)
    identifier = "id" if "id" in common_columns else None
    sqlite_range = _range(sqlite_connection, table, identifier)
    postgresql_range = _range(postgresql_connection, table, identifier)
    return {
        "table": table,
        "columns_match": sqlite_column_names == postgresql_column_names,
        "sqlite_columns": sqlite_column_names,
        "postgresql_columns": postgresql_column_names,
        "sqlite_primary_key": sqlite_primary,
        "postgresql_primary_key": postgresql_primary,
        "sqlite_count": sqlite_count,
        "postgresql_count": postgresql_count,
        "sqlite_id_range": sqlite_range,
        "postgresql_id_range": postgresql_range,
        "sqlite_sha256": sqlite_digest,
        "postgresql_sha256": postgresql_digest,
        "match": (
            sqlite_column_names == postgresql_column_names
            and sqlite_count == postgresql_count
            and sqlite_range == postgresql_range
            and sqlite_digest == postgresql_digest
        ),
    }


def _range(connection: Any, table: str, identifier: str | None) -> list[int | None] | None:
    if identifier is None:
        return None
    row = connection.execute(
        f"SELECT MIN({quote(identifier)}) AS minimum, MAX({quote(identifier)}) AS maximum "
        f"FROM {quote(table)}"
    ).fetchone()
    return [row["minimum"], row["maximum"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--postgresql-url", default=os.environ.get("PRINTORA_DATABASE_URL"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.postgresql_url:
        raise SystemExit("--postgresql-url ou PRINTORA_DATABASE_URL é obrigatório")
    sqlite_connection = sqlite3.connect(f"file:{args.sqlite}?mode=ro", uri=True)
    sqlite_connection.row_factory = sqlite3.Row
    with psycopg.connect(args.postgresql_url, row_factory=dict_row) as postgresql_connection:
        source_tables = sqlite_tables(sqlite_connection)
        target_tables = postgresql_tables(postgresql_connection)
        common = sorted(set(source_tables) & set(target_tables))
        reports = [table_report(sqlite_connection, postgresql_connection, table) for table in common]
        foreign_keys = postgresql_foreign_keys(postgresql_connection)
        sequences = postgresql_sequences(postgresql_connection)
    source_foreign_key_violations = sqlite_foreign_key_violations(sqlite_connection)
    sqlite_connection.close()
    payload = {
        "source_backend": "sqlite",
        "target_backend": "postgresql",
        "source_tables": len(source_tables),
        "target_tables": len(target_tables),
        "missing_in_postgresql": sorted(set(source_tables) - set(target_tables)),
        "extra_in_postgresql": sorted(set(target_tables) - set(source_tables)),
        "tables": reports,
        "matched_tables": sum(1 for report in reports if report["match"]),
        "mismatched_tables": [report["table"] for report in reports if not report["match"]],
        "sqlite_foreign_key_violations": source_foreign_key_violations,
        "postgresql_foreign_keys": foreign_keys,
        "postgresql_sequences": sequences,
        "unsafe_sequences": [item["sequence"] for item in sequences if not item["safe"]],
    }
    payload["status"] = (
        "ok"
        if not payload["missing_in_postgresql"]
        and not payload["extra_in_postgresql"]
        and not payload["mismatched_tables"]
        and not payload["sqlite_foreign_key_violations"]
        and payload["postgresql_foreign_keys"]["total"]
        == payload["postgresql_foreign_keys"]["validated"]
        and not payload["unsafe_sequences"]
        else "diverged"
    )
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    raise SystemExit(0 if payload["status"] == "ok" else 2)


if __name__ == "__main__":
    main()
