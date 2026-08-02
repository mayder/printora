from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.modules.platform.database_target import uses_postgresql
from app.agent_executor import AgentCommandExecutor, AgentJobFailedError
from app.agent_pairing import printer_for_user
from app.auth import AuthRepository
from app.print_delivery import PrintDeliveryCreate, PrintDeliveryRecord, PrintDeliveryRepository
from app.print_history import PrintFeedbackCreate, PrintHistoryRepository, PrintJobHistoryEvent, PrintJobHistoryRecord
from app.routes.auth import CurrentUser, require_current_user, require_current_user_when_configured
from app.print_preflight import PrintPreflightRecord, PrintPreflightRepository, _read_artifact_text
from app.slicing import SlicingDryRunResult, SlicingEngineBridge, SlicingEngineInfo, SlicingRepository, SlicingRequest, SlicerEngine
from app.slicing_pipeline import ProjectSlicingJobCreate, SlicingJob, SlicingJobCreate, SlicingPipelineRepository

router = APIRouter(prefix="/api/slicing", tags=["slicing"])


def get_slicing_bridge() -> SlicingEngineBridge:
    return SlicingEngineBridge(get_settings())


def get_slicing_repository() -> SlicingRepository:
    return SlicingRepository(get_settings().database_path)


def get_slicing_pipeline_repository() -> SlicingPipelineRepository:
    settings = get_settings()
    return SlicingPipelineRepository(settings.database_path, settings)


def get_print_preflight_repository() -> PrintPreflightRepository:
    settings = get_settings()
    return PrintPreflightRepository(settings.database_path, settings.data_dir)


def get_print_delivery_repository() -> PrintDeliveryRepository:
    settings = get_settings()
    return PrintDeliveryRepository(settings.database_path, settings.data_dir)


def get_print_history_repository() -> PrintHistoryRepository:
    return PrintHistoryRepository(get_settings().database_path)


@router.get("/engine", response_model=SlicingEngineInfo)
async def get_slicing_engine(
    engine: SlicerEngine | None = None,
    _current: CurrentUser = Depends(require_current_user),
    bridge: SlicingEngineBridge = Depends(get_slicing_bridge),
    repository: SlicingRepository = Depends(get_slicing_repository),
) -> SlicingEngineInfo:
    info = bridge.detect(engine)
    repository.record_engine_check(info)
    return info


@router.post("/dry-run", response_model=SlicingDryRunResult)
async def create_slicing_dry_run(
    payload: SlicingRequest,
    _current: CurrentUser = Depends(require_current_user),
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


@router.get("/projects/{project_id}/jobs", response_model=list[SlicingJob])
async def list_project_slicing_jobs(
    project_id: int,
    current: CurrentUser = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> list[SlicingJob]:
    if current is None:
        raise HTTPException(status_code=401, detail="autenticação obrigatória")
    return repository.list_project_jobs(current.user.id, project_id)


@router.post("/projects/{project_id}/jobs", response_model=SlicingJob)
async def create_project_slicing_job(
    project_id: int,
    payload: ProjectSlicingJobCreate,
    current: CurrentUser = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    if current is None:
        raise HTTPException(status_code=401, detail="autenticação obrigatória")
    try:
        return repository.create_project_job(current.user.id, payload.model_copy(update={"project_id": project_id}))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/run", response_model=SlicingJob)
async def run_slicing_job(
    job_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    try:
        if uses_postgresql():
            return repository.schedule_job(job_id, current.user.id if current else None)
        return repository.run_job(job_id, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/approve-preview", response_model=SlicingJob)
async def approve_slicing_preview(
    job_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    try:
        return repository.approve_gcode(job_id, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/gcode", response_class=PlainTextResponse)
async def get_slicing_gcode(
    job_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> PlainTextResponse:
    job = repository.get_job(job_id, current.user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="job de fatiamento não encontrado")
    artifact = next((item for item in job.artifacts if item.artifact_kind == "gcode"), None)
    if artifact is None:
        raise HTTPException(status_code=404, detail="G-code não encontrado")
    content = _read_artifact_text(get_settings().data_dir, artifact.storage_key)
    if not content:
        raise HTTPException(status_code=404, detail="G-code indisponível")
    return PlainTextResponse(content, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.post("/jobs/{job_id}/reprint", response_model=SlicingJob)
async def create_reprint_slicing_job(
    job_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
) -> SlicingJob:
    try:
        return repository.create_reprint_job(job_id, current.user.id)
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


@router.get("/preflights", response_model=list[PrintPreflightRecord])
async def list_print_preflights(
    slicing_job_id: int | None = None,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintPreflightRepository = Depends(get_print_preflight_repository),
) -> list[PrintPreflightRecord]:
    return repository.list_preflights(current.user.id if current else None, slicing_job_id)


@router.post("/jobs/{job_id}/preflight", response_model=PrintPreflightRecord)
async def create_print_preflight(
    job_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    pipeline: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
    repository: PrintPreflightRepository = Depends(get_print_preflight_repository),
) -> PrintPreflightRecord:
    settings = get_settings()
    actor_user_id = current.user.id if current else None
    job = pipeline.get_job(job_id, actor_user_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job de fatiamento não encontrado")
    printer = printer_for_user(settings.database_path, current.user, int(job.printer_id or 0)) if current else None
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.create_preflight(printer, actor_user_id, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/preflights/{preflight_id}/refresh", response_model=PrintPreflightRecord)
async def refresh_print_preflight(
    preflight_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintPreflightRepository = Depends(get_print_preflight_repository),
) -> PrintPreflightRecord:
    try:
        return repository.refresh_preflight(preflight_id, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/deliveries", response_model=list[PrintDeliveryRecord])
async def list_print_deliveries(
    preflight_id: int | None = None,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintDeliveryRepository = Depends(get_print_delivery_repository),
) -> list[PrintDeliveryRecord]:
    return repository.list_deliveries(current.user.id if current else None, preflight_id)


@router.post("/deliveries", response_model=PrintDeliveryRecord)
async def create_print_delivery(
    payload: PrintDeliveryCreate,
    authorization: str | None = Header(default=None),
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    preflights: PrintPreflightRepository = Depends(get_print_preflight_repository),
    pipeline: SlicingPipelineRepository = Depends(get_slicing_pipeline_repository),
    repository: PrintDeliveryRepository = Depends(get_print_delivery_repository),
    history: PrintHistoryRepository = Depends(get_print_history_repository),
) -> PrintDeliveryRecord:
    settings = get_settings()
    actor_user_id = current.user.id if current else None
    preflight = preflights.get_preflight(payload.preflight_id, actor_user_id)
    if preflight is None:
        raise HTTPException(status_code=404, detail="preflight não encontrado")
    job = pipeline.get_job(preflight.slicing_job_id, actor_user_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job de fatiamento não encontrado")
    printer = printer_for_user(settings.database_path, current.user, preflight.printer_id) if current else None
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    step_up_authorized = _consume_step_up_when_available(settings.database_path, authorization, actor_user_id, payload.step_up_token)
    prepared = repository.prepare_delivery(actor_user_id=actor_user_id, preflight=preflight, job=job, payload=payload, step_up_authorized=step_up_authorized)
    if prepared.delivery.status == "blocked":
        return prepared.delivery
    try:
        job_record = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_upload",
            payload=prepared.payload,
            timeout_seconds=max(settings.request_timeout_seconds, 45.0),
        )
        repository.mark_remote_job(prepared.delivery.id, job_record.id)
        delivery = repository.complete_delivery(prepared.delivery.id, job_record.result or {})
        history.upsert_from_delivery(delivery=delivery, job=job)
        return delivery
    except AgentJobFailedError as exc:
        repository.mark_remote_job(prepared.delivery.id, exc.job.id)
        delivery = repository.fail_delivery(prepared.delivery.id, str(exc.detail), exc.job.result or {})
        history.upsert_from_delivery(delivery=delivery, job=job, status="failed")
        return delivery
    except HTTPException as exc:
        delivery = repository.fail_delivery(prepared.delivery.id, str(exc.detail), {})
        history.upsert_from_delivery(delivery=delivery, job=job, status="failed")
        return delivery


@router.post("/deliveries/{delivery_id}/cancel", response_model=PrintDeliveryRecord)
async def cancel_print_delivery(
    delivery_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintDeliveryRepository = Depends(get_print_delivery_repository),
) -> PrintDeliveryRecord:
    try:
        return repository.cancel_delivery(delivery_id, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/deliveries/{delivery_id}/rollback", response_model=PrintDeliveryRecord)
async def rollback_print_delivery(
    delivery_id: int,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintDeliveryRepository = Depends(get_print_delivery_repository),
) -> PrintDeliveryRecord:
    settings = get_settings()
    delivery = repository.get_delivery(delivery_id, current.user.id if current else None)
    if delivery is None:
        raise HTTPException(status_code=404, detail="envio não encontrado")
    if delivery.mode != "save_only" or delivery.status not in {"saved", "rollback_failed"}:
        raise HTTPException(status_code=400, detail="rollback automático só remove arquivo salvo sem impressão iniciada")
    printer = printer_for_user(settings.database_path, current.user, delivery.printer_id) if current else None
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        job_record = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_delete",
            payload={"safe_mode": "print_gcode_rollback", "remote_filename": delivery.remote_filename, "delivery_id": delivery.id},
            timeout_seconds=max(settings.request_timeout_seconds, 20.0),
        )
        repository.mark_rollback_job(delivery.id, job_record.id)
        return repository.complete_rollback(delivery.id, job_record.result or {})
    except AgentJobFailedError as exc:
        repository.mark_rollback_job(delivery.id, exc.job.id)
        return repository.complete_rollback(delivery.id, exc.job.result or {"status": "failed", "detail": exc.detail})
    except HTTPException as exc:
        return repository.complete_rollback(delivery.id, {"status": "failed", "detail": str(exc.detail)})


@router.get("/history", response_model=list[PrintJobHistoryRecord])
async def list_print_history(
    include_public: bool = False,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintHistoryRepository = Depends(get_print_history_repository),
) -> list[PrintJobHistoryRecord]:
    return repository.list_history(current.user.id if current else None, include_public=include_public)


@router.post("/history/{history_id}/events", response_model=PrintJobHistoryRecord)
async def record_print_history_event(
    history_id: int,
    payload: PrintJobHistoryEvent,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintHistoryRepository = Depends(get_print_history_repository),
) -> PrintJobHistoryRecord:
    try:
        return repository.record_event(history_id, current.user.id if current else None, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/history/{history_id}/feedback", response_model=PrintJobHistoryRecord)
async def add_print_history_feedback(
    history_id: int,
    payload: PrintFeedbackCreate,
    current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: PrintHistoryRepository = Depends(get_print_history_repository),
) -> PrintJobHistoryRecord:
    try:
        return repository.add_feedback(history_id, current.user.id if current else None, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _consume_step_up_when_available(database_path, authorization: str | None, actor_user_id: int | None, step_up_token: str | None) -> bool:
    if not authorization or actor_user_id is None or not step_up_token:
        return False
    repository = AuthRepository(database_path)
    return repository.consume_step_up(actor_user_id, step_up_token, "destructive_action")
