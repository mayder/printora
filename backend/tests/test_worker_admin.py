from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import get_settings
from app.database import initialize_database
from app.main import app


def test_worker_admin_is_deny_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_PLATFORM_ADMIN_EMAILS", "platform-admin@example.test")
    get_settings.cache_clear()
    initialize_database(tmp_path / "printora.db")
    try:
        with TestClient(app) as client:
            ordinary = _register(client, "ordinary-worker@example.com")
            assert client.get("/api/admin/workers", headers=_auth(ordinary)).status_code == 403
            AuthRepository(tmp_path / "printora.db").create_user(
                UserRegisterRequest(email="platform-admin@example.test", password="correct-horse")
            )
            admin = _login(client, "platform-admin@example.test")
            overview = client.get("/api/admin/workers", headers=_auth(admin))
            assert overview.status_code == 200
            assert {item["queue_name"] for item in overview.json()["controls"]} == {
                "outbox",
                "critical",
                "default",
                "bulk",
            }
            controlled = client.post(
                "/api/admin/workers/control",
                json={"queue_name": "bulk", "desired_state": "paused"},
                headers={**_auth(admin), "Idempotency-Key": "worker-control-0001"},
            )
            assert controlled.status_code == 200
            assert controlled.json()["desired_state"] == "paused"
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
