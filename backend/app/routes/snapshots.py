from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.post("/api/printers/{printer_id}/snapshots/moonraker")
async def create_moonraker_snapshot(printer_id: int) -> SnapshotDetail:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"moonraker read failed: {exc}") from exc

    operation_objects = None
    try:
        available_objects = await client.printer_objects_list()
        operation_objects = await client.printer_objects(build_operation_query_objects(available_objects))
        operation_objects["objects"] = available_objects
    except httpx.HTTPError:
        operation_objects = None

    payload = build_moonraker_snapshot_payload(
        printer_id=printer.id,
        moonraker_url=printer.moonraker_url,
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
    snapshot_repository = get_snapshot_repository(settings)
    snapshot = snapshot_repository.get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return snapshot
