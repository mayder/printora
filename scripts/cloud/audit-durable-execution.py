#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

import psycopg
from psycopg.rows import dict_row


def main() -> int:
    database_url = os.environ.get("PRINTORA_DATABASE_URL", "")
    if not database_url.startswith("postgresql://"):
        print("PRINTORA_DATABASE_URL PostgreSQL obrigatória", file=sys.stderr)
        return 2
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        report = {
            "outbox": _grouped(connection, "SELECT status, COUNT(*) AS total FROM outbox_events GROUP BY status"),
            "jobs": _grouped(
                connection,
                "SELECT queue_name || ':' || status AS status, COUNT(*) AS total FROM durable_jobs GROUP BY queue_name, status",
            ),
            "workers": _grouped(
                connection,
                "SELECT queue_name || ':' || state AS status, COUNT(*) AS total FROM worker_instances GROUP BY queue_name, state",
            ),
            "expired_job_leases": _scalar(
                connection,
                "SELECT COUNT(*) FROM durable_jobs WHERE status = 'leased' AND lease_expires_at <= CAST(CURRENT_TIMESTAMP AS TEXT)",
            ),
            "expired_outbox_leases": _scalar(
                connection,
                "SELECT COUNT(*) FROM outbox_events WHERE status = 'publishing' AND lease_expires_at <= CAST(CURRENT_TIMESTAMP AS TEXT)",
            ),
            "agent_jobs_without_event": _scalar(
                connection,
                """
                SELECT COUNT(*)
                FROM agent_jobs AS jobs
                WHERE jobs.status IN ('pending', 'in_progress')
                  AND NOT EXISTS (
                    SELECT 1 FROM outbox_events AS events
                    WHERE events.event_id = 'agent-job:' || jobs.id || ':created'
                  )
                """,
            ),
        }
    report["status"] = "ok" if all(
        report[key] == 0
        for key in ("expired_job_leases", "expired_outbox_leases", "agent_jobs_without_event")
    ) else "attention"
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


def _grouped(connection, statement: str) -> dict[str, int]:
    rows = connection.execute(statement).fetchall()
    return {str(row["status"]): int(row["total"]) for row in rows}


def _scalar(connection, statement: str) -> int:
    return int(connection.execute(statement).fetchone()["count"])


if __name__ == "__main__":
    raise SystemExit(main())
