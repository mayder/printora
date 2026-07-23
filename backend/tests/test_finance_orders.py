from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.finance_orders import FinanceOrderService
from app.finance_payments import FinancePaymentService
from app.modules.finance.contracts import OrderCreateRequest, OrderItemRequest
from app.payment_provider import SandboxPaymentAdapter


def setup_catalog(database_path: Path) -> tuple[int, int, int]:
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        seller_id = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('seller@example.com', 'hash')"
        ).lastrowid
        buyer_id = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('buyer@example.com', 'hash')"
        ).lastrowid
        other_id = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('other@example.com', 'hash')"
        ).lastrowid
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license, price_cents,
                currency, commercial_terms
            ) VALUES (?, 'premium-project', 'Projeto Premium', 'public', 'active',
                      'approved', 'premium', 'CC-BY-4.0', 2500, 'BRL', 'Uso comercial permitido')
            """,
            (seller_id,),
        ).lastrowid
        version_id = connection.execute(
            """
            INSERT INTO print_project_versions (
                project_id, version_label, project_snapshot_json, files_snapshot_json,
                created_by_user_id
            ) VALUES (?, 'v1', '{"title":"Projeto Premium"}', '[]', ?)
            """,
            (project_id, seller_id),
        ).lastrowid
        connection.execute(
            "UPDATE print_projects SET current_version_id = ? WHERE id = ?",
            (version_id, project_id),
        )
    return int(buyer_id), int(other_id), int(project_id)


def payload(project_id: int, *, key: str = "order-idempotency-1", quantity: int = 2) -> OrderCreateRequest:
    return OrderCreateRequest(
        idempotency_key=key,
        items=[OrderItemRequest(project_id=project_id, quantity=quantity)],
        country_code="BR",
    )


def test_order_snapshots_approved_project_and_replay_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    buyer_id, _other_id, project_id = setup_catalog(database_path)
    service = FinanceOrderService(database_path)

    created = service.create(buyer_id, payload(project_id))
    replay = service.create(buyer_id, payload(project_id))
    with connect_database(database_path) as connection:
        connection.execute(
            "UPDATE print_projects SET title = 'Título alterado', price_cents = 9999 WHERE id = ?",
            (project_id,),
        )
    unchanged = service.detail(created.public_id, buyer_id)

    assert replay == created
    assert created.total_minor == 5000
    assert unchanged.items[0].title == "Projeto Premium"
    assert unchanged.items[0].unit_price_minor == 2500
    assert unchanged.items[0].license == "CC-BY-4.0"
    assert unchanged.tax_status == "not_configured"


def test_order_rejects_changed_replay_ineligible_project_and_cross_user_access(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    buyer_id, other_id, project_id = setup_catalog(database_path)
    service = FinanceOrderService(database_path)
    created = service.create(buyer_id, payload(project_id))

    with pytest.raises(ValueError, match="pedido diferente"):
        service.create(buyer_id, payload(project_id, quantity=3))
    with pytest.raises(ValueError, match="não encontrado"):
        service.detail(created.public_id, other_id)
    with connect_database(database_path) as connection:
        connection.execute("UPDATE print_projects SET publication_status = 'rejected' WHERE id = ?", (project_id,))
    with pytest.raises(ValueError, match="elegível"):
        service.create(buyer_id, payload(project_id, key="order-idempotency-2"))


def test_checkout_links_intent_and_snapshot_rows_are_immutable(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    buyer_id, _other_id, project_id = setup_catalog(database_path)
    order_service = FinanceOrderService(database_path)
    order = order_service.create(buyer_id, payload(project_id))
    payment_service = FinancePaymentService(
        database_path, SandboxPaymentAdapter("sandbox-secret-at-least-sixteen")
    )

    intent = order_service.checkout(order.public_id, buyer_id, "checkout-idempotency-1", payment_service)
    replay = order_service.checkout(order.public_id, buyer_id, "checkout-idempotency-1", payment_service)

    assert replay == intent
    assert order_service.detail(order.public_id, buyer_id).status == "pending_payment"
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT order_id FROM payment_intents WHERE public_id = ?", (intent.public_id,)
        ).fetchone()
        assert row["order_id"] is not None
    with pytest.raises(Exception, match="immutable"):
        with connect_database(database_path) as connection:
            connection.execute(
                "UPDATE commerce_order_items SET unit_price_minor = 1 WHERE order_id = ?", (row["order_id"],)
            )
    with pytest.raises(Exception, match="immutable"):
        with connect_database(database_path) as connection:
            connection.execute(
                "UPDATE commerce_orders SET total_minor = 1 WHERE id = ?", (row["order_id"],)
            )
