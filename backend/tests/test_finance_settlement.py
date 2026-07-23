from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.finance_orders import FinanceOrderService
from app.finance_payment_operations import FinancePaymentOperationsService
from app.finance_payments import FinancePaymentService
from app.finance_settlement import FinanceSettlementService
from app.modules.finance.contracts import OrderCreateRequest, OrderItemRequest, PaymentCommandRequest
from app.payment_provider import SandboxPaymentAdapter


def setup_capture(tmp_path: Path):
    database_path = tmp_path / "settlement.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        seller = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('settle-seller@example.com', 'hash')"
        ).lastrowid
        approver = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('settle-approver@example.com', 'hash')"
        ).lastrowid
        executor = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('settle-executor@example.com', 'hash')"
        ).lastrowid
        project = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license, price_cents,
                currency, commercial_terms
            ) VALUES (?, 'settlement-premium', 'Premium', 'public', 'active',
                      'approved', 'premium', 'CC-BY-4.0', 5000, 'BRL', 'Termos')
            """,
            (seller,),
        ).lastrowid
    orders = FinanceOrderService(database_path)
    order = orders.create(
        int(approver),
        OrderCreateRequest(
            idempotency_key="settlement-order-key",
            items=[OrderItemRequest(project_id=project)],
        ),
    )
    payment = orders.checkout(
        order.public_id, int(approver), "settlement-checkout-key",
        FinancePaymentService(database_path, SandboxPaymentAdapter("settlement-sandbox-secret")),
    )
    FinancePaymentOperationsService(database_path).execute(
        payment.public_id,
        PaymentCommandRequest(command="capture", idempotency_key="settlement-capture-key"),
        int(approver),
    )
    return database_path, int(seller), int(approver), int(executor), payment.public_id


def test_balance_payout_reconciliation_and_closing(tmp_path: Path) -> None:
    database_path, seller, approver, executor, _payment_id = setup_capture(tmp_path)
    service = FinanceSettlementService(database_path)

    balance = service.balance(seller, "BRL")
    payout = service.request_payout(seller, "BRL", 4000, "payout-request-key")
    replay = service.request_payout(seller, "BRL", 4000, "payout-request-key")
    assert balance.ledger_balance_minor == 5000 and balance.available_minor == 5000
    assert replay == payout
    assert service.balance(seller, "BRL").available_minor == 1000
    with pytest.raises(ValueError, match="excede"):
        service.request_payout(seller, "BRL", 1001, "payout-over-balance")
    with pytest.raises(PermissionError, match="próprio"):
        service.approve_payout(payout.public_id, seller)

    blocked = service.reconcile("BRL", 4999, "sandbox-report-mismatch", approver)
    approved = service.approve_payout(payout.public_id, approver)
    assert blocked.status == "blocked" and approved.status == "approved"
    with pytest.raises(ValueError, match="divergente"):
        service.execute_payout(payout.public_id, executor)

    passed = service.reconcile("BRL", 5000, "sandbox-report-match", approver)
    with pytest.raises(PermissionError, match="próprio"):
        service.execute_payout(payout.public_id, approver)
    paid = service.execute_payout(payout.public_id, executor)
    assert passed.status == "passed" and paid.status == "paid"
    assert service.balance(seller, "BRL").ledger_balance_minor == 1000

    stale = service.close("BRL", "2026-07-stale", approver)
    assert stale.status == "blocked"
    service.reconcile("BRL", 1000, "sandbox-report-after-payout", approver)
    closed = service.close("BRL", "2026-07", approver)
    assert closed.status == "closed"
    assert closed.ledger_imbalance_count == 0


def test_open_dispute_blocks_payout_execution(tmp_path: Path) -> None:
    database_path, seller, approver, executor, payment_id = setup_capture(tmp_path)
    settlement = FinanceSettlementService(database_path)
    payout = settlement.request_payout(seller, "BRL", 1000, "dispute-payout-key")
    settlement.approve_payout(payout.public_id, approver)
    FinancePaymentOperationsService(database_path).execute(
        payment_id,
        PaymentCommandRequest(
            command="open_dispute", idempotency_key="settlement-dispute-key", amount_minor=500
        ),
        approver,
    )
    settlement.reconcile("BRL", 4500, "sandbox-dispute-report", approver)

    with pytest.raises(ValueError, match="disputa aberta"):
        settlement.execute_payout(payout.public_id, executor)


def test_negative_balance_policy_blocks_new_payout(tmp_path: Path) -> None:
    database_path, seller, approver, _executor, payment_id = setup_capture(tmp_path)
    FinancePaymentOperationsService(database_path).execute(
        payment_id,
        PaymentCommandRequest(
            command="refund", idempotency_key="settlement-full-refund", amount_minor=5000
        ),
        approver,
    )
    balance = FinanceSettlementService(database_path).balance(seller, "BRL")
    assert balance.available_minor == 0
    assert "ganhos futuros" in balance.negative_balance_policy
    with pytest.raises(ValueError, match="excede"):
        FinanceSettlementService(database_path).request_payout(
            seller, "BRL", 1, "negative-payout-key"
        )
