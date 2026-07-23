from pathlib import Path
import json

import pytest

from app.database import connect_database, initialize_database
from app.finance_payments import FinancePaymentService
from app.modules.finance.domain import Money
from app.payment_provider import SandboxPaymentAdapter


SECRET = "sandbox-webhook-secret-for-tests"


def setup_service(tmp_path: Path) -> tuple[Path, FinancePaymentService, SandboxPaymentAdapter]:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    adapter = SandboxPaymentAdapter(SECRET)
    return database_path, FinancePaymentService(database_path, adapter), adapter


def event_body(intent_id: str, event_id: str, status: str, created_at: str) -> bytes:
    return json.dumps(
        {
            "event_id": event_id,
            "provider_intent_id": intent_id,
            "event_type": f"payment.{status}",
            "status": status,
            "created_at": created_at,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def provider_intent_id(database_path: Path, public_id: str) -> str:
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT provider_intent_id FROM payment_intents WHERE public_id = ?", (public_id,)
        ).fetchone()
    return str(row["provider_intent_id"])


def test_intent_uses_hosted_sandbox_and_is_idempotent(tmp_path: Path) -> None:
    database_path, service, _adapter = setup_service(tmp_path)

    first = service.create_intent("checkout-order-123", Money(2500, "BRL"), None)
    replay = service.create_intent("checkout-order-123", Money(2500, "BRL"), None)

    assert replay == first
    assert first.hosted_checkout_url.startswith("https://checkout.sandbox.invalid/")
    assert first.status == "requires_action"
    with pytest.raises(ValueError, match="intent diferente"):
        service.create_intent("checkout-order-123", Money(2501, "BRL"), None)
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) AS total FROM payment_intents").fetchone()["total"] == 1


def test_signed_webhook_replay_and_out_of_order_do_not_duplicate_state(tmp_path: Path) -> None:
    database_path, service, adapter = setup_service(tmp_path)
    intent = service.create_intent("checkout-order-456", Money(9900, "BRL"), None)
    provider_id = provider_intent_id(database_path, intent.public_id)
    captured = event_body(provider_id, "evt-captured", "captured", "2026-07-22T22:00:00+00:00")

    processed = service.process_webhook(captured, adapter.sign(captured))
    duplicate = service.process_webhook(captured, adapter.sign(captured))
    older = event_body(provider_id, "evt-older", "authorized", "2026-07-22T21:00:00+00:00")
    ignored = service.process_webhook(older, adapter.sign(older))

    assert processed.status == "processed"
    assert duplicate.duplicate is True
    assert ignored.status == "ignored_out_of_order"
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT status FROM payment_intents WHERE public_id = ?", (intent.public_id,)
        ).fetchone()
        assert row["status"] == "captured"
        assert connection.execute(
            "SELECT COUNT(*) AS total FROM payment_webhook_events"
        ).fetchone()["total"] == 2


def test_invalid_signature_card_data_and_invalid_transition_are_rejected(tmp_path: Path) -> None:
    database_path, service, adapter = setup_service(tmp_path)
    intent = service.create_intent("checkout-order-789", Money(5000, "BRL"), None)
    provider_id = provider_intent_id(database_path, intent.public_id)
    captured = event_body(provider_id, "evt-good", "captured", "2026-07-22T22:00:00+00:00")

    with pytest.raises(PermissionError, match="assinatura"):
        service.process_webhook(captured, "0" * 64)
    raw_card = json.dumps(
        {
            "event_id": "evt-card",
            "provider_intent_id": provider_id,
            "event_type": "payment.authorized",
            "status": "authorized",
            "created_at": "2026-07-22T21:00:00+00:00",
            "card_number": "4111111111111111",
        }
    ).encode()
    with pytest.raises(ValueError, match="cartão"):
        service.process_webhook(raw_card, adapter.sign(raw_card))

    service.process_webhook(captured, adapter.sign(captured))
    cancelled = event_body(provider_id, "evt-invalid", "cancelled", "2026-07-22T23:00:00+00:00")
    rejected = service.process_webhook(cancelled, adapter.sign(cancelled))
    assert rejected.status == "rejected"
    with connect_database(database_path) as connection:
        columns = connection.execute("PRAGMA table_info(payment_webhook_events)").fetchall()
        assert "payload" not in {str(row["name"]) for row in columns}
        assert connection.execute(
            "SELECT status FROM payment_intents WHERE public_id = ?", (intent.public_id,)
        ).fetchone()["status"] == "captured"
