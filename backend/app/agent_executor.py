from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.agent_channel import agent_ws_manager
from app.agent_pairing import AgentJobCreateRequest, AgentJobRecord, AgentPairingRepository
from app.auth import format_dt, utc_now
from app.printers import PrinterRecord


DEFAULT_AGENT_TIMEOUT_SECONDS = 12.0


class AgentCommandExecutor:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.repository = AgentPairingRepository(database_path)

    async def run(
        self,
        printer: PrinterRecord,
        *,
        job_type: str,
        payload: dict[str, Any] | None = None,
        timeout_seconds: float = DEFAULT_AGENT_TIMEOUT_SECONDS,
        require_online: bool = True,
    ) -> AgentJobRecord:
        agent = self.repository.latest_active_agent(printer.id)
        if require_online and agent is None:
            raise HTTPException(status_code=409, detail="nenhum agente online para esta impressora")
        expires_at = format_dt(utc_now() + timedelta(seconds=max(5, int(timeout_seconds) + 5)))
        try:
            job = self.repository.create_job(
                printer,
                AgentJobCreateRequest(
                    job_type=job_type,
                    agent_id=agent.id if agent is not None else None,
                    correlation_id=f"{job_type}_{uuid4().hex}",
                    payload=payload or {},
                    expires_at=expires_at,
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        websocket_delivered = await agent_ws_manager.push_job(job)
        return await self._wait(printer.id, job.id, timeout_seconds, websocket_delivered=websocket_delivered)

    async def _wait(self, printer_id: int, job_id: int, timeout_seconds: float, *, websocket_delivered: bool = True) -> AgentJobRecord:
        deadline = asyncio.get_running_loop().time() + max(1.0, timeout_seconds)
        interval = 0.15
        while True:
            job = self.repository.get_job(printer_id, job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="job do agente não encontrado")
            if job.status == "succeeded":
                return job
            if job.status in {"failed", "canceled"}:
                raise AgentJobFailedError(job)
            if asyncio.get_running_loop().time() >= deadline:
                raise HTTPException(status_code=504, detail=_timeout_detail(job.status, websocket_delivered))
            await asyncio.sleep(interval)
            interval = min(0.5, interval * 1.5)


def unwrap_moonraker_result(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get("result"), dict):
        return value["result"]
    return value if isinstance(value, dict) else {}


class AgentJobFailedError(HTTPException):
    def __init__(self, job: AgentJobRecord) -> None:
        self.job = job
        super().__init__(status_code=502, detail=job.error_message or "job do agente falhou")


def _timeout_detail(job_status: str, websocket_delivered: bool) -> str:
    if job_status == "pending" and not websocket_delivered:
        return "timeout aguardando resposta do agente; job ficou enfileirado para polling porque o WebSocket não confirmou entrega"
    if job_status == "pending":
        return "timeout aguardando o agente iniciar o job"
    if job_status == "in_progress":
        return "timeout aguardando o agente concluir o job"
    return "timeout aguardando resposta do agente"


def unwrap_moonraker_list(value: Any, key: str) -> list[str]:
    result = unwrap_moonraker_result(value)
    items = result.get(key)
    return [str(item) for item in items] if isinstance(items, list) else []
