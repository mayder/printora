from pathlib import Path

from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository
from app.z_offset import ZOffsetRecordCreate, ZOffsetRepository, build_z_offset_wizard_plan


def test_create_first_z_offset_record_without_delta(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = ZOffsetRepository(database_path)

    record = repository.create_record(
        printer.id,
        ZOffsetRecordCreate(
            plate_name="Texturizada",
            material="pla",
            nozzle="t0",
            offset_value=-0.295,
        ),
    )

    assert record.material == "PLA"
    assert record.nozzle == "T0"
    assert record.previous_offset_value is None
    assert record.delta_value is None
    assert record.alert_level == "ok"


def test_z_offset_delta_uses_previous_matching_plate_material_and_nozzle(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = ZOffsetRepository(database_path)
    repository.create_record(
        printer.id,
        ZOffsetRecordCreate(plate_name="Texturizada", material="PLA", nozzle="T0", offset_value=-0.295),
    )

    record = repository.create_record(
        printer.id,
        ZOffsetRecordCreate(plate_name="Texturizada", material="PLA", nozzle="T0", offset_value=-0.355),
    )

    assert record.previous_offset_value == -0.295
    assert round(record.delta_value or 0, 3) == -0.06
    assert record.alert_level == "monitorar"


def test_z_offset_large_delta_requires_review(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = ZOffsetRepository(database_path)
    repository.create_record(
        printer.id,
        ZOffsetRecordCreate(plate_name="Lisa", material="ABS", nozzle="T0", offset_value=-0.2),
    )

    record = repository.create_record(
        printer.id,
        ZOffsetRecordCreate(plate_name="Lisa", material="ABS", nozzle="T0", offset_value=-0.31),
    )

    assert record.alert_level == "revisar"


def test_z_offset_history_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Other", moonraker_url="http://other.local:7125"))
    repository = ZOffsetRepository(database_path)

    repository.create_record(first.id, ZOffsetRecordCreate(offset_value=-0.29))
    repository.create_record(second.id, ZOffsetRecordCreate(offset_value=-0.2))

    assert len(repository.list_records(first.id)) == 1
    assert repository.list_records(first.id)[0].offset_value == -0.29


def test_z_offset_wizard_plan_has_no_gcode_execution_and_warns_on_large_delta(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = ZOffsetRepository(database_path)
    previous = repository.create_record(
        printer.id,
        ZOffsetRecordCreate(plate_name="Texturizada", material="PLA", nozzle="T0", offset_value=-0.2),
    )

    plan = build_z_offset_wizard_plan(
        plate_name="Texturizada",
        material="PLA",
        nozzle="T0",
        proposed_offset_value=-0.32,
        previous_record=previous,
    )

    assert plan.safe_mode == "manual_guided_no_gcode"
    assert plan.alert_level == "revisar"
    assert plan.delta_value == -0.12
    assert any(step.command == "PROBE_CALIBRATE" for step in plan.steps)
    assert "não altera printer.cfg" in plan.steps[-1].detail


def test_z_offset_wizard_plan_allows_initial_reference() -> None:
    plan = build_z_offset_wizard_plan(
        plate_name="Lisa",
        material="ABS",
        nozzle="T0",
        proposed_offset_value=-0.25,
        previous_record=None,
    )

    assert plan.previous_offset_value is None
    assert plan.delta_value is None
    assert plan.alert_level == "ok"
    assert "referência inicial" in plan.recommendation
