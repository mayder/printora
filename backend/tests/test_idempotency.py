from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.platform.idempotency import IdempotencyRepository


def test_mutating_request_replays_persisted_response(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    initialize_database(tmp_path / "printora.db")
    try:
        with TestClient(app) as client:
            token = client.post(
                "/api/auth/register",
                json={"email": "idempotent@example.com", "password": "correct-horse"},
            ).json()["access_token"]
            headers = {
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "printer-create-0001",
            }
            payload = {
                "name": "Voron idempotente",
                "moonraker_url": "http://127.0.0.1:7125",
                "host_audit_mode": "disabled",
            }

            first = client.post("/api/printers", json=payload, headers=headers)
            repeated = client.post("/api/printers", json=payload, headers=headers)

            assert first.status_code == 200
            assert repeated.status_code == 200
            assert repeated.headers["idempotency-status"] == "replayed"
            assert repeated.json()["id"] == first.json()["id"]
        with connect_database(tmp_path / "printora.db") as connection:
            assert connection.execute("SELECT COUNT(*) AS total FROM printers").fetchone()["total"] == 1
    finally:
        get_settings.cache_clear()


def test_same_key_with_different_payload_is_conflict(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    initialize_database(tmp_path / "printora.db")
    try:
        with TestClient(app) as client:
            token = client.post(
                "/api/auth/register",
                json={"email": "idempotent-conflict@example.com", "password": "correct-horse"},
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "printer-create-0002"}
            first = client.post(
                "/api/printers",
                json={"name": "First", "moonraker_url": "http://127.0.0.1:7125", "host_audit_mode": "disabled"},
                headers=headers,
            )
            conflict = client.post(
                "/api/printers",
                json={"name": "Changed", "moonraker_url": "http://127.0.0.1:7125", "host_audit_mode": "disabled"},
                headers=headers,
            )
            assert first.status_code == 200
            assert conflict.status_code == 409
    finally:
        get_settings.cache_clear()


def test_inflight_key_is_not_executed_twice(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = IdempotencyRepository(database_path)

    first = repository.begin("http:actor:POST:/resource", "resource-key-0001", "hash-a")
    concurrent = repository.begin("http:actor:POST:/resource", "resource-key-0001", "hash-a")

    assert first.status == "acquired"
    assert concurrent.status == "processing"
