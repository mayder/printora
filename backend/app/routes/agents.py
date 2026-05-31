from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from app.agent_pairing import (
    AgentExchangeRequest,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentJobResponse,
    AgentPairingOverview,
    AgentPairingRepository,
    AgentSnapshotRequest,
    AgentCredentialExchangeResponse,
    AgentRecord,
    PairingTokenCreateRequest,
    PairingTokenRecord,
    PairingTokenResponse,
    printer_for_user,
)
from app.auth import CurrentUser
from app.config import Settings, get_settings
from app.routes.auth import require_current_user


router = APIRouter()


def get_pairing_repository(settings: Settings = Depends(get_settings)) -> AgentPairingRepository:
    return AgentPairingRepository(settings.database_path)


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


@router.post("/api/agent/pairing/exchange", response_model=AgentCredentialExchangeResponse)
async def exchange_agent_pairing_token(
    payload: AgentExchangeRequest,
    repository: AgentPairingRepository = Depends(get_pairing_repository),
) -> AgentCredentialExchangeResponse:
    try:
        return repository.exchange_token(payload)
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
    return repository.store_snapshot(agent, payload)


@router.get("/api/agent/jobs/next", response_model=AgentJobResponse)
async def agent_next_jobs(agent: AgentRecord = Depends(require_agent)) -> AgentJobResponse:
    return AgentJobResponse(jobs=[])
