from __future__ import annotations

from app.routes.support import *
from fastapi import Depends, Header

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import agent_preflight_payload, operation_payload
from app.auth import AuthRepository
from app.routes.auth import require_current_user_when_configured
from app.routes.auth import require_current_user

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


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
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        printer_info, server_info, system_info, proc_stats, objects, history_totals = operation_payload(job.result)
    except HTTPException as exc:
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
        history_totals=history_totals,
    )
    operation["temperature_history"] = build_temperature_history(recent_snapshots)
    return {
        "printer_id": printer.id,
        "moonraker_url": "agent",
        **operation,
    }




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
    _require_step_up_when_authenticated(settings, authorization, payload.step_up_token)
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
    _require_step_up_when_authenticated(settings, authorization, payload.step_up_token)
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


def _require_step_up_when_authenticated(settings, authorization: str | None, step_up_token: str | None) -> None:
    if not authorization:
        return
    repository = AuthRepository(settings.database_path)
    current = require_current_user(authorization=authorization, repository=repository)
    if not step_up_token or not repository.consume_step_up(current.user.id, step_up_token, "destructive_action"):
        raise HTTPException(status_code=403, detail="autenticação reforçada obrigatória para ação crítica")


async def _build_agent_operation_action_preview(settings, printer, action_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    executor = AgentCommandExecutor(settings.database_path)
    preflight_job = await executor.run(
        printer,
        job_type="remote_gcode_preflight",
        payload={"action_id": action_id, "parameters": parameters, "criticality": "preview"},
        timeout_seconds=max(settings.request_timeout_seconds, 10.0),
    )
    status_job = await executor.run(
        printer,
        job_type="remote_operation_status",
        timeout_seconds=max(settings.request_timeout_seconds, 10.0),
    )
    _printer_info, _server_info, _system_info, _proc_stats, objects, _history = operation_payload(status_job.result)
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
        timeout_seconds=max(settings.request_timeout_seconds, 10.0),
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
    if preflight.get("printing") is True:
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


def _nested_string(value, *keys: str) -> str:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return _string_value(current)
