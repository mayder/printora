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


class OrderItemRequest(BaseModel):
    project_id: int = Field(ge=1)
    quantity: int = Field(default=1, ge=1, le=100)


class OrderCreateRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=160)
    items: list[OrderItemRequest] = Field(min_length=1, max_length=50)
    country_code: str = Field(default="BR", min_length=2, max_length=2)


class OrderItemResponse(BaseModel):
    id: int
    project_id: int
    project_version_id: int | None
    title: str
    license: str
    terms: str
    unit_price_minor: int
    quantity: int
    currency: str


class OrderResponse(BaseModel):
    public_id: str
    buyer_user_id: int
    status: str
    currency: str
    subtotal_minor: int
    fee_minor: int
    tax_minor: int
    total_minor: int
    country_code: str
    tax_status: str
    items: list[OrderItemResponse]


class OrderCheckoutRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=160)
