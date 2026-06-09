from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agent_moonraker import agent_preflight_payload, calibration_capabilities_payload
from app.config import get_settings
from app.calibration import (
    CalibrationExecutionRequest,
    CalibrationRepository,
    CalibrationRunCreate,
    build_available_calibration_tests,
    build_calibration_execution_gate,
    build_calibration_preflight,
    _blocked_calibration_command,
)
from app.database import initialize_database
from app.main import app
from app.routes.calibration import _calibration_execution_results, _calibration_execution_timeout, _calibration_execution_wait_timeout
from app.printers import PrinterCreate, PrinterRepository


def test_calibration_catalog_is_seeded(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    tests = repository.list_tests()
    keys = {test.test_key for test in tests}

    assert "homing_endstops" in keys
    assert "quad_gantry_level" in keys
    assert "probe_accuracy_center" in keys
    assert "bed_mesh_regular" in keys
    assert "input_shaper" in keys
    assert "jog_xy_control" in keys
    assert "hotend_heat_control" in keys
    assert "part_fan_control" in keys
    assert "mechanical_preflight" in keys
    assert "pid_hotend" in keys
    assert "extruder_rotation_distance" in keys
    assert "temperature_tower" in keys
    assert "max_volumetric_speed" in keys
    assert "flow_rate_pass_1" in keys
    assert "retraction_tuning" in keys
    assert "dimensional_skew" in keys
    assert len(tests) >= 10


def test_pid_calibration_timeout_stays_below_gateway_limit(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    settings = type("Settings", (), {"request_timeout_seconds": 5.0})()

    pid_hotend = repository.get_test("pid_hotend")
    pid_bed = repository.get_test("pid_bed")

    assert pid_hotend is not None
    assert pid_bed is not None
    for test in (pid_hotend, pid_bed):
        command_timeout = _calibration_execution_timeout(test, settings)
        wait_timeout = _calibration_execution_wait_timeout(test, settings, command_timeout)
        assert command_timeout == 65.0
        assert wait_timeout == 75.0


def test_calibration_catalog_is_read_only_and_classified(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    qgl = repository.get_test("quad_gantry_level")

    assert qgl is not None
    assert qgl.execution_mode == "gcode_review_required"
    assert qgl.risk_level == "medium"
    assert qgl.blocked_while_printing is True
    assert "QUAD_GANTRY_LEVEL" in qgl.gcode


def test_calibration_catalog_can_filter_by_category(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    tests = repository.list_tests("qualidade")

    assert tests
    assert {test.category for test in tests} == {"qualidade"}


def test_create_calibration_run_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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


def test_calibration_run_requires_gcode_review_for_gcode_tests(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)

    with pytest.raises(ValueError, match="gcode_reviewed is required"):
        repository.create_run(
            printer.id,
            CalibrationRunCreate(
                test_key="probe_accuracy_center",
                result_status="passed",
                gcode_reviewed=False,
            ),
        )


def test_calibration_summary_recommends_unpassed_tests(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)
    repository.create_run(
        printer.id,
        CalibrationRunCreate(
            test_key="homing_endstops",
            result_status="passed",
            gcode_reviewed=True,
        ),
    )

    summary = repository.summary(printer.id)

    assert summary.safe_mode == "manual_read_only"
    assert summary.catalog_count >= 10
    assert summary.run_count == 1
    assert summary.result_counts["passed"] == 1
    assert summary.blocked_while_printing_count >= 1
    assert all(item["test_key"] != "homing_endstops" for item in summary.recommended_next_tests)


def test_calibration_sequence_plan_marks_completed_and_pending_steps(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)
    repository.create_run(
        printer.id,
        CalibrationRunCreate(
            test_key="homing_endstops",
            result_status="passed",
            gcode_reviewed=True,
        ),
    )

    plan = repository.sequence_plan(printer.id)

    assert plan.safe_mode == "manual_sequence_no_gcode"
    assert plan.completed_steps == 1
    assert plan.total_steps >= 10
    completed = [step for step in plan.steps if step.status == "completed"]
    pending = [step for step in plan.steps if step.status == "pending"]
    assert completed[0].test_key == "homing_endstops"
    assert pending
    assert all(step.phase for step in plan.steps)


def test_calibration_sequence_plan_marks_skipped_without_recommending_it(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)
    repository.create_run(
        printer.id,
        CalibrationRunCreate(
            test_key="mechanical_preflight",
            result_status="skipped",
            notes="Operador decidiu pular nesta rodada.",
        ),
    )

    plan = repository.sequence_plan(printer.id)
    summary = repository.summary(printer.id)

    skipped = [step for step in plan.steps if step.status == "skipped"]
    assert skipped[0].test_key == "mechanical_preflight"
    assert plan.completed_steps == 1
    assert all(item["test_key"] != "mechanical_preflight" for item in summary.recommended_next_tests)


def test_available_calibration_tests_hide_qgl_when_printer_does_not_support_it(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    response = build_available_calibration_tests(
        printer_id=1,
        tests=repository.list_tests(),
        available_objects=["toolhead", "probe", "bed_mesh", "print_stats"],
        connected=True,
    )

    visible_keys = {test.test_key for test in response.tests}
    hidden_keys = {test.test_key for test in response.hidden_tests}
    assert "quad_gantry_level" not in visible_keys
    assert "bed_mesh_regular" not in visible_keys
    assert "quad_gantry_level" in hidden_keys
    assert "bed_mesh_regular" in hidden_keys
    assert "probe_accuracy_center" in visible_keys


def test_available_calibration_tests_include_qgl_when_printer_supports_it(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    response = build_available_calibration_tests(
        printer_id=1,
        tests=repository.list_tests(),
        available_objects=["toolhead", "probe", "bed_mesh", "quad_gantry_level", "print_stats"],
        connected=True,
    )

    visible_keys = {test.test_key for test in response.tests}
    assert "quad_gantry_level" in visible_keys
    assert "bed_mesh_regular" in visible_keys


def test_calibration_capabilities_keeps_connected_when_optional_toolhead_query_fails() -> None:
    objects, object_status, connected = calibration_capabilities_payload(
        {
            "objects_list": ["toolhead", "probe", "bed_mesh", "quad_gantry_level", "print_stats"],
            "toolhead_error": "query failed",
        }
    )

    assert connected is True
    assert "toolhead" in objects
    assert object_status == {}


def test_calibration_capabilities_uses_toolhead_status_as_object_source() -> None:
    objects, object_status, connected = calibration_capabilities_payload(
        {
            "toolhead": {
                "result": {
                    "status": {
                        "toolhead": {"axis_minimum": [0, 0, 0], "axis_maximum": [350, 350, 350]},
                    }
                }
            }
        }
    )

    assert connected is True
    assert objects == ["toolhead"]
    assert object_status["toolhead"]["axis_maximum"] == [350, 350, 350]


def test_available_calibration_tests_hide_gcode_outside_printer_volume(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    response = build_available_calibration_tests(
        printer_id=1,
        tests=repository.list_tests(),
        available_objects=["toolhead", "probe", "print_stats"],
        object_status={"toolhead": {"axis_minimum": [0, 0, 0], "axis_maximum": [120, 120, 120]}},
        connected=True,
    )

    visible_keys = {test.test_key for test in response.tests}
    hidden = {test.test_key: test.reason for test in response.hidden_tests}
    assert "probe_accuracy_center" not in visible_keys
    assert hidden["probe_accuracy_center"] == "Coordenada X175 fora do volume configurado da impressora."


def test_calibration_preflight_never_releases_gcode_execution(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("probe_accuracy_center")
    assert test is not None

    preflight = build_calibration_preflight(
        printer_id=1,
        test=test,
        preflight={
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "available_objects": ["toolhead", "probe", "print_stats"],
        },
    )

    assert preflight.safe_mode == "read_only_calibration_preflight"
    assert preflight.data_state == "live"
    assert preflight.can_execute_gcode is True
    assert preflight.blocked is False
    assert preflight.block_reasons == []
    assert preflight.gcode_preview == test.gcode


def test_agent_calibration_preflight_exposes_live_capabilities(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("homing_endstops")
    assert test is not None

    preflight_payload = agent_preflight_payload(
        {
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "objects_list": ["print_stats", "toolhead", "gcode_move"],
            "object_status": {
                "result": {
                    "status": {
                        "print_stats": {"state": "standby"},
                        "toolhead": {"axis_minimum": [0, 0, 0], "axis_maximum": [120, 120, 120]},
                    }
                }
            },
        }
    )

    preflight = build_calibration_preflight(printer_id=1, test=test, preflight=preflight_payload)

    assert preflight.connected is True
    assert preflight.blocked is False
    assert preflight.can_execute_gcode is True


def test_calibration_preflight_blocks_while_printing(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("quad_gantry_level")
    assert test is not None

    preflight = build_calibration_preflight(
        printer_id=1,
        test=test,
        preflight={
            "connected": True,
            "printing": True,
            "print_state": "printing",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "available_objects": ["toolhead", "quad_gantry_level", "print_stats"],
        },
    )

    assert preflight.blocked is True
    assert "Teste bloqueado porque a impressora está imprimindo." in preflight.block_reasons
    assert preflight.printing is True


def test_calibration_summary_endpoint_is_local_only_with_offline_printer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
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

            response = client.get(f"/api/printers/{printer_id}/calibration/summary")

        assert response.status_code == 200
        assert response.json()["safe_mode"] == "manual_read_only"
        assert response.json()["catalog_count"] >= 10
    finally:
        get_settings.cache_clear()


def test_calibration_preflight_endpoint_is_read_only_with_offline_printer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_REQUEST_TIMEOUT_SECONDS", "0.05")
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
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

            response = client.get(f"/api/printers/{printer_id}/calibration/tests/probe_accuracy_center/preflight")

        assert response.status_code == 200
        payload = response.json()
        assert payload["safe_mode"] == "read_only_calibration_preflight"
        assert payload["data_state"] == "offline"
        assert payload["can_execute_gcode"] is False
        assert payload["blocked"] is True
    finally:
        get_settings.cache_clear()


def test_calibration_execution_gate_requires_operator_review_and_confirmation(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("probe_accuracy_center")
    assert test is not None

    gate = build_calibration_execution_gate(
        test=test,
        payload=CalibrationExecutionRequest(
            test_key=test.test_key,
            confirmation="wrong",
            operator_present=False,
            gcode_reviewed=False,
        ),
        preflight={
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "available_objects": ["toolhead", "probe", "print_stats"],
        },
    )

    assert gate.status == "blocked"
    assert "Frase de confirmação inválida." in gate.block_reasons
    assert "Operador presente não confirmado." in gate.block_reasons
    assert "Revisão explícita do G-code não confirmada." in gate.block_reasons


def test_calibration_execution_gate_can_be_ready_for_supervised_gcode(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("probe_accuracy_center")
    assert test is not None

    gate = build_calibration_execution_gate(
        test=test,
        payload=CalibrationExecutionRequest(
            test_key=test.test_key,
            confirmation="EXECUTE_CALIBRATION_GCODE",
            operator_present=True,
            gcode_reviewed=True,
        ),
        preflight={
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "available_objects": ["toolhead", "probe", "print_stats"],
        },
    )

    assert gate.status == "ready"
    assert gate.block_reasons == []
    assert gate.commands == test.gcode


def test_calibration_execution_gate_allows_pid_calibrate_command(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("pid_hotend")
    assert test is not None

    gate = build_calibration_execution_gate(
        test=test,
        payload=CalibrationExecutionRequest(
            test_key=test.test_key,
            confirmation="EXECUTE_CALIBRATION_GCODE",
            operator_present=True,
            gcode_reviewed=True,
        ),
        preflight={
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "available_objects": ["toolhead", "print_stats", "extruder"],
        },
    )

    assert gate.status == "ready"
    assert gate.block_reasons == []
    assert gate.commands == ["PID_CALIBRATE HEATER=extruder TARGET=220"]


def test_calibration_execution_results_preserve_pid_console_excerpt() -> None:
    results = _calibration_execution_results(
        {
            "results": [{"command": "PID_CALIBRATE HEATER=extruder TARGET=220", "accepted": True}],
            "console_excerpt": [
                "PID parameters: pid_Kp=42.725 pid_Ki=11.393 pid_Kd=40.055",
                "The SAVE_CONFIG command will update the printer config file",
                "with these parameters and restart the printer.",
            ],
        }
    )

    console = results[-1]
    assert console["kind"] == "moonraker_console"
    assert console["save_config_required"] is True
    assert console["pid_parameters"] == {"pid_Kp": 42.725, "pid_Ki": 11.393, "pid_Kd": 40.055}


def test_all_catalogued_gcode_commands_are_allowlisted(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)

    blocked = {
        test.test_key: _blocked_calibration_command(test.gcode)
        for test in repository.list_tests()
        if test.gcode and _blocked_calibration_command(test.gcode)
    }

    assert blocked == {}


def test_calibration_preflight_blocks_commands_outside_allowlist(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = CalibrationRepository(database_path)
    test = repository.get_test("homing_endstops")
    assert test is not None
    unsafe_test = test.model_copy(update={"gcode": ["SAVE_CONFIG"]})

    preflight = build_calibration_preflight(
        printer_id=1,
        test=unsafe_test,
        preflight={
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "available_objects": ["toolhead", "print_stats"],
        },
    )

    assert preflight.blocked is True
    assert preflight.can_execute_gcode is False
    assert "Comando fora da allowlist segura: SAVE_CONFIG." in preflight.block_reasons


def test_calibration_execution_attempt_persists_blocked_gate(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)
    test = repository.get_test("probe_accuracy_center")
    assert test is not None
    gate = build_calibration_execution_gate(
        test=test,
        payload=CalibrationExecutionRequest(test_key=test.test_key),
        preflight={"connected": False, "printing": False, "print_state": ""},
    )

    record = repository.create_execution_attempt(
        printer_id=printer.id,
        test=test,
        gate=gate,
        status="blocked",
        sent_commands=[],
        result=[],
        message=gate.message,
    )

    assert record.status == "blocked"
    assert record.sent_commands == []
    assert record.commands == test.gcode
    assert len(repository.list_execution_attempts(printer.id)) == 1


def test_calibration_execution_delete_keeps_latest_attempt(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)
    test = repository.get_test("probe_accuracy_center")
    assert test is not None
    gate = build_calibration_execution_gate(
        test=test,
        payload=CalibrationExecutionRequest(test_key=test.test_key),
        preflight={"connected": False, "printing": False, "print_state": ""},
    )
    first = repository.create_execution_attempt(
        printer_id=printer.id,
        test=test,
        gate=gate,
        status="blocked",
        sent_commands=[],
        result=[],
        message="first",
    )
    latest = repository.create_execution_attempt(
        printer_id=printer.id,
        test=test,
        gate=gate,
        status="blocked",
        sent_commands=[],
        result=[],
        message="latest",
    )

    assert repository.delete_execution_attempt_if_not_latest(printer.id, first.id) is True
    assert repository.get_execution_attempt(first.id) is None
    with pytest.raises(ValueError, match="última execução"):
        repository.delete_execution_attempt_if_not_latest(printer.id, latest.id)
    assert repository.get_execution_attempt(latest.id) is not None


def test_calibration_run_delete_keeps_latest_result(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CalibrationRepository(database_path)
    first = repository.create_run(
        printer.id,
        CalibrationRunCreate(
            test_key="probe_accuracy_center",
            result_status="passed",
            observed_value="first",
            gcode_reviewed=True,
        ),
    )
    latest = repository.create_run(
        printer.id,
        CalibrationRunCreate(
            test_key="probe_accuracy_center",
            result_status="passed",
            observed_value="latest",
            gcode_reviewed=True,
        ),
    )

    assert repository.delete_run_if_not_latest(printer.id, first.id) is True
    assert repository.get_run(first.id) is None
    with pytest.raises(ValueError, match="último resultado"):
        repository.delete_run_if_not_latest(printer.id, latest.id)
    assert repository.get_run(latest.id) is not None


def test_calibration_execute_endpoint_blocks_offline_without_sending_gcode(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_REQUEST_TIMEOUT_SECONDS", "0.05")
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
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

            response = client.post(
                f"/api/printers/{printer_id}/calibration/execute",
                json={
                    "test_key": "probe_accuracy_center",
                    "confirmation": "EXECUTE_CALIBRATION_GCODE",
                    "operator_present": True,
                    "gcode_reviewed": True,
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "blocked"
        assert payload["sent_commands"] == []
        assert "Moonraker/Klipper sem leitura ao vivo." in payload["block_reasons"]
    finally:
        get_settings.cache_clear()


def test_calibration_execute_endpoint_sends_gcode_when_gate_is_ready(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    calls: list[dict] = []

    async def fake_run(self, printer, *, job_type, payload=None, timeout_seconds=12.0, require_online=True):
        calls.append({"job_type": job_type, "payload": payload})
        if job_type == "remote_gcode_preflight":
            return type(
                "Job",
                (),
                {
                    "result": {
                        "connected": True,
                        "printing": False,
                        "print_state": "standby",
                        "klipper_state": "ready",
                        "klippy_state": "ready",
                        "objects_list": ["toolhead", "print_stats"],
                    }
                },
            )()
        return type("Job", (), {"result": {"sent_commands": ["G28"], "results": [{"accepted": True}]}})()

    monkeypatch.setattr("app.routes.calibration.AgentCommandExecutor.run", fake_run)
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://voron.local:7125",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200
            printer_id = created.json()["id"]

            response = client.post(
                f"/api/printers/{printer_id}/calibration/execute",
                json={
                    "test_key": "homing_endstops",
                    "confirmation": "EXECUTE_CALIBRATION_GCODE",
                    "operator_present": True,
                    "gcode_reviewed": True,
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "executed"
        assert payload["sent_commands"] == ["G28"]
        assert calls[-1]["job_type"] == "remote_gcode_execute"
        assert calls[-1]["payload"]["action_id"] == "calibration:homing_endstops"
        assert calls[-1]["payload"]["commands"] == ["G28"]
        assert calls[-1]["payload"]["timeout_seconds"] == 45.0
    finally:
        get_settings.cache_clear()


def test_calibration_execute_endpoint_preserves_dispatched_unconfirmed_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    async def fake_run(self, printer, *, job_type, payload=None, timeout_seconds=12.0, require_online=True):
        if job_type == "remote_gcode_preflight":
            return type(
                "Job",
                (),
                {
                    "result": {
                        "connected": True,
                        "printing": False,
                        "print_state": "standby",
                        "klipper_state": "ready",
                        "klippy_state": "ready",
                        "objects_list": ["toolhead", "print_stats"],
                    }
                },
            )()
        return type(
            "Job",
            (),
            {
                "result": {
                    "status": "dispatched_unconfirmed",
                    "sent_commands": ["G28"],
                    "results": [{"command": "G28", "accepted": True, "confirmation": "timeout_awaiting_headers"}],
                }
            },
        )()

    monkeypatch.setattr("app.routes.calibration.AgentCommandExecutor.run", fake_run)
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://voron.local:7125",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200
            printer_id = created.json()["id"]

            response = client.post(
                f"/api/printers/{printer_id}/calibration/execute",
                json={
                    "test_key": "homing_endstops",
                    "confirmation": "EXECUTE_CALIBRATION_GCODE",
                    "operator_present": True,
                    "gcode_reviewed": True,
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "dispatched_unconfirmed"
        assert payload["sent_commands"] == ["G28"]
        assert "despachado" in payload["message"]
    finally:
        get_settings.cache_clear()


def test_calibration_execute_endpoint_blocks_immediate_duplicate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    execute_calls = 0

    async def fake_run(self, printer, *, job_type, payload=None, timeout_seconds=12.0, require_online=True):
        nonlocal execute_calls
        if job_type == "remote_gcode_preflight":
            return type(
                "Job",
                (),
                {
                    "result": {
                        "connected": True,
                        "printing": False,
                        "print_state": "standby",
                        "klipper_state": "ready",
                        "klippy_state": "ready",
                        "objects_list": ["toolhead", "print_stats"],
                    }
                },
            )()
        execute_calls += 1
        return type(
            "Job",
            (),
            {
                "result": {
                    "status": "executed",
                    "sent_commands": ["G28"],
                    "results": [{"command": "G28", "accepted": True}],
                }
            },
        )()

    monkeypatch.setattr("app.routes.calibration.AgentCommandExecutor.run", fake_run)
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://voron.local:7125",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200
            printer_id = created.json()["id"]
            body = {
                "test_key": "homing_endstops",
                "confirmation": "EXECUTE_CALIBRATION_GCODE",
                "operator_present": True,
                "gcode_reviewed": True,
            }

            first = client.post(f"/api/printers/{printer_id}/calibration/execute", json=body)
            second = client.post(f"/api/printers/{printer_id}/calibration/execute", json=body)

        assert first.status_code == 200
        assert first.json()["status"] == "executed"
        assert second.status_code == 200
        assert second.json()["status"] == "blocked"
        assert second.json()["sent_commands"] == []
        assert "repetida bloqueada" in second.json()["message"]
        assert execute_calls == 1
    finally:
        get_settings.cache_clear()


def test_calibration_run_requires_existing_test(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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
