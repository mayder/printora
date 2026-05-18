from pathlib import Path

from app.calibration import CalibrationRepository
from app.database import initialize_database


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
