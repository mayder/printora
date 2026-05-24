from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/printers/{printer_id}/can/records")
async def list_can_bus_records(printer_id: int, limit: int = 50) -> dict[str, list[CanBusRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    can_repository = get_can_monitor_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"records": can_repository.list_records(printer_id, clean_limit)}




@router.get("/api/printers/{printer_id}/can/summary")
async def can_bus_summary(printer_id: int) -> CanBusSummary:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    can_repository = get_can_monitor_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return can_repository.summary(printer_id)




@router.get("/api/printers/{printer_id}/can/compare")
async def compare_can_bus_records(
    printer_id: int,
    before_record_id: int,
    after_record_id: int,
) -> CanBusRecordComparison:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    can_repository = get_can_monitor_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return can_repository.compare_records(printer_id, before_record_id, after_record_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/printers/{printer_id}/can/parse")
async def parse_can_bus_output(printer_id: int, payload: CanBusParseRequest) -> CanBusRecordCreate:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return parse_ip_link_can_output(payload)




@router.post("/api/printers/{printer_id}/can/records")
async def create_can_bus_record(printer_id: int, payload: CanBusRecordCreate) -> CanBusRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    can_repository = get_can_monitor_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return can_repository.create_record(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
