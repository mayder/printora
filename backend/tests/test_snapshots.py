import json
from pathlib import Path

from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository
from app.snapshots import (
    SnapshotRepository,
    build_moonraker_snapshot_payload,
    summarize_snapshot,
)


def test_create_and_list_moonraker_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    fixture = _load_fixture()
    payload = build_moonraker_snapshot_payload(
        printer_id=printer.id,
        moonraker_url=printer.moonraker_url,
        printer_info=fixture["printer_info"],
        server_info=fixture["server_info"],
        update_status=fixture["update_status"],
        system_info=fixture["system_info"],
        proc_stats=fixture["proc_stats"],
    )

    detail = snapshot_repository.create_snapshot(printer.id, "moonraker_status", payload)
    snapshots = snapshot_repository.list_snapshots(printer.id)

    assert detail.id == snapshots[0].id
    assert snapshots[0].summary["klipper_state"] == "ready"
    assert snapshots[0].summary["failed_components"] == []
    assert detail.payload["source"] == "moonraker"
    assert detail.payload["safe_mode"] == "read_only"


def test_snapshot_summary_flags_dirty_repos() -> None:
    fixture = _load_fixture()
    fixture["update_status"]["version_info"]["klipper"]["is_dirty"] = True

    summary = summarize_snapshot("moonraker_status", fixture)

    assert summary["dirty_repos"] == ["klipper"]
    assert summary["klipper_version"] == "v0.13.0-656-g4cc47cf5-dirty"


def test_snapshot_list_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    first = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    second = printer_repository.create_printer(
        PrinterCreate(name="Other", moonraker_url="http://other.local:7125")
    )

    snapshot_repository.create_snapshot(first.id, "manual", {"name": "first"})
    snapshot_repository.create_snapshot(second.id, "manual", {"name": "second"})

    assert len(snapshot_repository.list_snapshots(first.id)) == 1
    assert snapshot_repository.list_snapshots(first.id)[0].summary == {"keys": ["name"]}


def _load_fixture() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "moonraker_snapshot.json"
    return json.loads(fixture_path.read_text())
