from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import get_auth_repository, require_current_user
from app.technical_profiles import (
    TechnicalConfigComparison,
    TechnicalPrinterConfig,
    TechnicalPrinterConfigPayload,
    TechnicalProfilesRepository,
)


router = APIRouter(tags=["technical-profiles"])


def get_technical_profiles_repository() -> TechnicalProfilesRepository:
    return TechnicalProfilesRepository(get_settings().database_path)


def optional_current_user(authorization: str | None = Header(default=None)) -> CurrentUser | None:
    if not authorization:
        return None
    try:
        return require_current_user(authorization=authorization, repository=get_auth_repository())
    except HTTPException:
        return None


@router.get("/api/social/me/technical-configs", response_model=list[TechnicalPrinterConfig])
async def list_my_technical_configs(
    current: CurrentUser = Depends(require_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> list[TechnicalPrinterConfig]:
    return repository.my_configs(current.user.id)


@router.post("/api/social/technical-configs", response_model=TechnicalPrinterConfig)
async def create_technical_config(
    payload: TechnicalPrinterConfigPayload,
    current: CurrentUser = Depends(require_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> TechnicalPrinterConfig:
    try:
        return repository.create_config(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/social/technical-configs/{config_id}", response_model=TechnicalPrinterConfig)
async def update_technical_config(
    config_id: int,
    payload: TechnicalPrinterConfigPayload,
    current: CurrentUser = Depends(require_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> TechnicalPrinterConfig:
    try:
        return repository.update_config(config_id, current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404 if "não encontrada" in str(exc) else 400, detail=str(exc)) from exc


@router.delete("/api/social/technical-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_technical_config(
    config_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> None:
    try:
        repository.archive_config(config_id, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/social/communities/{slug}/technical-configs", response_model=list[TechnicalPrinterConfig])
async def list_community_technical_configs(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> list[TechnicalPrinterConfig]:
    return repository.community_configs(slug, current.user.id if current else None)


@router.get("/api/social/communities/{slug}/technical-configs/comparison", response_model=TechnicalConfigComparison)
async def compare_community_technical_configs(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> TechnicalConfigComparison:
    try:
        return repository.compare_community(slug, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/social/profiles/{slug}/technical-configs", response_model=list[TechnicalPrinterConfig])
async def list_profile_technical_configs(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: TechnicalProfilesRepository = Depends(get_technical_profiles_repository),
) -> list[TechnicalPrinterConfig]:
    return repository.profile_configs(slug, current.user.id if current else None)
