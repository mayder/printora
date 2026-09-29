from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.routes.social_catalog import is_social_admin
from app.social_object_downloads import ObjectDownloadToken, SocialObjectDownloadRepository
from app.social_storage import SocialStorageRepository, StorageReport, StorageRetentionPlan


router = APIRouter(tags=["social-storage"])


def get_storage_repository() -> SocialStorageRepository:
    return SocialStorageRepository(get_settings().database_path)


def get_download_repository() -> SocialObjectDownloadRepository:
    return SocialObjectDownloadRepository(get_settings().database_path)


@router.get("/api/social/me/library/storage", response_model=StorageReport)
async def library_storage_report(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialStorageRepository = Depends(get_storage_repository),
) -> StorageReport:
    return repository.report_for_user(current.user.id)


@router.post("/api/social/me/library/storage/retention-reviews", response_model=StorageRetentionPlan)
async def create_library_retention_review(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialStorageRepository = Depends(get_storage_repository),
) -> StorageRetentionPlan:
    return repository.create_retention_review(current.user.id, current.user.id)


@router.post("/api/storage/social-library-files/{file_id}/tokens", response_model=ObjectDownloadToken)
async def issue_social_file_download_token(
    file_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialObjectDownloadRepository = Depends(get_download_repository),
) -> ObjectDownloadToken:
    try:
        return repository.issue_social_file_token(file_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/storage/print-project-files/{file_id}/tokens", response_model=ObjectDownloadToken)
async def issue_project_file_download_token(
    file_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialObjectDownloadRepository = Depends(get_download_repository),
) -> ObjectDownloadToken:
    try:
        return repository.issue_project_file_token(file_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/storage/download")
async def download_promoted_object(
    authorization: str | None = Header(default=None),
    repository: SocialObjectDownloadRepository = Depends(get_download_repository),
) -> StreamingResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="token de download ausente")
    try:
        reader, file_name = repository.consume(authorization.removeprefix("Bearer ").strip())
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    def chunks() -> Iterator[bytes]:
        try:
            while chunk := reader.body.read(64 * 1024):
                yield chunk
        finally:
            reader.body.close()

    return StreamingResponse(
        chunks(),
        media_type=reader.content_type,
        headers={
            "Content-Length": str(reader.size_bytes),
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Cache-Control": "private, no-store",
        },
    )
