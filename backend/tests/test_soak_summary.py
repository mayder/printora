from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_summary() -> ModuleType:
    path = ROOT_DIR / "scripts/cloud/summarize-soak.py"
    spec = importlib.util.spec_from_file_location("soak_summary", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


summary_module = _load_summary()


def _observation(timestamp: str, *, rss: int, status: str = "passed") -> dict:
    return {
        "kind": "observation",
        "timestamp_utc": timestamp,
        "status": status,
        "failures": [] if status == "passed" else ["rss_growth"],
        "agent": {
            "fingerprint": "private-fingerprint",
            "heartbeat_age_seconds": 3,
        },
        "platform": {
            "active_backlog": 0,
            "dead_letters": 0,
            "duplicate_correlations": 0,
            "inactive_services": [],
            "failed_agent_jobs": 4,
            "database_connections": 2,
            "database_bytes": 1_000,
            "wal_lsn_bytes": 2_000,
            "wal_archive_bytes": 3_000,
            "object_storage_bytes": 4_000,
            "log_bytes": 5_000,
        },
        "processes": {
            "rss_bytes": rss,
            "file_descriptors": 100,
            "tasks": 70,
            "restart_count": 0,
            "cpu_nsec": 10_000,
        },
        "host": {"disk_free_bytes": 100_000},
    }


def _load(timestamp: str, *, p95: float = 200, p99: float = 300, errors: int = 0) -> dict:
    return {
        "kind": "load",
        "timestamp_utc": timestamp,
        "requests": 100,
        "target_rps": 5,
        "connection_mode": "pooled",
        "error_count": errors,
        "latency_ms": {"p95": p95, "p99": p99, "max": max(p95, p99)},
        "slo": {"p95_ms": 1_500, "p99_ms": 2_500},
    }


def test_summary_consolidates_sanitized_trends() -> None:
    records = [
        _load("2026-07-24T00:00:00Z"),
        _observation("2026-07-24T00:00:01Z", rss=1_000),
        _load("2026-07-24T00:01:00Z", p95=450, p99=700),
        _observation("2026-07-24T00:01:01Z", rss=1_250),
    ]
    result = summary_module.summarize(records, minimum_seconds=60, tolerance_seconds=1)
    assert result["status"] == "passed"
    assert result["load"] == {
        "batches": 2,
        "requests": 200,
        "errors": 0,
        "target_rps": [5.0],
        "connection_modes": ["pooled"],
        "worst_latency_ms": {"p95": 450.0, "p99": 700.0, "max": 700.0},
    }
    assert result["observations"]["rss_bytes"] == {
        "first": 1_000,
        "last": 1_250,
        "delta": 250,
        "maximum": 1_250,
    }
    assert "fingerprint" not in json.dumps(result)
    assert "private-fingerprint" not in json.dumps(result)


def test_summary_fails_closed_on_slo_observation_and_duration() -> None:
    records = [
        _load("2026-07-24T00:00:00Z", p95=1_501, errors=1),
        _observation("2026-07-24T00:00:10Z", rss=1_000, status="failed"),
    ]
    result = summary_module.summarize(records, minimum_seconds=60, tolerance_seconds=5)
    assert result["status"] == "failed"
    assert set(result["failures"]) == {
        "load_error",
        "load_p95_slo",
        "minimum_duration_not_reached",
        "rss_growth",
    }


def test_load_records_rejects_malformed_or_unsupported_evidence(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text('{"kind":"load"}\nnot-json\n', encoding="utf-8")
    try:
        summary_module.load_records(malformed)
    except ValueError as exc:
        assert "line" in str(exc)
    else:
        raise AssertionError("malformed evidence must fail")

    unsupported = tmp_path / "unsupported.jsonl"
    unsupported.write_text('{"kind":"secret","timestamp_utc":"2026-07-24T00:00:00Z"}\n', encoding="utf-8")
    try:
        summary_module.load_records(unsupported)
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("unsupported evidence must fail")

    incomplete = tmp_path / "incomplete.jsonl"
    incomplete.write_text(
        '{"kind":"load","timestamp_utc":"2026-07-24T00:00:00Z"}\n',
        encoding="utf-8",
    )
    try:
        summary_module.load_records(incomplete)
    except ValueError as exc:
        assert "line" in str(exc)
    else:
        raise AssertionError("incomplete evidence must fail")
