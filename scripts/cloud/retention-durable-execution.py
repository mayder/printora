#!/var/www/print3dmaker.xyz/current/venv/bin/python
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _backend in (
    Path("/var/www/print3dmaker.xyz/current/backend"),
    Path(__file__).resolve().parents[2] / "backend",
):
    if _backend.is_dir():
        sys.path.insert(0, str(_backend))
        break

import psycopg
from psycopg.rows import dict_row


CONFIRMATION = "DELETE_EXPIRED_DURABLE_RECORDS"
POLICIES = {
    "outbox_events": ("status IN ('published', 'dead_letter')", "updated_at", 30),
    "inbox_receipts": ("status IN ('processed', 'failed')", "received_at", 30),
    "durable_jobs": ("status IN ('succeeded', 'failed', 'dead_letter', 'canceled')", "updated_at", 30),
    "idempotency_records": ("1 = 1", "expires_at", 0),
    "realtime_sessions": ("disconnected_at IS NOT NULL", "disconnected_at", 7),
    "worker_instances": ("state = 'stopped'", "stopped_at", 7),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview e retenção supervisionada da execução durável")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.apply and args.confirm != CONFIRMATION:
        print(f"confirmação inválida; use --confirm {CONFIRMATION}", file=sys.stderr)
        return 2
    database_url = os.environ.get("PRINTORA_DATABASE_URL", "")
    if not database_url.startswith("postgresql://"):
        print("PRINTORA_DATABASE_URL PostgreSQL obrigatória", file=sys.stderr)
        return 2
    report: dict[str, int | str] = {"mode": "apply" if args.apply else "preview"}
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        for table, (condition, timestamp_column, days) in POLICIES.items():
            interval = f"{days} days"
            where = f"{condition} AND {timestamp_column} <= CAST(CURRENT_TIMESTAMP - %s::interval AS TEXT)"
            count = connection.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", (interval,)).fetchone()["count"]
            report[table] = int(count)
            if args.apply and count:
                connection.execute(f"DELETE FROM {table} WHERE {where}", (interval,))
        if not args.apply:
            connection.rollback()
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
