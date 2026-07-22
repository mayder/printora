import sqlite3
import hashlib
import json
import time
import tomllib
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path
from datetime import datetime, timezone
from importlib import metadata

from app.modules.platform.database_target import require_postgresql_url, uses_postgresql
from app.modules.platform.postgresql import PostgreSQLConnection
from app.modules.platform.transition_outbox import (
    ensure_transition_outbox,
    transition_outbox_enabled,
)

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
POSTGRESQL_SQL_DIR = SQL_DIR / "postgresql"
APP_NAME = "Printora"
VERSIONING_SCRIPT = "000_schema_versioning.sql"
SQLITE_TIMEOUT_SECONDS = 60.0
SQLITE_BUSY_TIMEOUT_MS = int(SQLITE_TIMEOUT_SECONDS * 1000)


class DatabaseSchemaError(RuntimeError):
    pass


def initialize_database(database_path: Path) -> None:
    if uses_postgresql():
        _initialize_postgresql()
        return
    database_path.parent.mkdir(parents=True, exist_ok=True)
    sql_files = sorted(SQL_DIR.glob("[0-9]*.sql"))
    _repair_optional_materialization_state(database_path)
    pending_files = _pending_sql_files(database_path, sql_files)
    backup_path: Path | None = None
    if database_path.exists() and pending_files:
        backup_path = _backup_database(database_path)

    connection = _connect_sqlite(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_versioning_tables(connection)
        _ensure_legacy_schema_compatibility(connection)
        applied_scripts = _applied_scripts(connection)
        for execution_order, sql_file in enumerate(sql_files, start=1):
            checksum = _sql_checksum(sql_file)
            applied_checksum = applied_scripts.get(sql_file.name)
            if applied_checksum == checksum:
                continue
            if applied_checksum is not None:
                raise DatabaseSchemaError(
                    f"Script SQL já aplicado com checksum diferente: {sql_file.name}"
                )
            connection.executescript(sql_file.read_text())
            connection.execute(
                """
                INSERT INTO schema_versions (script_name, checksum_sha256, execution_order)
                VALUES (?, ?, ?)
                """,
                (sql_file.name, checksum, execution_order),
            )
        schema_revision = len(sql_files)
        _upsert_app_version(connection, schema_revision)
        if transition_outbox_enabled():
            ensure_transition_outbox(connection)
        # A verificação integral pode varrer vários gigabytes. Ela pertence ao
        # gate de mudança de schema; reinícios e probes devem permanecer rápidos.
        if pending_files:
            _validate_database_integrity(connection, schema_revision)
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if backup_path is not None:
            _restore_database_backup(backup_path, database_path)
        if isinstance(exc, DatabaseSchemaError):
            raise
        raise DatabaseSchemaError(f"Falha ao aplicar schema SQLite: {exc}") from exc
    finally:
        connection.close()


@contextmanager
def connect_database(database_path: Path) -> Iterator[sqlite3.Connection | PostgreSQLConnection]:
    if uses_postgresql():
        connection = PostgreSQLConnection(require_postgresql_url())
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return
    connection = _connect_sqlite(database_path)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _initialize_postgresql() -> None:
    sql_files = sorted(SQL_DIR.glob("[0-9]*.sql"))
    connection = PostgreSQLConnection(require_postgresql_url())
    try:
        app_version_table = connection.execute(
            "SELECT to_regclass('public.app_version') AS table_name"
        ).fetchone()
        if app_version_table is None or app_version_table["table_name"] is None:
            baseline = POSTGRESQL_SQL_DIR / "001_baseline.sql"
            if not baseline.is_file():
                raise DatabaseSchemaError(f"Baseline PostgreSQL obrigatório não encontrado: {baseline.name}")
            connection.execute_script(baseline.read_text(encoding="utf-8"))
        for postgresql_script in sorted(POSTGRESQL_SQL_DIR.glob("[0-9]*.sql")):
            if postgresql_script.name == "001_baseline.sql":
                continue
            connection.execute_script(postgresql_script.read_text(encoding="utf-8"))
        for execution_order, sql_file in enumerate(sql_files, start=1):
            connection.execute(
                """
                INSERT INTO schema_versions (script_name, checksum_sha256, execution_order)
                VALUES (?, ?, ?)
                ON CONFLICT (script_name) DO NOTHING
                """,
                (sql_file.name, _sql_checksum(sql_file), execution_order),
            )
        applied_scripts = _applied_scripts(connection)
        for sql_file in sql_files:
            applied_checksum = applied_scripts.get(sql_file.name)
            expected_checksum = _sql_checksum(sql_file)
            if applied_checksum != expected_checksum:
                raise DatabaseSchemaError(
                    f"Schema PostgreSQL divergente em {sql_file.name}: "
                    f"esperado {expected_checksum}, recebido {applied_checksum or 'ausente'}"
                )
        _upsert_app_version(connection, len(sql_files))
        connection.execute("SELECT 1 FROM app_version WHERE id = 1").fetchone()
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, DatabaseSchemaError):
            raise
        raise DatabaseSchemaError(f"Falha ao validar schema PostgreSQL: {exc}") from exc
    finally:
        connection.close()


def get_database_version_info(database_path: Path, data_dir: Path | None = None) -> dict[str, object]:
    with connect_database(database_path) as connection:
        app_version = connection.execute(
            """
            SELECT app_name, version, schema_revision, updated_at
            FROM app_version
            WHERE id = 1
            """
        ).fetchone()
        applied_scripts = connection.execute(
            """
            SELECT script_name, execution_order, applied_at
            FROM schema_versions
            ORDER BY execution_order, script_name
            """
        ).fetchall()
        latest_schema = connection.execute(
            """
            SELECT script_name, execution_order, applied_at
            FROM schema_versions
            ORDER BY execution_order DESC, script_name DESC
            LIMIT 1
            """
        ).fetchone()
        latest_integrity = connection.execute(
            """
            SELECT status, result_json, checked_at
            FROM schema_integrity_checks
            ORDER BY checked_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        applied_count = len(applied_scripts)
        schema_revision = app_version["schema_revision"] if app_version else 0
        latest_validation = (
            {
                "status": latest_integrity["status"],
                "result": json.loads(latest_integrity["result_json"]),
                "checked_at": latest_integrity["checked_at"],
            }
            if latest_integrity
            else None
        )
        return {
            "app_name": app_version["app_name"] if app_version else APP_NAME,
            "version": app_version["version"] if app_version else _installed_app_version(),
            "data_dir": str(data_dir or database_path.parent),
            "database_path": str(database_path),
            "schema_revision": schema_revision,
            "schema_current": {
                "revision": schema_revision,
                "latest_script": latest_schema["script_name"] if latest_schema else None,
                "latest_execution_order": latest_schema["execution_order"] if latest_schema else None,
                "latest_applied_at": latest_schema["applied_at"] if latest_schema else None,
            },
            "schema_scripts_applied": applied_count,
            "applied_sql_scripts": [
                {
                    "script_name": row["script_name"],
                    "execution_order": row["execution_order"],
                    "applied_at": row["applied_at"],
                }
                for row in applied_scripts
            ],
            "latest_schema_script": latest_schema["script_name"] if latest_schema else None,
            "latest_schema_applied_at": latest_schema["applied_at"] if latest_schema else None,
            "latest_integrity_status": latest_integrity["status"] if latest_integrity else None,
            "latest_integrity_result": json.loads(latest_integrity["result_json"]) if latest_integrity else None,
            "latest_integrity_checked_at": latest_integrity["checked_at"] if latest_integrity else None,
            "latest_validation": latest_validation,
        }


def get_public_database_version_info(database_path: Path) -> dict[str, object]:
    with connect_database(database_path) as connection:
        app_version = connection.execute(
            """
            SELECT app_name, version, schema_revision
            FROM app_version
            WHERE id = 1
            """
        ).fetchone()
        latest_schema = connection.execute(
            """
            SELECT script_name, applied_at
            FROM schema_versions
            ORDER BY execution_order DESC, script_name DESC
            LIMIT 1
            """
        ).fetchone()
        latest_integrity = connection.execute(
            """
            SELECT status, checked_at
            FROM schema_integrity_checks
            ORDER BY checked_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        schema_revision = app_version["schema_revision"] if app_version else 0
        return {
            "app_name": app_version["app_name"] if app_version else APP_NAME,
            "version": app_version["version"] if app_version else _installed_app_version(),
            "schema_revision": schema_revision,
            "schema_current": {
                "revision": schema_revision,
                "latest_script": latest_schema["script_name"] if latest_schema else None,
                "latest_applied_at": latest_schema["applied_at"] if latest_schema else None,
            },
            "latest_integrity_status": latest_integrity["status"] if latest_integrity else None,
            "latest_integrity_checked_at": latest_integrity["checked_at"] if latest_integrity else None,
        }


def _ensure_legacy_schema_compatibility(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "app_events"):
        return
    if not _column_exists(connection, "app_events", "printer_id"):
        connection.execute("ALTER TABLE app_events ADD COLUMN printer_id INTEGER")


def _ensure_versioning_tables(connection: sqlite3.Connection) -> None:
    versioning_script = SQL_DIR / VERSIONING_SCRIPT
    if not versioning_script.is_file():
        raise DatabaseSchemaError(f"Script SQL obrigatório não encontrado: {VERSIONING_SCRIPT}")
    connection.executescript(versioning_script.read_text())


def _pending_sql_files(database_path: Path, sql_files: list[Path]) -> list[Path]:
    if not database_path.exists():
        return sql_files
    connection: sqlite3.Connection | None = None
    try:
        connection = _connect_sqlite(f"file:{database_path}?mode=ro", uri=True)
        if not _table_exists(connection, "schema_versions"):
            return sql_files
        applied = _applied_scripts(connection)
        pending: list[Path] = []
        for sql_file in sql_files:
            checksum = _sql_checksum(sql_file)
            applied_checksum = applied.get(sql_file.name)
            if applied_checksum is None:
                pending.append(sql_file)
            elif applied_checksum != checksum:
                raise DatabaseSchemaError(
                    f"Script SQL já aplicado com checksum diferente: {sql_file.name}"
                )
        return pending
    except sqlite3.DatabaseError as exc:
        raise DatabaseSchemaError(f"Não foi possível ler o banco SQLite existente: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def _applied_scripts(connection: sqlite3.Connection | PostgreSQLConnection) -> dict[str, str]:
    if not _table_exists(connection, "schema_versions"):
        return {}
    rows = connection.execute("SELECT script_name, checksum_sha256 FROM schema_versions").fetchall()
    return {
        str(row["script_name"] if hasattr(row, "keys") else row[0]): str(
            row["checksum_sha256"] if hasattr(row, "keys") else row[1]
        )
        for row in rows
    }


def _backup_database(database_path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = database_path.parent / f"{database_path.stem}.{timestamp}.before-schema{database_path.suffix}"
    source = _connect_sqlite(f"file:{database_path}?mode=ro", uri=True)
    target = sqlite3.connect(backup_path)
    try:
        source.backup(target, pages=4096, sleep=0.02)
    finally:
        target.close()
        source.close()
    return backup_path


def _restore_database_backup(backup_path: Path, database_path: Path) -> None:
    source = _connect_sqlite(f"file:{backup_path}?mode=ro", uri=True)
    target = sqlite3.connect(database_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def _repair_optional_materialization_state(database_path: Path) -> None:
    if not database_path.exists():
        return
    connection: sqlite3.Connection | None = None
    try:
        connection = _connect_sqlite(database_path)
        connection.execute("SELECT COUNT(*) FROM social_materialization_state").fetchone()
    except sqlite3.DatabaseError as exc:
        message = str(exc)
        if "social_materialization_state" not in message or "malformed database schema" not in message:
            return
        if connection is not None:
            connection.close()
            connection = None
        _backup_database(database_path)
        _remove_corrupt_materialization_state(database_path)
    finally:
        if connection is not None:
            connection.close()


def _remove_corrupt_materialization_state(database_path: Path) -> None:
    last_error: sqlite3.OperationalError | None = None
    for attempt in range(1, 5):
        connection: sqlite3.Connection | None = None
        try:
            connection = _connect_sqlite(database_path)
            connection.execute("PRAGMA writable_schema = ON")
            connection.execute(
                """
                DELETE FROM sqlite_schema
                WHERE name = 'social_materialization_state'
                   OR tbl_name = 'social_materialization_state'
                """
            )
            connection.execute("PRAGMA writable_schema = OFF")
            connection.execute(
                "DELETE FROM schema_versions WHERE script_name = '056_social_materialization_state.sql'"
            )
            connection.commit()
            connection.execute("VACUUM")
            return
        except sqlite3.OperationalError as exc:
            last_error = exc
            if "locked" not in str(exc).lower() or attempt == 4:
                raise
            time.sleep(5)
        finally:
            if connection is not None:
                connection.close()
    if last_error is not None:
        raise last_error


def _connect_sqlite(database_path: Path | str, *, uri: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=SQLITE_TIMEOUT_SECONDS, uri=uri)
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    return connection


def _upsert_app_version(
    connection: sqlite3.Connection | PostgreSQLConnection,
    schema_revision: int,
) -> None:
    version = _installed_app_version()
    updated_at = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """
        INSERT INTO app_version (id, app_name, version, schema_revision)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            app_name = excluded.app_name,
            version = excluded.version,
            schema_revision = excluded.schema_revision,
            updated_at = CASE
                WHEN app_version.app_name != excluded.app_name
                  OR app_version.version != excluded.version
                  OR app_version.schema_revision != excluded.schema_revision
                THEN ?
                ELSE app_version.updated_at
            END
        """,
        (APP_NAME, version, schema_revision, updated_at),
    )


def _installed_app_version() -> str:
    pyproject_version = _local_pyproject_version()
    if pyproject_version:
        return pyproject_version
    try:
        return metadata.version("printora-backend")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def _local_pyproject_version() -> str | None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject_path.is_file():
        return None
    try:
        payload = tomllib.loads(pyproject_path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return None
    project = payload.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    return str(version) if version else None


def _validate_database_integrity(connection: sqlite3.Connection, schema_revision: int) -> None:
    result = _run_integrity_check(connection)
    status = "ok" if result == ["ok"] else "failed"
    connection.execute(
        """
        INSERT INTO schema_integrity_checks (schema_revision, status, result_json)
        VALUES (?, ?, ?)
        """,
        (schema_revision, status, json.dumps(result, ensure_ascii=False)),
    )
    if status != "ok":
        connection.commit()
        raise DatabaseSchemaError(f"Falha na integridade do SQLite: {'; '.join(result)}")


def _run_integrity_check(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("PRAGMA integrity_check").fetchall()
    return [str(row[0]) for row in rows] if rows else ["integrity_check não retornou resultado"]


def _sql_checksum(sql_file: Path) -> str:
    return hashlib.sha256(sql_file.read_bytes()).hexdigest()


def _table_exists(
    connection: sqlite3.Connection | PostgreSQLConnection,
    table_name: str,
) -> bool:
    if isinstance(connection, PostgreSQLConnection):
        row = connection.execute(
            "SELECT to_regclass(?) AS table_name",
            (f"public.{table_name}",),
        ).fetchone()
        return row is not None and row["table_name"] is not None
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)
