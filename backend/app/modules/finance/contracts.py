from __future__ import annotations

from typing import Literal

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


class PaymentCommandRequest(BaseModel):
    command: Literal[
        "capture", "cancel", "refund", "open_dispute",
        "resolve_dispute_won", "resolve_dispute_lost",
    ]
    idempotency_key: str = Field(min_length=8, max_length=160)
    amount_minor: int | None = Field(default=None, gt=0)
    reason: str = Field(default="", max_length=240)


class PaymentCommandResponse(BaseModel):
    command_id: int
    payment_public_id: str
    command: str
    result_status: str
    amount_minor: int | None
    duplicate: bool = False


class FinanceBalanceResponse(BaseModel):
    seller_user_id: int
    currency: str
    ledger_balance_minor: int
    reserved_minor: int
    available_minor: int
    negative_balance_policy: str


class ReconciliationRequest(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    provider_reported_minor: int = Field(ge=0)
    evidence_reference: str = Field(min_length=3, max_length=240)


class ReconciliationResponse(BaseModel):
    public_id: str
    currency: str
    ledger_clearing_minor: int
    provider_reported_minor: int
    difference_minor: int
    status: str


class PayoutRequest(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    amount_minor: int = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=160)


class PayoutResponse(BaseModel):
    public_id: str
    seller_user_id: int
    currency: str
    amount_minor: int
    status: str
    requested_by_user_id: int
    approved_by_user_id: int | None


class ClosingRequest(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    period_key: str = Field(min_length=7, max_length=32)


class ClosingResponse(BaseModel):
    public_id: str
    currency: str
    period_key: str
    status: str
    ledger_transaction_count: int
    ledger_imbalance_count: int
    open_dispute_count: int


class FinanceRoleRequest(BaseModel):
    user_id: int = Field(ge=1)
    role: Literal[
        "finance_operator", "finance_approver", "finance_risk",
        "finance_support", "finance_auditor",
    ]
    active: bool = True


class FinanceRoleResponse(BaseModel):
    user_id: int
    role: str
    active: bool


class RiskCaseResponse(BaseModel):
    public_id: str
    order_id: int
    buyer_user_id: int
    score_basis_points: int
    risk_level: str
    reason_codes: list[str]
    recommended_action: str
    status: str


class RiskDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=3, max_length=500)


class RiskAppealRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ComplianceControlRequest(BaseModel):
    status: Literal["pending", "passed", "blocked"]
    evidence_reference: str = Field(min_length=3, max_length=500)
    expires_at: str | None = Field(default=None, max_length=80)


class ComplianceControlResponse(BaseModel):
    control_key: str
    status: str
    evidence_present: bool
    reviewed_by_user_id: int | None
    reviewed_at: str | None
    expires_at: str | None


class RetentionPolicyResponse(BaseModel):
    data_class: str
    retention_days: int
    legal_basis: str
    deletion_mode: str


class FinanceReadinessResponse(BaseModel):
    payment_mode: str
    runtime_supports_real_payments: bool
    real_payments_allowed: bool
    pending_controls: list[str]
    blocked_controls: list[str]
    controls: list[ComplianceControlResponse]
    retention_policies: list[RetentionPolicyResponse]
    expired_audit_rows_preview: int
