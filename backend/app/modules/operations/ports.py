from __future__ import annotations

from typing import Protocol

from app.modules.operations.contracts import AgentJobCreateRequest, AgentJobRecord, AgentRecord


class PrinterIdentity(Protocol):
    id: int


class AgentJobRepositoryPort(Protocol):
    def latest_active_agent(self, printer_id: int) -> AgentRecord | None: ...

    def create_job(
        self,
        printer: PrinterIdentity,
        request: AgentJobCreateRequest,
    ) -> AgentJobRecord: ...

    def create_or_reuse_job(
        self,
        printer: PrinterIdentity,
        request: AgentJobCreateRequest,
    ) -> AgentJobRecord: ...

    def get_job(self, printer_id: int, job_id: int) -> AgentJobRecord | None: ...
