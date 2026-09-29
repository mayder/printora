from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.finance_orders import FinanceOrderService
from app.finance_payment_operations import FinancePaymentOperationsService
from app.finance_payments import FinancePaymentService
from app.finance_security import FinanceRiskService, FinanceSecurityService
from app.modules.finance.contracts import OrderCreateRequest, OrderItemRequest, PaymentCommandRequest
from app.payment_provider import SandboxPaymentAdapter


def setup_high_risk_order(tmp_path: Path):
    database_path = tmp_path / "risk.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        seller = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('risk-seller@example.com', 'hash')"
        ).lastrowid
        buyer = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('risk-buyer@example.com', 'hash')"
        ).lastrowid
        reviewer = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('risk-reviewer@example.com', 'hash')"
        ).lastrowid
        project = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license, price_cents,
                currency, commercial_terms
            ) VALUES (?, 'high-risk-premium', 'Premium alto', 'public', 'active',
                      'approved', 'premium', 'CC-BY-4.0', 150000, 'BRL', 'Termos')
            """,
            (seller,),
        ).lastrowid
    orders = FinanceOrderService(database_path)
    order = orders.create(
        int(buyer),
        OrderCreateRequest(
            idempotency_key="risk-order-key", items=[OrderItemRequest(project_id=project)]
        ),
    )
    payment = orders.checkout(
        order.public_id, int(buyer), "risk-checkout-key",
        FinancePaymentService(database_path, SandboxPaymentAdapter("risk-sandbox-secret-value")),
    )
    return database_path, int(buyer), int(reviewer), order, payment


def test_high_risk_capture_requires_human_review_and_supports_appeal(tmp_path: Path) -> None:
    database_path, buyer, reviewer, order, payment = setup_high_risk_order(tmp_path)
    risk = FinanceRiskService(database_path)
    case = risk.list_cases("review_required")[0]
    assert case.order_id > 0 and case.score_basis_points == 5000
    assert case.reason_codes == ["high_amount"]

    operations = FinancePaymentOperationsService(database_path)
    with pytest.raises(ValueError, match="revisão de risco"):
        operations.execute(
            payment.public_id,
            PaymentCommandRequest(command="capture", idempotency_key="risk-capture-blocked"),
            reviewer,
        )
    rejected = risk.decide(case.public_id, "reject", "sinal exige comprovação", reviewer)
    assert rejected.status == "rejected"
    appealed = risk.appeal(case.public_id, "documentação enviada", buyer)
    assert appealed.status == "appealed"
    approved = risk.decide(case.public_id, "approve", "documentação validada", reviewer)
    assert approved.status == "approved"
    captured = operations.execute(
        payment.public_id,
        PaymentCommandRequest(command="capture", idempotency_key="risk-capture-approved"),
        reviewer,
    )
    assert captured.result_status == "captured"
    assert FinanceOrderService(database_path).detail(order.public_id, buyer).status == "paid"


def test_finance_roles_are_explicit_revocable_and_audited(tmp_path: Path) -> None:
    database_path, buyer, reviewer, _order, _payment = setup_high_risk_order(tmp_path)
    security = FinanceSecurityService(database_path)

    assigned = security.assign_role(reviewer, "finance_risk", True, buyer)
    assert assigned.active is True
    assert security.has_role(reviewer, {"finance_risk"}) is True
    security.assign_role(reviewer, "finance_risk", False, buyer)
    assert security.has_role(reviewer, {"finance_risk"}) is False
    with connect_database(database_path) as connection:
        audit = connection.execute(
            "SELECT event_type, details_json, retention_until FROM finance_audit_events ORDER BY id"
        ).fetchall()
        assert len(audit) == 2
        assert all(row["event_type"] == "finance.role.changed" for row in audit)
        assert all("password" not in row["details_json"] for row in audit)
        assert all(row["retention_until"] for row in audit)


def test_risk_decisions_and_audit_are_immutable(tmp_path: Path) -> None:
    database_path, _buyer, reviewer, _order, _payment = setup_high_risk_order(tmp_path)
    case = FinanceRiskService(database_path).list_cases("review_required")[0]
    FinanceRiskService(database_path).decide(case.public_id, "approve", "revisado", reviewer)

    with pytest.raises(Exception, match="immutable"):
        with connect_database(database_path) as connection:
            connection.execute("UPDATE finance_risk_decisions SET reason = 'changed'")
    with pytest.raises(Exception, match="cannot be deleted"):
        with connect_database(database_path) as connection:
            connection.execute("DELETE FROM finance_audit_events")
