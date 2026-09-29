from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.finance_orders import FinanceOrderService
from app.finance_payment_operations import FinancePaymentOperationsService
from app.finance_payments import FinancePaymentService
from app.modules.finance.contracts import (
    OrderCreateRequest,
    OrderItemRequest,
    PaymentCommandRequest,
)
from app.payment_provider import SandboxPaymentAdapter


def setup_paid_flow(tmp_path: Path, key: str = "one"):
    database_path = tmp_path / f"{key}.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        seller_id = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES (?, 'hash')", (f"seller-{key}@example.com",)
        ).lastrowid
        buyer_id = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES (?, 'hash')", (f"buyer-{key}@example.com",)
        ).lastrowid
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license, price_cents,
                currency, commercial_terms
            ) VALUES (?, ?, 'Premium', 'public', 'active', 'approved', 'premium',
                      'CC-BY-4.0', 5000, 'BRL', 'Termos')
            """,
            (seller_id, f"premium-{key}"),
        ).lastrowid
    order_service = FinanceOrderService(database_path)
    order = order_service.create(
        int(buyer_id),
        OrderCreateRequest(
            idempotency_key=f"order-key-{key}", items=[OrderItemRequest(project_id=project_id)]
        ),
    )
    payment = order_service.checkout(
        order.public_id,
        int(buyer_id),
        f"checkout-key-{key}",
        FinancePaymentService(database_path, SandboxPaymentAdapter("sandbox-secret-for-operations")),
    )
    return database_path, int(buyer_id), int(seller_id), order, payment


def command(name: str, key: str, amount: int | None = None, reason: str = "test") -> PaymentCommandRequest:
    return PaymentCommandRequest(
        command=name, idempotency_key=key, amount_minor=amount, reason=reason
    )


def test_capture_and_refunds_post_balanced_compensations(tmp_path: Path) -> None:
    database_path, buyer_id, seller_id, order, payment = setup_paid_flow(tmp_path)
    service = FinancePaymentOperationsService(database_path)

    captured = service.execute(payment.public_id, command("capture", "capture-key-one"), buyer_id)
    replay = service.execute(payment.public_id, command("capture", "capture-key-one"), buyer_id)
    partial = service.execute(payment.public_id, command("refund", "refund-key-one", 1200), buyer_id)
    with pytest.raises(ValueError, match="excede"):
        service.execute(payment.public_id, command("refund", "refund-key-too-much", 4000), buyer_id)
    final = service.execute(payment.public_id, command("refund", "refund-key-final", 3800), buyer_id)

    assert replay.duplicate is True and replay.command_id == captured.command_id
    assert partial.result_status == "partially_refunded"
    assert final.result_status == "refunded"
    with connect_database(database_path) as connection:
        assert connection.execute(
            "SELECT status FROM commerce_orders WHERE public_id = ?", (order.public_id,)
        ).fetchone()["status"] == "refunded"
        balance = connection.execute(
            """
            SELECT SUM(CASE WHEN entry.side = 'debit' THEN entry.amount_minor ELSE -entry.amount_minor END) AS balance
            FROM finance_ledger_entries entry
            """
        ).fetchone()["balance"]
        assert int(balance) == 0
        allocations = connection.execute(
            "SELECT seller_user_id, SUM(amount_minor) AS amount FROM payment_refund_allocations GROUP BY seller_user_id"
        ).fetchone()
        assert int(allocations["seller_user_id"]) == seller_id
        assert int(allocations["amount"]) == 5000


def test_cancel_before_capture_has_no_ledger_entry(tmp_path: Path) -> None:
    database_path, buyer_id, _seller_id, order, payment = setup_paid_flow(tmp_path, "cancel")
    result = FinancePaymentOperationsService(database_path).execute(
        payment.public_id, command("cancel", "cancel-command-key"), buyer_id
    )

    assert result.result_status == "cancelled"
    with connect_database(database_path) as connection:
        assert connection.execute(
            "SELECT status FROM commerce_orders WHERE public_id = ?", (order.public_id,)
        ).fetchone()["status"] == "cancelled"
        assert connection.execute(
            "SELECT COUNT(*) AS total FROM finance_ledger_transactions"
        ).fetchone()["total"] == 0


def test_dispute_open_and_win_restore_payable_without_mutating_prior_ledger(tmp_path: Path) -> None:
    database_path, buyer_id, _seller_id, order, payment = setup_paid_flow(tmp_path, "dispute")
    service = FinancePaymentOperationsService(database_path)
    service.execute(payment.public_id, command("capture", "capture-dispute-key"), buyer_id)
    opened = service.execute(
        payment.public_id, command("open_dispute", "open-dispute-key", 2000, "fraud"), buyer_id
    )
    won = service.execute(
        payment.public_id, command("resolve_dispute_won", "resolve-dispute-key"), buyer_id
    )

    assert opened.result_status == "disputed"
    assert won.result_status == "won"
    with connect_database(database_path) as connection:
        dispute = connection.execute("SELECT status FROM payment_disputes").fetchone()
        assert dispute["status"] == "won"
        assert connection.execute(
            "SELECT status FROM commerce_orders WHERE public_id = ?", (order.public_id,)
        ).fetchone()["status"] == "paid"
        assert connection.execute(
            "SELECT COUNT(*) AS total FROM finance_ledger_transactions WHERE status = 'posted'"
        ).fetchone()["total"] == 3
