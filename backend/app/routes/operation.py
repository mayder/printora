from __future__ import annotations

from app.routes.support import *
import json

from fastapi import Depends, Header, Query

from app.agent_executor import AgentCommandExecutor, AgentJobFailedError
from app.agent_moonraker import agent_preflight_payload, operation_payload
from app.agent_pairing import EXPECTED_AGENT_VERSION, AgentPairingRepository, printer_for_user
from app.auth import AuthRepository, CurrentUser
from app.database import connect_database
from app.gcode_files import (
    GcodeFileActionRequest,
    GcodeFileActionResponse,
    GcodeFileDetailResponse,
    GcodeFileHistoryEntry,
    build_gcode_file_action_response,
    build_gcode_file_detail_response,
    build_gcode_files_response,
    build_gcode_files_unavailable_response,
    gcode_file_action_is_mutable,
    gcode_file_action_payload,
    gcode_file_action_requires_step_up,
    gcode_file_confirmation_phrase,
    require_valid_gcode_file_path,
    sanitize_gcode_file_action_result,
)
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
GCODE_FILES_TIMEOUT_SECONDS = 35.0
GCODE_FILE_ACTION_TIMEOUT_SECONDS = 45.0


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
        printer_info, server_info, system_info, proc_stats, objects, history_totals, file_metadata, gcode_files = operation_payload(job.result)
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
        gcode_files=gcode_files,
    )
    operation["temperature_history"] = build_temperature_history(recent_snapshots)
    return {
        "printer_id": printer.id,
        "moonraker_url": "agent",
        "agent": _agent_operation_status(settings, printer.id),
        **operation,
    }


@router.get("/api/printers/{printer_id}/gcode-files")
async def list_printer_gcode_files(
    printer_id: int,
    refresh: bool = False,
    limit: int = Query(default=300, ge=1, le=500),
    current: CurrentUser = Depends(require_current_user),
) -> dict[str, Any]:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    agent_status = _agent_operation_status(settings, printer.id)
    if not agent_status["ready"]:
        response = build_gcode_files_unavailable_response(
            printer.id,
            agent_status["diagnostic"] or f"agente {EXPECTED_AGENT_VERSION} ou superior é necessário para listar G-code",
            agent=agent_status,
            data_state="unsupported",
        )
        return response.model_dump()
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_files_list",
            payload={"refresh": refresh, "limit": limit, "include_metadata": True, "include_thumbnails": True},
            timeout_seconds=max(settings.request_timeout_seconds, GCODE_FILES_TIMEOUT_SECONDS),
        )
    except AgentJobFailedError as exc:
        response = build_gcode_files_unavailable_response(
            printer.id,
            _remote_gcode_failure_detail(exc.job.result or {}) or exc.detail,
            agent=agent_status,
            data_state="error",
        )
        return response.model_dump()
    except HTTPException as exc:
        response = build_gcode_files_unavailable_response(
            printer.id,
            _http_exception_detail(exc),
            agent=agent_status,
            data_state="offline" if exc.status_code in {409, 504} else "error",
        )
        return response.model_dump()

    response = build_gcode_files_response(printer.id, job.result, agent=agent_status)
    return response.model_dump()


@router.get("/api/printers/{printer_id}/gcode-files/detail", response_model=GcodeFileDetailResponse)
async def get_printer_gcode_file_detail(
    printer_id: int,
    filename: str = Query(min_length=1, max_length=300),
    current: CurrentUser = Depends(require_current_user),
) -> GcodeFileDetailResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_filename = _require_gcode_filename(filename)
    files_response = await _load_gcode_files_for_action(settings, printer, refresh=False)
    file = next((item for item in files_response.files if item.path == clean_filename or item.filename == clean_filename), None)
    if file is None:
        raise HTTPException(status_code=404, detail="arquivo G-code não encontrado")
    current_print = await _gcode_file_current_print_context(settings, printer)
    history = _gcode_file_action_history(settings.database_path, printer.id, clean_filename)
    return build_gcode_file_detail_response(
        printer.id,
        file,
        current_print=current_print,
        history=history,
        agent=files_response.agent,
        data_state=files_response.data_state,
    )


@router.post("/api/printers/{printer_id}/gcode-files/actions", response_model=GcodeFileActionResponse)
async def execute_printer_gcode_file_action(
    printer_id: int,
    payload: GcodeFileActionRequest,
    authorization: str | None = Header(default=None),
    current: CurrentUser = Depends(require_current_user),
) -> GcodeFileActionResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_filename = _require_gcode_filename(payload.filename)
    payload.filename = clean_filename
    if not gcode_file_action_is_mutable(payload.action):
        return build_gcode_file_action_response(
            printer.id,
            payload,
            status="ready",
            summary="Ação somente leitura pronta no navegador.",
        )
    target_filename = _target_filename_for_action(payload)
    if target_filename is not None:
        payload.target_filename = target_filename
    expected_confirmation = gcode_file_confirmation_phrase(payload.action, clean_filename, payload.target_filename or "")
    if payload.confirmation_phrase.strip() != expected_confirmation:
        return build_gcode_file_action_response(
            printer.id,
            payload,
            status="blocked",
            summary="Confirmação textual obrigatória.",
            blockers=[f"Digite exatamente: {expected_confirmation}"],
        )
    if gcode_file_action_requires_step_up(payload.action):
        _require_step_up_when_authenticated(settings, authorization, payload.step_up_token, payload.action)
    files_response = await _load_gcode_files_for_action(settings, printer, refresh=False)
    file = next((item for item in files_response.files if item.path == clean_filename or item.filename == clean_filename), None)
    if file is None:
        raise HTTPException(status_code=404, detail="arquivo G-code não encontrado")
    current_print = await _gcode_file_current_print_context(settings, printer)
    action_state = next(
        (item for item in build_gcode_file_detail_response(printer.id, file, current_print=current_print, agent=files_response.agent).actions if item.action == payload.action),
        None,
    )
    if action_state is None or not action_state.enabled:
        return build_gcode_file_action_response(
            printer.id,
            payload,
            status="blocked",
            summary="Ação bloqueada pelas precondições atuais.",
            blockers=action_state.blockers if action_state else ["Ação não suportada."],
        )
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_file_action",
            payload=gcode_file_action_payload(payload),
            timeout_seconds=max(settings.request_timeout_seconds, GCODE_FILE_ACTION_TIMEOUT_SECONDS),
        )
        result = job.result or {}
        remote_status = str(result.get("status") or "")
        status = "executed" if remote_status in {"executed", "printed", "renamed", "moved", "duplicated", "deleted"} else "failed"
        summary = _gcode_file_action_summary(payload.action, status, result)
        blockers = [] if status == "executed" else [_remote_gcode_failure_detail(result)]
        return build_gcode_file_action_response(
            printer.id,
            payload,
            status=status,
            summary=summary,
            blockers=blockers,
            job_id=job.id,
            result=result,
        )
    except AgentJobFailedError as exc:
        result = sanitize_gcode_file_action_result(exc.job.result or {"detail": exc.detail})
        return build_gcode_file_action_response(
            printer.id,
            payload,
            status="failed",
            summary="Agente não concluiu a ação.",
            blockers=[_remote_gcode_failure_detail(result) or exc.detail],
            job_id=exc.job.id,
            result=result,
        )
    except HTTPException as exc:
        return build_gcode_file_action_response(
            printer.id,
            payload,
            status="failed",
            summary="Ação não confirmada pelo agente.",
            blockers=[_http_exception_detail(exc)],
        )


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


async def _load_gcode_files_for_action(settings, printer, *, refresh: bool):
    agent_status = _agent_operation_status(settings, printer.id)
    if not agent_status["ready"]:
        raise HTTPException(status_code=409, detail=agent_status["diagnostic"] or f"agente {EXPECTED_AGENT_VERSION} ou superior é necessário")
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_files_list",
            payload={"refresh": refresh, "limit": 500, "include_metadata": True, "include_thumbnails": True},
            timeout_seconds=max(settings.request_timeout_seconds, GCODE_FILES_TIMEOUT_SECONDS),
        )
    except AgentJobFailedError as exc:
        raise HTTPException(status_code=502, detail=_remote_gcode_failure_detail(exc.job.result or {}) or exc.detail) from exc
    return build_gcode_files_response(printer.id, job.result, agent=agent_status)


async def _gcode_file_current_print_context(settings, printer) -> dict[str, Any]:
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_operation_status",
            timeout_seconds=_operation_status_timeout(settings),
        )
    except (AgentJobFailedError, HTTPException) as exc:
        return {
            "connected": False,
            "printing": False,
            "print_state": "",
            "filename": "",
            "error": exc.detail if isinstance(exc, HTTPException) else str(exc),
        }
    printer_info, server_info, _system_info, _proc_stats, objects, _history, _metadata, _files = operation_payload(job.result)
    status = objects.get("status") if isinstance(objects.get("status"), dict) else {}
    print_stats = status.get("print_stats") if isinstance(status.get("print_stats"), dict) else {}
    print_state = str(print_stats.get("state") or "").strip()
    filename = str(print_stats.get("filename") or "").strip()
    connected = bool(server_info.get("klippy_connected", True)) and not any(str(key).endswith("_error") for key in (job.result or {}))
    return {
        "connected": connected,
        "printing": print_state not in {"", "standby", "complete", "cancelled", "error"},
        "print_state": print_state,
        "filename": filename,
        "klipper_state": str(printer_info.get("state") or ""),
        "klippy_state": str(server_info.get("klippy_state") or ""),
    }


def _gcode_file_action_history(database_path, printer_id: int, filename: str, limit: int = 12) -> list[GcodeFileHistoryEntry]:
    with connect_database(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, job_type, payload_json, status, result_json, error_message, created_at, finished_at
            FROM agent_jobs
            WHERE printer_id = ?
              AND job_type IN ('remote_gcode_file_action', 'remote_gcode_cache', 'remote_gcode_upload', 'remote_gcode_delete')
            ORDER BY created_at DESC, id DESC
            LIMIT 80
            """,
            (printer_id,),
        ).fetchall()
    entries: list[GcodeFileHistoryEntry] = []
    for row in rows:
        payload = _json_dict(row["payload_json"])
        result = _json_dict(row["result_json"])
        action = str(payload.get("action") or result.get("action") or _history_action_from_job(str(row["job_type"])))
        source = str(payload.get("filename") or payload.get("remote_filename") or result.get("filename") or result.get("remote_filename") or "")
        target = str(payload.get("target_filename") or result.get("target_filename") or "")
        if filename and filename not in {source, target}:
            continue
        entries.append(
            GcodeFileHistoryEntry(
                id=int(row["id"]),
                created_at=str(row["created_at"]),
                finished_at=row["finished_at"],
                job_type=str(row["job_type"]),
                action=action,
                status=str(row["status"]),
                summary=str(result.get("detail") or row["error_message"] or result.get("status") or row["status"]),
                filename=source,
                target_filename=target,
            )
        )
        if len(entries) >= limit:
            break
    return entries


def _history_action_from_job(job_type: str) -> str:
    return {
        "remote_gcode_cache": "download",
        "remote_gcode_upload": "upload",
        "remote_gcode_delete": "delete",
    }.get(job_type, "")


def _json_dict(value) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _require_gcode_filename(value: str) -> str:
    try:
        return require_valid_gcode_file_path(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _target_filename_for_action(payload: GcodeFileActionRequest) -> str | None:
    if payload.action not in {"rename", "move", "duplicate"}:
        return None
    if not payload.target_filename:
        raise HTTPException(status_code=400, detail="ação exige arquivo de destino")
    return _require_gcode_filename(payload.target_filename)


def _gcode_file_action_summary(action: str, status: str, result: dict[str, Any]) -> str:
    if status != "executed":
        return "Ação não concluída."
    return {
        "print": "Impressão iniciada pelo Moonraker.",
        "rename": "Arquivo renomeado no Moonraker.",
        "move": "Arquivo movido no Moonraker.",
        "duplicate": "Arquivo duplicado no Moonraker.",
        "delete": "Arquivo excluído no Moonraker.",
    }.get(action, str(result.get("detail") or "Ação concluída."))


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
    _printer_info, _server_info, _system_info, _proc_stats, objects, _history, _file_metadata, _gcode_files = operation_payload(status_job.result)
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
