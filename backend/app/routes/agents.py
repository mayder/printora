from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from app.agent_pairing import (
    AgentPairingConflictError,
    AgentExchangeRequest,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentInstallPlanResponse,
    AgentInstallStatusResponse,
    AgentJobCreateRequest,
    AgentJobErrorRequest,
    AgentJobRecord,
    AgentJobResultRequest,
    AgentJobResponse,
    AgentPairingOverview,
    AgentPairingRepository,
    AgentProtocolMessage,
    AgentSnapshotRequest,
    AgentCredentialExchangeResponse,
    AgentRecord,
    AGENT_PROTOCOL_VERSION,
    PairingTokenCreateRequest,
    PairingTokenRecord,
    PairingTokenResponse,
    printer_for_user,
)
from app.agent_channel import agent_ws_manager, job_message, protocol_message
from app.agent_parity import (
    AgentParityRepository,
    RemoteParityOverview,
    RemoteParityRunRequest,
)
from app.agent_support import (
    AgentSupportBundle,
    AgentSupportOverview,
    AgentSupportRepository,
    AgentUpdateRequestResponse,
)
from app.agent_updates import (
    AgentUpdateHistoryRecord,
    AgentUpdateManifest,
    AgentUpdateReportRequest,
    AgentUpdateRepository,
    load_agent_update_manifest,
)
from app.auth import CurrentUser
from app.config import Settings, get_settings
from app.gcode_cache import GcodeCacheEntry, store_gcode_cache_upload
from app.routes.auth import require_current_user
from app.remote_operations import (
    RemoteOperationCancelResponse,
    RemoteOperationExecuteRequest,
    RemoteOperationOverview,
    RemoteOperationPreflightRequest,
    RemoteOperationRepository,
)


router = APIRouter()
INSTALLER_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "install_agent_linux.sh"
AGENT_RELEASE_DIR = Path(__file__).resolve().parents[1] / "data" / "agent_releases"
AGENT_RELEASE_FILES = {
    "linux-arm64": "printora-agent-linux-arm64",
}


def get_pairing_repository(settings: Settings = Depends(get_settings)) -> AgentPairingRepository:
    return AgentPairingRepository(settings.database_path)


def get_update_repository(settings: Settings = Depends(get_settings)) -> AgentUpdateRepository:
    return AgentUpdateRepository(settings.database_path)


def get_parity_repository(settings: Settings = Depends(get_settings)) -> AgentParityRepository:
    return AgentParityRepository(settings.database_path)


def get_support_repository(settings: Settings = Depends(get_settings)) -> AgentSupportRepository:
    return AgentSupportRepository(settings.database_path)


def get_remote_operation_repository(settings: Settings = Depends(get_settings)) -> RemoteOperationRepository:
    return RemoteOperationRepository(settings.database_path)


def require_agent(
    authorization: str | None = Header(default=None),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentRecord:
    if not authorization:
        raise HTTPException(status_code=401, detail="credencial do agente obrigatória")
    scheme, _, credential = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credential:
        raise HTTPException(status_code=401, detail="credencial do agente inválida")
    agent = repository.authenticate_agent(credential.strip())
    if agent is None:
        raise HTTPException(status_code=401, detail="agente revogado ou credencial inválida")
    return agent


@router.get("/api/printers/{printer_id}/pairing", response_model=AgentPairingOverview)
async def printer_pairing_overview(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentPairingOverview:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.overview(printer.id)


@router.post("/api/printers/{printer_id}/pairing/tokens", response_model=PairingTokenResponse)
async def create_printer_pairing_token(
    printer_id: int,
    payload: PairingTokenCreateRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> PairingTokenResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.create_pairing_token(current.user, printer, payload)


@router.post("/api/printers/{printer_id}/pairing/tokens/{token_id}/revoke", response_model=PairingTokenRecord)
async def revoke_printer_pairing_token(
    printer_id: int,
    token_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> PairingTokenRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    token = repository.revoke_pairing_token(printer.id, token_id)
    if token is None:
        raise HTTPException(status_code=404, detail="token not found")
    return token


@router.delete("/api/printers/{printer_id}/pairing/tokens/{token_id}", response_model=PairingTokenRecord)
async def remove_printer_pairing_token(
    printer_id: int,
    token_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> PairingTokenRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        token = repository.remove_pairing_token(printer.id, token_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if token is None:
        raise HTTPException(status_code=404, detail="token not found")
    return token


@router.post("/api/printers/{printer_id}/agents/{agent_id}/rotate", response_model=AgentCredentialExchangeResponse)
async def rotate_printer_agent_credential(
    printer_id: int,
    agent_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentCredentialExchangeResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    rotated = repository.rotate_agent_credential(printer.id, agent_id)
    if rotated is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return rotated


@router.post("/api/printers/{printer_id}/agents/{agent_id}/revoke", response_model=AgentRecord)
async def revoke_printer_agent(
    printer_id: int,
    agent_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    agent = repository.revoke_agent(printer.id, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return agent


@router.delete("/api/printers/{printer_id}/agents/{agent_id}", response_model=AgentRecord)
async def remove_printer_agent(
    printer_id: int,
    agent_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    agent = repository.remove_agent(printer.id, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return agent


@router.post("/api/printers/{printer_id}/agent/install-plan", response_model=AgentInstallPlanResponse)
async def create_agent_install_plan(
    printer_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentInstallPlanResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.create_install_plan(
        current.user,
        printer,
        str(request.base_url).rstrip("/"),
        _linux_arm64_release_url(str(request.base_url)),
    )


@router.get("/api/printers/{printer_id}/agent/install-status", response_model=AgentInstallStatusResponse)
async def agent_install_status(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentInstallStatusResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.install_status(printer.id)


@router.get("/api/agent/install/linux.sh")
async def agent_linux_installer() -> FileResponse:
    return FileResponse(INSTALLER_SCRIPT_PATH, media_type="text/x-shellscript", filename="install-printora-agent.sh")


@router.get("/api/agent/update/manifest", response_model=AgentUpdateManifest)
async def agent_update_manifest(request: Request) -> AgentUpdateManifest:
    return load_agent_update_manifest(str(request.base_url))


@router.get("/api/agent/update/releases/{platform}")
async def agent_update_release(platform: str) -> FileResponse:
    filename = AGENT_RELEASE_FILES.get(platform)
    if filename is None:
        raise HTTPException(status_code=404, detail="agent release not found")
    path = AGENT_RELEASE_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="agent release file not published")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)


def _linux_arm64_release_url(public_base_url: str | None = None) -> str | None:
    manifest = load_agent_update_manifest(public_base_url)
    for release in manifest.releases:
        if release.platform == "linux/arm64" and release.url:
            return release.url
    return None


@router.post("/api/agent/update/reports", response_model=AgentUpdateHistoryRecord)
async def agent_update_report(
    payload: AgentUpdateReportRequest,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentUpdateRepository = Depends(get_update_repository),
) -> AgentUpdateHistoryRecord:
    return repository.report(agent, payload)


@router.get("/api/printers/{printer_id}/agent/update-history", response_model=list[AgentUpdateHistoryRecord])
async def printer_agent_update_history(
    printer_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    current: CurrentUser = Depends(require_current_user),
    repository: AgentUpdateRepository = Depends(get_update_repository),
) -> list[AgentUpdateHistoryRecord]:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.history(printer.id, limit)


@router.get("/api/printers/{printer_id}/remote/parity", response_model=RemoteParityOverview)
async def printer_remote_parity(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentParityRepository = Depends(get_parity_repository),
) -> RemoteParityOverview:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.overview(printer)


@router.post("/api/printers/{printer_id}/remote/parity/jobs", response_model=AgentJobRecord)
async def create_printer_remote_parity_job(
    printer_id: int,
    payload: RemoteParityRunRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentParityRepository = Depends(get_parity_repository),
) -> AgentJobRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.create_remote_job(printer, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/printers/{printer_id}/agent/support", response_model=AgentSupportOverview)
async def printer_agent_support(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentSupportRepository = Depends(get_support_repository),
) -> AgentSupportOverview:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.overview(printer)


@router.post("/api/printers/{printer_id}/agent/support/doctor", response_model=AgentJobRecord)
async def create_printer_agent_doctor_job(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentSupportRepository = Depends(get_support_repository),
) -> AgentJobRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.create_doctor_job(printer)


@router.post("/api/printers/{printer_id}/agents/{agent_id}/update-check", response_model=AgentUpdateRequestResponse)
async def create_printer_agent_update_job(
    printer_id: int,
    agent_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentSupportRepository = Depends(get_support_repository),
) -> AgentUpdateRequestResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        response = repository.request_agent_update(printer, agent_id, _public_base_url(request))
        delivered = await agent_ws_manager.push_job(response.job) if response.job else False
        detail = (
            "Update enviado ao agente online pelo canal remoto. O agente baixa, valida SHA-256 e reinicia só o serviço do agente."
            if delivered
            else "Update enfileirado. O agente buscará a ação no próximo heartbeat/polling, sem SSH."
        )
        return response.model_copy(update={"websocket_delivered": delivered, "detail": detail})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/printers/{printer_id}/agent/support/bundle", response_model=AgentSupportBundle)
async def printer_agent_support_bundle(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentSupportRepository = Depends(get_support_repository),
) -> AgentSupportBundle:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.support_bundle(printer)


@router.get("/api/printers/{printer_id}/remote/operations", response_model=RemoteOperationOverview)
async def printer_remote_operations(
    printer_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: RemoteOperationRepository = Depends(get_remote_operation_repository),
) -> RemoteOperationOverview:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.overview(printer)


@router.post("/api/printers/{printer_id}/remote/operations/preflight", response_model=AgentJobRecord)
async def create_printer_remote_operation_preflight(
    printer_id: int,
    payload: RemoteOperationPreflightRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: RemoteOperationRepository = Depends(get_remote_operation_repository),
) -> AgentJobRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.create_preflight(printer, current.user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/printers/{printer_id}/remote/operations/execute", response_model=AgentJobRecord)
async def create_printer_remote_operation_execution(
    printer_id: int,
    payload: RemoteOperationExecuteRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: RemoteOperationRepository = Depends(get_remote_operation_repository),
) -> AgentJobRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.create_execution(printer, current.user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/printers/{printer_id}/remote/operations/jobs/{job_id}/cancel", response_model=RemoteOperationCancelResponse)
async def cancel_printer_remote_operation_job(
    printer_id: int,
    job_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: RemoteOperationRepository = Depends(get_remote_operation_repository),
) -> RemoteOperationCancelResponse:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.cancel_job(printer, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/agent/pairing/exchange", response_model=AgentCredentialExchangeResponse)
async def exchange_agent_pairing_token(
    payload: AgentExchangeRequest,
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentCredentialExchangeResponse:
    try:
        return repository.exchange_token(payload)
    except AgentPairingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/agent/heartbeat", response_model=AgentHeartbeatResponse)
async def agent_heartbeat(
    payload: AgentHeartbeatRequest,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentHeartbeatResponse:
    return repository.heartbeat(agent, payload)


@router.post("/api/agent/snapshots", response_model=AgentHeartbeatResponse)
async def agent_snapshot(
    payload: AgentSnapshotRequest,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentHeartbeatResponse:
    try:
        return repository.store_snapshot(agent, payload)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@router.put("/api/agent/gcode-cache/{cache_key}", response_model=GcodeCacheEntry)
async def upload_agent_gcode_cache(
    cache_key: str,
    request: Request,
    filename: str | None = Header(default=None, alias="X-Printora-Filename"),
    agent: AgentRecord = Depends(require_agent),
    settings: Settings = Depends(get_settings),
) -> GcodeCacheEntry:
    return await store_gcode_cache_upload(settings, agent, cache_key, filename or "", request)


@router.get("/api/agent/jobs/next", response_model=AgentJobResponse)
async def agent_next_jobs(
    limit: int = Query(default=5, ge=1, le=20),
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentJobResponse:
    return repository.next_jobs(agent, limit)


@router.post("/api/printers/{printer_id}/agent/jobs", response_model=AgentJobRecord)
async def create_printer_agent_job(
    printer_id: int,
    payload: AgentJobCreateRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentJobRecord:
    settings = get_settings()
    printer = printer_for_user(settings.database_path, current.user, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        job = repository.create_job(printer, payload)
        await agent_ws_manager.push_job(job)
        return job
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/agent/jobs/{job_id}/ack", response_model=AgentJobRecord)
async def agent_ack_job(
    job_id: int,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentJobRecord:
    job = repository.ack_job(agent, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.post("/api/agent/jobs/{job_id}/nack", response_model=AgentJobRecord)
async def agent_nack_job(
    job_id: int,
    payload: AgentJobErrorRequest,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentJobRecord:
    job = repository.nack_job(agent, job_id, payload.error_message)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.post("/api/agent/jobs/{job_id}/result", response_model=AgentJobRecord)
async def agent_job_result(
    job_id: int,
    payload: AgentJobResultRequest,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentJobRecord:
    try:
        job = repository.finish_job(agent, job_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.post("/api/agent/jobs/{job_id}/error", response_model=AgentJobRecord)
async def agent_job_error(
    job_id: int,
    payload: AgentJobErrorRequest,
    agent: AgentRecord = Depends(require_agent),
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentJobRecord:
    try:
        job = repository.fail_job(agent, job_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.websocket("/api/agent/ws")
async def agent_websocket(websocket: WebSocket) -> None:
    repository = get_pairing_repository(get_settings())
    credential = _websocket_credential(websocket)
    agent = repository.authenticate_agent(credential) if credential else None
    if agent is None:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    await agent_ws_manager.register(agent, websocket)
    try:
        await agent_ws_manager.send(agent.id, _message("hello", {"protocol_version": AGENT_PROTOCOL_VERSION}))
        while True:
            raw = await websocket.receive_json()
            message = AgentProtocolMessage.model_validate(raw)
            if message.protocol_version != AGENT_PROTOCOL_VERSION:
                await agent_ws_manager.send(agent.id, _message("error", {"reason": "protocol_version_incompatible"}, message.correlation_id))
                await websocket.close(code=1003)
                return
            response = _handle_agent_message(repository, agent, message)
            await agent_ws_manager.send(agent.id, response)
            if message.message_type in {"hello", "heartbeat", "backpressure"}:
                for job in repository.next_jobs(agent, 10).jobs:
                    await agent_ws_manager.send(agent.id, _job_message(job))
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await agent_ws_manager.send(agent.id, _message("error", {"reason": str(exc)[:160]}))
    finally:
        await agent_ws_manager.unregister(agent.id, websocket)


def _websocket_credential(websocket: WebSocket) -> str | None:
    authorization = websocket.headers.get("authorization")
    if authorization:
        scheme, _, credential = authorization.partition(" ")
        if scheme.lower() == "bearer" and credential:
            return credential.strip()
    return None


def _public_base_url(request: Request) -> str:
    host = request.headers.get("host")
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    if host:
        return f"{proto}://{host}"
    return str(request.base_url).rstrip("/")


def _handle_agent_message(repository: AgentPairingRepository, agent: AgentRecord, message: AgentProtocolMessage) -> dict:
    if message.message_type == "hello":
        payload = message.payload
        repository.heartbeat(
            agent,
            AgentHeartbeatRequest(
                agent_version=payload.get("agent_version"),
                platform=payload.get("platform"),
                capabilities=payload.get("capabilities") or {},
            ),
        )
        return _message("ack", {"message_type": "hello"}, message.correlation_id)
    if message.message_type == "heartbeat":
        repository.heartbeat(agent, AgentHeartbeatRequest.model_validate(message.payload))
        return _message("ack", {"message_type": "heartbeat"}, message.correlation_id)
    if message.message_type == "snapshot":
        repository.store_snapshot(agent, AgentSnapshotRequest(payload=message.payload.get("payload") or message.payload))
        return _message("ack", {"message_type": "snapshot"}, message.correlation_id)
    if message.message_type == "ack":
        job = repository.ack_job(agent, int(message.payload["job_id"]))
        if job is None:
            return _message("error", {"reason": "job not found"}, message.correlation_id)
        return _message("ack", {"job_id": job.id}, message.correlation_id)
    if message.message_type == "nack":
        job = repository.nack_job(agent, int(message.payload["job_id"]), str(message.payload.get("reason") or "nack"))
        if job is None:
            return _message("error", {"reason": "job not found"}, message.correlation_id)
        return _message("ack", {"job_id": job.id}, message.correlation_id)
    if message.message_type == "result":
        request = AgentJobResultRequest(correlation_id=str(message.payload["correlation_id"]), result=message.payload.get("result") or {})
        job = repository.finish_job(agent, int(message.payload["job_id"]), request)
        if job is None:
            return _message("error", {"reason": "job not found"}, message.correlation_id)
        return _message("ack", {"job_id": job.id, "status": job.status}, message.correlation_id)
    if message.message_type == "error":
        request = AgentJobErrorRequest(
            correlation_id=str(message.payload["correlation_id"]),
            error_message=str(message.payload.get("error_message") or "agent error"),
            result=message.payload.get("result") or {},
        )
        job = repository.fail_job(agent, int(message.payload["job_id"]), request)
        if job is None:
            return _message("error", {"reason": "job not found"}, message.correlation_id)
        return _message("ack", {"job_id": job.id, "status": job.status}, message.correlation_id)
    if message.message_type == "backpressure":
        return _message("ack", {"message_type": "backpressure"}, message.correlation_id)
    return _message("error", {"reason": "message_type inválido"}, message.correlation_id)


def _message(message_type: str, payload: dict, correlation_id: str | None = None) -> dict:
    return protocol_message(message_type, payload, correlation_id)


def _job_message(job: AgentJobRecord) -> dict:
    return job_message(job)
