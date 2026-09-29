#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row


SERVICE_UNITS = (
    "postgresql@16-printora.service",
    "redis-printora.service",
    "minio-printora.service",
    "printora-cloud@replica.service",
    "printora-cloud-worker@outbox.service",
    "printora-cloud-worker@critical.service",
    "printora-cloud-worker@default.service",
    "printora-cloud-worker@bulk.service",
    "printora-cloud-intelligence.service",
)


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(len(ordered) * quantile) - 1))
    return ordered[index]


def parse_prometheus(payload: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, raw_value = line.rsplit(maxsplit=1)
        try:
            metrics[name] = float(raw_value)
        except ValueError:
            continue
    return metrics


def evaluate_sample(
    sample: dict[str, Any],
    baseline: dict[str, Any] | None,
    *,
    max_backlog: int,
    min_disk_free_percent: float,
    min_disk_free_bytes: int,
    max_rss_growth_bytes: int,
    max_fd_growth: int,
    max_connection_growth: int,
) -> list[str]:
    failures: list[str] = []
    agent = sample["agent"]
    if agent["heartbeat_age_seconds"] > agent["maximum_heartbeat_age_seconds"]:
        failures.append("agent_heartbeat_stale")
    if agent["version"] != agent["expected_version"]:
        failures.append("agent_version_mismatch")
    if agent["status"] != "active":
        failures.append("agent_not_active")

    platform = sample["platform"]
    if platform["redis_up"] != 1:
        failures.append("redis_unavailable")
    if platform["active_backlog"] > max_backlog:
        failures.append("active_backlog_limit")
    if platform["inactive_services"]:
        failures.append("required_service_inactive")
    if (
        sample["host"]["disk_free_percent"] < min_disk_free_percent
        and sample["host"]["disk_free_bytes"] < min_disk_free_bytes
    ):
        failures.append("disk_free_limit")

    if baseline:
        if platform["failed_agent_jobs"] > baseline["platform"]["failed_agent_jobs"]:
            failures.append("new_agent_job_failure")
        if platform["dead_letters"] > baseline["platform"]["dead_letters"]:
            failures.append("new_dead_letter")
        if platform["active_backlog"] > baseline["platform"]["active_backlog"] + max_backlog:
            failures.append("backlog_growth")
        if platform["database_connections"] > baseline["platform"]["database_connections"] + max_connection_growth:
            failures.append("database_connection_growth")
        if sample["processes"]["rss_bytes"] > baseline["processes"]["rss_bytes"] + max_rss_growth_bytes:
            failures.append("rss_growth")
        if sample["processes"]["file_descriptors"] > baseline["processes"]["file_descriptors"] + max_fd_growth:
            failures.append("file_descriptor_growth")
        if sample["processes"]["restart_count"] > baseline["processes"]["restart_count"]:
            failures.append("process_restart")
    return failures


def _command(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True, timeout=15)
    return result.stdout.strip()


def _service_properties(unit: str) -> dict[str, Any]:
    properties = (
        "ActiveState",
        "MainPID",
        "MemoryCurrent",
        "TasksCurrent",
        "NRestarts",
        "CPUUsageNSec",
    )
    try:
        output = _command("systemctl", "show", unit, "--property", ",".join(properties))
    except (OSError, subprocess.SubprocessError):
        return {"active": False, "pid": 0, "rss_bytes": 0, "tasks": 0, "restarts": 0, "cpu_nsec": 0, "fds": 0}
    values = dict(line.split("=", maxsplit=1) for line in output.splitlines() if "=" in line)
    pid = _integer(values.get("MainPID"))
    return {
        "active": values.get("ActiveState") == "active",
        "pid": pid,
        "rss_bytes": _integer(values.get("MemoryCurrent")),
        "tasks": _integer(values.get("TasksCurrent")),
        "restarts": _integer(values.get("NRestarts")),
        "cpu_nsec": _integer(values.get("CPUUsageNSec")),
        "fds": _fd_count(pid),
    }


def _integer(value: str | None) -> int:
    try:
        return int(value or 0)
    except ValueError:
        return 0


def _fd_count(pid: int) -> int:
    if pid <= 0:
        return 0
    try:
        return len(list(Path(f"/proc/{pid}/fd").iterdir()))
    except OSError:
        return 0


def _directory_metrics(path: Path) -> tuple[int, float | None]:
    total = 0
    newest: float | None = None
    try:
        for entry in path.iterdir():
            if not entry.is_file():
                continue
            stat = entry.stat()
            total += stat.st_size
            newest = max(newest or stat.st_mtime, stat.st_mtime)
    except OSError:
        return 0, None
    age = None if newest is None else max(0.0, time.time() - newest)
    return total, age


def _tree_size(path: Path) -> int:
    total = 0
    try:
        for root, _directories, files in os.walk(path):
            for filename in files:
                try:
                    total += (Path(root) / filename).stat().st_size
                except OSError:
                    continue
    except OSError:
        return 0
    return total


def _metrics_endpoint(base_path: Path) -> dict[str, float]:
    slot = (base_path / "shared/active-slot").read_text().strip()
    port = {"blue": 8069, "green": 8070}[slot]
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/metrics",
        headers={"Accept": "text/plain", "User-Agent": "Printora-Soak-Observer/1.0"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return parse_prometheus(response.read(2_000_000).decode("utf-8"))


def _database_metrics(database_url: str, stable_id: str) -> dict[str, Any]:
    with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, agent_version, status, last_seen_at
                FROM printer_agents
                WHERE stable_id = %s AND removed_at IS NULL AND revoked_at IS NULL
                ORDER BY id DESC LIMIT 1
                """,
                (stable_id,),
            )
            agent = cursor.fetchone()
            if agent is None:
                raise LookupError("agent not found")
            agent_id = int(agent["id"])
            cursor.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status IN ('pending', 'in_progress')) AS active_jobs,
                    COUNT(*) FILTER (WHERE status = 'failed') AS failed_jobs,
                    COUNT(correlation_id) - COUNT(DISTINCT correlation_id)
                        FILTER (WHERE correlation_id IS NOT NULL) AS duplicate_correlations
                FROM agent_jobs WHERE agent_id = %s OR (agent_id IS NULL AND printer_id = (
                    SELECT printer_id FROM printer_agents WHERE id = %s
                ))
                """,
                (agent_id, agent_id),
            )
            agent_jobs = cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database()) AS connections,
                    pg_database_size(current_database()) AS database_bytes,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0')::bigint AS wal_lsn_bytes,
                    (SELECT COUNT(*) FROM search_documents WHERE is_active = true) AS search_documents,
                    deadlocks,
                    temp_bytes
                FROM pg_stat_database WHERE datname = current_database()
                """
            )
            database = cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM durable_jobs WHERE status IN ('queued', 'leased')) AS durable_active,
                    (SELECT COUNT(*) FROM durable_jobs WHERE status = 'dead_letter') AS durable_dead,
                    (SELECT COUNT(*) FROM outbox_events WHERE status IN ('pending', 'publishing')) AS outbox_active,
                    (SELECT COUNT(*) FROM outbox_events WHERE status = 'dead_letter') AS outbox_dead
                """
            )
            durable = cursor.fetchone()
    return {
        "agent": agent,
        "agent_jobs": agent_jobs,
        "database": database,
        "durable": durable,
    }


def _parse_timestamp(value: Any) -> datetime:
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _load_baseline(evidence_file: Path) -> dict[str, Any] | None:
    for candidate in (evidence_file.with_name(f"{evidence_file.name}.1"), evidence_file):
        try:
            with candidate.open(encoding="utf-8") as handle:
                for line in handle:
                    record = json.loads(line)
                    if record.get("kind") == "observation" and record.get("status") == "passed":
                        return record
        except (OSError, json.JSONDecodeError):
            continue
    return None


def observe(args: argparse.Namespace) -> dict[str, Any]:
    database_url = os.environ.get("PRINTORA_DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("database URL missing")
    base_path = Path(args.base_path)
    database_metrics = _database_metrics(database_url, args.agent_stable_id)
    agent_row = database_metrics["agent"]
    heartbeat_age = max(0.0, (datetime.now(UTC) - _parse_timestamp(agent_row["last_seen_at"])).total_seconds())

    active_slot = (base_path / "shared/active-slot").read_text().strip()
    units = (*SERVICE_UNITS, f"printora-cloud@{active_slot}.service")
    services = {unit: _service_properties(unit) for unit in units}
    metrics = _metrics_endpoint(base_path)
    disk = shutil.disk_usage(base_path)
    wal_bytes, wal_latest_age = _directory_metrics(Path(args.wal_archive_path))
    active_backlog = (
        int(database_metrics["agent_jobs"]["active_jobs"] or 0)
        + int(database_metrics["durable"]["durable_active"] or 0)
        + int(database_metrics["durable"]["outbox_active"] or 0)
    )
    sample = {
        "kind": "observation",
        "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "agent": {
            "fingerprint": hashlib.sha256(args.agent_stable_id.encode()).hexdigest()[:16],
            "version": str(agent_row["agent_version"] or ""),
            "expected_version": args.expected_agent_version,
            "status": str(agent_row["status"]),
            "heartbeat_age_seconds": round(heartbeat_age, 3),
            "maximum_heartbeat_age_seconds": args.max_heartbeat_age,
        },
        "platform": {
            "redis_up": int(metrics.get("printora_recomposable_redis_up", 0)),
            "active_backlog": active_backlog,
            "failed_agent_jobs": int(database_metrics["agent_jobs"]["failed_jobs"] or 0),
            "dead_letters": int(database_metrics["durable"]["durable_dead"] or 0)
            + int(database_metrics["durable"]["outbox_dead"] or 0),
            "duplicate_correlations": int(database_metrics["agent_jobs"]["duplicate_correlations"] or 0),
            "database_connections": int(database_metrics["database"]["connections"] or 0),
            "database_bytes": int(database_metrics["database"]["database_bytes"] or 0),
            "search_documents": int(database_metrics["database"]["search_documents"] or 0),
            "wal_lsn_bytes": int(database_metrics["database"]["wal_lsn_bytes"] or 0),
            "wal_archive_bytes": wal_bytes,
            "wal_latest_age_seconds": None if wal_latest_age is None else round(wal_latest_age, 3),
            "object_storage_bytes": _tree_size(base_path / "shared/object-storage"),
            "log_bytes": _tree_size(base_path / "shared/logs"),
            "database_deadlocks": int(database_metrics["database"]["deadlocks"] or 0),
            "database_temp_bytes": int(database_metrics["database"]["temp_bytes"] or 0),
            "inactive_services": sorted(unit for unit, values in services.items() if not values["active"]),
        },
        "processes": {
            "rss_bytes": sum(item["rss_bytes"] for item in services.values()),
            "file_descriptors": sum(item["fds"] for item in services.values()),
            "tasks": sum(item["tasks"] for item in services.values()),
            "restart_count": sum(item["restarts"] for item in services.values()),
            "cpu_nsec": sum(item["cpu_nsec"] for item in services.values()),
        },
        "host": {
            "load_average": [round(value, 3) for value in os.getloadavg()],
            "disk_free_bytes": disk.free,
            "disk_free_percent": round(disk.free * 100 / disk.total, 3),
        },
    }
    baseline = _load_baseline(Path(args.evidence_file))
    failures = evaluate_sample(
        sample,
        baseline,
        max_backlog=args.max_backlog,
        min_disk_free_percent=args.min_disk_free_percent,
        min_disk_free_bytes=args.min_disk_free_bytes,
        max_rss_growth_bytes=args.max_rss_growth_bytes,
        max_fd_growth=args.max_fd_growth,
        max_connection_growth=args.max_connection_growth,
    )
    if sample["platform"]["duplicate_correlations"] > 0:
        failures.append("duplicate_agent_job_correlation")
    sample["failures"] = sorted(set(failures))
    sample["status"] = "failed" if failures else "passed"
    return sample


def main() -> int:
    parser = argparse.ArgumentParser(description="Observador sanitizado do soak cloud e agente")
    parser.add_argument("--agent-stable-id", required=True)
    parser.add_argument("--expected-agent-version", required=True)
    parser.add_argument("--evidence-file", required=True)
    parser.add_argument("--base-path", default="/var/www/print3dmaker.xyz")
    parser.add_argument("--wal-archive-path", default="/var/lib/postgresql/16/printora-wal-archive")
    parser.add_argument("--max-heartbeat-age", type=float, default=120.0)
    parser.add_argument("--max-backlog", type=int, default=25)
    parser.add_argument("--min-disk-free-percent", type=float, default=15.0)
    parser.add_argument("--min-disk-free-bytes", type=int, default=53_687_091_200)
    parser.add_argument("--max-rss-growth-bytes", type=int, default=268_435_456)
    parser.add_argument("--max-fd-growth", type=int, default=256)
    parser.add_argument("--max-connection-growth", type=int, default=20)
    args = parser.parse_args()
    try:
        sample = observe(args)
    except Exception as exc:
        sample = {
            "kind": "observation",
            "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "status": "failed",
            "failures": [f"observer_{type(exc).__name__}"],
        }
    print(json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if sample["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
