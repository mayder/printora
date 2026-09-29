from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import httpx


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


def test_request_with_client_reuses_the_supplied_client() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, float]] = []

        def get(self, url: str, *, timeout: float) -> SimpleNamespace:
            self.calls.append((url, timeout))
            return SimpleNamespace(status_code=200)

    client = FakeClient()
    first = LOAD_SMOKE.request_with_client(client, "https://example.invalid/health", 2)
    second = LOAD_SMOKE.request_with_client(client, "https://example.invalid/health", 2)

    assert first[0] is True
    assert second[0] is True
    assert client.calls == [
        ("https://example.invalid/health", 2),
        ("https://example.invalid/health", 2),
    ]


def test_request_with_client_reports_sanitized_httpx_error() -> None:
    class FailingClient:
        def get(self, url: str, *, timeout: float) -> None:
            request = httpx.Request("GET", url)
            raise httpx.ConnectTimeout("timeout", request=request)

    ok, _duration, error = LOAD_SMOKE.request_with_client(
        FailingClient(),
        "https://example.invalid/health",
        2,
    )
    assert ok is False
    assert error == "ConnectTimeout"


def test_request_with_client_reconnects_once_after_remote_protocol_error() -> None:
    class RecoveringClient:
        def __init__(self) -> None:
            self.calls = 0

        def get(self, url: str, *, timeout: float) -> SimpleNamespace:
            self.calls += 1
            if self.calls == 1:
                request = httpx.Request("GET", url)
                raise httpx.RemoteProtocolError("connection closed", request=request)
            return SimpleNamespace(status_code=200)

    client = RecoveringClient()
    result = LOAD_SMOKE.request_with_client(client, "https://example.invalid/health", 2)
    report = LOAD_SMOKE.build_report(
        [result],
        target_rps=5,
        connection_mode="pooled",
        p95_ms=1500,
        p99_ms=2500,
    )

    assert client.calls == 2
    assert result[0] is True
    assert report["error_count"] == 0
    assert report["retry_count"] == 1
    assert report["retries"] == {"RemoteProtocolError": 1}
    assert LOAD_SMOKE.report_passes(report)


def test_request_with_client_fails_after_second_remote_protocol_error() -> None:
    class FailingClient:
        def __init__(self) -> None:
            self.calls = 0

        def get(self, url: str, *, timeout: float) -> None:
            self.calls += 1
            request = httpx.Request("GET", url)
            raise httpx.RemoteProtocolError("connection closed", request=request)

    client = FailingClient()
    ok, _duration, error = LOAD_SMOKE.request_with_client(
        client,
        "https://example.invalid/health",
        2,
    )

    assert client.calls == 2
    assert ok is False
    assert error == "RemoteProtocolError"


def test_run_batches_reuses_requester_until_duration_finishes() -> None:
    clock = FakeClock()
    calls: list[float] = []

    def requester(_url: str, _timeout: float) -> tuple[bool, float, None]:
        calls.append(clock.now())
        return True, 0.01, None

    reports = list(
        LOAD_SMOKE.run_batches(
            "https://example.invalid/health",
            request_count=2,
            concurrency=1,
            timeout=1,
            target_rps=2,
            connection_mode="pooled",
            p95_ms=1500,
            p99_ms=2500,
            duration_seconds=1,
            requester=requester,
            clock=clock.now,
            sleeper=clock.sleep,
        )
    )

    assert len(reports) == 2
    assert len(calls) == 4
    assert {report["connection_mode"] for report in reports} == {"pooled"}
    assert all(LOAD_SMOKE.report_passes(report) for report in reports)
