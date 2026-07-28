from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import operation_payload, status_payload
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.post("/api/printers/{printer_id}/snapshots/moonraker")
async def create_moonraker_snapshot(printer_id: int) -> SnapshotDetail:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    try:
        status_job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_moonraker_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        operation_job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_operation_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
    except HTTPException as exc:
        raise HTTPException(status_code=502, detail=f"agent read failed: {exc.detail}") from exc
    printer_info, server_info, system_info, proc_stats, update_status = status_payload(status_job.result)
    _p, _s, _sys, _proc, operation_objects, _history, _file_metadata, _gcode_files = operation_payload(operation_job.result)

    payload = build_moonraker_snapshot_payload(
        printer_id=printer.id,
        moonraker_url="agent",
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        operation_objects=operation_objects,
    )
    return snapshot_repository.create_snapshot(printer.id, "moonraker_status", payload)




@router.get("/api/printers/{printer_id}/snapshots")
async def list_snapshots(printer_id: int, limit: int = 20) -> dict[str, list[SnapshotRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"snapshots": snapshot_repository.list_snapshots(printer_id, clean_limit)}




@router.get("/api/printers/{printer_id}/snapshots/diff")
async def diff_snapshots(printer_id: int, from_id: int, to_id: int) -> SnapshotDiff:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    diff = snapshot_repository.diff_snapshots(printer_id, from_id, to_id)
    if diff is None:
        raise HTTPException(status_code=404, detail="snapshots not found for printer")
    return diff




@router.get("/api/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: int) -> SnapshotDetail:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    snapshot = snapshot_repository.get_snapshot(snapshot_id)
    if snapshot is None or printer_repository.get_printer(snapshot.printer_id) is None:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return snapshot
