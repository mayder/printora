from pathlib import Path

import pytest

from app.calibration import CalibrationRepository, CalibrationRunCreate
from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository


def test_calibration_catalog_is_seeded(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    tests = repository.list_tests()
    keys = {test.test_key for test in tests}

    assert "homing_endstops" in keys
    assert "quad_gantry_level" in keys
    assert "probe_accuracy_center" in keys
    assert "bed_mesh_regular" in keys
    assert "input_shaper" in keys
    assert len(tests) >= 10


def test_calibration_catalog_is_read_only_and_classified(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    qgl = repository.get_test("quad_gantry_level")

    assert qgl is not None
    assert qgl.execution_mode == "gcode_review_required"
    assert qgl.risk_level == "medium"
    assert qgl.blocked_while_printing is True
    assert "QUAD_GANTRY_LEVEL" in qgl.gcode


def test_calibration_catalog_can_filter_by_category(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    tests = repository.list_tests("qualidade")

    assert tests
    assert {test.category for test in tests} == {"qualidade"}


def test_create_calibration_run_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)

    run = repository.create_run(
        printer.id,
        CalibrationRunCreate(
            test_key="probe_accuracy_center",
            result_status="passed",
            material="PLA",
            plate_name="Texturizada",
            nozzle="T0",
            observed_value="range 0.0125",
            notes="Probe repetível após ajuste mecânico.",
            gcode_reviewed=True,
        ),
    )

    assert run.printer_id == printer.id
    assert run.test_title == "Probe Accuracy no centro"
    assert run.result_status == "passed"
    assert run.gcode_reviewed is True
    assert len(repository.list_runs(printer.id)) == 1


def test_calibration_run_requires_existing_test(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)

    with pytest.raises(ValueError, match="calibration test not found"):
        repository.create_run(
            printer.id,
            CalibrationRunCreate(test_key="missing", result_status="failed"),
        )
