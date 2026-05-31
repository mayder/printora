from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app


def test_pairing_token_exchange_is_single_use_and_never_lists_secret(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner@example.com")
            created = _create_printer(client, owner_token)
            pairing = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            )
            assert pairing.status_code == 200
            token_payload = pairing.json()
            assert token_payload["token"].startswith("ptr_pair_")

            overview = client.get(f"/api/printers/{created['id']}/pairing", headers=_auth(owner_token))
            assert overview.status_code == 200
            assert token_payload["token"] not in overview.text
            assert overview.json()["pairing_tokens"][0]["status"] == "active"

            exchanged = client.post(
                "/api/agent/pairing/exchange",
                json={
                    "pairing_token": token_payload["token"],
                    "stable_id": "agent-owner-001",
                    "agent_version": "0.1.0",
                    "platform": "linux-aarch64",
                    "capabilities": {"heartbeat": True, "snapshot": True},
                },
            )
            assert exchanged.status_code == 200
            credential = exchanged.json()["credential"]
            assert credential.startswith("ptr_agent_")

            reused = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token_payload["token"], "stable_id": "agent-owner-002"},
            )
            assert reused.status_code == 400
            assert "já usado" in reused.json()["detail"]

            refreshed = client.get(f"/api/printers/{created['id']}/pairing", headers=_auth(owner_token)).json()
            assert refreshed["pairing_tokens"][0]["status"] == "used"
            assert credential not in str(refreshed)
    finally:
        get_settings.cache_clear()


def test_expired_and_revoked_pairing_tokens_are_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        database_path = tmp_path / "printora.db"
        initialize_database(database_path)
        with TestClient(app) as client:
            owner_token = _register(client, "owner@example.com")
            created = _create_printer(client, owner_token)
            expired = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 1},
                headers=_auth(owner_token),
            ).json()
            with connect_database(database_path) as connection:
                connection.execute(
                    "UPDATE printer_pairing_tokens SET expires_at = datetime('now', '-1 minute') WHERE id = ?",
                    (expired["id"],),
                )
            expired_exchange = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": expired["token"], "stable_id": "expired-agent"},
            )
            assert expired_exchange.status_code == 400
            assert "expirado" in expired_exchange.json()["detail"]

            revoked = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()
            revoke_response = client.post(
                f"/api/printers/{created['id']}/pairing/tokens/{revoked['id']}/revoke",
                headers=_auth(owner_token),
            )
            revoked_exchange = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": revoked["token"], "stable_id": "revoked-agent"},
            )
            assert revoke_response.status_code == 200
            assert revoke_response.json()["status"] == "revoked"
            assert revoked_exchange.status_code == 400
            assert "revogado" in revoked_exchange.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_pairing_tokens_can_be_removed_after_inactive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-token-remove@example.com")
            created = _create_printer(client, owner_token)
            active = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()

            blocked = client.delete(
                f"/api/printers/{created['id']}/pairing/tokens/{active['id']}",
                headers=_auth(owner_token),
            )
            assert blocked.status_code == 409

            revoked = client.post(
                f"/api/printers/{created['id']}/pairing/tokens/{active['id']}/revoke",
                headers=_auth(owner_token),
            )
            assert revoked.status_code == 200
            removed = client.delete(
                f"/api/printers/{created['id']}/pairing/tokens/{active['id']}",
                headers=_auth(owner_token),
            )
            assert removed.status_code == 200
            assert removed.json()["status"] == "removed"
            assert removed.json()["removed_at"] is not None

            overview = client.get(f"/api/printers/{created['id']}/pairing", headers=_auth(owner_token)).json()
            assert overview["pairing_tokens"] == []
    finally:
        get_settings.cache_clear()


def test_new_pairing_token_revokes_previous_active_token(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-token-single@example.com")
            created = _create_printer(client, owner_token)
            first = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()
            second = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()

            overview = client.get(f"/api/printers/{created['id']}/pairing", headers=_auth(owner_token)).json()
            statuses = {token["id"]: token["status"] for token in overview["pairing_tokens"]}
            assert statuses[first["id"]] == "revoked"
            assert statuses[second["id"]] == "active"
            assert list(statuses.values()).count("active") == 1
    finally:
        get_settings.cache_clear()


def test_pairing_ownership_and_revoked_agent_blocks_agent_endpoints(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner@example.com")
            other_token = _register(client, "other@example.com")
            created = _create_printer(client, owner_token)

            blocked = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(other_token),
            )
            assert blocked.status_code == 404

            token_payload = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()
            exchanged = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token_payload["token"], "stable_id": "agent-owner-003"},
            ).json()
            credential = exchanged["credential"]
            heartbeat = client.post(
                "/api/agent/heartbeat",
                json={"agent_version": "0.1.1", "platform": "linux"},
                headers=_auth(credential),
            )
            assert heartbeat.status_code == 200
            assert heartbeat.json()["accepted"] is True

            revoked = client.post(
                f"/api/printers/{created['id']}/agents/{exchanged['agent_id']}/revoke",
                headers=_auth(owner_token),
            )
            assert revoked.status_code == 200
            for path, method in [
                ("/api/agent/heartbeat", "POST"),
                ("/api/agent/snapshots", "POST"),
                ("/api/agent/jobs/next", "GET"),
            ]:
                if method == "POST":
                    response = client.post(path, json={}, headers=_auth(credential))
                else:
                    response = client.get(path, headers=_auth(credential))
                assert response.status_code == 401
    finally:
        get_settings.cache_clear()


def test_agent_credential_rotation_invalidates_previous_secret(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner@example.com")
            created = _create_printer(client, owner_token)
            token_payload = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()
            exchanged = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token_payload["token"], "stable_id": "agent-owner-004"},
            ).json()
            old_credential = exchanged["credential"]
            rotated = client.post(
                f"/api/printers/{created['id']}/agents/{exchanged['agent_id']}/rotate",
                headers=_auth(owner_token),
            )
            assert rotated.status_code == 200
            new_credential = rotated.json()["credential"]
            assert new_credential != old_credential
            assert client.post("/api/agent/heartbeat", json={}, headers=_auth(old_credential)).status_code == 401
            assert client.post("/api/agent/heartbeat", json={}, headers=_auth(new_credential)).status_code == 200
    finally:
        get_settings.cache_clear()


def test_removed_agent_is_hidden_and_can_pair_same_identity_again(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-remove@example.com")
            created = _create_printer(client, owner_token)
            token_payload = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()
            exchanged = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token_payload["token"], "stable_id": "agent-remove-001"},
            ).json()
            removed = client.delete(
                f"/api/printers/{created['id']}/agents/{exchanged['agent_id']}",
                headers=_auth(owner_token),
            )
            assert removed.status_code == 200
            assert removed.json()["status"] == "removed"
            assert removed.json()["removed_at"] is not None

            overview = client.get(f"/api/printers/{created['id']}/pairing", headers=_auth(owner_token)).json()
            assert overview["agents"] == []

            new_pairing = client.post(
                f"/api/printers/{created['id']}/pairing/tokens",
                json={"ttl_minutes": 15},
                headers=_auth(owner_token),
            ).json()
            reinstalled = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": new_pairing["token"], "stable_id": "agent-remove-001"},
            )
            assert reinstalled.status_code == 200
            assert reinstalled.json()["agent_id"] == exchanged["agent_id"]
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": "Voron Cloud", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
