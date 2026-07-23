from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.config import get_settings
from app.database import connect_database
from app.modules.identity.contracts import CurrentUser
from app.modules.platform.durable_execution import DurableExecutionRepository
from app.platform_access import is_platform_admin
from app.routes.auth import require_current_user


router = APIRouter(prefix="/api/admin/workers", tags=["workers"])


class WorkerControlRequest(BaseModel):
    queue_name: Literal["outbox", "critical", "default", "bulk"]
    desired_state: Literal["running", "paused", "draining"]


class DeadLetterReplayRequest(BaseModel):
    expected_job_key: str = Field(min_length=1, max_length=200)


def require_worker_admin(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    if not is_platform_admin(current.user.email):
        raise HTTPException(status_code=403, detail="acesso administrativo obrigatório")
    return current


@router.get("")
async def worker_overview(_current: CurrentUser = Depends(require_worker_admin)) -> dict:
    settings = get_settings()
    repository = DurableExecutionRepository(settings.database_path)
    with connect_database(settings.database_path) as connection:
        controls = connection.execute(
            "SELECT queue_name, desired_state, max_concurrency, updated_by, updated_at FROM worker_controls ORDER BY queue_name"
        ).fetchall()
        instances = connection.execute(
            """
            SELECT worker_id, queue_name, release_sha, state, concurrency, started_at, heartbeat_at, stopped_at
            FROM worker_instances ORDER BY heartbeat_at DESC LIMIT 100
            """
        ).fetchall()
    return {
        "metrics": repository.metrics(),
        "controls": [dict(row) for row in controls],
        "instances": [dict(row) for row in instances],
    }


@router.post("/control")
async def control_workers(
    payload: WorkerControlRequest,
    request: Request,
    current: CurrentUser = Depends(require_worker_admin),
) -> dict:
    _enforce_rate_limit(request, current.user.id)
    repository = DurableExecutionRepository(get_settings().database_path)
    repository.set_worker_state(payload.queue_name, payload.desired_state, current.user.email)
    return {"queue_name": payload.queue_name, "desired_state": payload.desired_state}


@router.get("/{queue_name}/dead-letter")
async def dead_letter_preview(
    queue_name: Literal["critical", "default", "bulk"],
    limit: int = Query(default=50, ge=1, le=100),
    _current: CurrentUser = Depends(require_worker_admin),
) -> dict:
    items = DurableExecutionRepository(get_settings().database_path).dead_letter_preview(queue_name, limit)
    return {"queue_name": queue_name, "count": len(items), "items": items}


@router.post("/{queue_name}/dead-letter/{job_id}/replay")
async def replay_dead_letter(
    queue_name: Literal["critical", "default", "bulk"],
    job_id: int,
    payload: DeadLetterReplayRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current: CurrentUser = Depends(require_worker_admin),
) -> dict:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key obrigatória para replay")
    _enforce_rate_limit(request, current.user.id)
    repository = DurableExecutionRepository(get_settings().database_path)
    try:
        job = repository.replay_dead_letter(
            job_id,
            payload.expected_job_key,
            idempotency_key,
            current.user.email,
            queue_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"job_id": job.id, "job_key": job.job_key, "status": job.status}


def _enforce_rate_limit(request: Request, user_id: int) -> None:
    service = getattr(request.app.state, "recomposable_redis", None)
    if service is None:
        return
    decision = service.rate_limit(f"worker-admin:{user_id}", 30, 60)
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="limite de operação administrativa atingido",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )
