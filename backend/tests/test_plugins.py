import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.plugins import build_plugin_audit
from app.printers import PrinterCreate, PrinterRepository
from app.snapshots import SnapshotRepository


def test_plugin_audit_detects_update_manager_plugins(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    payload = _load_fixture()
    payload["update_status"]["version_info"]["klipper-toolchanger-easy"] = {
        "is_dirty": False,
        "commits_behind_count": 0,
        "full_version_string": "v0.0.0-250-g5f0e5a3f-inferred",
    }
    payload["update_status"]["version_info"]["auto_speed"] = {
        "is_dirty": False,
        "commits_behind_count": 0,
        "full_version_string": "v0.3.4-11-g63315317",
    }
    payload["update_status"]["version_info"]["custom_unused_mod"] = {
        "is_dirty": True,
        "commits_behind_count": 2,
        "full_version_string": "v1.0.0",
    }
    snapshot = SnapshotRepository(database_path).create_snapshot(printer.id, "moonraker_status", payload)

    audit = build_plugin_audit(printer.id, snapshot)
    by_name = {item.name: item for item in audit.items}

    assert audit.source == f"latest_moonraker_snapshot:{snapshot.id}"
    assert audit.counts["detected"] >= 2
    assert audit.counts["unknown"] == 1
    assert audit.counts["investigate"] >= 1
    assert audit.unknown_update_manager_components == ["custom_unused_mod"]
    assert by_name["klipper-toolchanger-easy"].detected is True
    assert by_name["klipper-toolchanger-easy"].classification == "perigoso_remover_agora"
    assert by_name["klipper-toolchanger-easy"].action == "nao_remover_agora"
    assert by_name["klipper-toolchanger-easy"].removal_gates
    assert by_name["auto_speed"].classification == "legado_lixo_tecnico"
    assert by_name["auto_speed"].version == "v0.3.4-11-g63315317"
    assert by_name["custom_unused_mod"].classification == "precisa_confirmacao"
    assert by_name["custom_unused_mod"].action == "investigar"
    assert by_name["custom_unused_mod"].removal_gates


def test_plugin_audit_works_without_snapshot() -> None:
    audit = build_plugin_audit(1, None)

    assert audit.safe_mode == "read_only_no_host_commands"
    assert audit.source == "catalog_without_snapshot"
    assert audit.counts["detected"] == 0
    assert all(item.detected is False for item in audit.items)


def test_plugin_audit_endpoint_uses_snapshot_without_printer_online(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MAYDER_PRINT_LAB_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "mayderprintlab.db")
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Offline printer",
                    "moonraker_url": "http://127.0.0.1:1",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200
            printer_id = created.json()["id"]
            payload = _load_fixture()
            payload["update_status"]["version_info"]["led_effect"] = {
                "is_dirty": False,
                "commits_behind_count": 0,
                "full_version_string": "v0.1.0",
            }
            SnapshotRepository(tmp_path / "mayderprintlab.db").create_snapshot(printer_id, "moonraker_status", payload)

            response = client.get(f"/api/printers/{printer_id}/plugins/audit")

        assert response.status_code == 200
        body = response.json()
        assert body["safe_mode"] == "read_only_no_host_commands"
        assert body["counts"]["detected"] >= 1
        assert body["source"].startswith("latest_moonraker_snapshot:")
    finally:
        get_settings.cache_clear()


def _load_fixture() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "moonraker_snapshot.json"
    return json.loads(fixture_path.read_text())
