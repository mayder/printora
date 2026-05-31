from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app


def test_agent_support_overview_is_scoped_and_reports_alerts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        database_path = tmp_path / "printora.db"
        initialize_database(database_path)
        with TestClient(app) as client:
            owner_token = _register(client, "owner-support@example.com")
            other_token = _register(client, "other-support@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-support-001", version="0.0.1")

            heartbeat = client.post(
                "/api/agent/heartbeat",
                json={"agent_version": "0.0.1", "platform": "linux/arm64", "capabilities": {"protocol_v": 99}},
                headers=_auth(credential),
            )
            assert heartbeat.status_code == 200

            blocked = client.get(f"/api/printers/{printer['id']}/agent/support", headers=_auth(other_token))
            assert blocked.status_code == 404

            overview = client.get(f"/api/printers/{printer['id']}/agent/support", headers=_auth(owner_token))
            assert overview.status_code == 200
            payload = overview.json()
            assert payload["safe_mode"] == "agent_support_sanitized"
            assert payload["agents"][0]["state"] == "outdated"
            codes = {alert["code"] for alert in payload["alerts"]}
            assert "agent_outdated" in codes
            assert "protocol_incompatible" in codes
    finally:
        get_settings.cache_clear()


def test_agent_support_doctor_and_bundle_are_sanitized(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        database_path = tmp_path / "printora.db"
        initialize_database(database_path)
        with TestClient(app) as client:
            owner_token = _register(client, "owner-support-bundle@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-support-002")

            doctor = client.post(f"/api/printers/{printer['id']}/agent/support/doctor", headers=_auth(owner_token))
            assert doctor.status_code == 200
            doctor_job = doctor.json()
            assert doctor_job["job_type"] == "remote_doctor"

            assert client.post(f"/api/agent/jobs/{doctor_job['id']}/ack", headers=_auth(credential)).status_code == 200
            result = client.post(
                f"/api/agent/jobs/{doctor_job['id']}/result",
                json={
                    "correlation_id": doctor_job["correlation_id"],
                    "result": {
                        "safe_mode": "support_diagnostics",
                        "checks": [{"name": "api", "status": "ok", "detail": "ptr_agent_secret"}],
                        "api_token": "ptr_agent_secret",
                    },
                },
                headers=_auth(credential),
            )
            assert result.status_code == 200

            with connect_database(database_path) as connection:
                connection.execute(
                    """
                    INSERT INTO agent_jobs (printer_id, agent_id, correlation_id, job_type, payload_json, status, result_json, error_message)
                    VALUES (?, (SELECT id FROM printer_agents WHERE stable_id = 'agent-support-002'), 'support-secret-job', 'support_secret', ?, 'failed', ?, ?)
                    """,
                    (
                        printer["id"],
                        '{"credential":"ptr_agent_secret","nested":{"token":"ptr_pair_secret"}}',
                        '{"private_key":"secret-key"}',
                        "falha ptr_agent_secret",
                    ),
                )

            bundle = client.get(f"/api/printers/{printer['id']}/agent/support/bundle", headers=_auth(owner_token))
            assert bundle.status_code == 200
            text = bundle.text
            assert "ptr_agent_secret" not in text
            assert "ptr_pair_secret" not in text
            assert "secret-key" not in text
            assert "[redacted]" in text
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": "Voron Support", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    return response.json()


def _pair_agent(client: TestClient, token: str, printer_id: int, stable_id: str, version: str = "0.1.0") -> str:
    pairing = client.post(
        f"/api/printers/{printer_id}/pairing/tokens",
        json={"ttl_minutes": 15},
        headers=_auth(token),
    ).json()
    exchanged = client.post(
        "/api/agent/pairing/exchange",
        json={"pairing_token": pairing["token"], "stable_id": stable_id, "agent_version": version},
    )
    assert exchanged.status_code == 200
    return exchanged.json()["credential"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
