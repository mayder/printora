from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.operational import readiness


def test_health_is_liveness_and_ready_checks_database(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            assert client.get("/health").json()["status"] == "ok"
            response = client.get("/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"
        assert response.json()["schema_revision"] > 0
    finally:
        get_settings.cache_clear()


def test_ready_fails_closed_when_database_is_missing(tmp_path: Path, monkeypatch) -> None:
    missing_data_dir = tmp_path / "missing"
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(missing_data_dir))
    get_settings.cache_clear()
    try:
        settings = get_settings()
        initialize_database(settings.database_path)
        settings.database_path.unlink()
        is_ready, payload = readiness(settings)

        assert is_ready is False
        assert payload["status"] == "not_ready"
    finally:
        get_settings.cache_clear()


def test_request_id_is_propagated_and_metrics_are_exported(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/health", headers={"X-Request-ID": "deploy-smoke-123"})
            metrics = client.get("/metrics")

        assert response.headers["X-Request-ID"] == "deploy-smoke-123"
        assert "printora_http_requests_total" in metrics.text
        assert 'route="/health"' in metrics.text
    finally:
        get_settings.cache_clear()
