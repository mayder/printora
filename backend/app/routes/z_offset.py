from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/printers/{printer_id}/z-offsets")
async def list_z_offset_records(printer_id: int, limit: int = 50) -> dict[str, list[ZOffsetRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    z_offset_repository = get_z_offset_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"records": z_offset_repository.list_records(printer_id, clean_limit)}




@router.post("/api/printers/{printer_id}/z-offsets")
async def create_z_offset_record(printer_id: int, payload: ZOffsetRecordCreate) -> ZOffsetRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    z_offset_repository = get_z_offset_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return z_offset_repository.create_record(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/printers/{printer_id}/z-offsets/wizard-plan")
async def z_offset_wizard_plan(
    printer_id: int,
    plate_name: str = "Texturizada",
    material: str = "PLA",
    nozzle: str = "T0",
    proposed_offset_value: float = 0.0,
) -> ZOffsetWizardPlan:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    z_offset_repository = get_z_offset_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    previous = z_offset_repository.latest_matching_record(printer_id, plate_name, material, nozzle)
    return build_z_offset_wizard_plan(
        plate_name=plate_name,
        material=material,
        nozzle=nozzle,
        proposed_offset_value=proposed_offset_value,
        previous_record=previous,
    )
