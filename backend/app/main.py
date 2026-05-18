from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.audit import build_read_only_audit
from app.backups import BackupPolicyCreate, BackupPolicyRecord, BackupRepository, BackupRunRecord
from app.calibration import CalibrationRepository, CalibrationRunCreate, CalibrationRunRecord, CalibrationTestRecord
from app.can_monitor import CanBusRecord, CanBusRecordCreate, CanMonitorRepository
from app.checklists import build_post_update_checklist
from app.config import Settings, get_settings
from app.database import initialize_database
from app.firmware import (
    BoardPreset,
    FirmwareBoardCreate,
    FirmwareBoardRecord,
    FirmwareBoardRepository,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareBuildRunRecord,
    FirmwareFlashDryRunCreate,
    FirmwareFlashRunRecord,
)
from app.health import build_printer_health, build_unreachable_health
from app.host_audit import collect_host_audit, summarize_sections
from app.maintenance import (
    MaintenanceEventCreate,
    MaintenanceEventRecord,
    MaintenanceRepository,
    MaintenanceTaskComplete,
    MaintenanceTaskCreate,
    MaintenanceTaskRecord,
)
from app.moonraker import MoonrakerClient
from app.plugins import PluginAuditResponse, build_plugin_audit
from app.printers import PrinterCreate, PrinterRecord, PrinterRepository, PrinterUpdate
from app.reports import SanitizedReport, build_sanitized_report
from app.snapshots import (
    SnapshotDiff,
    SnapshotDetail,
    SnapshotRecord,
    SnapshotRepository,
    build_moonraker_snapshot_payload,
)
from app.z_offset import (
    ZOffsetRecord,
    ZOffsetRecordCreate,
    ZOffsetRepository,
    ZOffsetWizardPlan,
    build_z_offset_wizard_plan,
)


def get_moonraker_client(settings: Settings) -> MoonrakerClient:
    return MoonrakerClient(
        base_url=settings.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )


def get_printer_repository(settings: Settings) -> PrinterRepository:
    return PrinterRepository(settings.database_path)


def get_snapshot_repository(settings: Settings) -> SnapshotRepository:
    return SnapshotRepository(settings.database_path)


def get_backup_repository(settings: Settings) -> BackupRepository:
    return BackupRepository(settings.database_path)


def get_can_monitor_repository(settings: Settings) -> CanMonitorRepository:
    return CanMonitorRepository(settings.database_path)


def get_maintenance_repository(settings: Settings) -> MaintenanceRepository:
    return MaintenanceRepository(settings.database_path)


def get_z_offset_repository(settings: Settings) -> ZOffsetRepository:
    return ZOffsetRepository(settings.database_path)


def get_firmware_board_repository(settings: Settings) -> FirmwareBoardRepository:
    return FirmwareBoardRepository(settings.database_path)


def get_calibration_repository(settings: Settings) -> CalibrationRepository:
    return CalibrationRepository(settings.database_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_database(settings.database_path)
    yield


app = FastAPI(title="MayderPrintLab", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

_frontend_dist_dir = get_settings().frontend_dist_dir
_frontend_assets_dir = _frontend_dist_dir / "assets"
if _frontend_assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_assets_dir), name="frontend-assets")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "MayderPrintLab"}


@app.get("/")
async def frontend_index() -> FileResponse:
    index_path = get_settings().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return FileResponse(index_path)


@app.get("/api/moonraker/status")
async def moonraker_status() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
    except httpx.HTTPError as exc:
        return {
            "connected": False,
            "moonraker_url": settings.moonraker_url,
            "error": str(exc),
        }

    return {
        "connected": True,
        "moonraker_url": settings.moonraker_url,
        "printer": printer_info,
        "server": server_info,
        "system": system_info,
        "proc_stats": proc_stats,
    }


@app.get("/api/printers")
async def list_printers() -> dict[str, list[PrinterRecord]]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    return {"printers": repository.list_printers()}


@app.post("/api/printers")
async def create_printer(payload: PrinterCreate) -> PrinterRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    try:
        return repository.create_printer(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/printers/{printer_id}")
async def update_printer(printer_id: int, payload: PrinterUpdate) -> PrinterRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    try:
        record = repository.update_printer(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return record


@app.get("/api/printers/{printer_id}/moonraker/status")
async def printer_moonraker_status(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
    except httpx.HTTPError as exc:
        return {
            "connected": False,
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            "error": str(exc),
        }

    return {
        "connected": True,
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        "printer": printer_info,
        "server": server_info,
        "system": system_info,
        "proc_stats": proc_stats,
    }


@app.get("/api/printers/{printer_id}/health")
async def printer_health(printer_id: int) -> dict[str, Any]:
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
        return {
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            **build_unreachable_health(printer.moonraker_url, str(exc)),
        }

    snapshots = snapshot_repository.list_snapshots(printer.id, limit=2)
    latest_diff = None
    if len(snapshots) >= 2:
        latest_diff = snapshot_repository.diff_snapshots(printer.id, snapshots[1].id, snapshots[0].id)

    return {
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        **build_printer_health(
            printer_info=printer_info,
            server_info=server_info,
            update_status=update_status,
            system_info=system_info,
            proc_stats=proc_stats,
            snapshots=snapshots,
            latest_diff=latest_diff,
        ),
    }


@app.get("/api/printers/{printer_id}/reports/sanitized")
async def sanitized_report(printer_id: int) -> SanitizedReport:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    backup_repository = get_backup_repository(settings)
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
        snapshots = snapshot_repository.list_snapshots(printer.id, limit=2)
        latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
        health_payload = {
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            **build_printer_health(
                printer_info=printer_info,
                server_info=server_info,
                update_status=update_status,
                system_info=system_info,
                proc_stats=proc_stats,
                snapshots=snapshots,
                latest_diff=latest_diff,
            ),
        }
    except httpx.HTTPError as exc:
        snapshots = snapshot_repository.list_snapshots(printer.id, limit=2)
        latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
        health_payload = {
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            **build_unreachable_health(printer.moonraker_url, str(exc)),
        }

    backup_runs = backup_repository.list_runs(printer.id, limit=5)
    return build_sanitized_report(
        printer=printer,
        health=health_payload,
        snapshots=snapshots,
        latest_diff=latest_diff,
        backup_runs=backup_runs,
    )


@app.get("/api/printers/{printer_id}/z-offsets")
async def list_z_offset_records(printer_id: int, limit: int = 50) -> dict[str, list[ZOffsetRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    z_offset_repository = get_z_offset_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"records": z_offset_repository.list_records(printer_id, clean_limit)}


@app.post("/api/printers/{printer_id}/z-offsets")
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


@app.get("/api/printers/{printer_id}/z-offsets/wizard-plan")
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


@app.get("/api/printers/{printer_id}/can/records")
async def list_can_bus_records(printer_id: int, limit: int = 50) -> dict[str, list[CanBusRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    can_repository = get_can_monitor_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"records": can_repository.list_records(printer_id, clean_limit)}


@app.post("/api/printers/{printer_id}/can/records")
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


@app.get("/api/firmware/board-presets")
async def list_firmware_board_presets() -> dict[str, list[BoardPreset]]:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    return {"presets": firmware_repository.list_presets()}


@app.get("/api/printers/{printer_id}/firmware/boards")
async def list_firmware_boards(printer_id: int) -> dict[str, list[FirmwareBoardRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"boards": firmware_repository.list_boards(printer_id)}


@app.post("/api/printers/{printer_id}/firmware/boards")
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


@app.get("/api/printers/{printer_id}/firmware/build-runs")
async def list_firmware_build_runs(printer_id: int, limit: int = 20) -> dict[str, list[FirmwareBuildRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": firmware_repository.list_build_runs(printer_id, clean_limit)}


@app.post("/api/firmware/boards/{board_id}/build-runs/dry-run")
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


@app.post("/api/firmware/boards/{board_id}/build-runs/execute-local")
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


@app.get("/api/printers/{printer_id}/firmware/flash-runs")
async def list_firmware_flash_runs(printer_id: int, limit: int = 20) -> dict[str, list[FirmwareFlashRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": firmware_repository.list_flash_runs(printer_id, clean_limit)}


@app.post("/api/firmware/boards/{board_id}/flash-runs/dry-run")
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


@app.get("/api/calibration/tests")
async def list_calibration_tests(category: str | None = None) -> dict[str, list[CalibrationTestRecord]]:
    settings = get_settings()
    repository = get_calibration_repository(settings)
    return {"tests": repository.list_tests(category)}


@app.get("/api/calibration/tests/{test_key}")
async def get_calibration_test(test_key: str) -> CalibrationTestRecord:
    settings = get_settings()
    repository = get_calibration_repository(settings)
    record = repository.get_test(test_key)
    if record is None:
        raise HTTPException(status_code=404, detail="calibration test not found")
    return record


@app.get("/api/printers/{printer_id}/calibration/runs")
async def list_calibration_runs(printer_id: int, limit: int = 50) -> dict[str, list[CalibrationRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": repository.list_runs(printer_id, clean_limit)}


@app.post("/api/printers/{printer_id}/calibration/runs")
async def create_calibration_run(printer_id: int, payload: CalibrationRunCreate) -> CalibrationRunRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.create_run(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/printers/{printer_id}/plugins/audit")
async def plugin_audit(printer_id: int) -> PluginAuditResponse:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    snapshots = snapshot_repository.list_snapshots(printer_id, limit=20)
    latest_moonraker_snapshot = next((snapshot for snapshot in snapshots if snapshot.snapshot_type == "moonraker_status"), None)
    latest_snapshot = snapshot_repository.get_snapshot(latest_moonraker_snapshot.id) if latest_moonraker_snapshot else None
    return build_plugin_audit(printer_id, latest_snapshot)


@app.get("/api/printers/{printer_id}/maintenance/events")
async def list_maintenance_events(printer_id: int, limit: int = 50) -> dict[str, list[MaintenanceEventRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"events": maintenance_repository.list_events(printer_id, clean_limit)}


@app.post("/api/printers/{printer_id}/maintenance/events")
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


@app.get("/api/printers/{printer_id}/maintenance/tasks")
async def list_maintenance_tasks(printer_id: int) -> dict[str, list[MaintenanceTaskRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"tasks": maintenance_repository.list_tasks(printer_id)}


@app.post("/api/printers/{printer_id}/maintenance/tasks")
async def create_maintenance_task(
    printer_id: int,
    payload: MaintenanceTaskCreate,
) -> MaintenanceTaskRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return maintenance_repository.create_task(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/maintenance/tasks/{task_id}/complete")
async def complete_maintenance_task(
    task_id: int,
    payload: MaintenanceTaskComplete,
) -> MaintenanceEventRecord:
    settings = get_settings()
    maintenance_repository = get_maintenance_repository(settings)
    event = maintenance_repository.complete_task(task_id, payload)
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance task not found")
    return event


@app.get("/api/printers/{printer_id}/backup/policies")
async def list_backup_policies(printer_id: int) -> dict[str, list[BackupPolicyRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"policies": backup_repository.list_policies(printer_id)}


@app.post("/api/printers/{printer_id}/backup/policies")
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


@app.get("/api/printers/{printer_id}/backup/runs")
async def list_backup_runs(printer_id: int, limit: int = 20) -> dict[str, list[BackupRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": backup_repository.list_runs(printer_id, clean_limit)}


@app.post("/api/backup/policies/{policy_id}/dry-run")
async def create_backup_dry_run(policy_id: int) -> BackupRunRecord:
    settings = get_settings()
    backup_repository = get_backup_repository(settings)
    run = backup_repository.create_dry_run(policy_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backup policy not found")
    return run


@app.post("/api/backup/policies/{policy_id}/execute-local")
async def execute_local_backup(policy_id: int) -> BackupRunRecord:
    settings = get_settings()
    backup_repository = get_backup_repository(settings)
    run = backup_repository.execute_local_backup(policy_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backup policy not found")
    return run


@app.post("/api/printers/{printer_id}/snapshots/moonraker")
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

    payload = build_moonraker_snapshot_payload(
        printer_id=printer.id,
        moonraker_url=printer.moonraker_url,
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
    )
    return snapshot_repository.create_snapshot(printer.id, "moonraker_status", payload)


@app.get("/api/printers/{printer_id}/snapshots")
async def list_snapshots(printer_id: int, limit: int = 20) -> dict[str, list[SnapshotRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"snapshots": snapshot_repository.list_snapshots(printer_id, clean_limit)}


@app.get("/api/printers/{printer_id}/snapshots/diff")
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


@app.get("/api/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: int) -> SnapshotDetail:
    settings = get_settings()
    snapshot_repository = get_snapshot_repository(settings)
    snapshot = snapshot_repository.get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return snapshot


@app.get("/api/checklist/post-update")
async def post_update_checklist() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    printer_info = await client.printer_info()
    server_info = await client.server_info()
    update_status = await client.update_status()
    return build_post_update_checklist(printer_info, server_info, update_status)


@app.get("/api/audit/read-only")
async def read_only_audit() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        return {
            "safe_mode": "read_only",
            "connected": False,
            "moonraker_url": settings.moonraker_url,
            "summary": "Moonraker indisponível para auditoria somente leitura.",
            "error": str(exc),
            "counts": {
                "corrigir_agora": 0,
                "monitorar": 0,
                "ignorar": 0,
                "precisa_confirmacao": 1,
            },
            "findings": [
                {
                    "id": "moonraker_unreachable",
                    "title": "Moonraker não respondeu",
                    "category": "moonraker",
                    "classification": "precisa_confirmacao",
                    "severity": "warning",
                    "detail": str(exc),
                    "safe_action": "Validar URL e rede. Esta checagem não alterou a impressora.",
                }
            ],
        }

    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
    )
    return {
        "connected": True,
        "moonraker_url": settings.moonraker_url,
        **audit,
    }


@app.get("/api/audit/host-read-only")
async def host_read_only_audit() -> dict[str, Any]:
    settings = get_settings()
    result = await collect_host_audit(
        mode=settings.host_audit_mode,
        ssh_target=settings.host_audit_ssh_target,
        timeout_seconds=settings.host_audit_timeout_seconds,
    )
    return {
        "safe_mode": "read_only",
        "connected": result.executed and result.exit_code == 0,
        "mode": result.mode,
        "executed": result.executed,
        "exit_code": result.exit_code,
        "summary": _host_summary(result.findings),
        "counts": _count_findings(result.findings),
        "findings": [finding.__dict__ for finding in result.findings],
        "section_summary": summarize_sections(result.sections),
    }


async def _collect_status(client: MoonrakerClient) -> tuple[dict[str, Any], ...]:
    printer_info = await client.printer_info()
    server_info = await client.server_info()
    system_info = await client.system_info()
    proc_stats = await client.proc_stats()
    return printer_info, server_info, system_info, proc_stats


def _count_findings(findings: list[Any]) -> dict[str, int]:
    counts = {
        "corrigir_agora": 0,
        "monitorar": 0,
        "ignorar": 0,
        "precisa_confirmacao": 0,
    }
    for finding in findings:
        counts[finding.classification] += 1
    return counts


def _host_summary(findings: list[Any]) -> str:
    if any(finding.severity == "blocker" for finding in findings):
        return "Auditoria do host encontrou bloqueios."
    if any(finding.classification in {"monitorar", "precisa_confirmacao"} for finding in findings):
        return "Auditoria do host sem bloqueio crítico, mas com itens para revisar."
    return "Auditoria do host sem problemas críticos nos dados disponíveis."


def _latest_snapshot_diff(
    snapshot_repository: SnapshotRepository,
    printer_id: int,
    snapshots: list[SnapshotRecord],
) -> SnapshotDiff | None:
    if len(snapshots) < 2:
        return None
    return snapshot_repository.diff_snapshots(printer_id, snapshots[1].id, snapshots[0].id)


@app.get("/{frontend_path:path}")
async def frontend_fallback(frontend_path: str) -> FileResponse:
    if frontend_path == "health" or frontend_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="not found")
    index_path = get_settings().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return FileResponse(index_path)
