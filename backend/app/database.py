import sqlite3
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for sql_file in sorted(SQL_DIR.glob("*.sql")):
            connection.executescript(sql_file.read_text())


def connect_database(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
