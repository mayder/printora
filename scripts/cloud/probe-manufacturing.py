#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from app.database import connect_database
from app.manufacturing_workflow import ManufacturingWorkflowService


def main() -> None:
    database_path = Path(os.environ.get("PRINTORA_DATABASE_PATH", "/tmp/printora-probe.db"))
    run_id = uuid4().hex
    with connect_database(database_path) as connection:
        users = [_user(connection, f"manufacturing-{role}-{run_id}@example.invalid") for role in (
            "buyer", "operator", "inspector", "approver", "safety"
        )]
        project = connection.execute(
            "SELECT id,owner_user_id,title,license,price_cents,currency,commercial_terms FROM print_projects WHERE slug LIKE 'finance-sandbox-%%' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not project:
            raise SystemExit("projeto sintético financeiro ausente")
        order_public_id = f"ord_mfg_{run_id}"
        order_id = connection.execute(
            """INSERT INTO commerce_orders (
                public_id,buyer_user_id,idempotency_key,command_digest,currency,
                subtotal_minor,total_minor,status,country_code,tax_status
            ) VALUES (?,?,?,?,?,5000,5000,'paid','BR','not_configured')""",
            (order_public_id, users[0], f"mfg-order-{run_id}", run_id, "BRL"),
        ).lastrowid
        connection.execute(
            """INSERT INTO commerce_order_items (
                order_id,source_project_id,seller_user_id,title_snapshot,license_snapshot,
                terms_snapshot,project_snapshot_json,unit_price_minor,quantity,currency
            ) VALUES (?,?,?,?,?,?,?,?,1,'BRL')""",
            (order_id, project["id"], project["owner_user_id"], project["title"],
             project["license"], project["commercial_terms"], json.dumps(dict(project), default=str), 5000),
        )
        connection.execute(
            "INSERT INTO manufacturing_resources (resource_key,resource_type,available_units,unit) VALUES (?, 'capacity', 2, 'hour'), (?, 'material', 500, 'gram')",
            (f"machine-{run_id}", f"material-{run_id}"),
        )

    service = ManufacturingWorkflowService(database_path)
    quote = service.create_quote(order_public_id, {
        "idempotency_key": f"quote-{run_id}", "material": {"grams": 100},
        "machine": {"class": "synthetic"}, "files": [{"checksum": "a" * 64}],
        "tolerance": {"mm": 0.2}, "finish": {"type": "standard"},
        "shipping": {"service": "synthetic"}, "amount_minor": 5000,
        "currency": "BRL", "lead_time_days": 1,
    }, users[1])
    order = service.accept_and_reserve(quote["public_id"], users[0], [
        {"resource_key": f"machine-{run_id}", "units": 1},
        {"resource_key": f"material-{run_id}", "units": 100},
    ], f"reserve-{run_id}")
    for target in ("queued", "producing", "quality_pending"):
        service.transition(order["public_id"], target, f"{target}-{run_id}", users[1])
    service.record_quality(order["public_id"], "dimensions", {"mm": 10}, {"mm": 10.1}, True,
                           f"private/evidence/{run_id}", users[2], users[3])
    service.transition(order["public_id"], "quality_approved", f"approved-{run_id}", users[3])
    shipment = service.create_shipment(order["public_id"], "Synthetic Carrier", f"token-{run_id}",
                                       f"ciphertext-{run_id}", users[1])
    service.track(shipment["public_id"], f"track-1-{run_id}", "in_transit", b"moving",
                  "2026-07-23T00:00:00Z", users[1])
    service.track(shipment["public_id"], f"track-2-{run_id}", "delivered", b"delivered",
                  "2026-07-23T00:01:00Z", users[1])
    recall = service.recall(order["public_id"], f"private-recall-{run_id}", users[4])
    with connect_database(database_path) as connection:
        state = connection.execute("SELECT state FROM manufacturing_orders WHERE public_id=?", (order["public_id"],)).fetchone()["state"]
        leaks = connection.execute("SELECT COUNT(*) AS total FROM manufacturing_shipments WHERE tracking_token_hash LIKE 'token-%%'").fetchone()["total"]
    checks = {"accepted": order["state"] == "reserved", "delivered_then_recalled": state == "recalled",
              "tracking_token_hashed": int(leaks) == 0, "finance_is_command_only": bool(recall["finance_command_key"])}
    if not all(checks.values()):
        raise SystemExit(json.dumps(checks, sort_keys=True))
    print(json.dumps({"checks": checks, "run_id": run_id}, sort_keys=True))


def _user(connection, email: str) -> int:
    return int(connection.execute("INSERT INTO auth_users (email,password_hash) VALUES (?, 'synthetic-no-login')", (email,)).lastrowid)


if __name__ == "__main__":
    main()
