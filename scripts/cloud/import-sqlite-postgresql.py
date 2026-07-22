#!/usr/bin/env python3
"""Importa snapshot SQLite em schema PostgreSQL previamente criado."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


EXCLUDED_TABLES = {"postgresql_transition_outbox", "sqlite_sequence"}
STATE_TABLE = "printora_transition_replication_state"


def sqlite_tables(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_schema
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]) not in EXCLUDED_TABLES]


def sqlite_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [str(row[1]) for row in connection.execute(f"PRAGMA table_info({_quote(table)})")]


def snapshot_watermark(connection: sqlite3.Connection) -> int:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?",
        ("postgresql_transition_outbox",),
    ).fetchone()
    if exists is None:
        raise RuntimeError("Snapshot não contém a outbox de transição")
    row = connection.execute(
        "SELECT COALESCE(MAX(id), 0) FROM postgresql_transition_outbox"
    ).fetchone()
    return int(row[0])


def postgresql_columns(connection: psycopg.Connection[Any], table: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    ).fetchall()
    return [str(row["column_name"]) for row in rows]


def validate_target(connection: psycopg.Connection[Any], expected_database: str) -> None:
    row = connection.execute(
        "SELECT current_database() AS database_name, current_schema() AS schema_name"
    ).fetchone()
    if row is None or row["database_name"] != expected_database or row["schema_name"] != "public":
        raise RuntimeError("Banco PostgreSQL alvo não corresponde ao escopo confirmado")


def truncate_target(connection: psycopg.Connection[Any], tables: list[str]) -> None:
    if not tables:
        return
    statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
        sql.SQL(", ").join(map(sql.Identifier, tables))
    )
    connection.execute(statement)
    connection.commit()


def import_table(
    source: sqlite3.Connection,
    target: psycopg.Connection[Any],
    table: str,
    columns: list[str],
    batch_size: int,
    throttle_seconds: float,
) -> int:
    projection = ", ".join(_quote(column) for column in columns)
    source_cursor = source.execute(f"SELECT {projection} FROM {_quote(table)}")
    copy_statement = sql.SQL("COPY {} ({}) FROM STDIN").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    imported = 0
    with target.cursor().copy(copy_statement) as copy:
        while rows := source_cursor.fetchmany(batch_size):
            for row in rows:
                copy.write_row(tuple(row))
            imported += len(rows)
            if throttle_seconds:
                time.sleep(throttle_seconds)
    target.commit()
    return imported


def sync_sequences(connection: psycopg.Connection[Any]) -> int:
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
    synchronized = 0
    for row in rows:
        if not row["sequence_name"]:
            continue
        maximum = connection.execute(
            sql.SQL("SELECT MAX({}) AS maximum FROM {}").format(
                sql.Identifier(str(row["column_name"])),
                sql.Identifier(str(row["table_name"])),
            )
        ).fetchone()["maximum"]
        connection.execute(
            "SELECT setval(%s::regclass, %s, %s)",
            (
                row["sequence_name"],
                maximum if maximum is not None else 1,
                maximum is not None,
            ),
        )
        synchronized += 1
    connection.commit()
    return synchronized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--postgresql-url", default=os.environ.get("PRINTORA_DATABASE_URL"))
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--batch-size", type=int, default=1_000)
    parser.add_argument("--throttle-seconds", type=float, default=0.0)
    parser.add_argument("--replace-target", action="store_true", required=True)
    parser.add_argument("--initialize-watermark-from-outbox", action="store_true")
    args = parser.parse_args()
    if not args.postgresql_url:
        raise SystemExit("--postgresql-url ou PRINTORA_DATABASE_URL é obrigatório")
    if args.batch_size < 1 or args.batch_size > 10_000:
        raise SystemExit("--batch-size deve estar entre 1 e 10000")
    if args.throttle_seconds < 0 or args.throttle_seconds > 5:
        raise SystemExit("--throttle-seconds deve estar entre 0 e 5")

    source = sqlite3.connect(f"file:{args.sqlite}?mode=ro", uri=True)
    try:
        with psycopg.connect(args.postgresql_url, row_factory=dict_row) as target:
            validate_target(target, args.expected_database)
            initial_watermark = (
                snapshot_watermark(source)
                if args.initialize_watermark_from_outbox
                else 0
            )
            tables = sqlite_tables(source)
            for table in tables:
                source_columns = sqlite_columns(source, table)
                target_columns = postgresql_columns(target, table)
                if source_columns != target_columns:
                    raise RuntimeError(f"Colunas divergentes antes da importação: {table}")
            target.execute("SET session_replication_role = replica")
            truncate_target(target, tables)
            report: dict[str, int] = {}
            for table in tables:
                report[table] = import_table(
                    source,
                    target,
                    table,
                    sqlite_columns(source, table),
                    args.batch_size,
                    args.throttle_seconds,
                )
                print(
                    json.dumps(
                        {"event": "table_imported", "rows": report[table], "table": table},
                        sort_keys=True,
                    ),
                    flush=True,
                )
            target.execute("SET session_replication_role = origin")
            target.commit()
            sequences = sync_sequences(target)
            watermark = 0
            if args.initialize_watermark_from_outbox:
                watermark = initial_watermark
                target.execute(
                    f"""
                    UPDATE {STATE_TABLE}
                    SET watermark = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                    """,
                    (watermark,),
                )
                if target.execute(
                    f"SELECT watermark FROM {STATE_TABLE} WHERE id = 1"
                ).fetchone() is None:
                    raise RuntimeError("Estado de replicação PostgreSQL não inicializado")
                target.commit()
    finally:
        source.close()
    print(
        json.dumps(
            {
                "imported_rows": sum(report.values()),
                "sequences": sequences,
                "tables": report,
                "watermark": watermark,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


if __name__ == "__main__":
    main()
