import sqlite3
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_legacy_schema_compatibility(connection)
        for sql_file in sorted(SQL_DIR.glob("*.sql")):
            connection.executescript(sql_file.read_text())


def connect_database(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_legacy_schema_compatibility(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "app_events"):
        return
    if not _column_exists(connection, "app_events", "printer_id"):
        connection.execute("ALTER TABLE app_events ADD COLUMN printer_id INTEGER")


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)
