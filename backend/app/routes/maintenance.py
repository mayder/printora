from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/printers/{printer_id}/maintenance/events")
async def list_maintenance_events(printer_id: int, limit: int = 50) -> dict[str, list[MaintenanceEventRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"events": maintenance_repository.list_events(printer_id, clean_limit)}




@router.post("/api/printers/{printer_id}/maintenance/events")
async def create_maintenance_event(
    printer_id: int,
    payload: MaintenanceEventCreate,
) -> MaintenanceEventRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return maintenance_repository.create_event(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.delete("/api/maintenance/events/{event_id}")
async def delete_maintenance_event(event_id: int) -> MaintenanceEventRecord:
    settings = get_settings()
    maintenance_repository = get_maintenance_repository(settings)
    event = maintenance_repository.delete_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance event not found")
    return event




@router.get("/api/printers/{printer_id}/maintenance/tasks")
async def list_maintenance_tasks(printer_id: int) -> dict[str, list[MaintenanceTaskRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    maintenance_repository.ensure_default_tasks(printer_id)
    return {"tasks": maintenance_repository.list_tasks(printer_id)}




@router.get("/api/printers/{printer_id}/maintenance/summary")
async def maintenance_summary(printer_id: int) -> MaintenanceSummary:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    maintenance_repository.ensure_default_tasks(printer_id)
    return maintenance_repository.summary(printer_id)




@router.post("/api/printers/{printer_id}/maintenance/tasks")
async def create_maintenance_task(
    printer_id: int,
    payload: MaintenanceTaskCreate,
) -> MaintenanceTaskRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    if payload.interval_kind == "print_hours" and payload.last_done_at and payload.last_done_print_hours is None:
        print_hours = await _read_printer_print_hours(printer.moonraker_url)
        if print_hours is None:
            raise HTTPException(status_code=400, detail="print hours unavailable")
        payload.last_done_print_hours = print_hours
        payload.last_print_hours_read_at = _now_iso()
        maintenance_repository.update_current_print_hours(
            printer_id,
            print_hours,
            read_at=payload.last_print_hours_read_at,
            source="live",
        )
    try:
        return maintenance_repository.create_task(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/printers/{printer_id}/maintenance/tasks/defaults")
async def create_default_maintenance_tasks(printer_id: int) -> dict[str, list[MaintenanceTaskRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"tasks": maintenance_repository.create_default_tasks(printer_id)}




@router.get("/api/printers/{printer_id}/maintenance/print-hours")
async def refresh_maintenance_print_hours(printer_id: int) -> dict[str, object]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return await _refresh_maintenance_print_hours(printer_id, printer_repository, maintenance_repository)




@router.post("/api/maintenance/tasks/{task_id}/complete")
async def complete_maintenance_task(
    task_id: int,
    payload: MaintenanceTaskComplete,
) -> MaintenanceEventRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    task = maintenance_repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="maintenance task not found")
    interval_kind = payload.next_interval_kind or task.interval_kind
    if interval_kind == "print_hours" and payload.print_hours_at is None:
        printer = printer_repository.get_printer(task.printer_id)
        if printer is not None:
            print_hours = await _read_printer_print_hours(printer.moonraker_url)
            if print_hours is None:
                raise HTTPException(status_code=400, detail="print hours unavailable")
            payload.print_hours_at = print_hours
            payload.print_hours_read_at = _now_iso()
            maintenance_repository.update_current_print_hours(
                task.printer_id,
                print_hours,
                read_at=payload.print_hours_read_at,
                source="live",
            )
    try:
        event = maintenance_repository.complete_task(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance task not found")
    return event




@router.patch("/api/maintenance/tasks/{task_id}/applicability")
async def update_maintenance_task_applicability(
    task_id: int,
    payload: MaintenanceTaskApplicabilityUpdate,
) -> MaintenanceTaskRecord:
    settings = get_settings()
    maintenance_repository = get_maintenance_repository(settings)
    task = maintenance_repository.update_task_applicability(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="maintenance task not found")
    return task




@router.delete("/api/maintenance/tasks/{task_id}/latest-event")
async def delete_latest_maintenance_task_event(task_id: int) -> MaintenanceEventRecord:
    settings = get_settings()
    maintenance_repository = get_maintenance_repository(settings)
    event = maintenance_repository.delete_latest_task_event(task_id)
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance task event not found")
    return event
