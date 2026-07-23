from pathlib import Path
import hashlib

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app


def test_agent_update_manifest_is_public_and_versioned(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            response = client.get("/api/agent/update/manifest")
            assert response.status_code == 200
            payload = response.json()
            assert payload["manifest_version"] == 1
            assert payload["minimum_version"] == "0.1.17"
            assert payload["recommended_version"] == "0.1.34"
            assert payload["candidate_version"] is None
            assert payload["protocol_min"] == 1
            assert payload["protocol_max"] == 1
            assert payload["signature_algorithm"] == "ed25519-sha256"
            assert payload["signing_key_id"].startswith("sha256:")
            assert payload["releases"]
            assert {release["platform"] for release in payload["releases"]} == {"linux/arm64"}
            assert {release["version"] for release in payload["releases"]} == {"0.1.33", "0.1.34"}
            linux_arm64 = next(
                release
                for release in payload["releases"]
                if release["platform"] == "linux/arm64" and release["version"] == "0.1.34"
            )
            assert linux_arm64["version"] == "0.1.34"
            assert linux_arm64["url"].endswith("/api/agent/update/releases/0.1.34/linux-arm64")
            assert len(linux_arm64["sha256"]) == 64
            assert linux_arm64["signature"]

            release = client.get("/api/agent/update/releases/linux-arm64")
            assert release.status_code in {200, 404}
            if release.status_code == 404:
                assert release.json()["detail"] == "agent release file not published"
            else:
                assert release.headers["content-type"] == "application/octet-stream"
                assert hashlib.sha256(release.content).hexdigest() == linux_arm64["sha256"]

            candidate = next(release for release in payload["releases"] if release["version"] == "0.1.34")
            candidate_release = client.get("/api/agent/update/releases/0.1.34/linux-arm64")
            assert candidate_release.status_code == 200
            assert hashlib.sha256(candidate_release.content).hexdigest() == candidate["sha256"]

            candidate_manifest_unauthenticated = client.get("/api/agent/update/manifest/candidate")
            assert candidate_manifest_unauthenticated.status_code == 401

            owner_token = _register(client, "owner-agent-candidate@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-candidate-001")
            candidate_manifest = client.get(
                "/api/agent/update/manifest/candidate",
                headers=_auth(credential),
            )
            assert candidate_manifest.status_code == 404
            assert candidate_manifest.json()["detail"] == "agent candidate release not found"
    finally:
        get_settings.cache_clear()


def test_agent_update_report_is_authenticated_and_scoped_to_printer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-agent-update@example.com")
            other_token = _register(client, "other-agent-update@example.com")
            printer = _create_printer(client, owner_token)
            credential = _pair_agent(client, owner_token, printer["id"], "agent-update-001")

            unauthenticated = client.post(
                "/api/agent/update/reports",
                json={"status": "applied", "current_version": "0.1.0", "target_version": "0.1.1"},
            )
            assert unauthenticated.status_code == 401

            report = client.post(
                "/api/agent/update/reports",
                json={
                    "status": "applied",
                    "current_version": "0.1.0",
                    "target_version": "0.1.1",
                    "platform": "linux/arm64",
                    "detail": "updated without printer restart",
                },
                headers=_auth(credential),
            )
            assert report.status_code == 200
            assert report.json()["status"] == "applied"

            history = client.get(f"/api/printers/{printer['id']}/agent/update-history", headers=_auth(owner_token))
            assert history.status_code == 200
            assert history.json()[0]["status"] == "applied"
            assert "0.1.1" in history.json()[0]["detail"]

            blocked = client.get(f"/api/printers/{printer['id']}/agent/update-history", headers=_auth(other_token))
            assert blocked.status_code == 404
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": "Voron Update", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
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
