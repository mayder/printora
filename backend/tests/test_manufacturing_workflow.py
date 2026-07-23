from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.finance_orders import FinanceOrderService
from app.finance_payment_operations import FinancePaymentOperationsService
from app.finance_payments import FinancePaymentService
from app.manufacturing_workflow import ManufacturingWorkflowService
from app.modules.finance.contracts import OrderCreateRequest, OrderItemRequest, PaymentCommandRequest
from app.payment_provider import SandboxPaymentAdapter


def setup_flow(tmp_path: Path):
    database_path = tmp_path / "manufacturing.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        users = [int(connection.execute(
            "INSERT INTO auth_users (email,password_hash) VALUES (?, 'hash')", (f"mfg-{i}@example.com",)
        ).lastrowid) for i in range(5)]
        project = connection.execute(
            """INSERT INTO print_projects (
                owner_user_id,slug,title,visibility,lifecycle_status,publication_status,
                commercial_class,license,price_cents,currency,commercial_terms
            ) VALUES (?, 'mfg-project','Peça','public','active','approved','premium','CC-BY-4.0',5000,'BRL','Termos')""",
            (users[0],),
        ).lastrowid
        connection.execute(
            "INSERT INTO manufacturing_resources (resource_key,resource_type,available_units,unit) VALUES ('machine-hour','capacity',10,'hour'),('pla-black','material',1000,'gram')"
        )
    orders = FinanceOrderService(database_path)
    order = orders.create(users[1], OrderCreateRequest(
        idempotency_key="mfg-order-key", items=[OrderItemRequest(project_id=project)]
    ))
    payment = orders.checkout(order.public_id, users[1], "mfg-checkout-key", FinancePaymentService(
        database_path, SandboxPaymentAdapter("manufacturing-sandbox-secret")
    ))
    FinancePaymentOperationsService(database_path).execute(
        payment.public_id, PaymentCommandRequest(command="capture", idempotency_key="mfg-capture-key"), users[1]
    )
    return database_path, users, order


def quote_payload():
    return {
        "idempotency_key": "quote-key-001", "material": {"type": "PLA", "grams": 200},
        "machine": {"class": "enclosed"}, "files": [{"checksum": "a" * 64}],
        "tolerance": {"mm": 0.2}, "finish": {"type": "standard"},
        "shipping": {"service": "standard"}, "amount_minor": 6500,
        "currency": "BRL", "lead_time_days": 5,
    }


def advance_to_quality(service, public_id, actor):
    service.transition(public_id, "queued", "event-queued", actor)
    service.transition(public_id, "producing", "event-producing", actor)
    service.transition(public_id, "quality_pending", "event-quality", actor)


def test_quote_snapshot_reservation_and_state_machine(tmp_path: Path) -> None:
    database_path, users, order = setup_flow(tmp_path)
    service = ManufacturingWorkflowService(database_path)
    quote = service.create_quote(order.public_id, quote_payload(), users[2])
    replay = service.create_quote(order.public_id, quote_payload(), users[2])
    manufacturing = service.accept_and_reserve(quote["public_id"], users[1], [
        {"resource_key": "machine-hour", "units": 2}, {"resource_key": "pla-black", "units": 200}
    ], "reserve-001")
    assert replay["public_id"] == quote["public_id"]
    assert manufacturing["state"] == "reserved"
    with pytest.raises(ValueError, match="transição"):
        service.transition(manufacturing["public_id"], "shipped", "invalid-jump", users[2])
    with connect_database(database_path) as connection:
        assert connection.execute(
            "SELECT available_units FROM manufacturing_resources WHERE resource_key='machine-hour'"
        ).fetchone()["available_units"] == 8
    with pytest.raises(Exception, match="cannot be deleted"):
        with connect_database(database_path) as connection:
            connection.execute("DELETE FROM manufacturing_quotes WHERE public_id=?", (quote["public_id"],))


def test_quality_segregation_shipping_tracking_and_recall(tmp_path: Path) -> None:
    database_path, users, order = setup_flow(tmp_path)
    service = ManufacturingWorkflowService(database_path)
    quote = service.create_quote(order.public_id, quote_payload(), users[2])
    manufacturing = service.accept_and_reserve(quote["public_id"], users[1], [
        {"resource_key": "machine-hour", "units": 1}
    ], "reserve-002")
    advance_to_quality(service, manufacturing["public_id"], users[2])
    with pytest.raises(PermissionError, match="própria"):
        service.record_quality(manufacturing["public_id"], "dimensions", {}, {}, True, "private/key", users[2], users[2])
    service.record_quality(
        manufacturing["public_id"], "dimensions", {"mm": 10}, {"mm": 10.1}, True,
        "private/evidence-object", users[2], users[3]
    )
    service.transition(manufacturing["public_id"], "quality_approved", "event-approved", users[3])
    shipment = service.create_shipment(
        manufacturing["public_id"], "Synthetic Carrier", "secret-tracking-token", "ciphertext", users[2]
    )
    first = service.track(shipment["public_id"], "provider-1", "in_transit", b'{"status":"moving"}', "2026-07-22T12:00:00Z", users[2])
    replay = service.track(shipment["public_id"], "provider-1", "in_transit", b"ignored", "2026-07-22T12:00:00Z", users[2])
    service.track(shipment["public_id"], "provider-2", "delivered", b'{"status":"delivered"}', "2026-07-22T13:00:00Z", users[2])
    recall = service.recall(manufacturing["public_id"], "private-evidence", users[4])
    assert replay["id"] == first["id"]
    assert recall["finance_command_key"].startswith("manufacturing-recall:")
    with connect_database(database_path) as connection:
        stored = connection.execute("SELECT tracking_token_hash,address_ciphertext FROM manufacturing_shipments").fetchone()
        assert stored["tracking_token_hash"] != "secret-tracking-token"
        assert stored["address_ciphertext"] == "ciphertext"
        assert connection.execute("SELECT state FROM manufacturing_orders").fetchone()["state"] == "recalled"


def test_concurrent_capacity_guard_is_atomic(tmp_path: Path) -> None:
    database_path, users, order = setup_flow(tmp_path)
    service = ManufacturingWorkflowService(database_path)
    quote = service.create_quote(order.public_id, quote_payload(), users[2])
    with connect_database(database_path) as connection:
        connection.execute("UPDATE manufacturing_resources SET available_units=1 WHERE resource_key='machine-hour'")
    service.accept_and_reserve(quote["public_id"], users[1], [{"resource_key": "machine-hour", "units": 1}], "reserve-final")
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT available_units FROM manufacturing_resources WHERE resource_key='machine-hour'").fetchone()["available_units"] == 0
