from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.social_safety import (
    AbuseSignalRecord,
    AbuseSignalStatus,
    SocialSafetyRepository,
    SocialSafetySettings,
    SocialSafetySettingsUpdate,
    SocialSafetyStatus,
)


router = APIRouter(tags=["social-safety"])


def get_safety_repository() -> SocialSafetyRepository:
    return SocialSafetyRepository(get_settings().database_path)


def require_safety_admin(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="segurança social restrita ao administrador")
    return current


@router.get("/api/social/me/safety", response_model=SocialSafetyStatus)
async def get_my_social_safety(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialSafetyRepository = Depends(get_safety_repository),
) -> SocialSafetyStatus:
    return repository.status(current.user.id)


@router.put("/api/social/me/safety", response_model=SocialSafetySettings)
async def update_my_social_safety(
    payload: SocialSafetySettingsUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialSafetyRepository = Depends(get_safety_repository),
) -> SocialSafetySettings:
    try:
        return repository.update_settings(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/moderation/abuse-signals", response_model=list[AbuseSignalRecord])
async def list_social_abuse_signals(
    status: AbuseSignalStatus | None = None,
    _current: CurrentUser = Depends(require_safety_admin),
    repository: SocialSafetyRepository = Depends(get_safety_repository),
) -> list[AbuseSignalRecord]:
    return repository.abuse_signals(status=status)
