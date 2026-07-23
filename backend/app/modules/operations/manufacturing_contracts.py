from typing import Any, Literal

from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=160)
    material: dict[str, Any]
    machine: dict[str, Any]
    files: list[dict[str, Any]]
    tolerance: dict[str, Any]
    finish: dict[str, Any]
    shipping: dict[str, Any]
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    lead_time_days: int = Field(gt=0, le=365)


class ReservationItem(BaseModel):
    resource_key: str = Field(min_length=1, max_length=120)
    units: int = Field(gt=0)


class AcceptQuoteRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=160)
    resources: list[ReservationItem] = Field(min_length=1, max_length=20)


class TransitionRequest(BaseModel):
    target: str = Field(min_length=3, max_length=40)
    event_key: str = Field(min_length=8, max_length=160)
    reason: str = Field(default="", max_length=500)


class QualityRequest(BaseModel):
    check_key: str = Field(min_length=2, max_length=120)
    specification: dict[str, Any]
    measurement: dict[str, Any]
    passed: bool
    evidence_object_key: str = Field(min_length=3, max_length=500)
    approver_user_id: int = Field(gt=0)


class ShipmentRequest(BaseModel):
    carrier: str = Field(min_length=2, max_length=120)
    tracking_token: str = Field(min_length=6, max_length=240)
    address_ciphertext: str = Field(min_length=8, max_length=4000)


class TrackingRequest(BaseModel):
    provider_event_id: str = Field(min_length=3, max_length=160)
    status: Literal["in_transit", "exception", "delivered", "returned"]
    payload: dict[str, Any]
    occurred_at: str = Field(min_length=10, max_length=80)


class RecallRequest(BaseModel):
    evidence_reference: str = Field(min_length=8, max_length=500)
