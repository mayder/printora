from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.modules.operations.contracts import AgentJobCreateRequest, AgentJobRecord
from app.modules.operations.ports import AgentJobRepositoryPort, PrinterIdentity


@dataclass(frozen=True)
class AgentUnavailableError(Exception):
    message: str = "nenhum agente online para esta impressora"


@dataclass(frozen=True)
class AgentJobRejectedError(Exception):
    message: str


@dataclass(frozen=True)
class AgentJobNotFoundError(Exception):
    message: str = "job do agente não encontrado"


@dataclass(frozen=True)
class AgentJobFailedError(Exception):
    job: AgentJobRecord


@dataclass(frozen=True)
class AgentJobTimeoutError(Exception):
    job_status: str
    websocket_delivered: bool


COALESCIBLE_AGENT_JOB_TYPES = frozenset(
    {
        "remote_calibration_capabilities",
        "remote_firmware_inventory",
        "remote_gcode_files_list",
        "remote_moonraker_status",
        "remote_operation_status",
        "remote_update_status",
    }
)


@dataclass
class AgentJobService:
    repository: AgentJobRepositoryPort

    async def run(
        self,
        printer: PrinterIdentity,
        *,
        job_type: str,
        payload: dict[str, Any] | None = None,
        timeout_seconds: float = 12.0,
        require_online: bool = True,
    ) -> AgentJobRecord:
        agent = self.repository.latest_active_agent(printer.id)
        if require_online and agent is None:
            raise AgentUnavailableError()
        expires_at = _format_datetime(
            datetime.now(timezone.utc) + timedelta(seconds=max(5, int(timeout_seconds) + 5))
        )
        try:
            request = AgentJobCreateRequest(
                job_type=job_type,
                agent_id=agent.id if agent is not None else None,
                correlation_id=f"{job_type}_{uuid4().hex}",
                payload=payload or {},
                expires_at=expires_at,
            )
            if job_type in COALESCIBLE_AGENT_JOB_TYPES:
                job = self.repository.create_or_reuse_job(printer, request)
            else:
                job = self.repository.create_job(printer, request)
        except ValueError as exc:
            raise AgentJobRejectedError(str(exc)) from exc
        return await self._wait(
            printer.id,
            job.id,
            timeout_seconds,
            websocket_delivered=False,
        )

    async def _wait(
        self,
        printer_id: int,
        job_id: int,
        timeout_seconds: float,
        *,
        websocket_delivered: bool,
    ) -> AgentJobRecord:
        deadline = asyncio.get_running_loop().time() + max(1.0, timeout_seconds)
        interval = 0.15
        while True:
            job = self.repository.get_job(printer_id, job_id)
            if job is None:
                raise AgentJobNotFoundError()
            if job.status == "succeeded":
                return job
            if job.status in {"failed", "canceled"}:
                raise AgentJobFailedError(job)
            if asyncio.get_running_loop().time() >= deadline:
                raise AgentJobTimeoutError(job.status, websocket_delivered)
            await asyncio.sleep(interval)
            interval = min(0.5, interval * 1.5)


def timeout_detail(error: AgentJobTimeoutError) -> str:
    if error.job_status == "pending" and not error.websocket_delivered:
        return (
            "timeout aguardando resposta do agente; job ficou enfileirado para "
            "polling porque o WebSocket não confirmou entrega"
        )
    if error.job_status == "pending":
        return "timeout aguardando o agente iniciar o job"
    if error.job_status == "in_progress":
        return "timeout aguardando o agente concluir o job"
    return "timeout aguardando resposta do agente"


def _format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")
