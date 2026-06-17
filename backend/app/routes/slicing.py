from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.routes.auth import CurrentUser, require_current_user_when_configured
from app.slicing import SlicingDryRunResult, SlicingEngineBridge, SlicingEngineInfo, SlicingRepository, SlicingRequest, SlicerEngine
from app.slicing_pipeline import SlicingJob, SlicingJobCreate, SlicingPipelineRepository

router = APIRouter(prefix="/api/slicing", tags=["slicing"])


def get_slicing_bridge() -> SlicingEngineBridge:
    return SlicingEngineBridge(get_settings())


def get_slicing_repository() -> SlicingRepository:
    return SlicingRepository(get_settings().database_path)


def get_slicing_pipeline_repository() -> SlicingPipelineRepository:
    settings = get_settings()
    return SlicingPipelineRepository(settings.database_path, settings)


@router.get("/engine", response_model=SlicingEngineInfo)
async def get_slicing_engine(
    engine: SlicerEngine | None = None,
    bridge: SlicingEngineBridge = Depends(get_slicing_bridge),
    repository: SlicingRepository = Depends(get_slicing_repository),
) -> SlicingEngineInfo:
    info = bridge.detect(engine)
    repository.record_engine_check(info)
    return info


@router.post("/dry-run", response_model=SlicingDryRunResult)
async def create_slicing_dry_run(
    payload: SlicingRequest,
    bridge: SlicingEngineBridge = Depends(get_slicing_bridge),
    repository: SlicingRepository = Depends(get_slicing_repository),
) -> SlicingDryRunResult:
    result = bridge.dry_run(payload)
    repository.record_dry_run(result)
    return result


@router.get("/jobs", response_model=list[SlicingJob])
async def list_slicing_jobs(
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> list[SlicingJob]:
    return repository.list_jobs(current.user.id if current else None)


@router.post("/jobs", response_model=SlicingJob)
async def create_slicing_job(
    payload: SlicingJobCreate,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    try:
        return repository.create_job(current.user.id if current else None, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/run", response_model=SlicingJob)
async def run_slicing_job(
    job_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    try:
        return repository.run_job(job_id, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/cancel", response_model=SlicingJob)
async def cancel_slicing_job(
    job_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    try:
        return repository.cancel_job(job_id, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
