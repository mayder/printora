from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.database import connect_database
from app.manufacturing_workflow import ManufacturingWorkflowService
from app.modules.identity.contracts import CurrentUser
from app.modules.operations.manufacturing_contracts import (
    AcceptQuoteRequest, QualityApprovalRequest, QualityRequest, QuoteRequest, RecallRequest,
    ShipmentRequest, TrackingRequest, TransitionRequest,
)
from app.platform_access import is_platform_admin
from app.routes.auth import require_current_user

router = APIRouter(tags=["manufacturing"])


def require_platform_admin(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    if not is_platform_admin(current.user.email):
        raise HTTPException(status_code=403, detail="administração da plataforma obrigatória")
    return current


def require_role(*roles: str, allow_platform_admin: bool = False):
    def dependency(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
        if allow_platform_admin and is_platform_admin(current.user.email):
            return current
        with connect_database(get_settings().database_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM manufacturing_role_assignments WHERE user_id=? AND active=1 AND role IN (" +
                ",".join("?" for _ in roles) + ") LIMIT 1", (current.user.id, *roles),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=403, detail="papel de fabricação obrigatório")
        return current
    return dependency


TRANSITION_ROLES = {
    "queued": "production_operator",
    "producing": "production_operator",
    "paused": "production_operator",
    "failed": "production_operator",
    "rework": "production_operator",
    "quality_pending": "production_operator",
    "cancelled": "production_operator",
    "quality_approved": "quality_approver",
    "packed": "logistics_operator",
    "shipped": "logistics_operator",
    "delivered": "logistics_operator",
}


def require_transition_role(user_id: int, target: str) -> None:
    required_role = TRANSITION_ROLES.get(target)
    if required_role is None:
        raise HTTPException(status_code=400, detail="transição produtiva sem papel autorizado")
    with connect_database(get_settings().database_path) as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM manufacturing_role_assignments
            WHERE user_id = ? AND active = 1 AND role = ?
            LIMIT 1
            """,
            (user_id, required_role),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=403, detail=f"papel {required_role} obrigatório para esta transição")


@router.get("/api/admin/manufacturing/overview")
async def overview(current: CurrentUser = Depends(require_role(
    "production_operator", "quality_inspector", "quality_approver", "logistics_operator", "safety_manager",
    allow_platform_admin=True,
))):
    del current
    with connect_database(get_settings().database_path) as connection:
        orders = connection.execute(
            """SELECT mo.public_id, mo.state, q.version, q.currency, q.amount_minor, mo.updated_at
               FROM manufacturing_orders mo JOIN manufacturing_quotes q ON q.id=mo.quote_id
               ORDER BY mo.id DESC LIMIT 100"""
        ).fetchall()
        incidents = connection.execute(
            "SELECT public_id,incident_type,severity,status,created_at FROM manufacturing_incidents ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return {"orders": [dict(row) for row in orders], "incidents": [dict(row) for row in incidents]}


@router.post("/api/admin/manufacturing/orders/{order_public_id}/quotes")
async def create_quote(order_public_id: str, payload: QuoteRequest,
                       current: CurrentUser = Depends(require_role("production_operator"))):
    return ManufacturingWorkflowService(get_settings().database_path).create_quote(
        order_public_id, payload.model_dump(), current.user.id
    )


@router.post("/api/manufacturing/quotes/{quote_public_id}/accept")
async def accept_quote(quote_public_id: str, payload: AcceptQuoteRequest,
                       current: CurrentUser = Depends(require_current_user)):
    return ManufacturingWorkflowService(get_settings().database_path).accept_and_reserve(
        quote_public_id, current.user.id, [item.model_dump() for item in payload.resources], payload.idempotency_key
    )


@router.post("/api/admin/manufacturing/orders/{public_id}/transitions")
async def transition(public_id: str, payload: TransitionRequest,
                     current: CurrentUser = Depends(require_role("production_operator", "quality_approver", "logistics_operator"))):
    require_transition_role(current.user.id, payload.target)
    return ManufacturingWorkflowService(get_settings().database_path).transition(
        public_id, payload.target, payload.event_key, current.user.id, payload.reason
    )


@router.post("/api/admin/manufacturing/orders/{public_id}/quality")
async def quality(public_id: str, payload: QualityRequest,
                  current: CurrentUser = Depends(require_role("quality_inspector"))):
    return ManufacturingWorkflowService(get_settings().database_path).record_quality(
        public_id, payload.check_key, payload.specification, payload.measurement, payload.passed,
        payload.evidence_object_key, current.user.id, None
    )


@router.post("/api/admin/manufacturing/orders/{public_id}/quality/approve")
async def approve_quality(
    public_id: str,
    payload: QualityApprovalRequest,
    current: CurrentUser = Depends(require_role("quality_approver")),
):
    return ManufacturingWorkflowService(get_settings().database_path).approve_quality(
        public_id, payload.check_key, current.user.id
    )


@router.post("/api/admin/manufacturing/orders/{public_id}/shipments")
async def shipment(public_id: str, payload: ShipmentRequest,
                   current: CurrentUser = Depends(require_role("logistics_operator"))):
    return ManufacturingWorkflowService(get_settings().database_path).create_shipment(
        public_id, payload.carrier, payload.tracking_token, payload.address_ciphertext, current.user.id
    )


@router.post("/api/admin/manufacturing/shipments/{public_id}/tracking")
async def tracking(public_id: str, payload: TrackingRequest,
                   current: CurrentUser = Depends(require_role("logistics_operator"))):
    return ManufacturingWorkflowService(get_settings().database_path).track(
        public_id, payload.provider_event_id, payload.status,
        json.dumps(payload.payload, sort_keys=True).encode(), payload.occurred_at, current.user.id
    )


@router.post("/api/admin/manufacturing/orders/{public_id}/recall")
async def recall(public_id: str, payload: RecallRequest,
                 current: CurrentUser = Depends(require_role("safety_manager"))):
    return ManufacturingWorkflowService(get_settings().database_path).recall(
        public_id, payload.evidence_reference, current.user.id
    )


@router.put("/api/admin/manufacturing/roles/{user_id}/{role}")
async def assign_role(user_id: int, role: str, current: CurrentUser = Depends(require_platform_admin)):
    allowed = {"production_operator", "quality_inspector", "quality_approver", "logistics_operator", "safety_manager"}
    if role not in allowed:
        raise HTTPException(status_code=422, detail="papel inválido")
    with connect_database(get_settings().database_path) as connection:
        connection.execute(
            """INSERT INTO manufacturing_role_assignments (user_id,role,active,assigned_by_user_id)
               VALUES (?,?,1,?) ON CONFLICT(user_id,role) DO UPDATE SET active=1, assigned_by_user_id=excluded.assigned_by_user_id""",
            (user_id, role, current.user.id),
        )
    return {"user_id": user_id, "role": role, "active": True}
