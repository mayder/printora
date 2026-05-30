import sqlite3
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.database as database_module
from app.config import _default_data_dir, get_settings
from app.database import DatabaseSchemaError, initialize_database
from app.main import app


def test_initialize_database_registers_sql_scripts_on_new_database(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"

    initialize_database(database_path)

    expected_scripts = _sql_script_count()
    with sqlite3.connect(database_path) as connection:
        assert _table_exists(connection, "schema_versions")
        assert _table_exists(connection, "app_version")
        assert _table_exists(connection, "schema_integrity_checks")
        assert _count_rows(connection, "schema_versions") == expected_scripts
        assert _count_rows(connection, "app_version") == 1
        app_version = connection.execute(
            "SELECT app_name, version, schema_revision FROM app_version WHERE id = 1"
        ).fetchone()
        assert app_version == ("Printora", app.version, expected_scripts)


def test_initialize_database_ignores_macos_appledouble_sql_files(tmp_path: Path, monkeypatch) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    for sql_file in database_module.SQL_DIR.glob("[0-9]*.sql"):
        shutil.copy2(sql_file, sql_dir / sql_file.name)
    (sql_dir / "._018_app_update_runs.sql").write_bytes(b"\x00\x05bad appledouble")
    monkeypatch.setattr(database_module, "SQL_DIR", sql_dir)

    database_path = tmp_path / "printora.db"
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        scripts = [
            row[0]
            for row in connection.execute(
                "SELECT script_name FROM schema_versions ORDER BY execution_order"
            ).fetchall()
        ]
    assert "._018_app_update_runs.sql" not in scripts
    assert scripts[-1] == "021_setup_ssh_runs.sql"


def test_initialize_database_is_idempotent_and_preserves_existing_data(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO printers (name, moonraker_url, location, notes)
            VALUES ('Voron 2.4', 'http://127.0.0.1:7125', 'Lab', 'preservar')
            """
        )
        original_versions = _count_rows(connection, "schema_versions")

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        assert _count_rows(connection, "schema_versions") == original_versions
        assert _count_rows(connection, "app_version") == 1
        assert connection.execute("SELECT COUNT(*) FROM printers").fetchone()[0] == 1
        printer = connection.execute("SELECT name, notes FROM printers").fetchone()
        assert printer == ("Voron 2.4", "preservar")
    assert _schema_backups(tmp_path) == []


def test_initialize_database_updates_existing_database_without_data_loss(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    _create_legacy_database(database_path)

    initialize_database(database_path)

    backups = _schema_backups(tmp_path)
    expected_scripts = _sql_script_count()
    with sqlite3.connect(database_path) as connection:
        assert backups
        assert _count_rows(connection, "schema_versions") == expected_scripts
        assert _count_rows(connection, "app_version") == 1
        assert _column_exists(connection, "app_events", "printer_id")
        assert connection.execute("SELECT COUNT(*) FROM printers").fetchone()[0] == 1
        event = connection.execute("SELECT event_type, payload_json FROM app_events").fetchone()
        assert event == ("legacy", "{}")

    initialize_database(database_path)

    assert len(_schema_backups(tmp_path)) == len(backups)


def test_initialize_database_does_not_create_backup_for_new_database(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"

    initialize_database(database_path)

    assert _schema_backups(tmp_path) == []


def test_initialize_database_restores_original_database_when_sql_application_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    shutil.copy2(
        database_module.SQL_DIR / database_module.VERSIONING_SCRIPT,
        sql_dir / database_module.VERSIONING_SCRIPT,
    )
    shutil.copy2(
        database_module.SQL_DIR / "015_schema_integrity_checks.sql",
        sql_dir / "015_schema_integrity_checks.sql",
    )
    (sql_dir / "001_base.sql").write_text(
        """
        CREATE TABLE IF NOT EXISTS keep_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        );
        """,
    )
    monkeypatch.setattr(database_module, "SQL_DIR", sql_dir)

    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute("INSERT INTO keep_rows (value) VALUES ('original')")

    (sql_dir / "002_failing_schema.sql").write_text(
        """
        CREATE TABLE partial_table (
            id INTEGER PRIMARY KEY
        );
        INSERT INTO missing_table (id) VALUES (1);
        """,
    )

    with pytest.raises(DatabaseSchemaError):
        initialize_database(database_path)

    backups = _schema_backups(tmp_path)
    assert len(backups) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT value FROM keep_rows").fetchone() == ("original",)
        assert not _table_exists(connection, "partial_table")
        assert _count_rows(connection, "schema_versions") == 3


def test_system_version_endpoint_is_read_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/api/system/version")
        assert response.status_code == 200
        payload = response.json()
        assert payload["app_name"] == "Printora"
        assert payload["version"] == app.version
        assert payload["data_dir"] == str(tmp_path)
        assert payload["database_path"] == str(tmp_path / "printora.db")
        assert payload["schema_revision"] == _sql_script_count()
        assert payload["schema_current"]["revision"] == _sql_script_count()
        assert payload["schema_current"]["latest_script"] == "021_setup_ssh_runs.sql"
        assert payload["schema_scripts_applied"] == _sql_script_count()
        assert len(payload["applied_sql_scripts"]) == _sql_script_count()
        assert any(
            script["script_name"] == "018_app_update_runs.sql"
            for script in payload["applied_sql_scripts"]
        )
        assert payload["applied_sql_scripts"][0]["script_name"] == "000_schema_versioning.sql"
        assert set(payload["applied_sql_scripts"][0]) == {
            "script_name",
            "execution_order",
            "applied_at",
        }
        assert payload["latest_schema_script"].endswith(".sql")
        assert payload["latest_integrity_status"] == "ok"
        assert payload["latest_integrity_result"] == ["ok"]
        assert payload["latest_validation"]["status"] == "ok"
        assert payload["latest_validation"]["result"] == ["ok"]
        assert "printers" not in payload
        assert "payload_json" not in str(payload)
    finally:
        get_settings.cache_clear()


def test_default_data_dir_uses_macos_application_support(monkeypatch) -> None:
    monkeypatch.setattr("app.config.platform.system", lambda: "Darwin")

    assert _default_data_dir() == Path.home() / "Library/Application Support/Printora"


def test_initialize_database_records_successful_integrity_check(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        record = connection.execute(
            """
            SELECT schema_revision, status, result_json
            FROM schema_integrity_checks
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        assert record == (_sql_script_count(), "ok", '["ok"]')


def test_initialize_database_blocks_completion_when_integrity_check_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "printora.db"
    monkeypatch.setattr(database_module, "_run_integrity_check", lambda connection: ["simulated corruption"])

    with pytest.raises(DatabaseSchemaError, match="simulated corruption"):
        initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        record = connection.execute(
            """
            SELECT schema_revision, status, result_json
            FROM schema_integrity_checks
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        assert record == (_sql_script_count(), "failed", '["simulated corruption"]')


def _create_legacy_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE printers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                moonraker_url TEXT NOT NULL,
                host_audit_mode TEXT NOT NULL DEFAULT 'disabled',
                host_audit_ssh_target TEXT,
                location TEXT,
                notes TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            );

            CREATE TABLE app_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            INSERT INTO printers (name, moonraker_url)
            VALUES ('Legada', 'http://127.0.0.1:7125');

            INSERT INTO app_events (event_type, payload_json)
            VALUES ('legacy', '{}');
            """
        )


def _sql_script_count() -> int:
    return len(list(database_module.SQL_DIR.glob("*.sql")))


def _schema_backups(data_dir: Path) -> list[Path]:
    return sorted(data_dir.glob("printora.*.before-schema.db"))


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def _count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
