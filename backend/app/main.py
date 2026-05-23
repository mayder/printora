import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl

from app.audit import build_read_only_audit
from app.backups import (
    BackupArchiveCompareRequest,
    BackupArchiveCompareResponse,
    BackupPolicyCreate,
    BackupPolicyRecord,
    BackupRepository,
    BackupRestorePlanRequest,
    BackupRestorePlanResponse,
    BackupRestoreExecuteRequest,
    BackupRestoreGateResponse,
    BackupRunRecord,
    build_backup_restore_gate,
    build_backup_restore_plan,
    compare_backup_archives,
)
from app.calibration import (
    CalibrationAvailableTestsResponse,
    CalibrationExecutionRecord,
    CalibrationExecutionRequest,
    CalibrationPreflight,
    CalibrationRepository,
    CalibrationRunCreate,
    CalibrationRunRecord,
    CalibrationSequencePlan,
    CalibrationSummary,
    CalibrationTestRecord,
    build_available_calibration_tests,
    build_calibration_execution_gate,
    build_calibration_preflight,
)
from app.can_monitor import (
    CanBusParseRequest,
    CanBusRecord,
    CanBusRecordComparison,
    CanBusRecordCreate,
    CanBusSummary,
    CanMonitorRepository,
    parse_ip_link_can_output,
)
from app.checklists import build_post_update_checklist, build_unavailable_post_update_checklist
from app.config import Settings, get_settings
from app.database import get_database_version_info, initialize_database
from app.discovery import PrinterDiscoveryResponse, discover_moonraker_printers
from app.firmware import (
    BoardPreset,
    FirmwareBoardCreate,
    FirmwareBoardRecord,
    FirmwareBoardRepository,
    FirmwareBuildPreflight,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareBuildRunRecord,
    FirmwareFlashDryRunCreate,
    FirmwareFlashExecuteCreate,
    FirmwareFlashPreflight,
    FirmwareFlashRunRecord,
    FirmwareRecoveryPlan,
)
from app.health import build_printer_health, build_unreachable_health
from app.host_audit import collect_host_audit, summarize_sections
from app.maintenance import (
    MaintenanceEventCreate,
    MaintenanceEventRecord,
    MaintenanceRepository,
    MaintenanceSummary,
    MaintenanceTaskComplete,
    MaintenanceTaskCreate,
    MaintenanceTaskRecord,
)
from app.moonraker import MoonrakerClient
from app.operation import (
    build_operation_action_preflight,
    build_operation_action_preview,
    build_last_known_operation,
    build_offline_fixture_operation,
    build_operation_query_objects,
    build_operation_status,
    build_temperature_history,
    build_unreachable_operation,
)
from app.operation_history import (
    OperationActionExecutionAttemptRecord,
    OperationActionHistoryRepository,
    OperationActionPreviewRecord,
)
from app.plugins import PluginAuditResponse, build_plugin_audit
from app.printers import PrinterCreate, PrinterRecord, PrinterRepository, PrinterUpdate
from app.reports import SanitizedReport, build_sanitized_report
from app.releases import (
    GitHubReleaseClient,
    ReleasesResponse,
    build_releases_response,
    build_unavailable_releases_response,
)
from app.self_update import (
    SelfUpdateRepository,
    UpdateApplyRequest,
    UpdateApplyResponse,
    UpdateHistoryResponse,
    UpdatePlanRequest,
    UpdatePlanResponse,
    UpdateRollbackRequest,
    UpdateRollbackResponse,
    UpdateRunRecord,
    apply_self_update,
    build_update_plan,
    detect_update_environment,
    rollback_self_update,
)
from app.snapshots import (
    SnapshotDiff,
    SnapshotDetail,
    SnapshotRecord,
    SnapshotRepository,
    build_moonraker_snapshot_payload,
)
from app.updates import (
    UpdateActionResponse,
    UpdateRefreshRequest,
    UpdateRunRequest,
    UpdateStatusResponse,
    build_update_status,
    update_route_for_target,
)
from app.z_offset import (
    ZOffsetRecord,
    ZOffsetRecordCreate,
    ZOffsetRepository,
    ZOffsetWizardPlan,
    build_z_offset_wizard_plan,
)


class PrinterConnectionTestRequest(BaseModel):
    moonraker_url: HttpUrl
    ssh_host: str | None = Field(default=None, max_length=160)
    ssh_port: int = Field(default=22, ge=1, le=65535)


class ConnectionCheckResult(BaseModel):
    ok: bool
    target: str
    detail: str


class PrinterConnectionTestResponse(BaseModel):
    safe_mode: str
    moonraker: ConnectionCheckResult
    ssh: ConnectionCheckResult | None = None


class OperationActionPreviewRequest(BaseModel):
    action_id: str = Field(min_length=1, max_length=80)
    parameters: dict[str, Any] = Field(default_factory=dict)


class OperationActionExecuteRequest(BaseModel):
    preview_id: int = Field(gt=0)
    confirmation_phrase: str = Field(min_length=1, max_length=120)


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


def get_operation_action_history_repository(settings: Settings) -> OperationActionHistoryRepository:
    return OperationActionHistoryRepository(settings.database_path)


def get_z_offset_repository(settings: Settings) -> ZOffsetRepository:
    return ZOffsetRepository(settings.database_path)


def get_firmware_board_repository(settings: Settings) -> FirmwareBoardRepository:
    return FirmwareBoardRepository(settings.database_path)


def get_calibration_repository(settings: Settings) -> CalibrationRepository:
    return CalibrationRepository(settings.database_path)


def get_self_update_repository(settings: Settings) -> SelfUpdateRepository:
    return SelfUpdateRepository(settings.database_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_database(settings.database_path)
    yield


app = FastAPI(title="Printora", version="0.1.6", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

_frontend_dist_dir = get_settings().frontend_dist_dir
_frontend_assets_dir = _frontend_dist_dir / "assets"
_frontend_brand_dir = _frontend_dist_dir / "brand"
if _frontend_assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_assets_dir), name="frontend-assets")
if _frontend_brand_dir.is_dir():
    app.mount("/brand", StaticFiles(directory=_frontend_brand_dir), name="frontend-brand")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "Printora"}


@app.get("/api/system/version")
async def system_version() -> dict[str, object]:
    settings = get_settings()
    return get_database_version_info(settings.database_path, settings.data_dir)


@app.get("/api/system/releases")
async def system_releases() -> ReleasesResponse:
    settings = get_settings()
    if settings.release_source_mode == "disabled":
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status="disabled",
        )
    client = GitHubReleaseClient(
        owner=settings.release_github_owner,
        repo=settings.release_github_repo,
        api_base_url=settings.release_github_api_base_url,
        timeout_seconds=settings.release_request_timeout_seconds,
        fixture_path=settings.release_fixture_path if settings.release_source_mode == "fixture" else None,
    )
    try:
        raw_releases = await client.fetch_releases()
    except httpx.HTTPStatusError as exc:
        status = "rate_limited" if _is_github_rate_limit(exc.response) else "offline"
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status=status,
            error=_github_http_error_detail(exc),
        )
    except httpx.HTTPError as exc:
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status="offline",
            error=str(exc),
        )
    except (OSError, ValueError) as exc:
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status="error",
            error=str(exc),
        )
    return build_releases_response(
        raw_releases=raw_releases,
        source=settings.release_source_mode,
        channel=settings.release_channel,
    )


@app.get("/api/system/update/status")
async def system_update_status() -> dict[str, object]:
    releases = await system_releases()
    environment = detect_update_environment()
    update_supported = environment in {"android_termux", "unix", "windows"}
    return {
        "safe_mode": "read_only",
        "update_supported": update_supported,
        "environment": environment,
        "installed_version": releases.installed_version,
        "channel": releases.channel,
        "update_status": releases.update_status,
        "latest_release_available": releases.latest_release_available,
        "latest_release": releases.latest_release.model_dump() if releases.latest_release else None,
        "status": releases.status,
        "message": "Update real disponível para Android/Termux, Unix e Windows." if update_supported else "Update real não suportado neste ambiente.",
        "release_error": releases.error,
    }


@app.post("/api/system/update/plan")
async def system_update_plan(payload: UpdatePlanRequest) -> UpdatePlanResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    try:
        return build_update_plan(
            repository=repository,
            request=payload,
            project_root=Path(__file__).resolve().parents[2],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/system/update/history")
async def system_update_history(limit: int = 20) -> UpdateHistoryResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    return UpdateHistoryResponse(runs=repository.list_runs(limit=limit))


@app.post("/api/system/update/apply")
async def system_update_apply(payload: UpdateApplyRequest) -> UpdateApplyResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    releases = await system_releases()
    stable_tags = {
        release.tag
        for release in releases.releases
        if not release.prerelease and not release.draft and release.channel == "stable"
    }
    try:
        return apply_self_update(
            repository=repository,
            request=payload,
            project_root=Path(__file__).resolve().parents[2],
            script_path=settings.self_update_script_path,
            android_script_path=settings.self_update_android_script_path,
            unix_script_path=settings.self_update_unix_script_path,
            windows_script_path=settings.self_update_windows_script_path,
            stable_release_tags=stable_tags,
            timeout_seconds=settings.self_update_timeout_seconds,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "Já existe update" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@app.post("/api/system/update/rollback")
async def system_update_rollback(payload: UpdateRollbackRequest) -> UpdateRollbackResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    try:
        return rollback_self_update(
            repository=repository,
            request=payload,
            project_root=Path(__file__).resolve().parents[2],
            script_path=settings.self_update_script_path,
            android_script_path=settings.self_update_android_script_path,
            unix_script_path=settings.self_update_unix_script_path,
            windows_script_path=settings.self_update_windows_script_path,
            timeout_seconds=settings.self_update_timeout_seconds,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "Já existe update" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@app.get("/api/system/update/runs/{run_id}")
async def system_update_run(run_id: int) -> UpdateRunRecord:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="update run not found")
    return run


@app.get("/")
async def frontend_index() -> FileResponse:
    index_path = get_settings().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return FileResponse(index_path)


@app.get("/favicon.png")
async def frontend_favicon() -> FileResponse:
    favicon_path = get_settings().frontend_dist_dir / "favicon.png"
    if not favicon_path.is_file():
        raise HTTPException(status_code=404, detail="favicon not found")
    return FileResponse(favicon_path)


@app.get("/apple-touch-icon.png")
async def frontend_apple_touch_icon() -> FileResponse:
    icon_path = get_settings().frontend_dist_dir / "apple-touch-icon.png"
    if not icon_path.is_file():
        raise HTTPException(status_code=404, detail="apple touch icon not found")
    return FileResponse(icon_path)


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


@app.get("/api/printers/discover")
async def discover_printers(cidr: str | None = None) -> PrinterDiscoveryResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    try:
        return await discover_moonraker_printers(
            cidr=cidr,
            registered_printers=repository.list_printers(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/printers/test-connection")
async def test_printer_connection(payload: PrinterConnectionTestRequest) -> PrinterConnectionTestResponse:
    settings = get_settings()
    moonraker_url = str(payload.moonraker_url).rstrip("/")
    moonraker = await _test_moonraker_connection(moonraker_url, settings.request_timeout_seconds)
    ssh = None
    if payload.ssh_host:
        ssh_host = payload.ssh_host.strip()
        if ssh_host:
            ssh = await _test_tcp_connection(ssh_host, payload.ssh_port, settings.request_timeout_seconds)
    return PrinterConnectionTestResponse(
        safe_mode="read_only",
        moonraker=moonraker,
        ssh=ssh,
    )


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
    started_at = time.perf_counter()
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
            latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
            payload = latest_snapshot.payload
            return {
                "printer_id": printer.id,
                "moonraker_url": printer.moonraker_url,
                **build_printer_health(
                    printer_info=_dict(payload.get("printer_info")),
                    server_info=_dict(payload.get("server_info")),
                    update_status=_dict(payload.get("update_status")),
                    system_info=_dict(payload.get("system_info")),
                    proc_stats=_dict(payload.get("proc_stats")),
                    snapshots=snapshots,
                    latest_diff=latest_diff,
                    data_state="last_snapshot",
                    source=f"snapshot:{latest_snapshot.id}",
                    error=str(exc),
                ),
            }
        return {
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            **build_unreachable_health(printer.moonraker_url, str(exc)),
        }
    api_latency_ms = (time.perf_counter() - started_at) * 1000

    snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
    latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)

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
            source=printer.moonraker_url,
            api_latency_ms=api_latency_ms,
        ),
    }


@app.get("/api/printers/{printer_id}/updates/status")
async def printer_update_status(printer_id: int) -> UpdateStatusResponse:
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
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return build_update_status(update_status)


@app.get("/api/printers/{printer_id}/operation/status")
async def printer_operation_status(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    recent_snapshots = _recent_moonraker_snapshots(snapshot_repository, printer.id, limit=12)

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        available_objects = await client.printer_objects_list()
        objects = await client.printer_objects(build_operation_query_objects(available_objects))
        objects["objects"] = available_objects
    except httpx.HTTPError as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            operation = build_last_known_operation(latest_snapshot)
            operation["temperature_history"] = build_temperature_history(recent_snapshots)
            return {
                "printer_id": printer.id,
                **operation,
            }
        return build_unreachable_operation(printer.moonraker_url, str(exc))

    operation = build_operation_status(
        printer_info=printer_info,
        server_info=server_info,
        system_info=system_info,
        proc_stats=proc_stats,
        objects=objects,
    )
    operation["temperature_history"] = build_temperature_history(recent_snapshots)
    return {
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        **operation,
    }


@app.get("/api/operation/fixtures/voron-offline")
async def operation_voron_offline_fixture() -> dict[str, Any]:
    return {
        "printer_id": 0,
        **build_offline_fixture_operation(),
    }


@app.get("/api/printers/{printer_id}/operation/actions/history")
async def list_printer_operation_action_history(printer_id: int, limit: int = 20) -> dict[str, list[OperationActionPreviewRecord]]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    history_repository = get_operation_action_history_repository(settings)
    return {"previews": history_repository.list_previews(printer.id, limit=limit)}


@app.get("/api/printers/{printer_id}/operation/actions/executions")
async def list_printer_operation_action_executions(printer_id: int, limit: int = 20) -> dict[str, list[OperationActionExecutionAttemptRecord]]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    history_repository = get_operation_action_history_repository(settings)
    return {"attempts": history_repository.list_execution_attempts(printer.id, limit=limit)}


@app.post("/api/printers/{printer_id}/operation/actions/preview")
async def preview_printer_operation_action(printer_id: int, payload: OperationActionPreviewRequest) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        preview = build_operation_action_preview(
            action_id=payload.action_id,
            parameters=payload.parameters,
            connected=False,
            print_state="",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    history_repository = get_operation_action_history_repository(settings)
    record = history_repository.create_preview(printer.id, preview)
    return {
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        "history_id": record.id,
        "created_at": record.created_at,
        **preview,
    }


@app.post("/api/printers/{printer_id}/operation/actions/preflight")
async def preflight_printer_operation_action(printer_id: int, payload: OperationActionPreviewRequest) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    objects: dict[str, Any] = {}
    if preflight.get("connected") is not False:
        try:
            available_objects = await client.printer_objects_list()
            objects = {"objects": available_objects}
        except httpx.HTTPError:
            objects = {}
    try:
        action_preflight = build_operation_action_preflight(
            action_id=payload.action_id,
            parameters=payload.parameters,
            preflight=preflight,
            objects=objects,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        **action_preflight,
    }


@app.post("/api/printers/{printer_id}/operation/actions/execute")
async def execute_printer_operation_action(
    printer_id: int,
    payload: OperationActionExecuteRequest,
) -> OperationActionExecutionAttemptRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    history_repository = get_operation_action_history_repository(settings)
    preview = history_repository.get_preview(payload.preview_id)
    if preview is None or preview.printer_id != printer.id:
        raise HTTPException(status_code=404, detail="preview not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    return history_repository.create_execution_attempt(
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase=payload.confirmation_phrase,
        preflight=preflight,
    )


@app.post("/api/printers/{printer_id}/updates/refresh")
async def refresh_printer_update_status(
    printer_id: int,
    payload: UpdateRefreshRequest,
) -> UpdateActionResponse:
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
        result = await client.refresh_update_status(payload.name)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return UpdateActionResponse(
        safe_mode="moonraker_update_manager",
        action="refresh",
        target=payload.name or "all",
        accepted=True,
        message="Atualização de status solicitada ao Moonraker.",
        result=result,
    )


@app.post("/api/printers/{printer_id}/updates/run")
async def run_printer_update(printer_id: int, payload: UpdateRunRequest) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    route, target = update_route_for_target(payload.target)
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        if target == "all":
            result = await client.update_all()
        elif target == "system":
            result = await client.update_system()
        elif target in {"klipper", "moonraker"}:
            result = await client.update_core_component(target)
        else:
            result = await client.update_client(target)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=_http_error_detail(exc)) from exc
    return UpdateActionResponse(
        safe_mode="moonraker_update_manager",
        action="update",
        target=target,
        accepted=True,
        message=f"Update solicitado ao Moonraker via {route}.",
        result=result,
    )


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
        snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
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
                source=printer.moonraker_url,
            ),
        }
    except httpx.HTTPError as exc:
        snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
        latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            health_payload = {
                "printer_id": printer.id,
                "moonraker_url": printer.moonraker_url,
                **build_printer_health(
                    printer_info=_dict(payload.get("printer_info")),
                    server_info=_dict(payload.get("server_info")),
                    update_status=_dict(payload.get("update_status")),
                    system_info=_dict(payload.get("system_info")),
                    proc_stats=_dict(payload.get("proc_stats")),
                    snapshots=snapshots,
                    latest_diff=latest_diff,
                    data_state="last_snapshot",
                    source=f"snapshot:{latest_snapshot.id}",
                    error=str(exc),
                ),
            }
        else:
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


@app.get("/api/printers/{printer_id}/can/summary")
async def can_bus_summary(printer_id: int) -> CanBusSummary:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    can_repository = get_can_monitor_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return can_repository.summary(printer_id)


@app.get("/api/printers/{printer_id}/can/compare")
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


@app.post("/api/printers/{printer_id}/can/parse")
async def parse_can_bus_output(printer_id: int, payload: CanBusParseRequest) -> CanBusRecordCreate:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return parse_ip_link_can_output(payload)


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


@app.post("/api/firmware/boards/{board_id}/build-runs/preflight")
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


@app.post("/api/firmware/boards/{board_id}/flash-runs/preflight")
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


@app.post("/api/firmware/boards/{board_id}/flash-runs/execute")
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


@app.get("/api/firmware/boards/{board_id}/recovery-plan")
async def firmware_recovery_plan(board_id: int) -> FirmwareRecoveryPlan:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.build_recovery_plan(board_id)
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


@app.get("/api/printers/{printer_id}/calibration/available-tests")
async def list_available_calibration_tests(printer_id: int) -> CalibrationAvailableTestsResponse:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    connected = True
    try:
        available_objects = await client.printer_objects_list()
        object_payload = await client.printer_objects({"toolhead": ["axis_minimum", "axis_maximum"]}) if "toolhead" in available_objects else {}
    except httpx.HTTPError:
        connected = False
        available_objects = []
        object_payload = {}
    return build_available_calibration_tests(
        printer_id=printer.id,
        tests=repository.list_tests(),
        available_objects=available_objects,
        object_status=object_payload.get("status", object_payload) if isinstance(object_payload, dict) else {},
        connected=connected,
    )


@app.get("/api/printers/{printer_id}/calibration/runs")
async def list_calibration_runs(printer_id: int, limit: int = 50) -> dict[str, list[CalibrationRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": repository.list_runs(printer_id, clean_limit)}


@app.get("/api/printers/{printer_id}/calibration/executions")
async def list_calibration_executions(printer_id: int, limit: int = 20) -> dict[str, list[CalibrationExecutionRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"executions": repository.list_execution_attempts(printer_id, limit=limit)}


@app.get("/api/printers/{printer_id}/calibration/summary")
async def calibration_summary(printer_id: int) -> CalibrationSummary:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.summary(printer_id)


@app.get("/api/printers/{printer_id}/calibration/sequence")
async def calibration_sequence(printer_id: int) -> CalibrationSequencePlan:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.sequence_plan(printer_id)


@app.get("/api/printers/{printer_id}/calibration/tests/{test_key}/preflight")
async def calibration_test_preflight(printer_id: int, test_key: str) -> CalibrationPreflight:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    test = repository.get_test(test_key)
    if test is None:
        raise HTTPException(status_code=404, detail="calibration test not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    return build_calibration_preflight(printer_id=printer.id, test=test, preflight=preflight)


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


@app.post("/api/printers/{printer_id}/calibration/execute")
async def execute_calibration_test(
    printer_id: int,
    payload: CalibrationExecutionRequest,
) -> CalibrationExecutionRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    test = repository.get_test(payload.test_key)
    if test is None:
        raise HTTPException(status_code=404, detail="calibration test not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    gate = build_calibration_execution_gate(test=test, payload=payload, preflight=preflight)
    if gate.status == "blocked":
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status="blocked",
            sent_commands=[],
            result=[],
            message=gate.message,
        )

    sent_commands: list[str] = []
    results: list[dict[str, Any]] = []
    failed_command: str | None = None
    for command in gate.commands:
        result = await _send_and_monitor_gcode(client, command, settings.request_timeout_seconds)
        results.append(result)
        if result.get("accepted"):
            sent_commands.append(command)
            continue
        failed_command = command
        break

    if failed_command is not None:
        status = "failed_partial" if sent_commands else "failed"
        failed_result = results[-1] if results else {}
        error_detail = str(failed_result.get("transport_error") or failed_result.get("monitor_error") or "sem detalhe")
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status=status,
            sent_commands=sent_commands,
            result=results,
            message=f"Falha ao confirmar G-code '{failed_command}': {error_detail}",
        )

    return repository.create_execution_attempt(
        printer_id=printer.id,
        test=test,
        gate=gate,
        status="executed",
        sent_commands=sent_commands,
        result=results,
        message="G-code de calibração enviado e confirmado por monitoramento final do Moonraker.",
    )


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


@app.delete("/api/maintenance/events/{event_id}")
async def delete_maintenance_event(event_id: int) -> MaintenanceEventRecord:
    settings = get_settings()
    maintenance_repository = get_maintenance_repository(settings)
    event = maintenance_repository.delete_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance event not found")
    return event


@app.get("/api/printers/{printer_id}/maintenance/tasks")
async def list_maintenance_tasks(printer_id: int) -> dict[str, list[MaintenanceTaskRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    maintenance_repository.ensure_default_tasks(printer_id)
    return {"tasks": maintenance_repository.list_tasks(printer_id)}


@app.get("/api/printers/{printer_id}/maintenance/summary")
async def maintenance_summary(printer_id: int) -> MaintenanceSummary:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    maintenance_repository.ensure_default_tasks(printer_id)
    return maintenance_repository.summary(printer_id)


@app.post("/api/printers/{printer_id}/maintenance/tasks")
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


@app.post("/api/printers/{printer_id}/maintenance/tasks/defaults")
async def create_default_maintenance_tasks(printer_id: int) -> dict[str, list[MaintenanceTaskRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"tasks": maintenance_repository.create_default_tasks(printer_id)}


@app.get("/api/printers/{printer_id}/maintenance/print-hours")
async def refresh_maintenance_print_hours(printer_id: int) -> dict[str, object]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    maintenance_repository = get_maintenance_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return await _refresh_maintenance_print_hours(printer_id, printer_repository, maintenance_repository)


@app.post("/api/maintenance/tasks/{task_id}/complete")
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
    event = maintenance_repository.complete_task(task_id, payload)
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance task not found")
    return event


@app.delete("/api/maintenance/tasks/{task_id}/latest-event")
async def delete_latest_maintenance_task_event(task_id: int) -> MaintenanceEventRecord:
    settings = get_settings()
    maintenance_repository = get_maintenance_repository(settings)
    event = maintenance_repository.delete_latest_task_event(task_id)
    if event is None:
        raise HTTPException(status_code=404, detail="maintenance task event not found")
    return event


async def _refresh_maintenance_print_hours(
    printer_id: int,
    printer_repository: PrinterRepository,
    maintenance_repository: MaintenanceRepository,
) -> dict[str, object]:
    tasks = maintenance_repository.list_tasks(printer_id)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        return {"available": False, "total_print_hours": None, "read_at": None, "source": "unavailable"}
    print_hours = await _read_printer_print_hours(printer.moonraker_url)
    if print_hours is None:
        if any(task.current_print_hours is not None for task in tasks):
            maintenance_repository.update_current_print_hours(printer_id, None, read_at=_now_iso(), source="cached")
        return {"available": False, "total_print_hours": None, "read_at": None, "source": "unavailable"}
    read_at = _now_iso()
    maintenance_repository.update_current_print_hours(printer_id, print_hours, read_at=read_at, source="live")
    return {"available": True, "total_print_hours": print_hours, "read_at": read_at, "source": "live"}


async def _read_printer_print_hours(moonraker_url: str) -> float | None:
    client = MoonrakerClient(moonraker_url, timeout_seconds=3.0)
    try:
        totals = await client.history_totals()
    except Exception:
        return None
    job_totals = totals.get("job_totals")
    if not isinstance(job_totals, dict):
        return None
    total_seconds = job_totals.get("total_print_time")
    if not isinstance(total_seconds, int | float):
        return None
    # Limitação: não soma print_stats.print_duration em impressão ativa; isso exigiria combinar duas leituras.
    return round(float(total_seconds) / 3600.0, 3)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


@app.post("/api/backup/archives/compare")
async def compare_backup_archives_endpoint(payload: BackupArchiveCompareRequest) -> BackupArchiveCompareResponse:
    try:
        return compare_backup_archives(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/backup/restore-plan")
async def backup_restore_plan(payload: BackupRestorePlanRequest) -> BackupRestorePlanResponse:
    try:
        return build_backup_restore_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/backup/restore-gate")
async def backup_restore_gate(payload: BackupRestoreExecuteRequest) -> BackupRestoreGateResponse:
    try:
        return build_backup_restore_gate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
    try:
        printer_info = await client.printer_info()
        server_info = await client.server_info()
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        return build_unavailable_post_update_checklist(
            data_state="offline",
            source=settings.moonraker_url,
            error=str(exc),
        )
    return build_post_update_checklist(
        printer_info,
        server_info,
        update_status,
        source=settings.moonraker_url,
    )


@app.get("/api/printers/{printer_id}/checklist/post-update")
async def printer_post_update_checklist(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info = await client.printer_info()
        server_info = await client.server_info()
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            return build_post_update_checklist(
                _dict(payload.get("printer_info")),
                _dict(payload.get("server_info")),
                _dict(payload.get("update_status")),
                data_state="last_snapshot",
                source=f"snapshot:{latest_snapshot.id}",
                error=str(exc),
            )
        return build_unavailable_post_update_checklist(
            data_state="offline",
            source=printer.moonraker_url,
            error=str(exc),
        )
    return build_post_update_checklist(
        printer_info,
        server_info,
        update_status,
        source=printer.moonraker_url,
    )


@app.get("/api/audit/read-only")
async def read_only_audit() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        return _build_unreachable_audit(settings.moonraker_url, exc)

    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        source=settings.moonraker_url,
    )
    return {
        "connected": True,
        "moonraker_url": settings.moonraker_url,
        **audit,
    }


@app.get("/api/printers/{printer_id}/audit/read-only")
async def printer_read_only_audit(printer_id: int) -> dict[str, Any]:
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
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            audit = build_read_only_audit(
                printer_info=_dict(payload.get("printer_info")),
                server_info=_dict(payload.get("server_info")),
                update_status=_dict(payload.get("update_status")),
                system_info=_dict(payload.get("system_info")),
                proc_stats=_dict(payload.get("proc_stats")),
                data_state="last_snapshot",
                source=f"snapshot:{latest_snapshot.id}",
                error=str(exc),
            )
            return {
                "connected": False,
                "moonraker_url": printer.moonraker_url,
                **audit,
            }
        return _build_unreachable_audit(printer.moonraker_url, exc)

    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        source=printer.moonraker_url,
    )
    return {
        "connected": True,
        "moonraker_url": printer.moonraker_url,
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


def _latest_moonraker_snapshot(snapshot_repository: SnapshotRepository, printer_id: int) -> SnapshotDetail | None:
    snapshots = _recent_moonraker_snapshots(snapshot_repository, printer_id, limit=1)
    return snapshots[0] if snapshots else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _recent_moonraker_snapshots(snapshot_repository: SnapshotRepository, printer_id: int, limit: int) -> list[SnapshotDetail]:
    snapshots: list[SnapshotDetail] = []
    for snapshot in snapshot_repository.list_snapshots_by_type(printer_id, "moonraker_status", limit=limit):
        detail = snapshot_repository.get_snapshot(snapshot.id)
        if detail is not None:
            snapshots.append(detail)
    return snapshots


async def _operation_execution_preflight(client: MoonrakerClient) -> dict[str, Any]:
    try:
        printer_info = await client.printer_info()
        server_info = await client.server_info()
        available_objects = await client.printer_objects_list()
        query_objects: dict[str, list[str]] = {"print_stats": ["state", "filename"]}
        if "toolhead" in available_objects:
            query_objects["toolhead"] = ["axis_minimum", "axis_maximum"]
        objects = await client.printer_objects(query_objects)
    except httpx.HTTPError as exc:
        return {
            "safe_mode": "read_only_preflight",
            "connected": False,
            "printing": False,
            "print_state": "",
            "summary": "Moonraker indisponível no preflight.",
            "error": str(exc),
        }
    status = objects.get("status", objects)
    print_stats = status.get("print_stats") if isinstance(status, dict) else {}
    print_state = str(print_stats.get("state") or "") if isinstance(print_stats, dict) else ""
    return {
        "safe_mode": "read_only_preflight",
        "connected": bool(server_info.get("klippy_connected", True)),
        "printing": print_state not in {"", "standby", "complete", "cancelled", "error"},
        "print_state": print_state,
        "klipper_state": printer_info.get("state"),
        "klippy_state": server_info.get("klippy_state"),
        "available_objects": available_objects,
        "object_status": status if isinstance(status, dict) else {},
        "summary": "Preflight read-only concluído.",
    }


async def _send_and_monitor_gcode(
    client: MoonrakerClient,
    command: str,
    request_timeout_seconds: float,
) -> dict[str, Any]:
    started_at = time.monotonic()
    record: dict[str, Any] = {
        "command": command,
        "accepted": False,
        "transport_status": "pending",
        "monitor_status": "pending",
    }
    try:
        record["gcode_store_before"] = await client.gcode_store(count=8)
    except httpx.HTTPError as exc:
        record["gcode_store_before_error"] = _http_error_detail(exc)

    try:
        record["submit_result"] = await client.gcode_script(
            command,
            timeout_seconds=max(request_timeout_seconds, 30.0),
        )
        record["transport_status"] = "ok"
    except httpx.HTTPError as exc:
        record["transport_status"] = "error"
        record["transport_error"] = _http_error_detail(exc)

    final_state = await _monitor_gcode_final_state(client)
    record["final_state"] = final_state
    record["monitor_status"] = "ok" if final_state.get("connected") else "error"
    if final_state.get("error"):
        record["monitor_error"] = final_state["error"]
    record["duration_seconds"] = round(time.monotonic() - started_at, 3)

    transport_ok = record["transport_status"] == "ok"
    ready_after_send = bool(final_state.get("connected")) and _final_state_is_ready(final_state)
    record["accepted"] = transport_ok or ready_after_send
    if record["accepted"] and record["transport_status"] == "error":
        record["transport_status"] = "accepted_after_monitoring"
    return record


async def _monitor_gcode_final_state(client: MoonrakerClient, *, timeout_seconds: float = 15.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_state: dict[str, Any] = {}
    while True:
        try:
            printer_info = await client.printer_info()
            server_info = await client.server_info()
            available_objects = await client.printer_objects_list()
            query_objects: dict[str, list[str]] = {"print_stats": ["state", "filename"]}
            if "toolhead" in available_objects:
                query_objects["toolhead"] = ["homed_axes", "position"]
            objects = await client.printer_objects(query_objects)
            status = objects.get("status", objects)
            print_stats = status.get("print_stats") if isinstance(status, dict) else {}
            toolhead = status.get("toolhead") if isinstance(status, dict) else {}
            last_state = {
                "connected": bool(server_info.get("klippy_connected", True)),
                "klipper_state": printer_info.get("state"),
                "klippy_state": server_info.get("klippy_state"),
                "print_state": str(print_stats.get("state") or "") if isinstance(print_stats, dict) else "",
                "filename": print_stats.get("filename") if isinstance(print_stats, dict) else None,
                "homed_axes": toolhead.get("homed_axes") if isinstance(toolhead, dict) else None,
                "position": toolhead.get("position") if isinstance(toolhead, dict) else None,
            }
            try:
                last_state["gcode_store_after"] = await client.gcode_store(count=20)
            except httpx.HTTPError as exc:
                last_state["gcode_store_after_error"] = _http_error_detail(exc)
            if _final_state_is_ready(last_state) or time.monotonic() >= deadline:
                return last_state
        except httpx.HTTPError as exc:
            last_state = {
                "connected": False,
                "error": _http_error_detail(exc),
            }
            if time.monotonic() >= deadline:
                return last_state
        await asyncio.sleep(0.5)


def _final_state_is_ready(state: dict[str, Any]) -> bool:
    return (
        bool(state.get("connected"))
        and state.get("klipper_state") == "ready"
        and state.get("klippy_state") == "ready"
        and str(state.get("print_state") or "") in {"", "standby", "complete", "cancelled"}
    )


def _build_unreachable_audit(moonraker_url: str, exc: Exception) -> dict[str, Any]:
    return {
        "safe_mode": "read_only",
        "data_state": "offline",
        "source": moonraker_url,
        "connected": False,
        "moonraker_url": moonraker_url,
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


async def _test_moonraker_connection(moonraker_url: str, timeout_seconds: float) -> ConnectionCheckResult:
    target = f"{moonraker_url}/server/info"
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(target)
        if response.status_code >= 400:
            return ConnectionCheckResult(
                ok=False,
                target=target,
                detail=f"HTTP {response.status_code}",
            )
        payload = response.json()
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        state = result.get("klippy_state", "desconhecido")
        version = result.get("moonraker_version", "versao desconhecida")
        return ConnectionCheckResult(
            ok=True,
            target=target,
            detail=f"Moonraker respondeu. Klippy={state}. Moonraker={version}.",
        )
    except Exception as exc:
        return ConnectionCheckResult(ok=False, target=target, detail=str(exc))


async def _test_tcp_connection(host: str, port: int, timeout_seconds: float) -> ConnectionCheckResult:
    target = f"{host}:{port}"
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout_seconds)
        writer.close()
        await writer.wait_closed()
        del reader
        return ConnectionCheckResult(
            ok=True,
            target=target,
            detail="Porta SSH acessivel. Este teste nao autentica usuario/senha.",
        )
    except Exception as exc:
        return ConnectionCheckResult(ok=False, target=target, detail=str(exc))


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


def _http_error_detail(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        response_text = exc.response.text.strip()
        if response_text:
            return f"Moonraker HTTP {exc.response.status_code}: {response_text}"
        return f"Moonraker HTTP {exc.response.status_code}"
    return str(exc)


def _is_github_rate_limit(response: httpx.Response) -> bool:
    if response.status_code == 429:
        return True
    if response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
        return True
    return response.status_code == 403 and "rate limit" in response.text.lower()


def _github_http_error_detail(exc: httpx.HTTPStatusError) -> str:
    response_text = exc.response.text.strip()
    if response_text:
        return f"GitHub HTTP {exc.response.status_code}: {response_text}"
    return f"GitHub HTTP {exc.response.status_code}"


@app.get("/{frontend_path:path}")
async def frontend_fallback(frontend_path: str) -> FileResponse:
    if frontend_path == "health" or frontend_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="not found")
    index_path = get_settings().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return FileResponse(index_path)
