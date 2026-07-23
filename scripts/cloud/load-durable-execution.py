#!/var/www/print3dmaker.xyz/current/venv/bin/python
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

for _backend in (
    Path("/var/www/print3dmaker.xyz/current/backend"),
    Path(__file__).resolve().parents[2] / "backend",
):
    if _backend.is_dir():
        sys.path.insert(0, str(_backend))
        os.chdir(_backend)
        break

from app.config import get_settings
from app.database import initialize_database
from app.modules.platform.durable_execution import DurableExecutionRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga controlada da fila durável")
    parser.add_argument("--jobs", type=int, default=500)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    total = max(1, min(args.jobs, 500))
    workers = max(1, min(args.workers, 32))
    settings = get_settings()
    initialize_database(settings.database_path)
    repository = DurableExecutionRepository(settings.database_path)
    run_id = f"load-{uuid4().hex}"
    started = time.monotonic()
    for index in range(total):
        repository.enqueue_job(
            job_key=f"{run_id}:{index}",
            queue_name="load_probe",
            job_type="load.probe",
            payload={"run_id": run_id, "index": index},
            owner_type="load_probe",
            owner_id=f"{run_id}:{index}",
            max_attempts=3,
        )
    enqueue_seconds = time.monotonic() - started
    completed: set[int] = set()
    duplicates = 0
    latencies: list[float] = []
    lock = threading.Lock()

    def consume(worker_index: int) -> None:
        nonlocal duplicates
        while True:
            with lock:
                if len(completed) >= total:
                    return
            claimed_at = time.monotonic()
            job = repository.claim_job("load_probe", f"{run_id}:worker:{worker_index}", 15)
            if job is None:
                time.sleep(0.01)
                continue
            if job.payload.get("run_id") != run_id:
                repository.retry_job(job.id, job.lease_token or "", "job fora do ensaio", 1)
                continue
            result = repository.complete_job(job.id, job.lease_token or "", {"ok": True})
            if result is None:
                continue
            with lock:
                if job.id in completed:
                    duplicates += 1
                completed.add(job.id)
                latencies.append(time.monotonic() - claimed_at)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(consume, index) for index in range(workers)]
        for future in futures:
            future.result()
    elapsed = time.monotonic() - started
    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] if ordered else 0.0
    report = {
        "status": "ok" if len(completed) == total and duplicates == 0 else "failed",
        "run_id": run_id,
        "jobs": total,
        "workers": workers,
        "completed": len(completed),
        "duplicates": duplicates,
        "enqueue_seconds": round(enqueue_seconds, 3),
        "elapsed_seconds": round(elapsed, 3),
        "throughput_jobs_second": round(total / elapsed, 2),
        "mean_claim_seconds": round(statistics.fmean(latencies), 6) if latencies else 0.0,
        "p95_claim_seconds": round(p95, 6),
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
