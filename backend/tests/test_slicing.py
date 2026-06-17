from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.database import connect_database, initialize_database
from app.main import app
from app.slicing import SlicingEngineBridge, SlicingRequest


def test_slicing_engine_blocks_when_not_configured(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, slicer_engine_path=tmp_path / "missing-orca")
    bridge = SlicingEngineBridge(settings)

    info = bridge.detect("orcaslicer")
    result = bridge.dry_run(
        SlicingRequest(
            model_reference="library://model.stl",
            printer_reference="Voron 2.4 350",
            material_reference="ABS",
            quality_reference="0.20 qualidade",
        )
    )

    assert info.status == "blocked"
    assert result.status == "blocked"
    assert result.command_preview == []
    assert "indisponível" in result.sanitized_log


def test_slicing_engine_sanitizes_paths_and_tokens(tmp_path: Path) -> None:
    executable = tmp_path / "orcaslicer"
    executable.write_text("#!/usr/bin/env bash\necho \"$HOME/private/orca token=secret-value ptr_agent_abc123\"\n")
    executable.chmod(0o755)
    settings = Settings(data_dir=tmp_path, slicer_engine_path=executable)
    bridge = SlicingEngineBridge(settings)

    info = bridge.detect("orcaslicer")

    assert info.status == "ready"
    assert str(Path.home()) not in (info.version_text or "")
    assert "secret-value" not in (info.version_text or "")
    assert "ptr_agent_abc123" not in (info.version_text or "")


def test_slicing_routes_record_read_only_checks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_SLICER_ENGINE_PATH", str(tmp_path / "missing-orca"))
    from app.config import get_settings

    get_settings.cache_clear()
    initialize_database(tmp_path / "printora.db")
    client = TestClient(app)

    engine_response = client.get("/api/slicing/engine")
    dry_run_response = client.post(
        "/api/slicing/dry-run",
        json={
            "model_reference": "library://benchy.stl",
            "printer_reference": "Voron 0.2",
            "material_reference": "PLA",
            "quality_reference": "0.20 rapido",
        },
    )

    assert engine_response.status_code == 200
    assert engine_response.json()["status"] == "blocked"
    assert dry_run_response.status_code == 200
    assert dry_run_response.json()["status"] == "blocked"

    with connect_database(tmp_path / "printora.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM slicing_engine_checks").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM slicing_dry_run_logs").fetchone()[0] == 1
    get_settings.cache_clear()
