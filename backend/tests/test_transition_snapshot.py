import importlib.util
import sqlite3
from pathlib import Path

import pytest

from app.database import initialize_database


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/cloud/create-sqlite-transition-snapshot.py"
SPEC = importlib.util.spec_from_file_location("transition_snapshot", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_transition_snapshot_is_consistent_and_carries_watermark(tmp_path, monkeypatch):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    monkeypatch.setenv("PRINTORA_TRANSITION_OUTBOX_ENABLED", "1")
    initialize_database(source)
    connection = sqlite3.connect(source)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "INSERT INTO printers (name, moonraker_url) VALUES (?, ?)",
            ("snapshot", "http://127.0.0.1:7125"),
        )
        connection.commit()
    finally:
        connection.close()

    report = MODULE.create_snapshot(source, target)

    assert report["integrity"] == "ok"
    assert report["schema_revision"] == 74
    assert report["watermark"] >= 1
    copied = sqlite3.connect(target)
    try:
        assert copied.execute("SELECT name FROM printers").fetchone()[0] == "snapshot"
    finally:
        copied.close()


def test_transition_snapshot_refuses_existing_target(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    source.touch()
    target.touch()

    with pytest.raises(RuntimeError, match="Destino já existe"):
        MODULE.create_snapshot(source, target)
