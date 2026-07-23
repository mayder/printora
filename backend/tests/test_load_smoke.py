from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "printora_load_smoke",
    ROOT_DIR / "scripts/cloud/load-smoke.py",
)
assert SPEC is not None and SPEC.loader is not None
LOAD_SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOAD_SMOKE)


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


def test_run_requests_paces_request_starts_at_target_rate() -> None:
    clock = FakeClock()

    def requester(_url: str, _timeout: float) -> tuple[bool, float, None]:
        return True, 0.01, None

    results = LOAD_SMOKE.run_requests(
        "https://example.invalid/health",
        request_count=4,
        concurrency=1,
        timeout=1,
        target_rps=2,
        clock=clock.now,
        sleeper=clock.sleep,
        requester=requester,
    )

    assert len(results) == 4
    assert clock.sleeps == [0.5, 0.5, 0.5]
    assert clock.now() == 101.5


def test_run_requests_keeps_burst_mode_when_rate_is_zero() -> None:
    clock = FakeClock()

    def requester(_url: str, _timeout: float) -> tuple[bool, float, None]:
        return True, 0.01, None

    LOAD_SMOKE.run_requests(
        "https://example.invalid/health",
        request_count=3,
        concurrency=1,
        timeout=1,
        target_rps=0,
        clock=clock.now,
        sleeper=clock.sleep,
        requester=requester,
    )

    assert clock.sleeps == []
    assert clock.now() == 100.0
