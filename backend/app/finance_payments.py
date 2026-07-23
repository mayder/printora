from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid

from app.database import connect_database
from app.modules.finance.contracts import PaymentIntentResponse, PaymentWebhookResponse
from app.modules.finance.domain import Money, PaymentStatus, validate_payment_transition
from app.payment_provider import ProviderEvent, SandboxPaymentAdapter


class FinancePaymentService:
    def __init__(self, database_path: Path, adapter: SandboxPaymentAdapter) -> None:
        self.database_path = database_path
        self.adapter = adapter

    def create_intent(
        self,
        idempotency_key: str,
        money: Money,
        created_by_user_id: int | None,
        order_id: int | None = None,
    ) -> PaymentIntentResponse:
        digest = _intent_digest(idempotency_key, money, order_id, created_by_user_id)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM payment_intents WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                if existing["command_digest"] != digest:
                    raise ValueError("chave idempotente já usada com intent diferente")
                return _intent_response(existing)
            provider = self.adapter.create_intent(idempotency_key, money)
            public_id = f"pay_{uuid.uuid4().hex}"
            connection.execute(
                """
                INSERT INTO payment_intents (
                    public_id, order_id, provider, provider_intent_id, idempotency_key,
                    command_digest, amount_minor, currency, status,
                    hosted_checkout_url, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_id, order_id, provider.provider, provider.provider_intent_id,
                    idempotency_key, digest, money.amount_minor, money.currency,
                    provider.status, provider.hosted_checkout_url, created_by_user_id,
                ),
            )
            row = connection.execute(
                "SELECT * FROM payment_intents WHERE public_id = ?", (public_id,)
            ).fetchone()
        return _intent_response(row)

    def process_webhook(self, body: bytes, signature: str) -> PaymentWebhookResponse:
        event = self.adapter.authenticate_event(body, signature)
        with connect_database(self.database_path) as connection:
            duplicate = connection.execute(
                """
                SELECT processing_status FROM payment_webhook_events
                WHERE provider = ? AND provider_event_id = ?
                """,
                (self.adapter.name, event.event_id),
            ).fetchone()
            if duplicate is not None:
                return PaymentWebhookResponse(
                    event_id=event.event_id,
                    status=str(duplicate["processing_status"]),
                    duplicate=True,
                )
            status = self._apply_event(connection, event)
            connection.execute(
                """
                INSERT INTO payment_webhook_events (
                    provider, provider_event_id, provider_intent_id, event_type,
                    event_created_at, payload_sha256, signature_verified, processing_status
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    self.adapter.name, event.event_id, event.provider_intent_id,
                    event.event_type, event.created_at, event.payload_sha256, status,
                ),
            )
        return PaymentWebhookResponse(event_id=event.event_id, status=status)

    @staticmethod
    def _apply_event(connection, event: ProviderEvent) -> str:
        row = connection.execute(
            "SELECT id, status, latest_provider_event_at FROM payment_intents WHERE provider_intent_id = ?",
            (event.provider_intent_id,),
        ).fetchone()
        if row is None:
            return "rejected"
        if row["latest_provider_event_at"] and str(row["latest_provider_event_at"]) >= event.created_at:
            return "ignored_out_of_order"
        try:
            validate_payment_transition(str(row["status"]), event.status)  # type: ignore[arg-type]
        except ValueError:
            return "rejected"
        connection.execute(
            """
            UPDATE payment_intents
            SET status = ?, latest_provider_event_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (event.status, event.created_at, row["id"]),
        )
        return "processed"


def _intent_digest(
    idempotency_key: str,
    money: Money,
    order_id: int | None,
    created_by_user_id: int | None,
) -> str:
    payload = {
        "idempotency_key": idempotency_key,
        "amount_minor": money.amount_minor,
        "currency": money.currency,
        "order_id": order_id,
        "created_by_user_id": created_by_user_id,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _intent_response(row) -> PaymentIntentResponse:
    return PaymentIntentResponse(
        public_id=str(row["public_id"]),
        provider=str(row["provider"]),
        amount_minor=int(row["amount_minor"]),
        currency=str(row["currency"]),
        status=str(row["status"]),
        hosted_checkout_url=str(row["hosted_checkout_url"]),
    )
