from __future__ import annotations

from app.routes.support import *
from app.setup_can import (
    SetupCanApplyRequest,
    SetupCanApplyResponse,
    SetupCanPlanResponse,
    SetupCanPreflightResponse,
    SetupCanRequest,
    SetupCanRunRecord,
    SetupCanRunRepository,
    apply_setup_can,
    build_setup_can_plan,
    run_setup_can_preflight,
)
from app.setup_firmware import (
    SetupFirmwareBuildRequest,
    SetupFirmwareBuildResponse,
    SetupFirmwarePlanResponse,
    SetupFirmwareRequest,
    SetupFirmwareRunRecord,
    SetupFirmwareRunRepository,
    build_setup_firmware_plan,
    execute_setup_firmware_build,
)
from app.setup_wizard import (
    SetupSshPlanResponse,
    SetupSshPreflightResponse,
    SetupSshRunRecord,
    SetupSshRunRepository,
    SetupSshTarget,
    build_setup_plan,
    run_setup_ssh_preflight,
)

router = APIRouter()


def get_setup_ssh_repository(settings: Settings) -> SetupSshRunRepository:
    return SetupSshRunRepository(settings.database_path)


def get_setup_can_repository(settings: Settings) -> SetupCanRunRepository:
    return SetupCanRunRepository(settings.database_path)


def get_setup_firmware_repository(settings: Settings) -> SetupFirmwareRunRepository:
    return SetupFirmwareRunRepository(settings.database_path)


@router.post("/api/setup/ssh/preflight")
async def setup_ssh_preflight(payload: SetupSshTarget) -> SetupSshPreflightResponse:
    settings = get_settings()
    repository = get_setup_ssh_repository(settings)
    response = await run_setup_ssh_preflight(payload)
    response.history_id = repository.create_preflight(payload, response)
    return response


@router.post("/api/setup/ssh/plan")
async def setup_ssh_plan(payload: SetupSshTarget) -> SetupSshPlanResponse:
    settings = get_settings()
    repository = get_setup_ssh_repository(settings)
    preflight = await run_setup_ssh_preflight(payload)
    preflight.history_id = repository.create_preflight(payload, preflight)
    response = build_setup_plan(preflight)
    response.history_id = repository.create_plan(payload, response)
    return response


@router.get("/api/setup/ssh/history")
async def setup_ssh_history(limit: int = 20) -> dict[str, list[SetupSshRunRecord]]:
    settings = get_settings()
    repository = get_setup_ssh_repository(settings)
    return {"runs": repository.list_runs(limit=limit)}


@router.post("/api/setup/can/preflight")
async def setup_can_preflight(payload: SetupCanRequest) -> SetupCanPreflightResponse:
    settings = get_settings()
    repository = get_setup_can_repository(settings)
    response = await run_setup_can_preflight(payload)
    response.history_id = repository.create_preflight(payload, response)
    return response


@router.post("/api/setup/can/plan")
async def setup_can_plan(payload: SetupCanRequest) -> SetupCanPlanResponse:
    settings = get_settings()
    repository = get_setup_can_repository(settings)
    preflight = await run_setup_can_preflight(payload)
    preflight.history_id = repository.create_preflight(payload, preflight)
    response = build_setup_can_plan(preflight)
    response.history_id = repository.create_plan(payload, response)
    return response


@router.post("/api/setup/can/apply")
async def setup_can_apply(payload: SetupCanApplyRequest) -> SetupCanApplyResponse:
    settings = get_settings()
    repository = get_setup_can_repository(settings)
    response = await apply_setup_can(payload)
    response.history_id = repository.create_apply(payload, response)
    return response


@router.get("/api/setup/can/history")
async def setup_can_history(limit: int = 20) -> dict[str, list[SetupCanRunRecord]]:
    settings = get_settings()
    repository = get_setup_can_repository(settings)
    return {"runs": repository.list_runs(limit=limit)}


@router.post("/api/setup/firmware/plan")
async def setup_firmware_plan(payload: SetupFirmwareRequest) -> SetupFirmwarePlanResponse:
    settings = get_settings()
    repository = get_setup_firmware_repository(settings)
    try:
        response = build_setup_firmware_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.history_id = repository.create_plan(payload, response)
    return response


@router.post("/api/setup/firmware/build")
async def setup_firmware_build(payload: SetupFirmwareBuildRequest) -> SetupFirmwareBuildResponse:
    settings = get_settings()
    repository = get_setup_firmware_repository(settings)
    try:
        response = await execute_setup_firmware_build(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.history_id = repository.create_build(payload, response)
    return response


@router.get("/api/setup/firmware/history")
async def setup_firmware_history(limit: int = 20) -> dict[str, list[SetupFirmwareRunRecord]]:
    settings = get_settings()
    repository = get_setup_firmware_repository(settings)
    return {"runs": repository.list_runs(limit=limit)}
