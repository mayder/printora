from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app


def test_remote_parity_overview_lists_states_and_blocks_mutable_features(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-parity@example.com")
            other_token = _register(client, "other-parity@example.com")
            printer = _create_printer(client, owner_token)

            blocked_owner = client.get(f"/api/printers/{printer['id']}/remote/parity", headers=_auth(other_token))
            assert blocked_owner.status_code == 404

            overview = client.get(f"/api/printers/{printer['id']}/remote/parity", headers=_auth(owner_token))
            assert overview.status_code == 200
            payload = overview.json()
            assert payload["executor"] == "agent"
            assert payload["agent_online"] is False
            features = {feature["key"]: feature for feature in payload["features"]}
            assert features["health"]["state"] == "offline"
            assert features["audit"]["safety"] == "read_only"
            assert features["operation_preview"]["safety"] == "dry_run"
            assert features["mutable_operation"]["state"] == "blocked"
    finally:
        get_settings.cache_clear()


def test_remote_parity_job_flow_and_cached_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-parity-job@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-parity-001")

            created = client.post(
                f"/api/printers/{printer['id']}/remote/parity/jobs",
                json={"feature_key": "health"},
                headers=_auth(owner_token),
            )
            assert created.status_code == 200
            job = created.json()
            assert job["job_type"] == "remote_health"

            jobs = client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"]
            assert jobs[0]["id"] == job["id"]
            assert client.post(f"/api/agent/jobs/{job['id']}/ack", headers=_auth(credential)).status_code == 200
            result = client.post(
                f"/api/agent/jobs/{job['id']}/result",
                json={
                    "correlation_id": job["correlation_id"],
                    "result": {
                        "safe_mode": "read_only",
                        "kind": "health",
                        "detail": "PKG-47 ptr_agent_secret api_key=hidden-value",
                        "nested": {"password": "plain-secret", "private_key_material": "key-secret"},
                    },
                },
                headers=_auth(credential),
            )
            assert result.status_code == 200

            overview = client.get(f"/api/printers/{printer['id']}/remote/parity", headers=_auth(owner_token)).json()
            health = next(feature for feature in overview["features"] if feature["key"] == "health")
            assert health["state"] == "cached"
            assert health["latest_job"]["result"]["kind"] == "health"
            assert "PKG" not in str(health["latest_job"])
            assert "ptr_agent_" not in str(health["latest_job"])
            assert "hidden-value" not in str(health["latest_job"])
            assert "plain-secret" not in str(health["latest_job"])
            assert "key-secret" not in str(health["latest_job"])

            blocked = client.post(
                f"/api/printers/{printer['id']}/remote/parity/jobs",
                json={"feature_key": "mutable_operation"},
                headers=_auth(owner_token),
            )
            assert blocked.status_code == 400
            assert "bloqueada" in blocked.json()["detail"]
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": "Voron Parity", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
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


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
