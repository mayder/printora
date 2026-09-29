from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.auth import CurrentUser
from app.config import get_settings
from app.print_profiles import MaterialProfile, MaterialProfileExport, MaterialProfilePayload, PrintProfilesRepository
from app.routes.auth import get_auth_repository, require_current_user


router = APIRouter(tags=["print-profiles"])


def get_print_profiles_repository() -> PrintProfilesRepository:
    return PrintProfilesRepository(get_settings().database_path)


def optional_current_user(authorization: str | None = Header(default=None)) -> CurrentUser | None:
    if not authorization:
        return None
    try:
        return require_current_user(authorization=authorization, repository=get_auth_repository())
    except HTTPException:
        return None


@router.get("/api/social/me/material-profiles", response_model=list[MaterialProfile])
async def list_my_material_profiles(
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> list[MaterialProfile]:
    return repository.my_profiles(current.user.id)


@router.post("/api/social/material-profiles", response_model=MaterialProfile)
async def create_material_profile(
    payload: MaterialProfilePayload,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> MaterialProfile:
    try:
        return repository.create_profile(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/social/material-profiles/{profile_id}", response_model=MaterialProfile)
async def update_material_profile(
    profile_id: int,
    payload: MaterialProfilePayload,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> MaterialProfile:
    try:
        return repository.update_profile(profile_id, current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404 if "não encontrado" in str(exc) else 400, detail=str(exc)) from exc


@router.delete("/api/social/material-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_material_profile(
    profile_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> None:
    try:
        repository.archive_profile(profile_id, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/social/material-profiles/{profile_id}/export", response_model=MaterialProfileExport)
async def export_material_profile(
    profile_id: int,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> MaterialProfileExport:
    try:
        return repository.export_profile(profile_id, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/social/material-profiles/import", response_model=MaterialProfile)
async def import_material_profile(
    payload: MaterialProfileExport,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> MaterialProfile:
    try:
        return repository.import_profile(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/communities/{slug}/material-profiles", response_model=list[MaterialProfile])
async def list_community_material_profiles(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: PrintProfilesRepository = Depends(get_print_profiles_repository),
) -> list[MaterialProfile]:
    return repository.community_profiles(slug, current.user.id if current else None)
