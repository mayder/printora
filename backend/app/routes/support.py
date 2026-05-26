import asyncio
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, FastAPI, HTTPException
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
from app.firmware_catalog import FirmwareHardwareInventory, build_firmware_hardware_inventory
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
from app.network_diagnostics import build_network_diagnostics
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
    installed_app_version,
)
from app.self_update import (
    SelfUpdateRepository,
    UpdateApplyRequest,
    UpdateApplyResponse,
    UpdateHistoryResponse,
    UpdatePlanRequest,
    UpdatePlanResponse,
    UpdateReconcileResponse,
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
    RISK_UPDATE_CONFIRMATION_PHRASE,
    ROLLBACK_CONFIRMATION_PHRASE,
    UpdateActionResponse,
    UpdateAlertSilenceRepository,
    UpdateRefreshRequest,
    UpdateSilenceRequest,
    UpdateSilenceResponse,
    PrinterUpdateRollbackRequest,
    UpdateRunRequest,
    UpdateStatusResponse,
    apply_update_alert_silences,
    build_update_status,
    risky_update_components,
    update_component_version_key,
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


def get_update_alert_silence_repository(settings: Settings) -> UpdateAlertSilenceRepository:
    return UpdateAlertSilenceRepository(settings.database_path)


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
    main_module = sys.modules.get("app.main")
    override = getattr(main_module, "_read_printer_print_hours", None) if main_module is not None else None
    if override is not None and override is not _read_printer_print_hours:
        return await override(moonraker_url)

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




async def _collect_status(client: MoonrakerClient) -> tuple[dict[str, Any], ...]:
    printer_info, server_info, system_info, proc_stats = await asyncio.gather(
        client.printer_info(),
        client.server_info(),
        client.system_info(),
        client.proc_stats(),
    )
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


def _firmware_inventory_query_objects(object_names: list[str]) -> dict[str, list[str]]:
    objects: dict[str, list[str]] = {}
    for name in object_names:
        if name == "mcu" or name.startswith("mcu "):
            objects[name] = ["mcu_version", "mcu_build_versions"]
    if "configfile" in object_names:
        objects["configfile"] = ["settings"]
    return objects


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


__all__ = [name for name in globals() if not name.startswith("__")]
