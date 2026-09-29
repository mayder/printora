from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.modules.operations.reconstruction.contracts import ReconstructionCreate, ReconstructionJob
from app.modules.operations.reconstruction.repository import ReconstructionRepository
from app.modules.platform.durable_execution import QueueSaturatedError
from app.routes.auth import CurrentUser, require_current_user


router = APIRouter(prefix="/api/photo-reconstructions", tags=["photo-reconstructions"])


def get_reconstruction_repository() -> ReconstructionRepository:
    settings = get_settings()
    return ReconstructionRepository(settings.database_path, settings)


@router.get("", response_model=list[ReconstructionJob])
async def list_reconstructions(
    capture_session_id: int | None = None,
    current: CurrentUser = Depends(require_current_user),
    repository: ReconstructionRepository = Depends(get_reconstruction_repository),
) -> list[ReconstructionJob]:
    return repository.list_for_owner(current.user.id, capture_session_id)


@router.post("", response_model=ReconstructionJob)
async def create_reconstruction(
    payload: ReconstructionCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    current: CurrentUser = Depends(require_current_user),
    repository: ReconstructionRepository = Depends(get_reconstruction_repository),
) -> ReconstructionJob:
    try:
        return repository.create(current.user.id, payload, idempotency_key)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QueueSaturatedError as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "30"}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=ReconstructionJob)
async def get_reconstruction(
    job_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: ReconstructionRepository = Depends(get_reconstruction_repository),
) -> ReconstructionJob:
    try:
        return repository.get(current.user.id, job_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/cancel", response_model=ReconstructionJob)
async def cancel_reconstruction(
    job_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: ReconstructionRepository = Depends(get_reconstruction_repository),
) -> ReconstructionJob:
    try:
        return repository.cancel(current.user.id, job_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/retry", response_model=ReconstructionJob)
async def retry_reconstruction(
    job_id: int,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    current: CurrentUser = Depends(require_current_user),
    repository: ReconstructionRepository = Depends(get_reconstruction_repository),
) -> ReconstructionJob:
    try:
        return repository.retry(current.user.id, job_id, idempotency_key)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QueueSaturatedError as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "30"}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{job_id}/artifacts/{artifact_id}")
async def download_reconstruction_artifact(
    job_id: int,
    artifact_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: ReconstructionRepository = Depends(get_reconstruction_repository),
) -> StreamingResponse:
    try:
        reader, file_format = repository.open_artifact(current.user.id, job_id, artifact_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def stream() -> Iterator[bytes]:
        try:
            while chunk := reader.body.read(64 * 1024):
                yield chunk
        finally:
            reader.body.close()

    return StreamingResponse(
        stream(),
        media_type=reader.content_type,
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'attachment; filename="reconstrucao-{job_id}.{file_format}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
