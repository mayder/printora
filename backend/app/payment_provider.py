from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Any

from app.modules.finance.domain import Money, PaymentStatus, normalize_currency


FORBIDDEN_CARD_FIELDS = {
    "card_number", "pan", "cvv", "cvc", "security_code", "expiry", "expiration",
}


@dataclass(frozen=True)
class ProviderIntent:
    provider: str
    provider_intent_id: str
    hosted_checkout_url: str
    status: PaymentStatus


@dataclass(frozen=True)
class ProviderEvent:
    event_id: str
    provider_intent_id: str
    event_type: str
    status: PaymentStatus
    created_at: str
    payload_sha256: str


class SandboxPaymentAdapter:
    name = "sandbox"

    def __init__(self, webhook_secret: str) -> None:
        if len(webhook_secret) < 16:
            raise ValueError("segredo de webhook sandbox deve ter ao menos 16 caracteres")
        self.webhook_secret = webhook_secret.encode()

    def create_intent(self, idempotency_key: str, money: Money) -> ProviderIntent:
        token = hashlib.sha256(
            f"{idempotency_key}:{money.amount_minor}:{money.currency}".encode()
        ).hexdigest()[:32]
        return ProviderIntent(
            provider=self.name,
            provider_intent_id=f"sandbox_intent_{token}",
            hosted_checkout_url=f"https://checkout.sandbox.invalid/session/{token}",
            status="requires_action",
        )

    def sign(self, body: bytes) -> str:
        return hmac.new(self.webhook_secret, body, hashlib.sha256).hexdigest()

    def authenticate_event(self, body: bytes, signature: str) -> ProviderEvent:
        expected = self.sign(body)
        if not hmac.compare_digest(expected, signature.strip().lower()):
            raise PermissionError("assinatura do webhook inválida")
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("payload de webhook inválido")
        _reject_card_data(payload)
        return ProviderEvent(
            event_id=_required_text(payload, "event_id"),
            provider_intent_id=_required_text(payload, "provider_intent_id"),
            event_type=_required_text(payload, "event_type"),
            status=_payment_status(payload.get("status")),
            created_at=_required_text(payload, "created_at"),
            payload_sha256=hashlib.sha256(body).hexdigest(),
        )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"campo obrigatório ausente: {key}")
    return value.strip()


def _payment_status(value: object) -> PaymentStatus:
    allowed = {
        "requires_action", "authorized", "captured", "cancelled", "partially_refunded",
        "refunded", "disputed", "failed",
    }
    if not isinstance(value, str) or value not in allowed:
        raise ValueError("status de pagamento inválido")
    return value  # type: ignore[return-value]


def _reject_card_data(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).strip().lower() in FORBIDDEN_CARD_FIELDS:
                raise ValueError("dados brutos de cartão são proibidos")
            _reject_card_data(child)
    elif isinstance(value, list):
        for child in value:
            _reject_card_data(child)
