from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import AuthRepository
from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.identity.contracts import UserRegisterRequest
from app.modules.identity.protection import AccountProtectionService


def _user(repository: AuthRepository, email: str = "owner@example.com"):
    return repository.create_user(
        UserRegisterRequest(
            email=email,
            password="correct-horse",
            display_name="Owner",
            whatsapp="+553199999999",
            telegram="@owner",
        )
    )


def test_platform_protection_schema_and_export_are_verifiable(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)
    user = _user(repository)
    service = AccountProtectionService(database_path)

    first = service.export_account(user.id, "export-0001")
    retried = service.export_account(user.id, "export-0001")

    assert first.request.status == "ready"
    assert first.request.artifact_sha256 == retried.request.artifact_sha256
    assert first.data == retried.data
    serialized = str(first.data)
    assert "password_hash" not in serialized
    assert "token_hash" not in serialized
    assert "mfa_secret" not in serialized
    with connect_database(database_path) as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(auth_users)").fetchall()
        }
        account_requests = connection.execute(
            "SELECT retention_until FROM auth_account_requests WHERE request_key = ?",
            ("export-0001",),
        ).fetchone()
        appeals = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'social_moderation_appeals'"
        ).fetchone()
    assert "mfa_pending_secret_protected" in columns
    assert account_requests is not None and account_requests["retention_until"]
    assert appeals is not None


def test_account_deactivation_is_idempotent_logical_and_revokes_access(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)
    user = _user(repository)
    session, _ = repository.create_session(user.id)
    step_up, _ = repository.create_step_up(user.id, "account_deletion")
    service = AccountProtectionService(database_path)

    first = service.deactivate_account(user.id, "deletion-0001")
    retried = service.deactivate_account(user.id, "deletion-0001")

    assert first == retried
    assert first.status == "completed"
    assert repository.get_user_by_session(session) is None
    assert repository.consume_step_up(user.id, step_up, "account_deletion") is False
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT is_active, whatsapp, telegram, mfa_secret_protected FROM auth_users WHERE id = ?",
            (user.id,),
        ).fetchone()
    assert row is not None
    assert row["is_active"] == 0
    assert row["whatsapp"] is None
    assert row["telegram"] is None
    assert row["mfa_secret_protected"] is None


def test_step_up_token_is_consumed_exactly_once_under_concurrency(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)
    user = _user(repository)
    token, _ = repository.create_step_up(user.id, "account_export")

    def consume() -> bool:
        return AuthRepository(database_path).consume_step_up(
            user.id, token, "account_export"
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: consume(), range(8)))

    assert results.count(True) == 1
    assert results.count(False) == 7


def test_session_api_is_opaque_and_password_change_revokes_all(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            registered = client.post(
                "/api/auth/register",
                json={"email": "session@example.com", "password": "correct-horse"},
            ).json()
            token = registered["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            sessions = client.get("/api/auth/sessions", headers=headers)
            assert sessions.status_code == 200
            assert sessions.json()[0]["current"] is True
            assert "token" not in str(sessions.json()).lower()

            changed = client.patch(
                "/api/auth/password",
                headers=headers,
                json={
                    "current_password": "correct-horse",
                    "new_password": "new-correct-horse",
                },
            )
            assert changed.status_code == 200
            assert client.get("/api/auth/me", headers=headers).status_code == 401
    finally:
        get_settings.cache_clear()


def test_raw_agent_job_endpoint_rejects_host_script(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            registered = client.post(
                "/api/auth/register",
                json={"email": "jobs@example.com", "password": "correct-horse"},
            ).json()
            headers = {"Authorization": f"Bearer {registered['access_token']}"}
            printer = client.post(
                "/api/printers",
                headers=headers,
                json={
                    "name": "Voron",
                    "moonraker_url": "http://voron.local:7125",
                    "host_audit_mode": "disabled",
                },
            ).json()
            response = client.post(
                f"/api/printers/{printer['id']}/agent/jobs",
                headers=headers,
                json={
                    "job_type": "remote_host_script",
                    "payload": {"script": "id"},
                    "correlation_id": "blocked-host-script",
                },
            )
            assert response.status_code == 403
    finally:
        get_settings.cache_clear()
