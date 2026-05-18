import json
from pathlib import Path

from app.database import initialize_database
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
    snapshot = SnapshotRepository(database_path).create_snapshot(printer.id, "moonraker_status", payload)

    audit = build_plugin_audit(printer.id, snapshot)
    by_name = {item.name: item for item in audit.items}

    assert audit.source == "latest_moonraker_snapshot"
    assert by_name["klipper-toolchanger-easy"].detected is True
    assert by_name["klipper-toolchanger-easy"].classification == "perigoso_remover_agora"
    assert by_name["auto_speed"].classification == "legado_lixo_tecnico"
    assert by_name["auto_speed"].version == "v0.3.4-11-g63315317"


def test_plugin_audit_works_without_snapshot() -> None:
    audit = build_plugin_audit(1, None)

    assert audit.safe_mode == "read_only_no_host_commands"
    assert audit.source == "catalog_without_snapshot"
    assert all(item.detected is False for item in audit.items)


def _load_fixture() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "moonraker_snapshot.json"
    return json.loads(fixture_path.read_text())
