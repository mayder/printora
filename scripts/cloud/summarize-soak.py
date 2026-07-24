#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


def _timestamp(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _require_mapping(record: dict[str, Any], key: str) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing {key}")
    return value


def _validate_record(record: dict[str, Any]) -> None:
    if record["kind"] == "load":
        latency = _require_mapping(record, "latency_ms")
        slo = _require_mapping(record, "slo")
        required = (
            record.get("requests"),
            record.get("target_rps"),
            record.get("error_count"),
            latency.get("p95"),
            latency.get("p99"),
            latency.get("max"),
            slo.get("p95_ms"),
            slo.get("p99_ms"),
        )
    else:
        agent = _require_mapping(record, "agent")
        platform = _require_mapping(record, "platform")
        processes = _require_mapping(record, "processes")
        host = _require_mapping(record, "host")
        if record.get("status") not in {"passed", "failed"} or not isinstance(record.get("failures"), list):
            raise ValueError("invalid observation status")
        required = (
            agent.get("heartbeat_age_seconds"),
            platform.get("active_backlog"),
            platform.get("dead_letters"),
            platform.get("duplicate_correlations"),
            platform.get("inactive_services"),
            platform.get("failed_agent_jobs"),
            platform.get("database_connections"),
            platform.get("database_bytes"),
            platform.get("wal_lsn_bytes"),
            platform.get("wal_archive_bytes"),
            platform.get("object_storage_bytes"),
            platform.get("log_bytes"),
            processes.get("rss_bytes"),
            processes.get("file_descriptors"),
            processes.get("tasks"),
            processes.get("restart_count"),
            processes.get("cpu_nsec"),
            host.get("disk_free_bytes"),
        )
    if any(value is None for value in required):
        raise ValueError("incomplete evidence")


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid evidence line {line_number}") from exc
            if not isinstance(record, dict) or record.get("kind") not in {"load", "observation"}:
                raise ValueError(f"unsupported evidence line {line_number}")
            try:
                _timestamp(record.get("timestamp_utc"))
                _validate_record(record)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid evidence line {line_number}") from exc
            records.append(record)
    if not records:
        raise ValueError("empty evidence")
    return records


def _integer(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _series(records: Iterable[dict[str, Any]], *keys: str) -> list[float]:
    values: list[float] = []
    for record in records:
        current: Any = record
        for key in keys:
            current = current.get(key) if isinstance(current, dict) else None
        values.append(_number(current))
    return values


def _trend(records: list[dict[str, Any]], *keys: str) -> dict[str, int | float]:
    values = _series(records, *keys)
    first = values[0]
    last = values[-1]
    maximum = max(values)
    if all(value.is_integer() for value in values):
        return {"first": int(first), "last": int(last), "delta": int(last - first), "maximum": int(maximum)}
    return {
        "first": round(first, 3),
        "last": round(last, 3),
        "delta": round(last - first, 3),
        "maximum": round(maximum, 3),
    }


def _aggregate_counts(records: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for record in records:
        counts = record.get(key)
        if not isinstance(counts, dict):
            continue
        for category, value in counts.items():
            name = str(category)
            totals[name] = totals.get(name, 0) + _integer(value)
    return dict(sorted(totals.items()))


def summarize(records: list[dict[str, Any]], *, minimum_seconds: int, tolerance_seconds: int) -> dict[str, Any]:
    ordered = sorted(records, key=lambda item: _timestamp(item["timestamp_utc"]))
    started_at = _timestamp(ordered[0]["timestamp_utc"])
    finished_at = _timestamp(ordered[-1]["timestamp_utc"])
    observed_seconds = max(0, round((finished_at - started_at).total_seconds()))
    loads = [record for record in ordered if record["kind"] == "load"]
    observations = [record for record in ordered if record["kind"] == "observation"]
    failures: set[str] = set()

    if not loads:
        failures.add("load_evidence_missing")
    if not observations:
        failures.add("observation_evidence_missing")
    required_coverage = max(0, minimum_seconds - tolerance_seconds)
    if minimum_seconds and observed_seconds < required_coverage:
        failures.add("minimum_duration_not_reached")

    for record in loads:
        if _integer(record.get("error_count")) > 0:
            failures.add("load_error")
        latency = record.get("latency_ms") or {}
        slo = record.get("slo") or {}
        if _number(latency.get("p95")) > _number(slo.get("p95_ms")):
            failures.add("load_p95_slo")
        if _number(latency.get("p99")) > _number(slo.get("p99_ms")):
            failures.add("load_p99_slo")
    for record in observations:
        record_failures = [str(item) for item in record.get("failures") or []]
        if record.get("status") != "passed" or record_failures:
            failures.update(record_failures or ["observation_failed"])

    summary: dict[str, Any] = {
        "kind": "soak_summary",
        "status": "failed" if failures else "passed",
        "failures": sorted(failures),
        "sanitized": True,
        "window": {
            "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
            "finished_at_utc": finished_at.isoformat().replace("+00:00", "Z"),
            "observed_seconds": observed_seconds,
            "minimum_seconds": minimum_seconds,
            "tolerance_seconds": tolerance_seconds,
        },
        "load": {
            "batches": len(loads),
            "requests": sum(_integer(record.get("requests")) for record in loads),
            "errors": sum(_integer(record.get("error_count")) for record in loads),
            "retries": sum(_integer(record.get("retry_count")) for record in loads),
            "retry_types": _aggregate_counts(loads, "retries"),
            "target_rps": sorted({_number(record.get("target_rps")) for record in loads}),
            "connection_modes": sorted(
                {str(record.get("connection_mode") or "legacy") for record in loads}
            ),
            "worst_latency_ms": {
                "p95": round(max(_series(loads, "latency_ms", "p95"), default=0.0), 3),
                "p99": round(max(_series(loads, "latency_ms", "p99"), default=0.0), 3),
                "max": round(max(_series(loads, "latency_ms", "max"), default=0.0), 3),
            },
        },
        "observations": {"samples": len(observations)},
    }
    if observations:
        summary["observations"].update(
            {
                "maximum_heartbeat_age_seconds": round(
                    max(_series(observations, "agent", "heartbeat_age_seconds")),
                    3,
                ),
                "maximum_active_backlog": int(max(_series(observations, "platform", "active_backlog"))),
                "maximum_dead_letters": int(max(_series(observations, "platform", "dead_letters"))),
                "maximum_duplicate_correlations": int(
                    max(_series(observations, "platform", "duplicate_correlations"))
                ),
                "inactive_service_samples": sum(
                    bool((record.get("platform") or {}).get("inactive_services")) for record in observations
                ),
                "failed_agent_jobs": _trend(observations, "platform", "failed_agent_jobs"),
                "database_connections": _trend(observations, "platform", "database_connections"),
                "database_bytes": _trend(observations, "platform", "database_bytes"),
                "wal_lsn_bytes": _trend(observations, "platform", "wal_lsn_bytes"),
                "wal_archive_bytes": _trend(observations, "platform", "wal_archive_bytes"),
                "object_storage_bytes": _trend(observations, "platform", "object_storage_bytes"),
                "log_bytes": _trend(observations, "platform", "log_bytes"),
                "rss_bytes": _trend(observations, "processes", "rss_bytes"),
                "file_descriptors": _trend(observations, "processes", "file_descriptors"),
                "tasks": _trend(observations, "processes", "tasks"),
                "restart_count": _trend(observations, "processes", "restart_count"),
                "cpu_nsec": _trend(observations, "processes", "cpu_nsec"),
                "disk_free_bytes": _trend(observations, "host", "disk_free_bytes"),
            }
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolida evidência sanitizada do soak Printora")
    parser.add_argument("evidence_file")
    parser.add_argument("--minimum-seconds", type=int, default=0)
    parser.add_argument("--tolerance-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.minimum_seconds < 0 or args.tolerance_seconds < 0:
        parser.error("duração e tolerância devem ser não negativas")
    if args.minimum_seconds and args.tolerance_seconds >= args.minimum_seconds:
        parser.error("tolerância deve ser menor que a duração mínima")
    try:
        summary = summarize(
            load_records(Path(args.evidence_file)),
            minimum_seconds=args.minimum_seconds,
            tolerance_seconds=args.tolerance_seconds,
        )
    except (OSError, TypeError, ValueError):
        summary = {
            "kind": "soak_summary",
            "status": "failed",
            "failures": ["invalid_evidence"],
            "sanitized": True,
        }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
