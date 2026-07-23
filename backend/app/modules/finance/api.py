from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import get_settings
from app.auth import AuthRepository
from app.finance_payments import FinancePaymentService
from app.finance_orders import FinanceOrderService
from app.finance_payment_operations import FinancePaymentOperationsService
from app.finance_settlement import FinanceSettlementService
from app.finance_security import FinanceRiskService, FinanceSecurityService
from app.finance_compliance import FinanceComplianceService
from app.finance_queries import FinanceAdminQueryService
from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.modules.finance.contracts import (
    PaymentIntentResponse,
    PaymentWebhookResponse,
    SandboxIntentRequest,
    OrderCheckoutRequest,
    OrderCreateRequest,
    OrderResponse,
    PaymentCommandRequest,
    PaymentCommandResponse,
    ClosingRequest,
    ClosingResponse,
    FinanceBalanceResponse,
    PayoutRequest,
    PayoutResponse,
    ReconciliationRequest,
    ReconciliationResponse,
    FinanceRoleRequest,
    FinanceRoleResponse,
    RiskAppealRequest,
    RiskCaseResponse,
    RiskDecisionRequest,
    ComplianceControlRequest,
    ComplianceControlResponse,
    FinanceReadinessResponse,
)
from app.modules.finance.domain import Money
from app.modules.identity.contracts import CurrentUser
from app.payment_provider import PaymentProviderCircuitBreaker, SandboxPaymentAdapter
from app.platform_access import is_platform_admin
from app.routes.auth import require_current_user


router = APIRouter(tags=["finance"])
PAYMENT_PROVIDER_BREAKER = PaymentProviderCircuitBreaker()


def require_platform_admin(
    current: CurrentUser = Depends(require_current_user),
) -> CurrentUser:
    if not is_platform_admin(current.user.email):
        raise HTTPException(status_code=403, detail="acesso financeiro obrigatório")
    return current


def _require_finance_role(current: CurrentUser, roles: set[str]) -> CurrentUser:
    if not FinanceSecurityService(get_settings().database_path).has_role(current.user.id, roles):
        raise HTTPException(status_code=403, detail="papel financeiro obrigatório")
    return current


def require_finance_operator(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    return _require_finance_role(current, {"finance_operator"})


def require_finance_approver(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    return _require_finance_role(current, {"finance_approver"})


def require_finance_auditor(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    return _require_finance_role(current, {"finance_auditor"})


def require_finance_risk(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    return _require_finance_role(current, {"finance_risk"})


def require_finance_any(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    return _require_finance_role(
        current,
        {"finance_operator", "finance_approver", "finance_risk", "finance_support", "finance_auditor"},
    )


def _require_finance_step_up(current: CurrentUser, token: str | None) -> None:
    repository = AuthRepository(get_settings().database_path)
    if not token or not repository.consume_step_up(
        current.user.id, token, "finance_sensitive_action"
    ):
        raise HTTPException(
            status_code=403,
            detail="autenticação reforçada obrigatória para ação financeira",
        )


def payment_service() -> FinancePaymentService:
    settings = get_settings()
    if settings.payment_mode != "sandbox":
        raise HTTPException(status_code=503, detail="pagamentos permanecem desativados")
    try:
        adapter = SandboxPaymentAdapter(settings.payment_webhook_secret)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="sandbox de pagamento não configurado") from exc
    return FinancePaymentService(settings.database_path, adapter, PAYMENT_PROVIDER_BREAKER)


@router.post("/api/finance/orders", response_model=OrderResponse)
async def create_order(
    payload: OrderCreateRequest,
    current: CurrentUser = Depends(require_current_user),
) -> OrderResponse:
    try:
        return FinanceOrderService(get_settings().database_path).create(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/finance/orders/{public_id}", response_model=OrderResponse)
async def order_detail(
    public_id: str,
    current: CurrentUser = Depends(require_current_user),
) -> OrderResponse:
    try:
        return FinanceOrderService(get_settings().database_path).detail(public_id, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/finance/orders/{public_id}/checkout", response_model=PaymentIntentResponse)
async def checkout_order(
    public_id: str,
    payload: OrderCheckoutRequest,
    current: CurrentUser = Depends(require_current_user),
) -> PaymentIntentResponse:
    try:
        return FinanceOrderService(get_settings().database_path).checkout(
            public_id, current.user.id, payload.idempotency_key, payment_service()
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/admin/finance/sandbox/intents", response_model=PaymentIntentResponse)
async def create_sandbox_intent(
    payload: SandboxIntentRequest,
    current: CurrentUser = Depends(require_finance_operator),
) -> PaymentIntentResponse:
    service = payment_service()
    try:
        return service.create_intent(
            payload.idempotency_key,
            Money(payload.amount_minor, payload.currency),
            current.user.id,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/api/admin/finance/payments/{payment_public_id}/commands",
    response_model=PaymentCommandResponse,
)
async def execute_payment_command(
    payment_public_id: str,
    payload: PaymentCommandRequest,
    current: CurrentUser = Depends(require_current_user),
) -> PaymentCommandResponse:
    if get_settings().payment_mode != "sandbox":
        raise HTTPException(status_code=503, detail="comandos financeiros permanecem desativados")
    required_roles = (
        {"finance_operator"}
        if payload.command in {"capture", "cancel"}
        else {"finance_support", "finance_risk"}
    )
    _require_finance_role(current, required_roles)
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinancePaymentOperationsService(get_settings().database_path).execute(
            payment_public_id, payload, current.user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/finance/balance", response_model=FinanceBalanceResponse)
async def finance_balance(
    currency: str = "BRL",
    current: CurrentUser = Depends(require_current_user),
) -> FinanceBalanceResponse:
    try:
        return FinanceSettlementService(get_settings().database_path).balance(current.user.id, currency)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/finance/payouts", response_model=PayoutResponse)
async def request_payout(
    payload: PayoutRequest,
    current: CurrentUser = Depends(require_current_user),
) -> PayoutResponse:
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinanceSettlementService(get_settings().database_path).request_payout(
            current.user.id, payload.currency, payload.amount_minor, payload.idempotency_key
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/admin/finance/reconciliations", response_model=ReconciliationResponse)
async def reconcile_finance(
    payload: ReconciliationRequest,
    current: CurrentUser = Depends(require_finance_auditor),
) -> ReconciliationResponse:
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinanceSettlementService(get_settings().database_path).reconcile(
            payload.currency, payload.provider_reported_minor,
            payload.evidence_reference, current.user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/admin/finance/payouts/{public_id}/approve", response_model=PayoutResponse)
async def approve_payout(
    public_id: str,
    step_up_token: str | None = Header(default=None, alias="X-Printora-Step-Up"),
    current: CurrentUser = Depends(require_finance_approver),
) -> PayoutResponse:
    _require_finance_step_up(current, step_up_token)
    try:
        return FinanceSettlementService(get_settings().database_path).approve_payout(
            public_id, current.user.id
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/admin/finance/payouts/{public_id}/execute", response_model=PayoutResponse)
async def execute_payout(
    public_id: str,
    step_up_token: str | None = Header(default=None, alias="X-Printora-Step-Up"),
    current: CurrentUser = Depends(require_finance_operator),
) -> PayoutResponse:
    _require_finance_step_up(current, step_up_token)
    try:
        return FinanceSettlementService(get_settings().database_path).execute_payout(
            public_id, current.user.id
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/admin/finance/closings", response_model=ClosingResponse)
async def close_finance_period(
    payload: ClosingRequest,
    current: CurrentUser = Depends(require_finance_auditor),
) -> ClosingResponse:
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinanceSettlementService(get_settings().database_path).close(
            payload.currency, payload.period_key, current.user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/api/admin/finance/roles", response_model=FinanceRoleResponse)
async def assign_finance_role(
    payload: FinanceRoleRequest,
    current: CurrentUser = Depends(require_platform_admin),
) -> FinanceRoleResponse:
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinanceSecurityService(get_settings().database_path).assign_role(
            payload.user_id, payload.role, payload.active, current.user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/admin/finance/risk-cases", response_model=list[RiskCaseResponse])
async def list_risk_cases(
    status: str | None = None,
    _current: CurrentUser = Depends(require_finance_risk),
) -> list[RiskCaseResponse]:
    return FinanceRiskService(get_settings().database_path).list_cases(status)


@router.post("/api/admin/finance/risk-cases/{public_id}/decision", response_model=RiskCaseResponse)
async def decide_risk_case(
    public_id: str,
    payload: RiskDecisionRequest,
    current: CurrentUser = Depends(require_finance_risk),
) -> RiskCaseResponse:
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinanceRiskService(get_settings().database_path).decide(
            public_id, payload.decision, payload.reason, current.user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/finance/risk-cases/{public_id}/appeal", response_model=RiskCaseResponse)
async def appeal_risk_case(
    public_id: str,
    payload: RiskAppealRequest,
    current: CurrentUser = Depends(require_current_user),
) -> RiskCaseResponse:
    try:
        return FinanceRiskService(get_settings().database_path).appeal(
            public_id, payload.reason, current.user.id
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/admin/finance/readiness", response_model=FinanceReadinessResponse)
async def finance_readiness(
    _current: CurrentUser = Depends(require_finance_auditor),
) -> FinanceReadinessResponse:
    return FinanceComplianceService(get_settings().database_path).readiness()


@router.get("/api/admin/finance/overview")
async def finance_admin_overview(
    _current: CurrentUser = Depends(require_finance_any),
) -> dict[str, object]:
    return FinanceAdminQueryService(get_settings().database_path).overview()


@router.put(
    "/api/admin/finance/compliance/{control_key}",
    response_model=ComplianceControlResponse,
)
async def review_compliance_control(
    control_key: str,
    payload: ComplianceControlRequest,
    current: CurrentUser = Depends(require_finance_auditor),
) -> ComplianceControlResponse:
    _require_finance_step_up(current, payload.step_up_token)
    try:
        return FinanceComplianceService(get_settings().database_path).review_control(
            control_key, payload.status, payload.evidence_reference,
            payload.expires_at, current.user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/finance/provider-webhooks/sandbox", response_model=PaymentWebhookResponse)
async def sandbox_webhook(
    request: Request,
    signature: str = Header(alias="X-Printora-Sandbox-Signature", min_length=64, max_length=64),
) -> PaymentWebhookResponse:
    body = await request.body()
    if len(body) > 65_536:
        raise HTTPException(status_code=413, detail="webhook excede limite permitido")
    try:
        return payment_service().process_webhook(body, signature)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


MODULE = ModuleDefinition(
    key="finance",
    owner="Finanças e pedidos",
    contract_version="1.0.0",
    routers=(RouterRegistration(305, router),),
)
