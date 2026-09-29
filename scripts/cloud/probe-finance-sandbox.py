#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from app.database import connect_database, initialize_database
from app.finance_compliance import FinanceComplianceService
from app.finance_orders import FinanceOrderService
from app.finance_payment_operations import FinancePaymentOperationsService
from app.finance_payments import FinancePaymentService
from app.finance_settlement import FinanceSettlementService
from app.modules.finance.contracts import OrderCreateRequest, OrderItemRequest, PaymentCommandRequest
from app.payment_provider import SandboxPaymentAdapter


def main() -> None:
    database_path = Path(os.environ["PRINTORA_DATABASE_PATH"])
    secret = os.environ["PRINTORA_PAYMENT_WEBHOOK_SECRET"]
    if os.environ.get("PRINTORA_PAYMENT_MODE") != "sandbox":
        raise SystemExit("probe exige PRINTORA_PAYMENT_MODE=sandbox")
    if len(secret) < 16:
        raise SystemExit("segredo sandbox ausente ou curto")

    initialize_database(database_path)
    run_id = uuid4().hex
    with connect_database(database_path) as connection:
        seller_id = _user(connection, f"finance-seller-{run_id}@example.invalid")
        buyer_id = _user(connection, f"finance-buyer-{run_id}@example.invalid")
        approver_id = _user(connection, f"finance-approver-{run_id}@example.invalid")
        executor_id = _user(connection, f"finance-executor-{run_id}@example.invalid")
        connection.execute("LOCK TABLE print_projects IN EXCLUSIVE MODE")
        project_id = int(
            connection.execute(
                "SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM print_projects"
            ).fetchone()["next_id"]
        )
        connection.execute(
            """
            INSERT INTO print_projects (
                id, owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license, price_cents,
                currency, commercial_terms
            ) VALUES (?, ?, ?, 'Projeto sintético financeiro', 'public', 'active',
                      'approved', 'premium', 'CC-BY-4.0', 5000, 'BRL',
                      'Somente validação sandbox')
            """,
            (project_id, seller_id, f"finance-sandbox-{run_id}"),
        )

    orders = FinanceOrderService(database_path)
    order = orders.create(
        buyer_id,
        OrderCreateRequest(
            idempotency_key=f"order-{run_id}",
            items=[OrderItemRequest(project_id=project_id)],
            country_code="BR",
        ),
    )
    payment = orders.checkout(
        order.public_id,
        buyer_id,
        f"checkout-{run_id}",
        FinancePaymentService(database_path, SandboxPaymentAdapter(secret)),
    )
    operations = FinancePaymentOperationsService(database_path)
    captured = operations.execute(
        payment.public_id,
        PaymentCommandRequest(command="capture", idempotency_key=f"capture-{run_id}"),
        buyer_id,
    )
    replay = operations.execute(
        payment.public_id,
        PaymentCommandRequest(command="capture", idempotency_key=f"capture-{run_id}"),
        buyer_id,
    )
    refunded = operations.execute(
        payment.public_id,
        PaymentCommandRequest(
            command="refund",
            idempotency_key=f"refund-{run_id}",
            amount_minor=1000,
            reason="prova sintética",
        ),
        buyer_id,
    )

    settlement = FinanceSettlementService(database_path)
    with connect_database(database_path) as connection:
        clearing_minor = int(connection.execute(
            """SELECT COALESCE(SUM(CASE WHEN entry.side = 'debit' THEN entry.amount_minor ELSE -entry.amount_minor END), 0) AS amount
               FROM finance_accounts account
               LEFT JOIN finance_ledger_entries entry ON entry.account_id = account.id
               WHERE account.code = 'provider_clearing:BRL'"""
        ).fetchone()["amount"])
    reconciliation = settlement.reconcile(
        "BRL", clearing_minor, f"sandbox-report-{run_id}", approver_id
    )
    payout = settlement.request_payout(seller_id, "BRL", 3000, f"payout-{run_id}")
    approved = settlement.approve_payout(payout.public_id, approver_id)
    paid = settlement.execute_payout(payout.public_id, executor_id)
    balance = settlement.balance(seller_id, "BRL")
    readiness = FinanceComplianceService(database_path).readiness()

    with connect_database(database_path) as connection:
        ledger_balance = connection.execute(
            """
            SELECT COALESCE(SUM(CASE WHEN side = 'debit' THEN amount_minor ELSE -amount_minor END), 0)
                   AS balance
            FROM finance_ledger_entries
            """
        ).fetchone()["balance"]
        raw_payload_columns = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'payment_webhook_events'
              AND column_name IN ('payload', 'raw_payload', 'pan', 'cvv')
            """
        ).fetchone()["total"]

    checks = {
        "capture": captured.result_status == "captured",
        "idempotent_replay": replay.duplicate is True,
        "partial_refund": refunded.result_status == "partially_refunded",
        "reconciliation": reconciliation.status == "passed",
        "payout_segregation": approved.status == "approved" and paid.status == "paid",
        "remaining_balance_minor": balance.available_minor == 1000,
        "ledger_balanced": int(ledger_balance) == 0,
        "no_raw_card_payload_columns": int(raw_payload_columns) == 0,
        "real_payments_blocked": readiness.real_payments_allowed is False,
    }
    if not all(checks.values()):
        raise SystemExit(json.dumps({"checks": checks}, sort_keys=True))
    print(json.dumps({"checks": checks, "run_id": run_id}, sort_keys=True))


def _user(connection, email: str) -> int:
    return int(
        connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES (?, 'synthetic-no-login')",
            (email,),
        ).lastrowid
    )


if __name__ == "__main__":
    main()
