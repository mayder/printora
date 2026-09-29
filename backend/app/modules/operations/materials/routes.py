from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.agent_executor import AgentCommandExecutor, AgentJobFailedError
from app.agent_pairing import printer_for_user
from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user

from .contracts import (
    CompatibilityRequest,
    CompatibilityResult,
    ConsumptionPayload,
    MaterialConsumption,
    MaterialQualitySample,
    MaterialSpool,
    QualitySamplePayload,
    SpoolPayload,
    SpoolUpdatePayload,
    SpoolmanSyncResult,
)
from .repository import MaterialConflictError, MaterialInventoryRepository, MaterialNotFoundError
from .service import MaterialInventoryService, extract_spoolman_items


router = APIRouter(prefix="/api/materials", tags=["materials"])


def get_material_service() -> MaterialInventoryService:
    settings = get_settings()
    return MaterialInventoryService(MaterialInventoryRepository(settings.database_path))


@router.get("/spools", response_model=list[MaterialSpool])
async def list_spools(
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> list[MaterialSpool]:
    return service.list_spools(current.user.id)


@router.post("/spools", response_model=MaterialSpool, status_code=status.HTTP_201_CREATED)
async def create_spool(
    payload: SpoolPayload,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> MaterialSpool:
    return _call(service.create_spool, current.user.id, payload)


@router.get("/spools/{spool_id}", response_model=MaterialSpool)
async def get_spool(
    spool_id: int,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> MaterialSpool:
    return _call(service.spool, spool_id, current.user.id)


@router.put("/spools/{spool_id}", response_model=MaterialSpool)
async def update_spool(
    spool_id: int,
    payload: SpoolUpdatePayload,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> MaterialSpool:
    return _call(service.update_spool, spool_id, current.user.id, payload)


@router.delete("/spools/{spool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_spool(
    spool_id: int,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> None:
    _call(service.archive_spool, spool_id, current.user.id)


@router.post("/compatibility", response_model=CompatibilityResult)
async def check_compatibility(
    payload: CompatibilityRequest,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> CompatibilityResult:
    return _call(service.compatibility, current.user.id, payload)


@router.get("/spools/{spool_id}/consumptions", response_model=list[MaterialConsumption])
async def list_consumptions(
    spool_id: int,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> list[MaterialConsumption]:
    return _call(service.consumptions, spool_id, current.user.id)


@router.post("/consumptions", response_model=MaterialConsumption, status_code=status.HTTP_201_CREATED)
async def record_consumption(
    payload: ConsumptionPayload,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> MaterialConsumption:
    return _call(service.record_consumption, current.user.id, payload)


@router.get("/spools/{spool_id}/quality", response_model=list[MaterialQualitySample])
async def list_quality_samples(
    spool_id: int,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> list[MaterialQualitySample]:
    return _call(service.quality_samples, spool_id, current.user.id)


@router.post("/quality", response_model=MaterialQualitySample, status_code=status.HTTP_201_CREATED)
async def create_quality_sample(
    payload: QualitySamplePayload,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> MaterialQualitySample:
    return _call(service.create_quality_sample, current.user.id, payload)


@router.post("/spoolman/sync/{printer_id}", response_model=SpoolmanSyncResult)
async def sync_spoolman(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    service: MaterialInventoryService = Depends(get_material_service),
) -> SpoolmanSyncResult:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_spoolman_inventory",
            timeout_seconds=max(settings.request_timeout_seconds, 20.0),
        )
    except (AgentJobFailedError, HTTPException) as exc:
        return SpoolmanSyncResult(
            printer_id=printer_id,
            status="unavailable",
            detail=f"Spoolman não respondeu pelo agente: {_safe_detail(exc)}",
        )
    if not extract_spoolman_items(job.result) and _contains_error(job.result):
        return SpoolmanSyncResult(
            printer_id=printer_id,
            status="unavailable",
            detail="Spoolman não está configurado ou não respondeu. O inventário local continua disponível.",
        )
    imported, updated, total = service.import_spoolman(current.user.id, job.result)
    return SpoolmanSyncResult(
        printer_id=printer_id,
        status="synced",
        imported=imported,
        updated=updated,
        total=total,
        detail="Inventário do Spoolman sincronizado sem alterar o catálogo canônico.",
    )


def _call(function, *args):
    try:
        return function(*args)
    except MaterialNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MaterialConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _contains_error(value) -> bool:
    if isinstance(value, dict):
        return any(str(key).endswith("_error") or _contains_error(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_error(item) for item in value)
    return False


def _safe_detail(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)[:240]
    return "falha temporária"
