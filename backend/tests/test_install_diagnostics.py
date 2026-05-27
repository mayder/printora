from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.install_diagnostics import _parse_raspberry_throttling
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
        assert any(item["key"] == "raspberry_throttling" for item in payload["items"])
        assert "Diagnóstico de instalação do Printora" in payload["copy_text"]
    finally:
        get_settings.cache_clear()


def test_parse_raspberry_throttling_reports_normal() -> None:
    status, detail = _parse_raspberry_throttling("throttled=0x0")

    assert status == "ok"
    assert "sem throttling" in detail


def test_parse_raspberry_throttling_reports_current_issue() -> None:
    status, detail = _parse_raspberry_throttling("throttled=0x5")

    assert status == "error"
    assert "undervoltage atual" in detail
    assert "throttled agora" in detail


def test_parse_raspberry_throttling_reports_historical_issue() -> None:
    status, detail = _parse_raspberry_throttling("throttled=0x50000")

    assert status == "warning"
    assert "undervoltage já ocorreu" in detail
    assert "throttling já ocorreu" in detail
