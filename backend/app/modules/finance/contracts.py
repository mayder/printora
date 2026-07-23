from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.finance.domain import PaymentStatus


class PaymentIntentResponse(BaseModel):
    public_id: str
    provider: str
    amount_minor: int
    currency: str
    status: PaymentStatus
    hosted_checkout_url: str


class PaymentWebhookResponse(BaseModel):
    event_id: str
    status: str
    duplicate: bool = False


class SandboxIntentRequest(BaseModel):
    amount_minor: int = Field(gt=0, le=100_000_000)
    currency: str = Field(min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=8, max_length=160)
