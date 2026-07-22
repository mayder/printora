#!/usr/bin/env python3
"""Replica de modo idempotente a outbox SQLite para o PostgreSQL sombra."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


OUTBOX_TABLE = "postgresql_transition_outbox"
STATE_TABLE = "printora_transition_replication_state"


@dataclass(frozen=True)
class TableShape:
    columns: frozenset[str]
    primary_key: tuple[str, ...]


def load_shapes(connection: psycopg.Connection[Any]) -> dict[str, TableShape]:
    column_rows = connection.execute(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
        ORDER BY table_name, ordinal_position
        """
    ).fetchall()
    primary_rows = connection.execute(
        """
        SELECT table_definition.relname AS table_name,
               attribute.attname AS column_name,
               array_position(index_definition.indkey, attribute.attnum) AS key_order
        FROM pg_index index_definition
        JOIN pg_class table_definition ON table_definition.oid = index_definition.indrelid
        JOIN pg_namespace namespace ON namespace.oid = table_definition.relnamespace
        JOIN pg_attribute attribute
          ON attribute.attrelid = table_definition.oid
         AND attribute.attnum = ANY(index_definition.indkey)
        WHERE namespace.nspname = current_schema() AND index_definition.indisprimary
        ORDER BY table_definition.relname, key_order
        """
    ).fetchall()
    columns: dict[str, set[str]] = {}
    primary: dict[str, list[str]] = {}
    for row in column_rows:
        columns.setdefault(str(row["table_name"]), set()).add(str(row["column_name"]))
    for row in primary_rows:
        primary.setdefault(str(row["table_name"]), []).append(str(row["column_name"]))
    return {
        table: TableShape(frozenset(table_columns), tuple(primary.get(table, [])))
        for table, table_columns in columns.items()
    }


def apply_event(
    connection: psycopg.Connection[Any],
    shapes: dict[str, TableShape],
    event: sqlite3.Row,
) -> None:
    table = str(event["table_name"])
    shape = shapes.get(table)
    if shape is None or not shape.primary_key:
        raise RuntimeError(f"Tabela alvo ausente ou sem chave primária: {table}")
    primary = json.loads(str(event["primary_key_json"]))
    if set(primary) != set(shape.primary_key):
        raise RuntimeError(f"Chave primária divergente para {table}")
    if event["operation"] == "delete":
        predicates = sql.SQL(" AND ").join(
            sql.SQL("{} = {}").format(sql.Identifier(column), sql.Placeholder())
            for column in shape.primary_key
        )
        connection.execute(
            sql.SQL("DELETE FROM {} WHERE ").format(sql.Identifier(table)) + predicates,
            tuple(primary[column] for column in shape.primary_key),
        )
        return
    row = json.loads(str(event["row_json"]))
    unknown = set(row) - shape.columns
    if unknown:
        raise RuntimeError(f"Colunas desconhecidas em {table}: {sorted(unknown)}")
    columns = list(row)
    updates = [column for column in columns if column not in shape.primary_key]
    conflict_action = (
        sql.SQL("DO UPDATE SET ")
        + sql.SQL(", ").join(
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(column), sql.Identifier(column))
            for column in updates
        )
        if updates
        else sql.SQL("DO NOTHING")
    )
    statement = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) ").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        sql.SQL(", ").join(map(sql.Identifier, shape.primary_key)),
    ) + conflict_action
    connection.execute(statement, tuple(row[column] for column in columns))


def replicate_batch(
    sqlite_connection: sqlite3.Connection,
    postgresql_connection: psycopg.Connection[Any],
    shapes: dict[str, TableShape],
    batch_size: int,
) -> tuple[int, int]:
    state = postgresql_connection.execute(
        f"SELECT watermark FROM {STATE_TABLE} WHERE id = 1 FOR UPDATE"
    ).fetchone()
    if state is None:
        raise RuntimeError("Estado de replicação PostgreSQL não inicializado")
    watermark = int(state["watermark"])
    events = sqlite_connection.execute(
        f"""
        SELECT id, table_name, operation, primary_key_json, row_json
        FROM {OUTBOX_TABLE}
        WHERE id > ?
        ORDER BY id
        LIMIT ?
        """,
        (watermark, batch_size),
    ).fetchall()
    for event in events:
        apply_event(postgresql_connection, shapes, event)
        watermark = int(event["id"])
    if events:
        postgresql_connection.execute(
            f"""
            UPDATE {STATE_TABLE}
            SET watermark = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (watermark,),
        )
    return len(events), watermark


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
        sequence_name = row["sequence_name"]
        if not sequence_name:
            continue
        maximum = connection.execute(
            sql.SQL("SELECT MAX({}) AS maximum FROM {}").format(
                sql.Identifier(str(row["column_name"])),
                sql.Identifier(str(row["table_name"])),
            )
        ).fetchone()["maximum"]
        connection.execute(
            "SELECT setval(%s::regclass, %s, %s)",
            (sequence_name, maximum if maximum is not None else 1, maximum is not None),
        )
        synchronized += 1
    return synchronized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--postgresql-url", default=os.environ.get("PRINTORA_DATABASE_URL"))
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--until-idle", action="store_true")
    parser.add_argument("--sync-sequences", action="store_true")
    args = parser.parse_args()
    if not args.postgresql_url:
        raise SystemExit("--postgresql-url ou PRINTORA_DATABASE_URL é obrigatório")
    if args.batch_size < 1 or args.batch_size > 10_000:
        raise SystemExit("--batch-size deve estar entre 1 e 10000")
    os.umask(0o007)
    sqlite_connection = sqlite3.connect(f"file:{args.sqlite}?mode=ro", uri=True)
    sqlite_connection.row_factory = sqlite3.Row
    total = 0
    watermark = 0
    synchronized_sequences = 0
    try:
        with psycopg.connect(args.postgresql_url, row_factory=dict_row) as target:
            shapes = load_shapes(target)
            while True:
                processed, watermark = replicate_batch(
                    sqlite_connection,
                    target,
                    shapes,
                    args.batch_size,
                )
                target.commit()
                total += processed
                if not args.until_idle or processed < args.batch_size:
                    break
            if args.sync_sequences:
                synchronized_sequences = sync_sequences(target)
                target.commit()
    finally:
        sqlite_connection.close()
    print(
        json.dumps(
            {
                "processed": total,
                "synchronized_sequences": synchronized_sequences,
                "watermark": watermark,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
