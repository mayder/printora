from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_observer() -> ModuleType:
    path = ROOT_DIR / "scripts/cloud/soak-observer.py"
    spec = importlib.util.spec_from_file_location("soak_observer", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


observer = _load_observer()


def _sample() -> dict:
    return {
        "agent": {
            "heartbeat_age_seconds": 20,
            "maximum_heartbeat_age_seconds": 120,
            "version": "0.1.36",
            "expected_version": "0.1.36",
            "status": "active",
        },
        "platform": {
            "redis_up": 1,
            "active_backlog": 2,
            "failed_agent_jobs": 1,
            "dead_letters": 0,
            "database_connections": 8,
            "inactive_services": [],
        },
        "processes": {
            "rss_bytes": 300_000_000,
            "file_descriptors": 120,
            "restart_count": 0,
        },
        "host": {"disk_free_bytes": 120_000_000_000, "disk_free_percent": 40},
    }


def test_percentile_and_prometheus_parsing_include_tail_latency() -> None:
    assert observer.percentile(list(range(1, 101)), 0.95) == 95
    assert observer.percentile(list(range(1, 101)), 0.99) == 99
    metrics = observer.parse_prometheus(
        "# HELP sample test\nprintora_recomposable_redis_up 1\n"
        'printora_durable_items{kind="job",status="queued"} 3\n'
    )
    assert metrics["printora_recomposable_redis_up"] == 1
    assert metrics['printora_durable_items{kind="job",status="queued"}'] == 3


def test_healthy_observation_passes_against_baseline() -> None:
    sample = _sample()
    assert observer.evaluate_sample(
        sample,
        _sample(),
        max_backlog=25,
        min_disk_free_percent=15,
        min_disk_free_bytes=53_687_091_200,
        max_rss_growth_bytes=268_435_456,
        max_fd_growth=256,
        max_connection_growth=20,
    ) == []


def test_observation_fails_closed_on_agent_service_and_growth_regressions() -> None:
    baseline = _sample()
    sample = _sample()
    sample["agent"]["heartbeat_age_seconds"] = 121
    sample["platform"]["redis_up"] = 0
    sample["platform"]["failed_agent_jobs"] = 2
    sample["platform"]["dead_letters"] = 1
    sample["platform"]["database_connections"] = 29
    sample["platform"]["inactive_services"] = ["redis-printora.service"]
    sample["processes"]["rss_bytes"] += 268_435_457
    sample["processes"]["file_descriptors"] += 257
    sample["processes"]["restart_count"] = 1
    failures = observer.evaluate_sample(
        sample,
        baseline,
        max_backlog=25,
        min_disk_free_percent=15,
        min_disk_free_bytes=53_687_091_200,
        max_rss_growth_bytes=268_435_456,
        max_fd_growth=256,
        max_connection_growth=20,
    )
    assert set(failures) == {
        "agent_heartbeat_stale",
        "redis_unavailable",
        "required_service_inactive",
        "new_agent_job_failure",
        "new_dead_letter",
        "database_connection_growth",
        "rss_growth",
        "file_descriptor_growth",
        "process_restart",
    }


def test_disk_gate_accepts_large_absolute_reserve_and_blocks_low_reserve() -> None:
    sample = _sample()
    sample["host"] = {"disk_free_bytes": 114_000_000_000, "disk_free_percent": 11.8}
    assert observer.evaluate_sample(
        sample,
        None,
        max_backlog=25,
        min_disk_free_percent=15,
        min_disk_free_bytes=53_687_091_200,
        max_rss_growth_bytes=268_435_456,
        max_fd_growth=256,
        max_connection_growth=20,
    ) == []
    sample["host"]["disk_free_bytes"] = 40_000_000_000
    assert "disk_free_limit" in observer.evaluate_sample(
        sample,
        None,
        max_backlog=25,
        min_disk_free_percent=15,
        min_disk_free_bytes=53_687_091_200,
        max_rss_growth_bytes=268_435_456,
        max_fd_growth=256,
        max_connection_growth=20,
    )
