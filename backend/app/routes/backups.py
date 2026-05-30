from __future__ import annotations

from fastapi import Depends

from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/printers/{printer_id}/backup/policies")
async def list_backup_policies(printer_id: int) -> dict[str, list[BackupPolicyRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"policies": backup_repository.list_policies(printer_id)}




@router.post("/api/printers/{printer_id}/backup/policies")
async def create_backup_policy(printer_id: int, payload: BackupPolicyCreate) -> BackupPolicyRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return backup_repository.create_policy(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/printers/{printer_id}/backup/runs")
async def list_backup_runs(printer_id: int, limit: int = 20) -> dict[str, list[BackupRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": backup_repository.list_runs(printer_id, clean_limit)}




@router.post("/api/backup/policies/{policy_id}/dry-run")
async def create_backup_dry_run(policy_id: int) -> BackupRunRecord:
    settings = get_settings()
    backup_repository = get_backup_repository(settings)
    run = backup_repository.create_dry_run(policy_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backup policy not found")
    return run




@router.post("/api/backup/policies/{policy_id}/execute-local")
async def execute_local_backup(policy_id: int) -> BackupRunRecord:
    settings = get_settings()
    backup_repository = get_backup_repository(settings)
    run = backup_repository.execute_local_backup(policy_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backup policy not found")
    return run




@router.post("/api/backup/archives/compare")
async def compare_backup_archives_endpoint(payload: BackupArchiveCompareRequest) -> BackupArchiveCompareResponse:
    try:
        return compare_backup_archives(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/backup/restore-plan")
async def backup_restore_plan(payload: BackupRestorePlanRequest) -> BackupRestorePlanResponse:
    try:
        return build_backup_restore_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/backup/restore-gate")
async def backup_restore_gate(payload: BackupRestoreExecuteRequest) -> BackupRestoreGateResponse:
    try:
        return build_backup_restore_gate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
