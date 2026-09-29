from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import get_settings
from app.modules.accessibility.catalog import build_catalog
from app.modules.accessibility.contracts import (
    AccessibilityCatalogContract,
    AccessibilityPreferencesContract,
    AccessibilityPreferencesUpdateRequest,
)
from app.modules.accessibility.repository import (
    AccessibilityPreferencesConflict,
    AccessibilityPreferencesRepository,
)
from app.modules.accessibility.service import AccessibilityPreferencesService
from app.modules.identity.contracts import CurrentUser
from app.routes.auth import require_current_user


router = APIRouter(prefix="/api/accessibility/v1", tags=["accessibility"])


def _service() -> AccessibilityPreferencesService:
    return AccessibilityPreferencesService(
        AccessibilityPreferencesRepository(get_settings().database_path)
    )


@router.get("/capabilities", response_model=AccessibilityCatalogContract)
async def list_capabilities(
    _current: CurrentUser = Depends(require_current_user),
) -> AccessibilityCatalogContract:
    return build_catalog()


@router.get("/preferences", response_model=AccessibilityPreferencesContract)
async def get_preferences(
    current: CurrentUser = Depends(require_current_user),
) -> AccessibilityPreferencesContract:
    return _service().get(current.user.id)


@router.put("/preferences", response_model=AccessibilityPreferencesContract)
async def update_preferences(
    payload: AccessibilityPreferencesUpdateRequest,
    _idempotency_key: str = Header(
        min_length=8,
        max_length=128,
        alias="Idempotency-Key",
    ),
    current: CurrentUser = Depends(require_current_user),
) -> AccessibilityPreferencesContract:
    try:
        return _service().save(current.user.id, payload)
    except AccessibilityPreferencesConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

