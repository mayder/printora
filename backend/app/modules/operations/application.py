from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Hashable
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
        "remote_gcode_cache",
        "remote_gcode_files_list",
        "remote_moonraker_status",
        "remote_operation_status",
        "remote_spoolman_inventory",
        "remote_update_status",
    }
)


class AgentJobWaitCoordinator:
    def __init__(self) -> None:
        self._tasks: dict[
            tuple[asyncio.AbstractEventLoop, Hashable, int, int, float],
            asyncio.Task[AgentJobRecord],
        ] = {}

    async def wait(
        self,
        *,
        repository_scope: Hashable,
        printer_id: int,
        job_id: int,
        timeout_seconds: float,
        poll: Callable[[], Awaitable[AgentJobRecord]],
    ) -> AgentJobRecord:
        loop = asyncio.get_running_loop()
        key = (loop, repository_scope, printer_id, job_id, timeout_seconds)
        task = self._tasks.get(key)
        if task is None:
            task = loop.create_task(poll())
            self._tasks[key] = task
            task.add_done_callback(lambda completed, task_key=key: self._discard(task_key, completed))
        return await asyncio.shield(task)

    def _discard(
        self,
        key: tuple[asyncio.AbstractEventLoop, Hashable, int, int, float],
        completed: asyncio.Task[AgentJobRecord],
    ) -> None:
        if self._tasks.get(key) is completed:
            self._tasks.pop(key, None)


_WAIT_COORDINATOR = AgentJobWaitCoordinator()


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
        agent = await asyncio.to_thread(self.repository.latest_active_agent, printer.id)
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
                job = await asyncio.to_thread(
                    self.repository.create_or_reuse_job,
                    printer,
                    request,
                )
            else:
                job = await asyncio.to_thread(
                    self.repository.create_job,
                    printer,
                    request,
                )
        except ValueError as exc:
            raise AgentJobRejectedError(str(exc)) from exc
        return await _WAIT_COORDINATOR.wait(
            repository_scope=_repository_scope(self.repository),
            printer_id=printer.id,
            job_id=job.id,
            timeout_seconds=timeout_seconds,
            poll=lambda: self._poll_job(
                printer.id,
                job.id,
                timeout_seconds,
                websocket_delivered=False,
            ),
        )

    async def _poll_job(
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
            job = await asyncio.to_thread(self.repository.get_job, printer_id, job_id)
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


def _repository_scope(repository: AgentJobRepositoryPort) -> Hashable:
    database_path = getattr(repository, "database_path", None)
    if isinstance(database_path, (Path, str)):
        return ("database", str(database_path))
    return ("repository", id(repository))


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
