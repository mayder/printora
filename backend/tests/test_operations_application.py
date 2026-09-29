from __future__ import annotations

import asyncio
import threading
import time
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
        self.create_calls = 0
        self.coalesced_create_calls = 0
        self.get_calls = 0

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
        self.create_calls += 1
        self.request = request
        return self._job(printer.id, 11, "pending")

    def create_or_reuse_job(self, printer: Printer, request: AgentJobCreateRequest) -> AgentJobRecord:
        self.coalesced_create_calls += 1
        self.request = request
        return self._job(printer.id, 11, "pending")

    def get_job(self, printer_id: int, job_id: int) -> AgentJobRecord:
        self.get_calls += 1
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
    assert repository.create_calls == 1
    assert repository.coalesced_create_calls == 0


def test_agent_job_service_coalesces_high_frequency_read_jobs() -> None:
    repository = Repository()

    job = asyncio.run(
        AgentJobService(repository).run(
            Printer(),
            job_type="remote_operation_status",
        )
    )

    assert job.status == "succeeded"
    assert repository.create_calls == 0
    assert repository.coalesced_create_calls == 1


def test_agent_job_service_coalesces_gcode_cache_reads() -> None:
    repository = Repository()

    job = asyncio.run(
        AgentJobService(repository).run(
            Printer(),
            job_type="remote_gcode_cache",
            payload={"filename": "跳舞_PLA_23m3s.gcode", "cache_key": "a" * 64},
        )
    )

    assert job.status == "succeeded"
    assert repository.create_calls == 0
    assert repository.coalesced_create_calls == 1


def test_agent_job_service_rejects_required_offline_agent() -> None:
    service = AgentJobService(Repository(online=False))

    with pytest.raises(AgentUnavailableError):
        asyncio.run(service.run(Printer(), job_type="status"))


def test_agent_job_service_reports_failed_job_without_fastapi_error() -> None:
    service = AgentJobService(Repository(status="failed"))

    with pytest.raises(AgentJobFailedError) as exc_info:
        asyncio.run(service.run(Printer(), job_type="status"))

    assert exc_info.value.job.error_message == "falha controlada"


def test_agent_job_service_keeps_event_loop_responsive_during_repository_io() -> None:
    entered = threading.Event()
    release = threading.Event()

    class BlockingRepository(Repository):
        def latest_active_agent(self, printer_id: int) -> AgentRecord | None:
            entered.set()
            release.wait(timeout=0.5)
            return super().latest_active_agent(printer_id)

    async def run_scenario() -> None:
        started_at = time.perf_counter()
        task = asyncio.create_task(
            AgentJobService(BlockingRepository()).run(Printer(), job_type="status")
        )
        assert await asyncio.to_thread(entered.wait, 0.2)
        await asyncio.sleep(0.02)
        assert time.perf_counter() - started_at < 0.2
        release.set()
        assert (await task).status == "succeeded"

    asyncio.run(run_scenario())


def test_agent_job_service_shares_polling_for_same_coalesced_job() -> None:
    entered = threading.Event()
    release = threading.Event()

    class BlockingRepository(Repository):
        def get_job(self, printer_id: int, job_id: int) -> AgentJobRecord:
            self.get_calls += 1
            entered.set()
            release.wait(timeout=0.5)
            return self._job(printer_id, job_id, self.status)

    async def run_scenario() -> None:
        repository = BlockingRepository()
        first = asyncio.create_task(
            AgentJobService(repository).run(
                Printer(),
                job_type="remote_moonraker_status",
                timeout_seconds=10.0,
            )
        )
        second = asyncio.create_task(
            AgentJobService(repository).run(
                Printer(),
                job_type="remote_moonraker_status",
                timeout_seconds=10.0,
            )
        )
        assert await asyncio.to_thread(entered.wait, 0.2)
        await asyncio.sleep(0.02)
        release.set()
        first_job, second_job = await asyncio.gather(first, second)
        assert first_job.id == second_job.id == 11
        assert repository.get_calls == 1

    asyncio.run(run_scenario())
