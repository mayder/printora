from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.config import get_settings
from app.modules.community.photo_capture import PhotoCaptureRepository
from app.modules.community.photo_capture_contracts import (
    HeightBand,
    PhotoCaptureCreate,
    PhotoCaptureScaleUpdate,
    PhotoCaptureSession,
)
from app.modules.community.photo_capture_exports import PhotoCaptureExportRepository
from app.routes.auth import CurrentUser, require_current_user
from app.upload_stream import read_limited_upload


router = APIRouter(prefix="/api/photo-captures", tags=["photo-captures"])


def get_photo_capture_repository() -> PhotoCaptureRepository:
    return PhotoCaptureRepository(get_settings().database_path)


def get_photo_capture_export_repository() -> PhotoCaptureExportRepository:
    return PhotoCaptureExportRepository(get_settings().database_path)


@router.get("", response_model=list[PhotoCaptureSession])
async def list_photo_captures(
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> list[PhotoCaptureSession]:
    return repository.list_for_owner(current.user.id)


@router.post("", response_model=PhotoCaptureSession)
async def create_photo_capture(
    payload: PhotoCaptureCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> PhotoCaptureSession:
    try:
        return repository.create(current.user.id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{session_id}", response_model=PhotoCaptureSession)
async def get_photo_capture(
    session_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> PhotoCaptureSession:
    try:
        return repository.get(current.user.id, session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{session_id}/export")
async def export_photo_capture(
    session_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureExportRepository = Depends(get_photo_capture_export_repository),
) -> FileResponse:
    try:
        exported = repository.build(current.user.id, session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FileResponse(
        exported.path,
        filename=exported.file_name,
        media_type="application/zip",
        headers={"Cache-Control": "private, no-store"},
        background=BackgroundTask(exported.path.unlink, missing_ok=True),
    )


@router.post(
    "/{session_id}/photos",
    response_model=PhotoCaptureSession,
    openapi_extra={"requestBody": {"required": True, "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}}},
)
async def upload_capture_photo(
    session_id: int,
    request: Request,
    file_name: str,
    capture_index: int,
    height_band: HeightBand,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> PhotoCaptureSession:
    try:
        body = await read_limited_upload(request, 15 * 1024 * 1024)
        return repository.upload(current.user.id, session_id, file_name, capture_index, height_band, body, idempotency_key)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{session_id}/scale", response_model=PhotoCaptureSession)
async def update_capture_scale(
    session_id: int,
    payload: PhotoCaptureScaleUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> PhotoCaptureSession:
    try:
        return repository.update_scale(current.user.id, session_id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/complete", response_model=PhotoCaptureSession)
async def complete_photo_capture(
    session_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> PhotoCaptureSession:
    try:
        return repository.complete(current.user.id, session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/cancel", response_model=PhotoCaptureSession)
async def cancel_photo_capture(
    session_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: PhotoCaptureRepository = Depends(get_photo_capture_repository),
) -> PhotoCaptureSession:
    try:
        return repository.cancel(current.user.id, session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
