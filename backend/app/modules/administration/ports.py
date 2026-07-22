from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.modules.administration.contracts import (
    BackupPolicyCreate,
    BackupPolicyRecord,
    BackupRunRecord,
)


@runtime_checkable
class BackupRepositoryPort(Protocol):
    def list_policies(self, printer_id: int) -> list[BackupPolicyRecord]: ...

    def get_policy(self, policy_id: int) -> BackupPolicyRecord | None: ...

    def create_policy(
        self,
        printer_id: int,
        payload: BackupPolicyCreate,
    ) -> BackupPolicyRecord: ...

    def list_runs(self, printer_id: int, limit: int = 20) -> list[BackupRunRecord]: ...
