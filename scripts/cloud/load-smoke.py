#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.error
import urllib.request


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga HTTP pequena e verificável para o smoke blue/green")
    parser.add_argument("url")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--p95-ms", type=float, default=1000.0)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or args.concurrency > 200:
        parser.error("requests/concurrency fora do limite")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(lambda _: request_once(args.url, args.timeout), range(args.requests)))
    latencies = sorted(duration * 1000 for _, duration, _ in results)
    errors: dict[str, int] = {}
    for ok, _, error in results:
        if not ok:
            errors[error or "unknown"] = errors.get(error or "unknown", 0) + 1
    p95_index = max(0, min(len(latencies) - 1, round(len(latencies) * 0.95) - 1))
    report = {
        "requests": len(results),
        "errors": errors,
        "error_count": sum(errors.values()),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 3),
            "p95": round(latencies[p95_index], 3),
            "max": round(max(latencies), 3),
        },
        "slo": {"zero_errors": True, "p95_ms": args.p95_ms},
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["error_count"] == 0 and latencies[p95_index] <= args.p95_ms else 1


if __name__ == "__main__":
    raise SystemExit(main())
