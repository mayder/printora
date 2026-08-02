from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.slicing_profile_bundles import (
    ProfileBundle,
    ProfileBundleImport,
    ProfileDiff,
    SlicingProfileBundlesRepository,
)


router = APIRouter(tags=["slicing-profile-bundles"])


def get_slicing_profile_bundles_repository() -> SlicingProfileBundlesRepository:
    return SlicingProfileBundlesRepository(get_settings().database_path)


@router.get("/api/slicing/profile-bundles", response_model=list[ProfileBundle])
async def list_slicing_profile_bundles(
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingProfileBundlesRepository = Depends(get_slicing_profile_bundles_repository),
) -> list[ProfileBundle]:
    return repository.list_for_owner(current.user.id)


@router.post("/api/slicing/profile-bundles/import", response_model=ProfileBundle)
async def import_slicing_profile_bundle(
    payload: ProfileBundleImport,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingProfileBundlesRepository = Depends(get_slicing_profile_bundles_repository),
) -> ProfileBundle:
    try:
        return repository.import_bundle(current.user.id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/slicing/profile-bundles/{bundle_id}", response_model=ProfileBundle)
async def get_slicing_profile_bundle(
    bundle_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingProfileBundlesRepository = Depends(get_slicing_profile_bundles_repository),
) -> ProfileBundle:
    bundle = repository.detail(current.user.id, bundle_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="pacote de perfil não encontrado")
    return bundle


@router.get("/api/slicing/profile-revisions/{revision_id}/export")
async def export_slicing_profile_revision(
    revision_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingProfileBundlesRepository = Depends(get_slicing_profile_bundles_repository),
) -> dict:
    try:
        return repository.export_revision(current.user.id, revision_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/slicing/profile-revisions/{from_revision_id}/diff/{to_revision_id}", response_model=ProfileDiff)
async def diff_slicing_profile_revisions(
    from_revision_id: int,
    to_revision_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingProfileBundlesRepository = Depends(get_slicing_profile_bundles_repository),
) -> ProfileDiff:
    try:
        return repository.diff(current.user.id, from_revision_id, to_revision_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
