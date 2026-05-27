from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/printers/{printer_id}/operation/status")
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

    try:
        history_totals = await client.history_totals()
    except httpx.HTTPError:
        history_totals = None

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
        "moonraker_url": printer.moonraker_url,
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
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preview = await _build_live_operation_action_preview(client, payload.action_id, payload.parameters)
    history_repository = get_operation_action_history_repository(settings)
    record = history_repository.create_preview(printer.id, preview)
    return {
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
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
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    action_preflight = await _build_live_operation_action_preview(client, payload.action_id, payload.parameters)
    return {
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        **action_preflight,
    }




@router.post("/api/printers/{printer_id}/operation/actions/execute")
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
    return await _execute_operation_preview(
        client=client,
        history_repository=history_repository,
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase=payload.confirmation_phrase,
        timeout_seconds=settings.request_timeout_seconds,
    )


@router.post("/api/printers/{printer_id}/operation/actions/execute-direct")
async def execute_direct_printer_operation_action(
    printer_id: int,
    payload: OperationActionDirectExecuteRequest,
) -> OperationActionExecutionAttemptRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preview = await _build_live_operation_action_preview(client, payload.action_id, payload.parameters)
    history_repository = get_operation_action_history_repository(settings)
    record = history_repository.create_preview(printer.id, preview)
    preview_record = history_repository.get_preview(record.id)
    if preview_record is None:
        raise HTTPException(status_code=500, detail="preview not persisted")
    return await _execute_operation_preview(
        client=client,
        history_repository=history_repository,
        printer_id=printer.id,
        preview=preview_record,
        confirmation_phrase=str(preview.get("confirmation_phrase") or ""),
        timeout_seconds=settings.request_timeout_seconds,
    )


async def _build_live_operation_action_preview(client: MoonrakerClient, action_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    preflight = await _operation_execution_preflight(client)
    objects: dict[str, Any] = {}
    if preflight.get("connected") is not False:
        try:
            available_objects = await client.printer_objects_list()
            objects = {"objects": available_objects}
        except httpx.HTTPError:
            objects = {}
    try:
        return build_operation_action_preflight(
            action_id=action_id,
            parameters=parameters,
            preflight=preflight,
            objects=objects,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _execute_operation_preview(
    *,
    client: MoonrakerClient,
    history_repository: OperationActionHistoryRepository,
    printer_id: int,
    preview: OperationActionPreviewRecord,
    confirmation_phrase: str,
    timeout_seconds: float,
) -> OperationActionExecutionAttemptRecord:
    preflight = await _operation_execution_preflight(client)
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
        blockers.append("Bloqueado: preflight sem leitura ao vivo do Moonraker.")
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
    command = "\n".join(preview.command_preview)
    result = await _send_and_monitor_gcode(client, command, timeout_seconds)
    status = "executed" if result.get("accepted") else "failed"
    block_reason = "" if status == "executed" else str(result.get("transport_error") or result.get("monitor_error") or "Moonraker não confirmou o comando.")
    return history_repository.create_execution_result(
        printer_id=printer_id,
        preview=preview,
        confirmation_phrase=confirmation_phrase,
        preflight=preflight,
        moonraker_response=result,
        status=status,
        block_reason=block_reason,
    )
