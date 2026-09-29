from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app


def test_remote_operation_requires_scope_preflight_and_confirmation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-remote-op@example.com")
            other_token = _register(client, "other-remote-op@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-remote-op-001")

            blocked_scope = client.post(
                f"/api/printers/{printer['id']}/remote/operations/preflight",
                json={"action_id": "set_fan", "parameters": {"speed_percent": 25}},
                headers=_auth(other_token),
            )
            assert blocked_scope.status_code == 404

            overview = client.get(f"/api/printers/{printer['id']}/remote/operations", headers=_auth(owner_token))
            assert overview.status_code == 200
            assert any(action["action_id"] == "set_fan" for action in overview.json()["actions"])

            preflight = client.post(
                f"/api/printers/{printer['id']}/remote/operations/preflight",
                json={"action_id": "set_fan", "parameters": {"speed_percent": 25}},
                headers=_auth(owner_token),
            )
            assert preflight.status_code == 200
            preflight_job = preflight.json()
            assert preflight_job["job_type"] == "remote_mutation_preflight"
            assert preflight_job["payload"]["confirmation_phrase"].startswith("CONFIRM_REMOTE_SET_FAN_")

            wrong_confirmation = client.post(
                f"/api/printers/{printer['id']}/remote/operations/execute",
                json={"preflight_job_id": preflight_job["id"], "confirmation_phrase": "wrong"},
                headers=_auth(owner_token),
            )
            assert wrong_confirmation.status_code == 400
            assert "preflight remoto precisa estar aprovado" in wrong_confirmation.json()["detail"]

            _finish_job(
                client,
                credential,
                preflight_job,
                {"safe_mode": "remote_mutation_preflight", "can_execute": True, "printing": False, "print_state": "standby"},
            )

            execute = client.post(
                f"/api/printers/{printer['id']}/remote/operations/execute",
                json={
                    "preflight_job_id": preflight_job["id"],
                    "confirmation_phrase": preflight_job["payload"]["confirmation_phrase"],
                },
                headers=_auth(owner_token),
            )
            assert execute.status_code == 200
            execute_job = execute.json()
            assert execute_job["job_type"] == "remote_mutation_execute"
            assert execute_job["payload"]["preflight_job_id"] == preflight_job["id"]
            assert execute_job["payload"]["confirmed_by"]["email"] == "owner-remote-op@example.com"

            jobs = client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"]
            assert any(job["id"] == execute_job["id"] for job in jobs)

            cancel = client.post(
                f"/api/printers/{printer['id']}/remote/operations/jobs/{execute_job['id']}/cancel",
                headers=_auth(owner_token),
            )
            assert cancel.status_code == 200
            assert cancel.json()["canceled"] is True
    finally:
        get_settings.cache_clear()


def test_remote_operation_blocks_printing_preflight(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-remote-printing@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-remote-op-002")
            preflight_job = client.post(
                f"/api/printers/{printer['id']}/remote/operations/preflight",
                json={"action_id": "move_z", "parameters": {"distance_mm": 1}},
                headers=_auth(owner_token),
            ).json()
            _finish_job(
                client,
                credential,
                preflight_job,
                {
                    "safe_mode": "remote_mutation_preflight",
                    "can_execute": False,
                    "printing": True,
                    "print_state": "printing",
                    "blockers": ["Impressão em andamento."],
                },
            )
            execute = client.post(
                f"/api/printers/{printer['id']}/remote/operations/execute",
                json={
                    "preflight_job_id": preflight_job["id"],
                    "confirmation_phrase": preflight_job["payload"]["confirmation_phrase"],
                },
                headers=_auth(owner_token),
            )
            assert execute.status_code == 400
            assert "preflight remoto bloqueou" in execute.json()["detail"]
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": "Voron Remote", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    return response.json()


def _pair_agent(client: TestClient, token: str, printer_id: int, stable_id: str) -> str:
    pairing = client.post(
        f"/api/printers/{printer_id}/pairing/tokens",
        json={"ttl_minutes": 15},
        headers=_auth(token),
    ).json()
    exchanged = client.post(
        "/api/agent/pairing/exchange",
        json={"pairing_token": pairing["token"], "stable_id": stable_id, "agent_version": "0.1.0"},
    )
    assert exchanged.status_code == 200
    return exchanged.json()["credential"]


def _finish_job(client: TestClient, credential: str, job: dict, result: dict) -> None:
    assert client.post(f"/api/agent/jobs/{job['id']}/ack", headers=_auth(credential)).status_code == 200
    response = client.post(
        f"/api/agent/jobs/{job['id']}/result",
        json={"correlation_id": job["correlation_id"], "result": result},
        headers=_auth(credential),
    )
    assert response.status_code == 200


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
