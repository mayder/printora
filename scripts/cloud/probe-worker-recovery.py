#!/var/www/print3dmaker.xyz/current/venv/bin/python
from __future__ import annotations

import json
import os
import sys
import time
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
    settings = get_settings()
    initialize_database(settings.database_path)
    repository = DurableExecutionRepository(settings.database_path)
    probe_id = uuid4().hex
    queued = repository.enqueue_job(
        job_key=f"failure-probe:{probe_id}",
        queue_name="failure_probe",
        job_type="failure.probe",
        payload={"probe_id": probe_id},
        owner_type="failure_probe",
        owner_id=probe_id,
        max_attempts=3,
    )
    first_claim = repository.claim_job("failure_probe", f"failure-probe:{probe_id}:dead", 5)
    if first_claim is None:
        print(json.dumps({"status": "failed", "reason": "first_claim_missing"}))
        return 1
    time.sleep(6)
    resumed = repository.claim_job("failure_probe", f"failure-probe:{probe_id}:recovery", 5)
    if resumed is None:
        print(json.dumps({"status": "failed", "reason": "lease_not_recovered"}))
        return 1
    completed = repository.complete_job(resumed.id, resumed.lease_token or "", {"recovered": True})
    stale_completion = repository.complete_job(queued.id, first_claim.lease_token or "", {"stale": True})
    report = {
        "status": "ok" if completed is not None and stale_completion is None else "failed",
        "job_id": queued.id,
        "first_attempt": first_claim.attempts,
        "recovered_attempt": resumed.attempts,
        "stale_completion_accepted": stale_completion is not None,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
