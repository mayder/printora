#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


WAL_PATTERN = re.compile(r"^[0-9A-F]{24}$")
STATE_DIR = Path(os.environ.get("PRINTORA_RECOVERY_STATE_DIR", "/var/lib/printora-cloud/recovery"))
ARCHIVE_DIR = Path(
    os.environ.get(
        "PRINTORA_WAL_ARCHIVE_DIR",
        "/var/lib/postgresql/16/printora-wal-archive",
    )
)
MAX_SYNC_AGE = int(os.environ.get("PRINTORA_RECOVERY_MAX_SYNC_AGE_SECONDS", "210"))
MAX_FULL_BACKUP_AGE = int(
    os.environ.get("PRINTORA_RECOVERY_MAX_FULL_BACKUP_AGE_SECONDS", "90000")
)
MAX_RESTORE_AGE = int(
    os.environ.get("PRINTORA_RECOVERY_MAX_RESTORE_AGE_SECONDS", "648000")
)
CONFIGURED_RPO_SECONDS = 120 + 60 + 110
DISK_WARNING_PERCENT = 15
DISK_FAILURE_PERCENT = 10


def run(*command: str) -> str:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()


def parse_time(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def read_state(name: str) -> dict[str, Any]:
    payload = json.loads((STATE_DIR / name).read_text())
    if payload.get("status") != "passed":
        raise ValueError(f"{name}:status")
    return payload


def latest_local_wal() -> str:
    candidates = [
        item
        for item in ARCHIVE_DIR.iterdir()
        if item.is_file() and WAL_PATTERN.fullmatch(item.name)
    ]
    if not candidates:
        raise ValueError("wal_local_absent")
    return max(candidates, key=lambda item: item.stat().st_mtime).name


def age_seconds(payload: dict[str, Any], field: str, now: float) -> int:
    return max(0, int(now - parse_time(str(payload[field]))))


def check_unit(name: str) -> None:
    if run("systemctl", "is-active", name) != "active":
        raise ValueError(f"unit:{name}")


def collect() -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {
        "alert_owner": "operations",
        "configured_physical_rpo_seconds": CONFIGURED_RPO_SECONDS,
    }
    now = time.time()

    for unit in (
        "printora-cloud-wal-sync.timer",
        "printora-cloud-restore-test.timer",
        "printora-cloud-recovery-monitor.timer",
        "printora-cloud-backup.timer",
        "postgresql@16-printora.service",
    ):
        try:
            check_unit(unit)
        except (OSError, subprocess.SubprocessError, ValueError):
            failures.append(f"unit_inactive:{unit}")

    try:
        database_state = run(
            "runuser",
            "-u",
            "postgres",
            "--",
            "psql",
            "-p",
            "5433",
            "-d",
            "printora_cloud",
            "-X",
            "-Atqc",
            "SELECT extract(epoch FROM current_setting('archive_timeout')::interval)::int"
            " || ':' || failed_count FROM pg_stat_archiver",
        )
        archive_timeout, failed_count = (int(value) for value in database_state.split(":"))
        report["archive_timeout_seconds"] = archive_timeout
        report["archive_failed_count"] = failed_count
        if archive_timeout > 120:
            failures.append("archive_timeout")
        if failed_count:
            failures.append("archive_failures")
    except (OSError, subprocess.SubprocessError, ValueError):
        failures.append("postgresql_archive_state")

    try:
        wal_state = read_state("wal-sync.json")
        sync_age = age_seconds(wal_state, "checked_at", now)
        report["wal_sync_age_seconds"] = sync_age
        report["wal_sync_duration_seconds"] = int(wal_state["duration_seconds"])
        report["wal_files"] = int(wal_state["wal_file_count"])
        report["wal_archive_bytes"] = int(wal_state["archive_bytes"])
        report["wal_external_snapshots"] = int(wal_state["external_snapshot_count"])
        report["wal_external_current"] = wal_state["uploaded_wal"] == latest_local_wal()
        report["wal_external_within_alert_window"] = (
            report["wal_external_current"] or sync_age <= MAX_SYNC_AGE
        )
        if sync_age > MAX_SYNC_AGE:
            failures.append("wal_sync_late")
        if not report["wal_external_within_alert_window"]:
            failures.append("wal_external_behind")
        if report["wal_sync_duration_seconds"] > 110:
            failures.append("wal_sync_duration")
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        failures.append("wal_sync_state")

    for filename, field, maximum, report_key, failure in (
        (
            "full-backup.json",
            "completed_at",
            MAX_FULL_BACKUP_AGE,
            "full_backup_age_seconds",
            "full_backup_late",
        ),
        (
            "restore-test.json",
            "completed_at",
            MAX_RESTORE_AGE,
            "restore_test_age_seconds",
            "restore_test_late",
        ),
    ):
        try:
            value = age_seconds(read_state(filename), field, now)
            report[report_key] = value
            if value > maximum:
                failures.append(failure)
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            failures.append(f"{failure}_state")

    try:
        usage = shutil.disk_usage(STATE_DIR)
        report["state_disk_free_percent"] = round(usage.free * 100 / usage.total, 2)
        if report["state_disk_free_percent"] < DISK_WARNING_PERCENT:
            warnings.append("disk_capacity")
        if report["state_disk_free_percent"] < DISK_FAILURE_PERCENT:
            failures.append("disk_capacity")
    except OSError:
        failures.append("disk_capacity_state")

    if CONFIGURED_RPO_SECONDS > 300:
        failures.append("configured_rpo")
    report["failures"] = sorted(set(failures))
    report["warnings"] = sorted(set(warnings))
    report["status"] = "passed" if not failures else "failed"
    return report, failures


def main() -> int:
    report, failures = collect()
    print(json.dumps(report, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
