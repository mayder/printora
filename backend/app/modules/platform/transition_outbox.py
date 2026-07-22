from __future__ import annotations

import os
import sqlite3


OUTBOX_TABLE = "postgresql_transition_outbox"
OUTBOX_ENABLED_ENV = "PRINTORA_TRANSITION_OUTBOX_ENABLED"
EXCLUDED_TABLES = {OUTBOX_TABLE}


def transition_outbox_enabled() -> bool:
    return os.environ.get(OUTBOX_ENABLED_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def ensure_transition_outbox(connection: sqlite3.Connection) -> int:
    """Instala captura atômica de alterações para a transição ao PostgreSQL."""
    tables = _application_tables(connection)
    for table in tables:
        columns, primary_key = _table_shape(connection, table)
        if not primary_key:
            raise RuntimeError(f"Tabela sem chave primária não pode ser replicada: {table}")
        _create_triggers(connection, table, columns, primary_key)
    return len(tables)


def transition_watermark(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        f"SELECT COALESCE(MAX(id), 0) AS watermark FROM {_quote(OUTBOX_TABLE)}"
    ).fetchone()
    return int(row[0] if row is not None else 0)


def _application_tables(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_schema
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]) not in EXCLUDED_TABLES]


def _table_shape(
    connection: sqlite3.Connection,
    table: str,
) -> tuple[list[str], list[str]]:
    rows = connection.execute(f"PRAGMA table_info({_quote(table)})").fetchall()
    columns = [str(row[1]) for row in rows]
    primary_key = [
        str(row[1])
        for row in sorted(rows, key=lambda item: int(item[5]))
        if int(row[5]) > 0
    ]
    return columns, primary_key


def _create_triggers(
    connection: sqlite3.Connection,
    table: str,
    columns: list[str],
    primary_key: list[str],
) -> None:
    trigger_prefix = f"printora_pg_transition_{table}"
    new_primary = _json_object(primary_key, "NEW")
    old_primary = _json_object(primary_key, "OLD")
    new_row = _json_object(columns, "NEW")
    old_row = _json_object(columns, "OLD")
    quoted_table = _quote(table)
    quoted_outbox = _quote(OUTBOX_TABLE)
    table_literal = "'" + table.replace("'", "''") + "'"
    definitions = {
        "insert": ("AFTER INSERT", new_primary, new_row),
        "update": ("AFTER UPDATE", new_primary, new_row),
        "delete": ("AFTER DELETE", old_primary, old_row),
    }
    for operation, (timing, primary_payload, row_payload) in definitions.items():
        trigger = _quote(f"{trigger_prefix}_{operation}")
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {trigger}
            {timing} ON {quoted_table}
            BEGIN
                INSERT INTO {quoted_outbox}
                    (table_name, operation, primary_key_json, row_json)
                VALUES ({table_literal}, '{operation}', {primary_payload}, {row_payload});
            END
            """
        )


def _json_object(columns: list[str], record: str) -> str:
    arguments: list[str] = []
    for column in columns:
        escaped_key = column.replace("'", "''")
        arguments.extend((f"'{escaped_key}'", f"{record}.{_quote(column)}"))
    return f"json_object({', '.join(arguments)})"


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
