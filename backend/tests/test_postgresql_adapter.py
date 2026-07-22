import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.modules.platform.database_target import uses_postgresql
from app.modules.platform.postgresql import translate_sql


def test_local_profile_keeps_sqlite_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("PRINTORA_DATABASE_URL", raising=False)
    monkeypatch.delenv("PRINTORA_RUNTIME_PROFILE", raising=False)

    assert uses_postgresql() is False


def test_cloud_profile_rejects_sqlite_fallback(monkeypatch) -> None:
    monkeypatch.delenv("PRINTORA_DATABASE_URL", raising=False)
    monkeypatch.setenv("PRINTORA_RUNTIME_PROFILE", "cloud")

    with pytest.raises(RuntimeError, match="Perfil cloud exige"):
        uses_postgresql()


def test_invalid_database_url_never_falls_back_to_sqlite(monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATABASE_URL", "sqlite:///unsafe.db")

    with pytest.raises(RuntimeError, match="deve usar PostgreSQL"):
        uses_postgresql()


def test_cloud_process_does_not_load_sqlite_adapter() -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "PRINTORA_RUNTIME_PROFILE": "cloud",
            "PRINTORA_DATABASE_URL": "postgresql://example.invalid/printora_cloud",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import app.database; "
                "assert 'sqlite3' not in sys.modules; "
                "assert 'app.modules.platform.transition_outbox' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        cwd=Path(__file__).resolve().parents[1],
    )

    assert result.returncode == 0, result.stderr


def test_postgresql_adapter_rewrites_parameters_without_touching_literals() -> None:
    translated = translate_sql("SELECT '?' AS literal, name FROM users WHERE id = ?")

    assert translated == "SELECT '?' AS literal, name FROM users WHERE id = %s"


def test_postgresql_adapter_rewrites_insert_or_ignore() -> None:
    translated = translate_sql(
        "INSERT OR IGNORE INTO social_favorites (user_id, item_id) VALUES (?, ?);"
    )

    assert translated == (
        "INSERT INTO social_favorites (user_id, item_id) VALUES (%s, %s) "
        "ON CONFLICT DO NOTHING"
    )


def test_postgresql_adapter_rewrites_sqlite_datetime_modifiers() -> None:
    dynamic = translate_sql("SELECT * FROM jobs WHERE updated_at >= datetime('now', ?)")
    static = translate_sql(
        "SELECT * FROM jobs WHERE updated_at >= datetime('now', '-24 hours')"
    )

    assert dynamic.endswith("updated_at >= CAST(CURRENT_TIMESTAMP + (%s)::interval AS TEXT)")
    assert static.endswith(
        "updated_at >= CAST(CURRENT_TIMESTAMP + INTERVAL '-24 hours' AS TEXT)"
    )


def test_postgresql_adapter_compares_text_timestamps_with_text(monkeypatch) -> None:
    translated = translate_sql("SELECT * FROM sessions WHERE expires_at > CURRENT_TIMESTAMP")

    assert translated.endswith("expires_at > CAST(CURRENT_TIMESTAMP AS TEXT)")


def test_postgresql_adapter_rewrites_group_concat() -> None:
    translated = translate_sql("SELECT GROUP_CONCAT(DISTINCT c.name) FROM communities c")

    assert "STRING_AGG(DISTINCT c.name, ',')" in translated


def test_postgresql_adapter_rewrites_plain_group_concat() -> None:
    translated = translate_sql(
        "SELECT group_concat(file_kind) FROM social_library_files WHERE item_id = ?"
    )

    assert "STRING_AGG(file_kind, ',')" in translated
    assert "item_id = %s" in translated
