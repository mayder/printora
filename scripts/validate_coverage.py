#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path

PYTHON_CRITICAL_PATTERNS = (
    "app/auth.py",
    "app/finance_*.py",
    "app/modules/finance/*.py",
    "app/modules/identity/security.py",
    "app/modules/platform/idempotency.py",
    "app/idempotency_middleware.py",
    "app/object_storage.py",
    "app/upload_stream.py",
    "app/remote_operations.py",
    "app/rate_limit_middleware.py",
)
FRONTEND_CRITICAL_SUFFIXES = (
    "/src/services/http.ts",
    "/src/components/monitoring/gcodePreview.ts",
    "/src/utils/sequentialPoll.ts",
)


def ratio(covered: int, total: int) -> float:
    if total <= 0:
        raise ValueError("cobertura sem statements/linhas mensuráveis")
    return covered / total * 100


def python_metrics(path: Path) -> tuple[float, float]:
    report = json.loads(path.read_text())
    global_percent = float(report["totals"]["percent_covered"])
    critical = [
        summary["summary"]
        for name, summary in report["files"].items()
        if any(fnmatch.fnmatch(name, pattern) for pattern in PYTHON_CRITICAL_PATTERNS)
    ]
    return global_percent, ratio(
        sum(item["covered_lines"] for item in critical),
        sum(item["num_statements"] for item in critical),
    )


def go_percent(path: Path) -> float:
    match = re.search(r"^total:.*?([0-9]+(?:\.[0-9]+)?)%$", path.read_text(), re.M)
    if not match:
        raise ValueError(f"total de cobertura Go ausente em {path}")
    return float(match.group(1))


def frontend_metrics(path: Path) -> tuple[float, float]:
    report = json.loads(path.read_text())
    global_percent = ratio(
        report["total"]["lines"]["covered"],
        report["total"]["lines"]["total"],
    )
    critical = [
        summary["lines"]
        for name, summary in report.items()
        if name != "total"
        and any(name.endswith(suffix) for suffix in FRONTEND_CRITICAL_SUFFIXES)
    ]
    return global_percent, ratio(
        sum(item["covered"] for item in critical),
        sum(item["total"] for item in critical),
    )


def validate(name: str, actual: tuple[float, float], baseline: dict[str, float]) -> None:
    for index, key in enumerate(("global", "critical")):
        value = actual[index]
        minimum_key = "minimum" if key == "global" else "critical_minimum"
        required = max(float(baseline[key]), float(baseline[minimum_key]))
        if value + 1e-9 < required:
            raise SystemExit(
                f"{name} {key} regrediu: {value:.4f}% < {required:.4f}%"
            )
    print(f"{name}: global={actual[0]:.4f}% critical={actual[1]:.4f}%")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--go-global", type=Path, required=True)
    parser.add_argument("--go-critical", type=Path, required=True)
    parser.add_argument("--frontend", type=Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text())
    validate("python", python_metrics(args.python), baseline["python"])
    validate(
        "go",
        (go_percent(args.go_global), go_percent(args.go_critical)),
        baseline["go"],
    )
    validate("frontend", frontend_metrics(args.frontend), baseline["frontend"])
    print("coverage gate passed")


if __name__ == "__main__":
    main()
