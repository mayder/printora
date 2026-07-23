from pathlib import Path

import pytest
from fastapi import HTTPException

from app.auth import AuthRepository
from app.config import get_settings
from app.database import connect_database, initialize_database
from app.finance_compliance import FinanceComplianceService
from app.modules.finance.api import _require_finance_step_up
from app.modules.identity.contracts import CurrentUser
from app.payment_provider import PaymentProviderCircuitBreaker


def setup_compliance(tmp_path: Path) -> tuple[Path, int, FinanceComplianceService]:
    database_path = tmp_path / "compliance.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        auditor = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('auditor@example.com', 'hash')"
        ).lastrowid
    return database_path, int(auditor), FinanceComplianceService(database_path)


def test_real_payment_remains_unavailable_even_after_all_controls_pass(tmp_path: Path) -> None:
    database_path, auditor, service = setup_compliance(tmp_path)
    initial = service.readiness()
    assert len(initial.pending_controls) == 8
    assert initial.payment_mode == "disabled"
    assert initial.real_payments_allowed is False

    for key in initial.pending_controls:
        reviewed = service.review_control(
            key, "passed", f"controlled-evidence:{key}", None, auditor
        )
        assert reviewed.evidence_present is True
    ready = service.readiness()
    assert ready.pending_controls == [] and ready.blocked_controls == []
    assert ready.runtime_supports_real_payments is False
    assert ready.real_payments_allowed is False
    with connect_database(database_path) as connection:
        values = connection.execute(
            "SELECT evidence_sha256 FROM finance_compliance_controls"
        ).fetchall()
        assert all("controlled-evidence" not in row["evidence_sha256"] for row in values)


def test_retention_is_explicit_and_cleanup_is_preview_only(tmp_path: Path) -> None:
    database_path, _auditor, service = setup_compliance(tmp_path)
    readiness = service.readiness()
    policies = {row.data_class: row for row in readiness.retention_policies}
    assert policies["ledger_and_orders"].retention_days == 3650
    assert policies["finance_audit"].deletion_mode == "anonymize_after_retention"
    with pytest.raises(Exception, match="immutable"):
        with connect_database(database_path) as connection:
            connection.execute(
                "UPDATE finance_retention_policies SET retention_days = 1 WHERE data_class = 'finance_audit'"
            )


def test_provider_circuit_breaker_opens_and_recovers() -> None:
    now = [100.0]
    breaker = PaymentProviderCircuitBreaker(
        failure_threshold=2, recovery_seconds=10, clock=lambda: now[0]
    )

    def fail():
        raise TimeoutError("provider timeout")

    with pytest.raises(TimeoutError):
        breaker.call(fail)
    with pytest.raises(TimeoutError):
        breaker.call(fail)
    with pytest.raises(RuntimeError, match="aberto"):
        breaker.call(lambda: "should-not-run")
    now[0] += 11
    assert breaker.call(lambda: "recovered") == "recovered"


def test_sensitive_finance_action_consumes_single_use_step_up(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        user_id = connection.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES ('stepup@example.com', 'hash')"
        ).lastrowid
    repository = AuthRepository(database_path)
    user = repository.get_user(int(user_id))
    assert user is not None
    current = CurrentUser(user=user, token="session")
    with pytest.raises(HTTPException, match="autenticação reforçada"):
        _require_finance_step_up(current, None)
    token, _expires_at = repository.create_step_up(int(user_id), "finance_sensitive_action")
    _require_finance_step_up(current, token)
    with pytest.raises(HTTPException, match="autenticação reforçada"):
        _require_finance_step_up(current, token)
    get_settings.cache_clear()
