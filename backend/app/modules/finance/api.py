from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import get_settings
from app.finance_payments import FinancePaymentService
from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.modules.finance.contracts import (
    PaymentIntentResponse,
    PaymentWebhookResponse,
    SandboxIntentRequest,
)
from app.modules.finance.domain import Money
from app.modules.identity.contracts import CurrentUser
from app.payment_provider import SandboxPaymentAdapter
from app.routes.auth import require_current_user


router = APIRouter(tags=["finance"])


def require_finance_admin(
    current: CurrentUser = Depends(require_current_user),
) -> CurrentUser:
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="acesso financeiro obrigatório")
    return current


def payment_service() -> FinancePaymentService:
    settings = get_settings()
    if settings.payment_mode != "sandbox":
        raise HTTPException(status_code=503, detail="pagamentos permanecem desativados")
    try:
        adapter = SandboxPaymentAdapter(settings.payment_webhook_secret)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="sandbox de pagamento não configurado") from exc
    return FinancePaymentService(settings.database_path, adapter)


@router.post("/api/admin/finance/sandbox/intents", response_model=PaymentIntentResponse)
async def create_sandbox_intent(
    payload: SandboxIntentRequest,
    current: CurrentUser = Depends(require_finance_admin),
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
