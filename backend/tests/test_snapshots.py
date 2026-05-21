import json
from pathlib import Path

from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository
from app.snapshots import (
    SnapshotRepository,
    build_snapshot_diff,
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


def test_moonraker_snapshot_can_store_operation_objects() -> None:
    payload = build_moonraker_snapshot_payload(
        printer_id=1,
        moonraker_url="http://voron.local:7125",
        printer_info={"state": "ready"},
        server_info={"klippy_state": "ready"},
        update_status={},
        system_info={},
        proc_stats={},
        operation_objects={"status": {"extruder": {"temperature": 25}}},
    )

    assert payload["operation_objects"]["status"]["extruder"]["temperature"] == 25


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


def test_snapshot_list_by_type_filters_before_limit(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )

    moonraker = snapshot_repository.create_snapshot(printer.id, "moonraker_status", {"server_info": {"klippy_state": "ready"}})
    snapshot_repository.create_snapshot(printer.id, "manual", {"name": "newer"})
    snapshot_repository.create_snapshot(printer.id, "host_audit", {"hostname": "voron"})

    snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=1)

    assert [snapshot.id for snapshot in snapshots] == [moonraker.id]


def test_snapshot_diff_reports_no_relevant_changes(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    fixture = _load_fixture()

    first = snapshot_repository.create_snapshot(printer.id, "moonraker_status", fixture)
    second = snapshot_repository.create_snapshot(printer.id, "moonraker_status", fixture)

    diff = build_snapshot_diff(first, second)

    assert diff.summary == "Sem mudanças relevantes entre os snapshots."
    assert diff.highest_severity == "info"
    assert diff.changes == []


def test_snapshot_diff_flags_blocking_moonraker_failure(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    before_payload = _load_fixture()
    after_payload = _load_fixture()
    after_payload["server_info"]["failed_components"] = ["spoolman"]

    first = snapshot_repository.create_snapshot(printer.id, "moonraker_status", before_payload)
    second = snapshot_repository.create_snapshot(printer.id, "moonraker_status", after_payload)

    diff = snapshot_repository.diff_snapshots(printer.id, first.id, second.id)

    assert diff is not None
    assert diff.highest_severity == "bloqueio"
    assert diff.changes[0].field == "failed_components"


def test_snapshot_diff_flags_dirty_repo_as_risk(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    before_payload = _load_fixture()
    after_payload = _load_fixture()
    after_payload["update_status"]["version_info"]["klipper"]["is_dirty"] = True

    first = snapshot_repository.create_snapshot(printer.id, "moonraker_status", before_payload)
    second = snapshot_repository.create_snapshot(printer.id, "moonraker_status", after_payload)

    diff = snapshot_repository.diff_snapshots(printer.id, first.id, second.id)

    assert diff is not None
    assert diff.highest_severity == "risco"
    assert [change.field for change in diff.changes] == ["dirty_repos"]


def test_snapshot_diff_rejects_cross_printer_snapshots(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    snapshot_repository = SnapshotRepository(database_path)
    first_printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    second_printer = printer_repository.create_printer(
        PrinterCreate(name="Other", moonraker_url="http://other.local:7125")
    )
    first = snapshot_repository.create_snapshot(first_printer.id, "manual", {"name": "first"})
    second = snapshot_repository.create_snapshot(second_printer.id, "manual", {"name": "second"})

    assert snapshot_repository.diff_snapshots(first_printer.id, first.id, second.id) is None


def _load_fixture() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "moonraker_snapshot.json"
    return json.loads(fixture_path.read_text())
