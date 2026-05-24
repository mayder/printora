from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/firmware/board-presets")
async def list_firmware_board_presets() -> dict[str, list[BoardPreset]]:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    return {"presets": firmware_repository.list_presets()}




@router.get("/api/printers/{printer_id}/firmware/boards")
async def list_firmware_boards(printer_id: int) -> dict[str, list[FirmwareBoardRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"boards": firmware_repository.list_boards(printer_id)}




@router.get("/api/printers/{printer_id}/firmware/hardware-inventory")
async def firmware_hardware_inventory(printer_id: int) -> FirmwareHardwareInventory:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        object_names = await client.printer_objects_list()
        query_objects = _firmware_inventory_query_objects(object_names)
        object_payload = await client.printer_objects(query_objects) if query_objects else {"status": {}}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Moonraker indisponível para inventário de firmware: {exc}") from exc
    return build_firmware_hardware_inventory(
        printer_id=printer_id,
        registered_boards=firmware_repository.list_boards(printer_id),
        object_names=object_names,
        object_payload=object_payload,
    )




@router.post("/api/printers/{printer_id}/firmware/boards")
async def create_firmware_board(printer_id: int, payload: FirmwareBoardCreate) -> FirmwareBoardRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return firmware_repository.create_board(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/printers/{printer_id}/firmware/build-runs")
async def list_firmware_build_runs(printer_id: int, limit: int = 20) -> dict[str, list[FirmwareBuildRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": firmware_repository.list_build_runs(printer_id, clean_limit)}




@router.post("/api/firmware/boards/{board_id}/build-runs/dry-run")
async def create_firmware_build_dry_run(
    board_id: int,
    payload: FirmwareBuildDryRunCreate,
) -> FirmwareBuildRunRecord:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.create_build_dry_run(board_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/build-runs/preflight")
async def firmware_build_preflight(
    board_id: int,
    payload: FirmwareBuildDryRunCreate,
) -> FirmwareBuildPreflight:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.build_build_preflight(
            board_id=board_id,
            payload=payload,
            mode=settings.firmware_build_mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/build-runs/execute-local")
async def execute_firmware_build_local(
    board_id: int,
    payload: FirmwareBuildExecuteCreate,
) -> FirmwareBuildRunRecord:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.execute_build_local(
            board_id=board_id,
            payload=payload,
            mode=settings.firmware_build_mode,
            timeout_seconds=settings.firmware_build_timeout_seconds,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/printers/{printer_id}/firmware/flash-runs")
async def list_firmware_flash_runs(printer_id: int, limit: int = 20) -> dict[str, list[FirmwareFlashRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": firmware_repository.list_flash_runs(printer_id, clean_limit)}




@router.post("/api/firmware/boards/{board_id}/flash-runs/dry-run")
async def create_firmware_flash_dry_run(
    board_id: int,
    payload: FirmwareFlashDryRunCreate,
) -> FirmwareFlashRunRecord:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.create_flash_dry_run(board_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/flash-runs/preflight")
async def firmware_flash_preflight(
    board_id: int,
    payload: FirmwareFlashDryRunCreate,
) -> FirmwareFlashPreflight:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    board = firmware_repository.get_board(board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="firmware board not found")
    printer_repository = get_printer_repository(settings)
    printer = printer_repository.get_printer(board.printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    try:
        return firmware_repository.build_flash_preflight(board_id, payload, preflight)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/flash-runs/execute")
async def execute_firmware_flash_blocked(
    board_id: int,
    payload: FirmwareFlashExecuteCreate,
) -> FirmwareFlashRunRecord:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.execute_flash_blocked(board_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/firmware/boards/{board_id}/recovery-plan")
async def firmware_recovery_plan(board_id: int) -> FirmwareRecoveryPlan:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.build_recovery_plan(board_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
