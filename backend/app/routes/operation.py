from __future__ import annotations

from app.routes.support import *
from fastapi import Depends, Header

from app.agent_executor import AgentCommandExecutor, AgentJobFailedError
from app.agent_moonraker import agent_preflight_payload, operation_payload
from app.agent_pairing import EXPECTED_AGENT_VERSION, AgentPairingRepository, printer_for_user
from app.auth import AuthRepository, CurrentUser
from app.gcode_cache import (
    GcodeCacheEntry,
    GcodeCachePrepareRequest,
    MAX_GCODE_CACHE_BYTES,
    gcode_cache_file_response,
    gcode_cache_key,
    normalize_gcode_filename,
    read_gcode_cache_entry,
)
from app.operation import operation_action_blocks_when_printing, operation_action_requires_step_up
from app.routes.auth import require_current_user_when_configured
from app.routes.auth import require_current_user

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])

OPERATION_STATUS_TIMEOUT_SECONDS = 25.0
OPERATION_PREFLIGHT_TIMEOUT_SECONDS = 12.0
OPERATION_GCODE_CACHE_TIMEOUT_SECONDS = 120.0


@router.get("/api/printers/{printer_id}/operation/status")
async def printer_operation_status(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    recent_snapshots = _recent_moonraker_snapshots(snapshot_repository, printer.id, limit=12)

    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_operation_status",
            timeout_seconds=_operation_status_timeout(settings),
        )
        printer_info, server_info, system_info, proc_stats, objects, history_totals, file_metadata = operation_payload(job.result)
    except HTTPException as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            operation = build_last_known_operation(latest_snapshot)
            operation["temperature_history"] = build_temperature_history(recent_snapshots)
            return {
                "printer_id": printer.id,
                "agent": _agent_operation_status(settings, printer.id),
                **operation,
            }
        operation = build_unreachable_operation(printer.moonraker_url, _http_exception_detail(exc))
        return {"printer_id": printer.id, "agent": _agent_operation_status(settings, printer.id), **operation}

    operation = build_operation_status(
        printer_info=printer_info,
        server_info=server_info,
        system_info=system_info,
        proc_stats=proc_stats,
        objects=objects,
        history_totals=history_totals,
        print_metadata=file_metadata,
    )
    operation["temperature_history"] = build_temperature_history(recent_snapshots)
    return {
        "printer_id": printer.id,
        "moonraker_url": "agent",
        "agent": _agent_operation_status(settings, printer.id),
        **operation,
    }


@router.post("/api/printers/{printer_id}/operation/gcode-cache", response_model=GcodeCacheEntry)
async def prepare_printer_operation_gcode_cache(
    printer_id: int,
    payload: GcodeCachePrepareRequest,
    current: CurrentUser = Depends(require_current_user),
) -> GcodeCacheEntry:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    filename = normalize_gcode_filename(payload.filename)
    cache_key = gcode_cache_key(printer.id, filename)
    cached = read_gcode_cache_entry(settings, printer.id, cache_key)
    if cached is not None:
        return cached
    install_status = AgentPairingRepository(settings.database_path).install_status(printer.id)
    if not install_status.ready:
        raise HTTPException(
            status_code=409,
            detail=f"agente {EXPECTED_AGENT_VERSION} ou superior é necessário para cache de G-code",
        )

    job = await AgentCommandExecutor(settings.database_path).run(
        printer,
        job_type="remote_gcode_cache",
        payload={
            "filename": filename,
            "cache_key": cache_key,
            "max_bytes": MAX_GCODE_CACHE_BYTES,
        },
        timeout_seconds=max(settings.request_timeout_seconds, OPERATION_GCODE_CACHE_TIMEOUT_SECONDS),
    )
    cached = read_gcode_cache_entry(settings, printer.id, cache_key)
    if cached is not None:
        return cached
    result = job.result or {}
    if result.get("status") == "cached" and result.get("cache_key") == cache_key:
        try:
            return GcodeCacheEntry.model_validate(result)
        except ValueError:
            pass
    raise HTTPException(status_code=502, detail="agente não confirmou o cache do G-code")


@router.get("/api/printers/{printer_id}/operation/gcode-cache/{cache_key}")
async def get_printer_operation_gcode_cache(
    printer_id: int,
    cache_key: str,
    current: CurrentUser = Depends(require_current_user),
):
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return gcode_cache_file_response(settings, printer.id, cache_key)




@router.get("/api/operation/fixtures/voron-offline")
async def operation_voron_offline_fixture() -> dict[str, Any]:
    return {
        "printer_id": 0,
        **build_offline_fixture_operation(),
    }




@router.get("/api/printers/{printer_id}/operation/actions/history")
async def list_printer_operation_action_history(printer_id: int, limit: int = 20) -> dict[str, list[OperationActionPreviewRecord]]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    history_repository = get_operation_action_history_repository(settings)
    return {"previews": history_repository.list_previews(printer.id, limit=limit)}




@router.get("/api/printers/{printer_id}/operation/actions/executions")
async def list_printer_operation_action_executions(printer_id: int, limit: int = 20) -> dict[str, list[OperationActionExecutionAttemptRecord]]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    history_repository = get_operation_action_history_repository(settings)
    return {"attempts": history_repository.list_execution_attempts(printer.id, limit=limit)}




@router.post("/api/printers/{printer_id}/operation/actions/preview")
async def preview_printer_operation_action(printer_id: int, payload: OperationActionPreviewRequest) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    preview = await _build_agent_operation_action_preview(settings, printer, payload.action_id, payload.parameters)
    history_repository = get_operation_action_history_repository(settings)
    record = history_repository.create_preview(printer.id, preview)
    return {
        "printer_id": printer.id,
        "moonraker_url": "agent",
        "history_id": record.id,
        "created_at": record.created_at,
        **preview,
    }




@router.post("/api/printers/{printer_id}/operation/actions/preflight")
async def preflight_printer_operation_action(printer_id: int, payload: OperationActionPreviewRequest) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    action_preflight = await _build_agent_operation_action_preview(settings, printer, payload.action_id, payload.parameters)
    return {
        "printer_id": printer.id,
        "moonraker_url": "agent",
        **action_preflight,
    }




@router.post("/api/printers/{printer_id}/operation/actions/execute")
async def execute_printer_operation_action(
    printer_id: int,
    payload: OperationActionExecuteRequest,
    authorization: str | None = Header(default=None),
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
    _require_step_up_when_authenticated(settings, authorization, payload.step_up_token, preview.action_id)
    return await _execute_operation_preview_via_agent(
        settings=settings,
        printer=printer,
        history_repository=history_repository,
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase=payload.confirmation_phrase,
    )


@router.post("/api/printers/{printer_id}/operation/actions/execute-direct")
async def execute_direct_printer_operation_action(
    printer_id: int,
    payload: OperationActionDirectExecuteRequest,
    authorization: str | None = Header(default=None),
) -> OperationActionExecutionAttemptRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    _require_step_up_when_authenticated(settings, authorization, payload.step_up_token, payload.action_id)
    preview = await _build_agent_operation_action_preview(settings, printer, payload.action_id, payload.parameters)
    history_repository = get_operation_action_history_repository(settings)
    record = history_repository.create_preview(printer.id, preview)
    preview_record = history_repository.get_preview(record.id)
    if preview_record is None:
        raise HTTPException(status_code=500, detail="preview not persisted")
    return await _execute_operation_preview_via_agent(
        settings=settings,
        printer=printer,
        history_repository=history_repository,
        printer_id=printer.id,
        preview=preview_record,
        confirmation_phrase=str(preview.get("confirmation_phrase") or ""),
    )


def _require_step_up_when_authenticated(settings, authorization: str | None, step_up_token: str | None, action_id: str) -> None:
    if not operation_action_requires_step_up(action_id):
        return
    if not authorization:
        return
    repository = AuthRepository(settings.database_path)
    current = require_current_user(authorization=authorization, repository=repository)
    if not step_up_token or not repository.consume_step_up(current.user.id, step_up_token, "destructive_action"):
        raise HTTPException(status_code=403, detail="autenticação reforçada obrigatória para ação crítica")


def _agent_operation_status(settings, printer_id: int) -> dict[str, Any]:
    install_status = AgentPairingRepository(settings.database_path).install_status(printer_id)
    return {
        "version": install_status.latest_version,
        "expected_version": install_status.expected_agent_version,
        "ready": install_status.ready,
        "diagnostic": install_status.diagnostic,
    }


async def _build_agent_operation_action_preview(settings, printer, action_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    executor = AgentCommandExecutor(settings.database_path)
    preflight_job = await executor.run(
        printer,
        job_type="remote_gcode_preflight",
        payload={"action_id": action_id, "parameters": parameters, "criticality": "preview"},
        timeout_seconds=max(settings.request_timeout_seconds, OPERATION_PREFLIGHT_TIMEOUT_SECONDS),
    )
    status_job = await executor.run(
        printer,
        job_type="remote_operation_status",
        timeout_seconds=_operation_status_timeout(settings),
    )
    _printer_info, _server_info, _system_info, _proc_stats, objects, _history, _file_metadata = operation_payload(status_job.result)
    try:
        return build_operation_action_preflight(
            action_id=action_id,
            parameters=parameters,
            preflight=agent_preflight_payload(preflight_job.result),
            objects=objects,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _execute_operation_preview_via_agent(
    *,
    settings,
    printer,
    history_repository: OperationActionHistoryRepository,
    printer_id: int,
    preview: OperationActionPreviewRecord,
    confirmation_phrase: str,
) -> OperationActionExecutionAttemptRecord:
    preflight_job = await AgentCommandExecutor(settings.database_path).run(
        printer,
        job_type="remote_gcode_preflight",
        payload={
            "action_id": preview.action_id,
            "criticality": "operation",
            "command_preview": preview.command_preview,
        },
        timeout_seconds=max(settings.request_timeout_seconds, OPERATION_PREFLIGHT_TIMEOUT_SECONDS),
    )
    preflight = agent_preflight_payload(preflight_job.result)
    confirmation_matched = confirmation_phrase.strip() == str(preview.payload.get("confirmation_phrase") or "")
    if not confirmation_matched:
        return history_repository.create_execution_attempt(
            printer_id=printer_id,
            preview=preview,
            confirmation_phrase=confirmation_phrase,
            preflight=preflight,
        )
    blockers = []
    if preflight.get("connected") is False:
        blockers.append("Bloqueado: preflight sem leitura ao vivo pelo agente.")
    if operation_action_blocks_when_printing(preview.action_id) and preflight.get("printing") is True:
        blockers.append("Bloqueado: preflight detectou impressão em andamento.")
    if not preview.executable or not preview.would_send_gcode:
        blockers.append("Bloqueado: preview marcado como não executável.")
    if blockers:
        return history_repository.create_execution_result(
            printer_id=printer_id,
            preview=preview,
            confirmation_phrase=confirmation_phrase,
            preflight=preflight,
            moonraker_response=None,
            status="blocked",
            block_reason=" ".join(blockers),
        )
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_execute",
            payload={
                "action_id": preview.action_id,
                "criticality": "operation",
                "commands": preview.command_preview,
                "timeout_seconds": max(settings.request_timeout_seconds, 45.0),
            },
            timeout_seconds=max(settings.request_timeout_seconds, 30.0),
        )
        result = job.result or {}
        result_status = str(result.get("status") or "")
        status = "executed" if result_status in {"executed", "dispatched_unconfirmed"} else "failed"
        block_reason = "" if status == "executed" else _remote_gcode_failure_detail(result)
    except AgentJobFailedError as exc:
        result = exc.job.result or {"accepted": False, "agent_error": exc.detail}
        result.setdefault("agent_error", exc.detail)
        status = "failed"
        block_reason = _remote_gcode_failure_detail(result)
    except HTTPException as exc:
        result = {"accepted": False, "agent_error": exc.detail}
        status = "failed"
        block_reason = str(exc.detail)
    return history_repository.create_execution_result(
        printer_id=printer_id,
        preview=preview,
        confirmation_phrase=confirmation_phrase,
        preflight=preflight,
        moonraker_response=result,
        status=status,
        block_reason=block_reason,
    )


def _remote_gcode_failure_detail(result: dict) -> str:
    candidates = [
        _string_value(result.get("moonraker_response_error")),
        _nested_string(result.get("moonraker_response"), "error", "message"),
        _nested_string(result.get("moonraker_response"), "error"),
        _nested_string(result.get("moonraker_response"), "result"),
    ]
    for item in result.get("results") or []:
        if not isinstance(item, dict):
            continue
        candidates.extend(
            [
                _string_value(item.get("detail")),
                _string_value(item.get("moonraker_response_error")),
                _nested_string(item.get("moonraker_response"), "error", "message"),
                _nested_string(item.get("moonraker_response"), "error"),
                _nested_string(item.get("moonraker_response"), "result"),
            ]
        )
    for message in result.get("console_excerpt") or []:
        text = _string_value(message)
        if "SAVE_CONFIG" in text or "conflicts with included value" in text:
            candidates.append(text)
    candidates.extend([_string_value(result.get("detail")), _string_value(result.get("agent_error"))])
    for candidate in candidates:
        if candidate:
            return candidate
    return "Agente não confirmou o comando."


def _string_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        message = value.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
        error = value.get("error")
        if isinstance(error, str) and error.strip():
            return error.strip()
    return str(value).strip()


def _operation_status_timeout(settings) -> float:
    return max(settings.request_timeout_seconds, OPERATION_STATUS_TIMEOUT_SECONDS)


def _http_exception_detail(exc: HTTPException) -> str:
    detail = exc.detail
    if isinstance(detail, str):
        return detail
    return str(detail)


def _nested_string(value, *keys: str) -> str:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return _string_value(current)
