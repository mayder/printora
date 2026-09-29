from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import get_settings
from app.database import connect_database
from app.finance_security import _audit
from app.modules.finance.contracts import (
    ComplianceControlResponse,
    FinanceReadinessResponse,
    RetentionPolicyResponse,
)


class FinanceComplianceService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def readiness(self) -> FinanceReadinessResponse:
        with connect_database(self.database_path) as connection:
            controls = connection.execute(
                "SELECT * FROM finance_compliance_controls ORDER BY control_key"
            ).fetchall()
            policies = connection.execute(
                "SELECT * FROM finance_retention_policies ORDER BY data_class"
            ).fetchall()
            expired = connection.execute(
                "SELECT COUNT(*) AS total FROM finance_audit_events WHERE retention_until < CURRENT_TIMESTAMP"
            ).fetchone()
        control_models = [_control_response(row) for row in controls]
        pending = [row.control_key for row in control_models if row.status == "pending"]
        blocked = [row.control_key for row in control_models if row.status == "blocked"]
        settings = get_settings()
        runtime_supports_real = False
        return FinanceReadinessResponse(
            payment_mode=settings.payment_mode,
            runtime_supports_real_payments=runtime_supports_real,
            real_payments_allowed=runtime_supports_real and not pending and not blocked,
            pending_controls=pending,
            blocked_controls=blocked,
            controls=control_models,
            retention_policies=[_policy_response(row) for row in policies],
            expired_audit_rows_preview=int(expired["total"]),
        )

    def review_control(
        self,
        control_key: str,
        status: str,
        evidence_reference: str,
        expires_at: str | None,
        actor_user_id: int,
    ) -> ComplianceControlResponse:
        if status not in {"pending", "passed", "blocked"}:
            raise ValueError("status de compliance inválido")
        digest = hashlib.sha256(evidence_reference.strip().encode()).hexdigest()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT id FROM finance_compliance_controls WHERE control_key = ?", (control_key,)
            ).fetchone()
            if row is None:
                raise ValueError("controle de compliance desconhecido")
            connection.execute(
                """
                UPDATE finance_compliance_controls
                SET status = ?, evidence_sha256 = ?, reviewed_by_user_id = ?,
                    reviewed_at = CURRENT_TIMESTAMP, expires_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, digest, actor_user_id, expires_at, row["id"]),
            )
            _audit(
                connection, "finance.compliance.reviewed", actor_user_id,
                "compliance_control", control_key, f"compliance:{control_key}",
                {"status": status, "evidence_sha256": digest},
            )
            updated = connection.execute(
                "SELECT * FROM finance_compliance_controls WHERE id = ?", (row["id"],)
            ).fetchone()
        return _control_response(updated)


def _control_response(row) -> ComplianceControlResponse:
    return ComplianceControlResponse(
        control_key=str(row["control_key"]), status=str(row["status"]),
        evidence_present=bool(row["evidence_sha256"]),
        reviewed_by_user_id=row["reviewed_by_user_id"],
        reviewed_at=str(row["reviewed_at"]) if row["reviewed_at"] else None,
        expires_at=str(row["expires_at"]) if row["expires_at"] else None,
    )


def _policy_response(row) -> RetentionPolicyResponse:
    return RetentionPolicyResponse(
        data_class=str(row["data_class"]), retention_days=int(row["retention_days"]),
        legal_basis=str(row["legal_basis"]), deletion_mode=str(row["deletion_mode"]),
    )
