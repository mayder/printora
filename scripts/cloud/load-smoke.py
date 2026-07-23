#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime


def request_once(url: str, timeout: float) -> tuple[bool, float, str | None]:
    started_at = time.monotonic()
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "Printora-Load-Smoke/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(4096)
            ok = 200 <= response.status < 400
            error = None if ok else f"http_{response.status}"
    except urllib.error.HTTPError as exc:
        ok = False
        error = f"http_{exc.code}"
    except (OSError, urllib.error.URLError) as exc:
        ok = False
        error = type(exc).__name__
    return ok, time.monotonic() - started_at, error


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
    args = parser.parse_args()
    if (
        args.requests < 1
        or args.concurrency < 1
        or args.concurrency > 200
        or args.target_rps < 0
        or args.target_rps > 1000
    ):
        parser.error("requests/concurrency/target-rps fora do limite")

    results = run_requests(
        args.url,
        args.requests,
        args.concurrency,
        args.timeout,
        args.target_rps,
    )
    latencies = sorted(duration * 1000 for _, duration, _ in results)
    errors: dict[str, int] = {}
    for ok, _, error in results:
        if not ok:
            errors[error or "unknown"] = errors.get(error or "unknown", 0) + 1
    p95_index = max(0, min(len(latencies) - 1, round(len(latencies) * 0.95) - 1))
    p99_index = max(0, min(len(latencies) - 1, round(len(latencies) * 0.99) - 1))
    report = {
        "kind": "load",
        "timestamp_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "requests": len(results),
        "target_rps": args.target_rps,
        "errors": errors,
        "error_count": sum(errors.values()),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 3),
            "p95": round(latencies[p95_index], 3),
            "p99": round(latencies[p99_index], 3),
            "max": round(max(latencies), 3),
        },
        "slo": {"zero_errors": True, "p95_ms": args.p95_ms, "p99_ms": args.p99_ms},
    }
    print(json.dumps(report, sort_keys=True))
    return (
        0
        if report["error_count"] == 0
        and latencies[p95_index] <= args.p95_ms
        and latencies[p99_index] <= args.p99_ms
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
