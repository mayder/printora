import json
import sqlite3

from app.database import initialize_database
from app.modules.platform.transition_outbox import (
    OUTBOX_TABLE,
    ensure_transition_outbox,
    transition_watermark,
)


def test_outbox_captures_insert_update_delete_atomically(tmp_path):
    database_path = tmp_path / "transition.db"
    initialize_database(database_path)
    connection = sqlite3.connect(database_path)
    try:
        ensure_transition_outbox(connection)
        connection.execute(
            "INSERT INTO printers (name, moonraker_url) VALUES (?, ?)",
            ("transition-test", "http://127.0.0.1:7125"),
        )
        connection.execute(
            "UPDATE printers SET notes = ? WHERE name = ?",
            ("two", "transition-test"),
        )
        connection.execute("DELETE FROM printers WHERE name = ?", ("transition-test",))
        rows = connection.execute(
            f"""
            SELECT operation, primary_key_json, row_json
            FROM {OUTBOX_TABLE}
            WHERE table_name = 'printers'
            ORDER BY id
            """
        ).fetchall()
        assert [row[0] for row in rows] == ["insert", "update", "delete"]
        assert json.loads(rows[0][1]) == {"id": 1}
        assert json.loads(rows[1][2])["notes"] == "two"
        assert json.loads(rows[2][2])["notes"] == "two"
        assert transition_watermark(connection) >= 3
    finally:
        connection.close()


def test_outbox_rolls_back_with_business_transaction(tmp_path):
    database_path = tmp_path / "rollback.db"
    initialize_database(database_path)
    connection = sqlite3.connect(database_path)
    try:
        ensure_transition_outbox(connection)
        connection.execute(
            "INSERT INTO printers (name, moonraker_url) VALUES (?, ?)",
            ("rolled-back", "http://127.0.0.1:7125"),
        )
        connection.rollback()
        business_count = connection.execute(
            "SELECT COUNT(*) FROM printers WHERE name = 'rolled-back'"
        ).fetchone()[0]
        outbox_count = connection.execute(
            f"SELECT COUNT(*) FROM {OUTBOX_TABLE} WHERE table_name = 'printers'"
        ).fetchone()[0]
        assert business_count == 0
        assert outbox_count == 0
    finally:
        connection.close()


def test_initialization_enables_outbox_only_by_explicit_flag(tmp_path, monkeypatch):
    database_path = tmp_path / "enabled.db"
    monkeypatch.setenv("PRINTORA_TRANSITION_OUTBOX_ENABLED", "1")
    initialize_database(database_path)
    connection = sqlite3.connect(database_path)
    try:
        trigger_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_schema
            WHERE type = 'trigger' AND name LIKE 'printora_pg_transition_%'
            """
        ).fetchone()[0]
        assert trigger_count > 0
    finally:
        connection.close()
