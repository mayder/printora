from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.social_moderation import (
    ModerationActionPayload,
    ModerationQueueResponse,
    ModerationReportCreate,
    ModerationReportRecord,
    ModerationReportStatus,
    SocialModerationRepository,
)
from app.social_safety import SocialSafetyRepository


router = APIRouter(tags=["social-moderation"])


def get_moderation_repository() -> SocialModerationRepository:
    return SocialModerationRepository(get_settings().database_path)


def get_safety_repository() -> SocialSafetyRepository:
    return SocialSafetyRepository(get_settings().database_path)


def require_moderation_admin(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="moderação restrita ao administrador")
    return current


@router.post("/api/social/reports", response_model=ModerationReportRecord)
async def report_social_content(
    payload: ModerationReportCreate,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialModerationRepository = Depends(get_moderation_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> ModerationReportRecord:
    try:
        result = safety.check_rate_limit(
            actor_user_id=current.user.id,
            action="moderation_report",
            subject=f"user:{current.user.id}:{request.headers.get('user-agent', '')[:120]}",
            target_user_id=None,
        )
        if not result.allowed:
            raise HTTPException(status_code=429, detail=result.reason, headers={"Retry-After": str(result.retry_after_seconds)})
        return repository.create_report(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/moderation/queue", response_model=ModerationQueueResponse)
async def moderation_queue(
    status: ModerationReportStatus | None = None,
    current: CurrentUser = Depends(require_moderation_admin),
    repository: SocialModerationRepository = Depends(get_moderation_repository),
) -> ModerationQueueResponse:
    return repository.queue(status=status)


@router.post("/api/social/moderation/reports/{report_id}/actions", response_model=ModerationReportRecord)
async def apply_moderation_action(
    report_id: int,
    payload: ModerationActionPayload,
    current: CurrentUser = Depends(require_moderation_admin),
    repository: SocialModerationRepository = Depends(get_moderation_repository),
) -> ModerationReportRecord:
    try:
        return repository.apply_action(report_id, current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
