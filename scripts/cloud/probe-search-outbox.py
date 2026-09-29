#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from uuid import uuid4

from app.config import get_settings
from app.database import connect_database
from app.modules.platform.durable_execution import DurableExecutionRepository, EventEnvelope


def main() -> None:
    settings = get_settings()
    repository = DurableExecutionRepository(settings.database_path)
    event_id = f"search-proof:{uuid4().hex}"
    with connect_database(settings.database_path) as connection:
        sequence = int(connection.execute("SELECT nextval('search_outbox_sequence') AS value").fetchone()["value"])
        repository.append_event(
            connection,
            EventEnvelope(
                event_id=event_id,
                aggregate_type="search_source",
                aggregate_id="validation",
                event_type="search.source.changed",
                ordering_key="search:index",
                sequence_no=sequence,
                payload={"source": "validation", "source_id": "synthetic", "operation": "rebuild"},
                headers={"owner_type": "search_index", "owner_id": "global"},
            ),
        )
    started = time.monotonic()
    event_status = "pending"
    job_status = "absent"
    for _attempt in range(120):
        with connect_database(settings.database_path) as connection:
            event = connection.execute("SELECT status FROM outbox_events WHERE event_id = ?", (event_id,)).fetchone()
            job = connection.execute(
                "SELECT status FROM durable_jobs WHERE job_key = ?",
                (f"event:{event_id}:search-index-v1",),
            ).fetchone()
        event_status = str(event["status"]) if event else "absent"
        job_status = str(job["status"]) if job else "absent"
        if event_status == "published" and job_status == "succeeded":
            break
        time.sleep(0.25)
    if event_status != "published" or job_status != "succeeded":
        raise RuntimeError(f"outbox/search job não concluiu: event={event_status} job={job_status}")
    print(
        json.dumps(
            {
                "status": "passed",
                "event_status": event_status,
                "job_status": job_status,
                "duration_seconds": round(time.monotonic() - started, 3),
                "payload_contains_user_data": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
