from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import (
    AgentCredentialCreateRequest,
    AuthRepository,
    LoginRequest,
    MfaLoginRequest,
    OrganizationCreateRequest,
    OrganizationMemberAddRequest,
    StepUpRequest,
    UserRegisterRequest,
    complete_mfa_login,
    login,
    setup_mfa,
    totp_code,
    validate_step_up,
)
from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.printers import PrinterCreate, PrinterRepository, PrinterUpdate
from app.routes.operation import _require_step_up_when_authenticated
from app.self_update import SelfUpdateRepository
from app.setup_wizard import SetupSshRunRepository


def test_auth_schema_is_created(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"

    initialize_database(database_path)

    with connect_database(database_path) as connection:
        users = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'auth_users'").fetchone()
        organizations = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'auth_organizations'").fetchone()
        credentials = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'agent_credentials'").fetchone()

    assert users is not None
    assert organizations is not None
    assert credentials is not None


def test_register_login_and_session_do_not_expose_password(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)

    user = repository.create_user(
        UserRegisterRequest(
            email="owner@example.com",
            password="correct-horse",
            whatsapp="+550099999999",
            telegram="@owner",
        )
    )
    response = login(repository, LoginRequest(email="owner@example.com", password="correct-horse"))
    session_user = repository.get_user_by_session(response.access_token or "")

    assert user.email == "owner@example.com"
    assert response.access_token is not None
    assert session_user is not None
    assert session_user.whatsapp == "+550099999999"

    with connect_database(database_path) as connection:
        row = connection.execute("SELECT password_hash FROM auth_users WHERE id = ?", (user.id,)).fetchone()

    assert row is not None
    assert "correct-horse" not in row["password_hash"]


def test_organization_is_optional_and_membership_is_isolated(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)
    owner = repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    operator = repository.create_user(UserRegisterRequest(email="operator@example.com", password="correct-horse"))

    assert owner.organizations == []

    organization = repository.create_organization(owner.id, OrganizationCreateRequest(name="Voron Lab"))
    linked = repository.add_organization_member(
        owner.id,
        organization.id,
        OrganizationMemberAddRequest(email=operator.email, role="operator"),
    )

    assert organization.role == "owner"
    assert linked.role == "operator"
    assert repository.user_has_organization(operator.id, organization.id) is True


def test_mfa_login_and_step_up_for_destructive_action(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)
    user = repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    mfa = setup_mfa(user)
    repository.set_mfa_secret(user.id, mfa.secret, enabled=True)

    login_response = login(repository, LoginRequest(email=user.email, password="correct-horse"))
    assert login_response.mfa_required is True
    assert login_response.challenge_token is not None

    session = complete_mfa_login(
        repository,
        payload=MfaLoginRequest(challenge_token=login_response.challenge_token, code=totp_code(mfa.secret)),
    )
    refreshed_user = repository.get_user_by_session(session.access_token)
    assert refreshed_user is not None
    step_up = validate_step_up(repository, refreshed_user, StepUpRequest(code=totp_code(mfa.secret)))
    assert repository.consume_step_up(refreshed_user.id, step_up.step_up_token, "destructive_action") is True
    assert repository.consume_step_up(refreshed_user.id, step_up.step_up_token, "destructive_action") is False


def test_agent_credential_is_returned_once_and_verified_by_hash(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = AuthRepository(database_path)
    user = repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))

    created = repository.create_agent_credential(user.id, AgentCredentialCreateRequest(label="Voron agent"))
    listed = repository.list_agent_credentials(user.id)
    verified = repository.verify_agent_credential(created.credential)

    assert created.credential.startswith("ptr_agent_")
    assert listed[0].credential_prefix == created.credential_prefix
    assert not hasattr(listed[0], "credential")
    assert verified is not None
    assert verified.label == "Voron agent"

    with connect_database(database_path) as connection:
        row = connection.execute("SELECT credential_hash FROM agent_credentials WHERE id = ?", (created.id,)).fetchone()

    assert row is not None
    assert created.credential not in row["credential_hash"]


def test_auth_api_blocks_anonymous_and_returns_current_user(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            blocked = client.get("/api/auth/me")
            assert blocked.status_code == 401

            registered = client.post(
                "/api/auth/register",
                json={"email": "owner@example.com", "password": "correct-horse"},
            )
            assert registered.status_code == 200
            token = registered.json()["access_token"]
            current = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

            assert current.status_code == 200
            assert current.json()["email"] == "owner@example.com"
            assert "password" not in current.text
    finally:
        get_settings.cache_clear()


def test_authenticated_operation_requires_step_up_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        database_path = tmp_path / "printora.db"
        initialize_database(database_path)
        repository = AuthRepository(database_path)
        user = repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
        session_token, _ = repository.create_session(user.id)
        settings = get_settings()

        try:
            _require_step_up_when_authenticated(settings, f"Bearer {session_token}", None)
            raised = False
        except Exception:
            raised = True
        step_up = validate_step_up(repository, user, StepUpRequest(password="correct-horse"))
        _require_step_up_when_authenticated(settings, f"Bearer {session_token}", step_up.step_up_token)

        assert raised is True
    finally:
        get_settings.cache_clear()


def test_printers_are_isolated_by_owner_and_shared_by_organization(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth_repository = AuthRepository(database_path)
    owner = auth_repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    guest = auth_repository.create_user(UserRegisterRequest(email="guest@example.com", password="correct-horse"))
    organization = auth_repository.create_organization(owner.id, OrganizationCreateRequest(name="Mayder"))

    owner_printers = PrinterRepository(database_path, user_id=owner.id)
    created = owner_printers.create_printer(
        PrinterCreate(name="Voron Owner", moonraker_url="http://owner.local:7125", host_audit_mode="disabled")
    )
    guest_printers = PrinterRepository(database_path, user_id=guest.id)

    assert [printer.name for printer in owner_printers.list_printers()] == ["Voron Owner"]
    assert guest_printers.list_printers() == []
    assert guest_printers.get_printer(created.id) is None

    owner_printers.update_printer(created.id, PrinterUpdate(organization_id=organization.id))
    assert guest_printers.list_printers() == []

    auth_repository.add_organization_member(
        owner.id,
        organization.id,
        OrganizationMemberAddRequest(email=guest.email, role="operator"),
    )
    guest_scoped = PrinterRepository(database_path, user_id=guest.id, organization_ids=(organization.id,))

    assert [printer.name for printer in guest_scoped.list_printers()] == ["Voron Owner"]
    assert guest_scoped.get_printer(created.id) is not None


def test_cloud_api_does_not_fall_back_to_global_printer_for_other_user(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_response = client.post(
                "/api/auth/register",
                json={"email": "owner@example.com", "password": "correct-horse"},
            )
            guest_response = client.post(
                "/api/auth/register",
                json={"email": "guest@example.com", "password": "correct-horse"},
            )
            owner_token = owner_response.json()["access_token"]
            guest_token = guest_response.json()["access_token"]

            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron Owner",
                    "moonraker_url": "http://owner.local:7125",
                    "host_audit_mode": "disabled",
                },
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            owner_printers = client.get("/api/printers", headers={"Authorization": f"Bearer {owner_token}"})
            guest_printers = client.get("/api/printers", headers={"Authorization": f"Bearer {guest_token}"})
            guest_detail = client.get(
                f"/api/printers/{created.json()['id']}/operation/status",
                headers={"Authorization": f"Bearer {guest_token}"},
            )
            guest_singleton = client.get("/api/moonraker/status", headers={"Authorization": f"Bearer {guest_token}"})

        assert created.status_code == 200
        assert [printer["name"] for printer in owner_printers.json()["printers"]] == ["Voron Owner"]
        assert guest_printers.json()["printers"] == []
        assert guest_detail.status_code == 404
        assert guest_singleton.status_code == 404
    finally:
        get_settings.cache_clear()


def test_operational_histories_are_scoped_by_user(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth_repository = AuthRepository(database_path)
    owner = auth_repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    guest = auth_repository.create_user(UserRegisterRequest(email="guest@example.com", password="correct-horse"))

    with connect_database(database_path) as connection:
        connection.execute(
            """
            INSERT INTO setup_ssh_runs (
                run_type, status, safe_mode, target_host, target_port, target_user,
                auth_method, summary_json, plan_json, error_message, owner_user_id
            )
            VALUES ('preflight', 'ok', 'read_only', 'owner.local', 22, 'pi', 'agent', '{}', NULL, NULL, ?)
            """,
            (owner.id,),
        )
        connection.execute(
            """
            INSERT INTO setup_ssh_runs (
                run_type, status, safe_mode, target_host, target_port, target_user,
                auth_method, summary_json, plan_json, error_message, owner_user_id
            )
            VALUES ('preflight', 'ok', 'read_only', 'guest.local', 22, 'pi', 'agent', '{}', NULL, NULL, ?)
            """,
            (guest.id,),
        )

    owner_setup = SetupSshRunRepository(database_path, user_id=owner.id)
    guest_setup = SetupSshRunRepository(database_path, user_id=guest.id)
    unrelated_setup = SetupSshRunRepository(database_path, user_id=999)

    assert [run.target_host for run in owner_setup.list_runs()] == ["owner.local"]
    assert [run.target_host for run in guest_setup.list_runs()] == ["guest.local"]
    assert unrelated_setup.list_runs() == []


def test_app_update_runs_are_scoped_by_user(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth_repository = AuthRepository(database_path)
    owner = auth_repository.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    guest = auth_repository.create_user(UserRegisterRequest(email="guest@example.com", password="correct-horse"))

    owner_repo = SelfUpdateRepository(database_path, user_id=owner.id)
    guest_repo = SelfUpdateRepository(database_path, user_id=guest.id)
    owner_repo.create_plan(
        target_tag="v1.0.0",
        source_url=None,
        environment="unix",
        current_project_path="/tmp/owner",
        steps=[("plan", "Plano")],
    )
    guest_repo.create_plan(
        target_tag="v2.0.0",
        source_url=None,
        environment="unix",
        current_project_path="/tmp/guest",
        steps=[("plan", "Plano")],
    )

    assert [run.target_tag for run in owner_repo.list_runs()] == ["v1.0.0"]
    assert [run.target_tag for run in guest_repo.list_runs()] == ["v2.0.0"]
