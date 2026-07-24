from __future__ import annotations

import importlib.util
import json
import time
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType


ROOT_DIR = Path(__file__).resolve().parents[2]


def load_module() -> ModuleType:
    path = ROOT_DIR / "scripts/cloud/recovery-readiness.py"
    spec = importlib.util.spec_from_file_location("recovery_readiness", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_state(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps({"status": "passed", **payload}))


def configure_healthy_state(module: ModuleType, tmp_path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state_dir = tmp_path / "state"
    archive_dir = tmp_path / "archive"
    state_dir.mkdir()
    archive_dir.mkdir()
    wal = "000000010000000000000001"
    (archive_dir / wal).write_bytes(b"wal")
    write_state(
        state_dir / "wal-sync.json",
        {
            "archive_bytes": 3,
            "checked_at": now,
            "duration_seconds": 4,
            "uploaded_at": now,
            "uploaded_wal": wal,
            "wal_file_count": 1,
        },
    )
    write_state(state_dir / "full-backup.json", {"completed_at": now})
    write_state(state_dir / "restore-test.json", {"completed_at": now})
    module.STATE_DIR = state_dir
    module.ARCHIVE_DIR = archive_dir
    module.run = lambda *command: (
        "120:0" if command[0] == "runuser" else "active"
    )
    usage = namedtuple("usage", "total used free")
    module.shutil.disk_usage = lambda _path: usage(100, 50, 50)


def test_recovery_readiness_passes_with_current_external_wal(tmp_path: Path) -> None:
    module = load_module()
    configure_healthy_state(module, tmp_path)

    report, failures = module.collect()

    assert failures == []
    assert report["status"] == "passed"
    assert report["wal_external_current"] is True
    assert report["configured_physical_rpo_seconds"] == 290


def test_recovery_readiness_fails_before_physical_rpo_breach(tmp_path: Path) -> None:
    module = load_module()
    configure_healthy_state(module, tmp_path)
    state_path = module.STATE_DIR / "wal-sync.json"
    state = json.loads(state_path.read_text())
    state["checked_at"] = datetime.fromtimestamp(
        time.time() - module.MAX_SYNC_AGE - 1,
        timezone.utc,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    state_path.write_text(json.dumps(state))

    report, failures = module.collect()

    assert "wal_sync_late" in failures
    assert report["status"] == "failed"
