from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.external_library import (
    ExternalImportPreview,
    ExternalLibraryRepository,
    ExternalReferenceCreate,
    ExternalReferenceRecord,
    ExternalSourceCreate,
    ExternalSourceRecord,
)
from app.routes.auth import CurrentUser, require_current_user

router = APIRouter(prefix="/api/social/external-library", tags=["external-library"])


def get_external_repository() -> ExternalLibraryRepository:
    return ExternalLibraryRepository(get_settings().database_path)


@router.get("/sources", response_model=list[ExternalSourceRecord])
async def list_external_sources(
    current: CurrentUser = Depends(require_current_user),
    repository: ExternalLibraryRepository = Depends(get_external_repository),
) -> list[ExternalSourceRecord]:
    return repository.list_sources(current.user.id)


@router.post("/sources", response_model=ExternalSourceRecord)
async def create_external_source(
    payload: ExternalSourceCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: ExternalLibraryRepository = Depends(get_external_repository),
) -> ExternalSourceRecord:
    try:
        return repository.create_source(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/preview", response_model=ExternalImportPreview)
async def preview_external_import(
    external_url: str,
    checksum_sha256: str | None = None,
    current: CurrentUser = Depends(require_current_user),
    repository: ExternalLibraryRepository = Depends(get_external_repository),
) -> ExternalImportPreview:
    try:
        return repository.preview_import(current.user.id, external_url, checksum_sha256)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/references", response_model=list[ExternalReferenceRecord])
async def list_external_references(
    current: CurrentUser = Depends(require_current_user),
    repository: ExternalLibraryRepository = Depends(get_external_repository),
) -> list[ExternalReferenceRecord]:
    return repository.list_references(current.user.id)


@router.post("/references", response_model=ExternalReferenceRecord)
async def create_external_reference(
    payload: ExternalReferenceCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: ExternalLibraryRepository = Depends(get_external_repository),
) -> ExternalReferenceRecord:
    try:
        return repository.create_reference(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
