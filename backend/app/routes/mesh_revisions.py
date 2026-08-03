from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.modules.operations.mesh_qualification.contracts import MeshRepairCreate, MeshRevision
from app.modules.operations.mesh_qualification.repository import MeshRevisionRepository
from app.modules.platform.durable_execution import QueueSaturatedError
from app.routes.auth import CurrentUser, require_current_user


router = APIRouter(prefix="/api/photo-reconstructions/{job_id}/mesh-revisions", tags=["mesh-revisions"])


def get_repository() -> MeshRevisionRepository:
    settings = get_settings()
    return MeshRevisionRepository(settings.database_path, settings)


@router.get("", response_model=list[MeshRevision])
async def list_revisions(job_id: int, current: CurrentUser = Depends(require_current_user), repository: MeshRevisionRepository = Depends(get_repository)) -> list[MeshRevision]:
    return repository.list(current.user.id, job_id)


@router.post("", response_model=MeshRevision)
async def create_revision(payload: MeshRepairCreate, job_id: int, idempotency_key: str = Header(alias="Idempotency-Key"), current: CurrentUser = Depends(require_current_user), repository: MeshRevisionRepository = Depends(get_repository)) -> MeshRevision:
    try:
        return repository.create(current.user.id, job_id, payload, idempotency_key)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QueueSaturatedError as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "30"}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{revision_id}", response_model=MeshRevision)
async def get_revision(job_id: int, revision_id: int, current: CurrentUser = Depends(require_current_user), repository: MeshRevisionRepository = Depends(get_repository)) -> MeshRevision:
    try:
        return repository.get(current.user.id, job_id, revision_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{revision_id}/cancel", response_model=MeshRevision)
async def cancel_revision(job_id: int, revision_id: int, current: CurrentUser = Depends(require_current_user), repository: MeshRevisionRepository = Depends(get_repository)) -> MeshRevision:
    try:
        return repository.cancel(current.user.id, job_id, revision_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{revision_id}/download")
async def download_revision(job_id: int, revision_id: int, current: CurrentUser = Depends(require_current_user), repository: MeshRevisionRepository = Depends(get_repository)) -> StreamingResponse:
    try:
        reader, file_format = repository.open(current.user.id, job_id, revision_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def stream() -> Iterator[bytes]:
        try:
            while chunk := reader.body.read(64 * 1024):
                yield chunk
        finally:
            reader.body.close()

    return StreamingResponse(stream(), media_type=reader.content_type, headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'attachment; filename="versao-revisada-{revision_id}.{file_format}"',
    })
