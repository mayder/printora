#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from functools import partial

import httpx


def request_with_client(client: httpx.Client, url: str, timeout: float) -> tuple[bool, float, str | None]:
    started_at = time.monotonic()
    try:
        response = client.get(url, timeout=timeout)
        ok = 200 <= response.status_code < 400
        error = None if ok else f"http_{response.status_code}"
    except httpx.HTTPError as exc:
        ok = False
        error = type(exc).__name__
    return ok, time.monotonic() - started_at, error


def request_once(url: str, timeout: float) -> tuple[bool, float, str | None]:
    with httpx.Client(
        headers={"Accept": "application/json", "User-Agent": "Printora-Load-Smoke/1.0"},
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        return request_with_client(client, url, timeout)


def run_requests(
    url: str,
    request_count: int,
    concurrency: int,
    timeout: float,
    target_rps: float,
    *,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    requester: Callable[[str, float], tuple[bool, float, str | None]] = request_once,
) -> list[tuple[bool, float, str | None]]:
    started_at = clock()
    futures: list[concurrent.futures.Future[tuple[bool, float, str | None]]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        for index in range(request_count):
            if target_rps > 0:
                scheduled_at = started_at + (index / target_rps)
                delay = scheduled_at - clock()
                if delay > 0:
                    sleeper(delay)
            futures.append(executor.submit(requester, url, timeout))
        return [future.result() for future in futures]


def build_report(
    results: list[tuple[bool, float, str | None]],
    *,
    target_rps: float,
    connection_mode: str,
    p95_ms: float,
    p99_ms: float,
) -> dict[str, object]:
    latencies = sorted(duration * 1000 for _, duration, _ in results)
    errors: dict[str, int] = {}
    for ok, _, error in results:
        if not ok:
            errors[error or "unknown"] = errors.get(error or "unknown", 0) + 1
    p95_index = max(0, min(len(latencies) - 1, round(len(latencies) * 0.95) - 1))
    p99_index = max(0, min(len(latencies) - 1, round(len(latencies) * 0.99) - 1))
    return {
        "kind": "load",
        "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "requests": len(results),
        "target_rps": target_rps,
        "connection_mode": connection_mode,
        "errors": errors,
        "error_count": sum(errors.values()),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 3),
            "p95": round(latencies[p95_index], 3),
            "p99": round(latencies[p99_index], 3),
            "max": round(max(latencies), 3),
        },
        "slo": {"zero_errors": True, "p95_ms": p95_ms, "p99_ms": p99_ms},
    }


def report_passes(report: dict[str, object]) -> bool:
    latency = report["latency_ms"]
    slo = report["slo"]
    assert isinstance(latency, dict) and isinstance(slo, dict)
    return (
        report["error_count"] == 0
        and float(latency["p95"]) <= float(slo["p95_ms"])
        and float(latency["p99"]) <= float(slo["p99_ms"])
    )


def run_batches(
    url: str,
    request_count: int,
    concurrency: int,
    timeout: float,
    target_rps: float,
    connection_mode: str,
    p95_ms: float,
    p99_ms: float,
    duration_seconds: int,
    *,
    requester: Callable[[str, float], tuple[bool, float, str | None]],
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> Iterator[dict[str, object]]:
    deadline = clock() + duration_seconds if duration_seconds else None
    while True:
        results = run_requests(
            url,
            request_count,
            concurrency,
            timeout,
            target_rps,
            clock=clock,
            sleeper=sleeper,
            requester=requester,
        )
        report = build_report(
            results,
            target_rps=target_rps,
            connection_mode=connection_mode,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
        )
        yield report
        if not report_passes(report) or deadline is None or clock() >= deadline:
            return


def emit_batches(
    args: argparse.Namespace,
    requester: Callable[[str, float], tuple[bool, float, str | None]],
) -> int:
    for report in run_batches(
        args.url,
        args.requests,
        args.concurrency,
        args.timeout,
        args.target_rps,
        args.connection_mode,
        args.p95_ms,
        args.p99_ms,
        args.duration_seconds,
        requester=requester,
    ):
        print(json.dumps(report, sort_keys=True), flush=True)
        if not report_passes(report):
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga HTTP pequena e verificável para o smoke blue/green")
    parser.add_argument("url")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument(
        "--target-rps",
        type=float,
        default=0.0,
        help="distribui os inícios das requisições; zero mantém o modo burst",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--p95-ms", type=float, default=1000.0)
    parser.add_argument("--p99-ms", type=float, default=2500.0)
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=0,
        help="mantém o mesmo pool entre lotes até esta duração; zero executa um lote",
    )
    parser.add_argument(
        "--connection-mode",
        choices=("pooled", "cold"),
        default="pooled",
        help="pooled reutiliza keep-alive; cold abre uma conexão por requisição",
    )
    args = parser.parse_args()
    if (
        args.requests < 1
        or args.concurrency < 1
        or args.concurrency > 200
        or args.target_rps < 0
        or args.target_rps > 1000
        or args.duration_seconds < 0
    ):
        parser.error("requests/concurrency/target-rps/duration fora do limite")

    if args.connection_mode == "pooled":
        limits = httpx.Limits(
            max_connections=args.concurrency,
            max_keepalive_connections=args.concurrency,
            keepalive_expiry=30,
        )
        with httpx.Client(
            headers={"Accept": "application/json", "User-Agent": "Printora-Load-Smoke/1.0"},
            follow_redirects=True,
            timeout=args.timeout,
            limits=limits,
        ) as client:
            return emit_batches(args, partial(request_with_client, client))
    return emit_batches(args, request_once)


if __name__ == "__main__":
    raise SystemExit(main())
