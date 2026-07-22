from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from app.modules.operations.application import (
    AgentJobFailedError,
    AgentJobService,
    AgentUnavailableError,
)
from app.modules.operations.contracts import AgentJobCreateRequest, AgentJobRecord, AgentRecord


@dataclass(frozen=True)
class Printer:
    id: int = 7


class Repository:
    def __init__(self, status: str = "succeeded", online: bool = True) -> None:
        self.status = status
        self.online = online
        self.request: AgentJobCreateRequest | None = None

    def latest_active_agent(self, printer_id: int) -> AgentRecord | None:
        if not self.online:
            return None
        return AgentRecord(
            id=3,
            printer_id=printer_id,
            stable_id="printer-7",
            credential_prefix="ptr_agent_test",
            agent_version="1.0.0",
            platform="linux",
            capabilities={},
            status="active",
            paired_at="2026-07-22 00:00:00",
            last_seen_at="2026-07-22 00:00:00",
            revoked_at=None,
            rotated_at=None,
        )

    def create_job(self, printer: Printer, request: AgentJobCreateRequest) -> AgentJobRecord:
        self.request = request
        return self._job(printer.id, 11, "pending")

    def get_job(self, printer_id: int, job_id: int) -> AgentJobRecord:
        return self._job(printer_id, job_id, self.status)

    def _job(self, printer_id: int, job_id: int, status: str) -> AgentJobRecord:
        return AgentJobRecord(
            id=job_id,
            printer_id=printer_id,
            agent_id=3,
            correlation_id="status_test",
            job_type="status",
            payload={},
            status=status,
            attempts=1,
            result={"ok": True} if status == "succeeded" else None,
            error_message="falha controlada" if status == "failed" else None,
            created_at="2026-07-22 00:00:00",
            updated_at="2026-07-22 00:00:01",
        )


def test_agent_job_service_dispatches_without_http_dependency() -> None:
    repository = Repository()

    job = asyncio.run(AgentJobService(repository).run(Printer(), job_type="status"))

    assert job.status == "succeeded"
    assert repository.request is not None
    assert repository.request.agent_id == 3


def test_agent_job_service_rejects_required_offline_agent() -> None:
    service = AgentJobService(Repository(online=False))

    with pytest.raises(AgentUnavailableError):
        asyncio.run(service.run(Printer(), job_type="status"))


def test_agent_job_service_reports_failed_job_without_fastapi_error() -> None:
    service = AgentJobService(Repository(status="failed"))

    with pytest.raises(AgentJobFailedError) as exc_info:
        asyncio.run(service.run(Printer(), job_type="status"))

    assert exc_info.value.job.error_message == "falha controlada"
