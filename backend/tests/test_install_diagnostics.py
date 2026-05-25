from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_install_diagnostics_endpoint_returns_actionable_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_PORT", "8069")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/api/system/install-diagnostics")

        assert response.status_code == 200
        payload = response.json()
        assert payload["safe_mode"] == "read_only"
        assert payload["port"] == "8069"
        assert payload["counts"]["ok"] >= 1
        assert any(item["key"] == "python" for item in payload["items"])
        assert "Diagnóstico de instalação do Printora" in payload["copy_text"]
    finally:
        get_settings.cache_clear()
