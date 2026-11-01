"""Exercise the shell policy with isolated systemd/PostgreSQL adapters."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "scripts/cloud/no-backup-policy.sh"
NAMES = ("backup", "wal-sync", "wal-retention", "restore-test", "recovery-monitor")


def setup_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    units = tmp_path / "units"
    units.mkdir()
    adapter = tmp_path / "bin"
    adapter.mkdir()
    systemctl = adapter / "systemctl"
    systemctl.write_text('''#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];root=pathlib.Path(os.environ['TEST_UNITS']);unit=args[1]
with open(os.environ['TEST_CALLS'],'a') as log: log.write(json.dumps(args)+'\\n')
p=root/unit
masked=p.is_symlink() and str(p.readlink())=='/dev/null'
if args[0]=='cat': sys.exit(1 if masked or not p.exists() else 0)
if args[0]=='is-enabled': print('masked' if masked else 'disabled');sys.exit(1)
if args[0]=='show': print(os.environ.get('TEST_ACTIVE','inactive'))
'''.replace("unit=args[1]", "unit=args[1] if len(args)>1 else ''"))
    systemctl.chmod(0o755)
    runuser = adapter / "runuser"
    runuser.write_text("#!/bin/sh\nprintf '%s\\n' \"${TEST_DB_STATE:-on:off:0:on:on:on:0:0}\"\n")
    runuser.chmod(0o755)
    monkeypatch.setenv("PATH", f"{adapter}:{os.environ['PATH']}")
    monkeypatch.setenv("TEST_UNITS", str(units))
    monkeypatch.setenv("TEST_CALLS", str(tmp_path / "calls"))
    return units


def run_policy(units: Path, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-euc", 'source "$1"; ' + command, "test", str(POLICY), str(units)],
        capture_output=True, text=True, check=False,
    )


def mask_all(units: Path) -> None:
    for name in NAMES:
        for suffix in ("timer", "service"):
            (units / f"printora-cloud-{name}.{suffix}").symlink_to("/dev/null")


def test_disables_jobs_idempotently_without_enabling_anything(tmp_path, monkeypatch):
    units = setup_policy(tmp_path, monkeypatch)
    for name in NAMES:
        for suffix in ("timer", "service"):
            (units / f"printora-cloud-{name}.{suffix}").write_text("[Unit]\n")
    for _ in range(2):
        result = run_policy(units, 'disable_recovery_units "$2"; validate_no_backup_policy')
        assert result.returncode == 0, result.stderr
        assert "backup_available=false" in result.stdout
    assert all(p.is_symlink() and p.readlink() == Path("/dev/null") for p in units.iterdir())
    calls = [json.loads(line) for line in (tmp_path / "calls").read_text().splitlines()]
    assert not any(call[0] in {"enable", "start", "unmask"} for call in calls)
    assert len([call for call in calls if call[0] == "stop"]) == 10


@pytest.mark.parametrize("state", [
    "on:on:120:on:on:on:0:0", "off:off:0:on:on:on:0:0",
    "on:off:0:off:on:on:0:0", "on:off:0:on:off:on:0:0",
    "on:off:0:on:on:off:0:0", "on:off:0:on:on:on:1:0",
    "on:off:0:on:on:on:0:1", "on:off:120:on:on:on:0:0",
])
def test_rejects_unsafe_database_state(tmp_path, monkeypatch, state):
    units = setup_policy(tmp_path, monkeypatch)
    mask_all(units)
    monkeypatch.setenv("TEST_DB_STATE", state)
    assert run_policy(units, "validate_no_backup_policy").returncode != 0


def test_rejects_missing_mask_and_running_masked_job(tmp_path, monkeypatch):
    units = setup_policy(tmp_path, monkeypatch)
    assert run_policy(units, "validate_no_backup_policy").returncode != 0
    mask_all(units)
    monkeypatch.setenv("TEST_ACTIVE", "active")
    assert run_policy(units, "validate_no_backup_policy").returncode != 0


def test_deploy_and_bootstrap_do_not_replace_recovery_masks():
    for name in ("deploy-blue-green.sh", "bootstrap-blue-green.sh"):
        script = (ROOT / "scripts/cloud" / name).read_text()
        assert "disable_recovery_units" in script
        for recovery in NAMES:
            assert f"enable --now printora-cloud-{recovery}" not in script
            assert f'/etc/systemd/system/printora-cloud-{recovery}.timer' not in script
            assert f'/etc/systemd/system/printora-cloud-{recovery}.service' not in script


def test_preserved_schema_compares_applied_sql_and_grants(tmp_path):
    source, candidate = tmp_path / "source", tmp_path / "candidate"
    for directory in (source, candidate):
        (directory / "backend/sql/postgresql/admin").mkdir(parents=True)
        (directory / "scripts/cloud").mkdir(parents=True)
        (directory / "backend/sql/postgresql/001_baseline.sql").write_text("SELECT 1;\n")
        (directory / "scripts/cloud/postgresql-runtime-permissions.sql").write_text("SELECT 2;\n")
    def compare():
        return subprocess.run(["bash", "-c", 'source "$1"; postgresql_schema_matches "$2" "$3"',
            "test", str(ROOT / "scripts/cloud/common.sh"), str(source), str(candidate)],
            capture_output=True, check=False).returncode
    (candidate / "backend/sql/postgresql/admin/manual.sql").write_text("ALTER SYSTEM SET archive_mode = off;")
    assert compare() == 0
    (candidate / "backend/sql/postgresql/002_change.sql").write_text("SELECT 3;")
    assert compare() != 0
    (candidate / "backend/sql/postgresql/002_change.sql").unlink()
    (candidate / "backend/sql/postgresql/001_baseline.sql").write_text("SELECT 4;")
    assert compare() != 0
    (candidate / "backend/sql/postgresql/001_baseline.sql").write_text("SELECT 1;\n")
    (candidate / "scripts/cloud/postgresql-runtime-permissions.sql").write_text("SELECT 5;")
    assert compare() != 0
