from __future__ import annotations

from app.routes.support import *
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
