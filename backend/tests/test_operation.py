from app.operation import (
    build_last_known_operation,
    build_offline_fixture_operation,
    build_operation_action_preflight,
    build_operation_action_preview,
    build_operation_actions,
    build_operation_capabilities,
    build_operation_query_objects,
    build_operation_status,
    build_temperature_history,
    build_unreachable_operation,
)
from app.snapshots import SnapshotDetail


def test_operation_query_objects_adds_only_discovered_optional_objects() -> None:
    objects = build_operation_query_objects(["fan", "heater_fan hotend_fan", "temperature_sensor raspberry_pi"])

    assert objects["fan"] == ["speed", "rpm"]
    assert objects["heater_fan hotend_fan"] == ["speed", "rpm"]
    assert objects["temperature_sensor raspberry_pi"] == ["temperature", "target", "power"]


def test_operation_status_is_read_only_and_groups_mainsail_like_panels() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready", "moonraker_version": "v0.10.0"},
        system_info={"system_info": {"cpu_info": {"cpu_desc": "Raspberry Pi"}, "memory": {"available": 1234}}},
        proc_stats={"cpu_temp": 44.5, "system_load": 0.42},
        history_totals={"job_totals": {"total_print_time": 44100}},
        objects={
            "status": {
                "print_stats": {"state": "standby", "filename": "", "filament_used": 0},
                "toolhead": {"position": [1, 2, 3, 0], "homed_axes": "xyz", "max_velocity": 300},
                "gcode_move": {"speed_factor": 1.0, "extrude_factor": 0.95},
                "extruder": {"temperature": 210.5, "target": 215, "pressure_advance": 0.04},
                "heater_bed": {"temperature": 60.1, "target": 60},
                "fan": {"speed": 0.75, "rpm": 4200},
            }
        },
    )

    assert result["safe_mode"] == "read_only"
    assert result["can_send_commands"] is False
    assert result["summary"] == "Operação read-only carregada. Klipper: ready."
    assert len(result["system_loads"]) >= 4
    assert {row["name"] for row in result["temperatures"]} == {"Extruder", "Heater Bed"}
    assert result["toolhead"]["homed_axes"] == "xyz"
    assert result["extruder"]["extrusion_factor"] == 0.95
    assert result["miscellaneous"]["fans"][0]["name"] == "Fan"
    assert result["miscellaneous"]["total_print_hours"] == 12.25
    assert result["actions"][0]["enabled"] is False
    assert result["actions"][0]["confirmation_required"] is True
    assert result["capabilities"]


def test_unreachable_operation_blocks_actions() -> None:
    result = build_unreachable_operation("http://voron.local:7125", "connection failed")

    assert result["connected"] is False
    assert result["data_state"] == "offline"
    assert result["can_send_commands"] is False
    assert result["temperatures"] == []
    assert result["actions"][0]["block_reason"] == "Bloqueado: exige leitura ao vivo do Moonraker."


def test_offline_fixture_populates_panels_without_enabling_commands() -> None:
    result = build_offline_fixture_operation()

    assert result["data_state"] == "fixture"
    assert result["connected"] is False
    assert result["can_send_commands"] is False
    assert result["temperatures"]
    assert result["miscellaneous"]["fans"]
    assert result["toolhead"]["homed_axes"] == "xyz"
    assert result["actions"][0]["block_reason"] == "Bloqueado: exige leitura ao vivo do Moonraker."


def test_last_known_operation_uses_snapshot_payload() -> None:
    snapshot = SnapshotDetail(
        id=42,
        printer_id=1,
        created_at="2026-05-19 09:30:00",
        snapshot_type="moonraker_status",
        summary={},
        payload={
            "moonraker_url": "http://voron.local:7125",
            "printer_info": {"state": "ready"},
            "server_info": {"klippy_connected": True, "klippy_state": "ready", "moonraker_version": "v0.10.0"},
            "system_info": {"system_info": {"cpu_info": {"cpu_desc": "Raspberry Pi"}}},
            "proc_stats": {"cpu_temp": 43.2},
            "operation_objects": {
                "status": {
                    "toolhead": {"position": [10, 20, 30, 0], "homed_axes": "xyz"},
                    "extruder": {"temperature": 25, "target": 0},
                    "fan": {"speed": 0.4, "rpm": 2200},
                }
            },
        },
    )

    result = build_last_known_operation(snapshot)

    assert result["data_state"] == "last_snapshot"
    assert result["connected"] is False
    assert result["last_snapshot"]["id"] == 42
    assert result["toolhead"]["position"] == [10, 20, 30, 0]
    assert result["temperatures"][0]["name"] == "Extruder"
    assert result["miscellaneous"]["fans"][0]["rpm"] == 2200
    assert result["actions"][0]["block_reason"] == "Bloqueado: exige leitura ao vivo do Moonraker."


def test_last_known_operation_keeps_capabilities_from_snapshot_object_list() -> None:
    snapshot = SnapshotDetail(
        id=43,
        printer_id=1,
        created_at="2026-05-19 09:31:00",
        snapshot_type="moonraker_status",
        summary={},
        payload={
            "printer_info": {"state": "ready"},
            "server_info": {"klippy_connected": True, "klippy_state": "ready"},
            "system_info": {},
            "proc_stats": {},
            "operation_objects": {
                "objects": ["extruder", "heater_bed", "quad_gantry_level", "neopixel status_led"],
                "status": {"extruder": {}, "heater_bed": {}, "neopixel status_led": {}},
            },
        },
    )

    capabilities = {item["action_id"]: item["status"] for item in build_last_known_operation(snapshot)["capabilities"]}

    assert capabilities["quad_gantry_level"] == "supported"
    assert capabilities["set_led"] == "supported"
    assert capabilities["set_fan"] == "unknown"


def test_temperature_history_uses_snapshot_order_and_host_fallback() -> None:
    first = SnapshotDetail(
        id=1,
        printer_id=1,
        created_at="2026-05-19 09:00:00",
        snapshot_type="moonraker_status",
        summary={},
        payload={
            "proc_stats": {"cpu_temp": 44.0},
            "operation_objects": {
                "status": {
                    "extruder": {"temperature": 25.0, "target": 0},
                    "heater_bed": {"temperature": 26.0, "target": 0},
                }
            },
        },
    )
    second = SnapshotDetail(
        id=2,
        printer_id=1,
        created_at="2026-05-19 10:00:00",
        snapshot_type="moonraker_status",
        summary={},
        payload={"proc_stats": {"cpu_temp": 45.5}},
    )

    history = build_temperature_history([second, first])

    assert [row["snapshot_id"] for row in history] == [1, 2]
    assert history[0]["readings"][0]["name"] == "Extruder"
    assert history[1]["readings"] == [{"name": "Host", "temperature": 45.5, "target": None}]


def test_operation_actions_block_printing_and_standby_differently() -> None:
    printing_actions = build_operation_actions(connected=True, print_state="printing")
    standby_actions = build_operation_actions(connected=True, print_state="standby")

    assert {action["id"] for action in standby_actions} >= {"home_xyz", "quad_gantry_level", "set_hotend_temp"}
    assert all(action["enabled"] is False for action in standby_actions)
    assert printing_actions[0]["block_reason"] == "Bloqueado: impressão em andamento."
    assert standby_actions[0]["block_reason"] == "Bloqueado: operação mutável ainda não implementada."
    assert "requer macro/comando QUAD_GANTRY_LEVEL" in next(action for action in standby_actions if action["id"] == "quad_gantry_level")["compatibility"]


def test_operation_action_preview_is_dry_run_only() -> None:
    preview = build_operation_action_preview(
        action_id="move_z",
        parameters={"distance_mm": 2, "feedrate": 900},
        connected=False,
        print_state="",
    )

    assert preview["safe_mode"] == "dry_run_only"
    assert preview["would_send_gcode"] is False
    assert preview["executable"] is False
    assert preview["command_preview"] == ["G91", "G0 Z2 F900", "G90"]
    assert preview["blockers"][0] == "Bloqueado: exige leitura ao vivo do Moonraker."


def test_operation_action_preview_normalizes_parameters() -> None:
    preview = build_operation_action_preview(
        action_id="move_xy",
        parameters={"axis": "E", "distance_mm": 500, "feedrate": 50},
        connected=False,
        print_state="",
    )

    assert preview["parameters"] == {"axis": "X", "distance_mm": 50, "feedrate": 600}
    assert preview["command_preview"] == ["G91", "G0 X50 F600", "G90"]


def test_led_preview_requires_generic_led_name() -> None:
    preview = build_operation_action_preview(
        action_id="set_led",
        parameters={"led_name": "case light! unsafe", "brightness_percent": 42},
        connected=False,
        print_state="",
    )

    assert preview["parameters"] == {"led_name": "caselightunsafe", "brightness_percent": 42}
    assert preview["command_preview"] == ["SET_LED LED=caselightunsafe WHITE=0.42"]
    assert "requer LED Klipper informado no parâmetro led_name" in preview["action"]["compatibility"]


def test_operation_capabilities_use_known_objects_without_assuming_voron() -> None:
    capabilities = build_operation_capabilities(
        {
            "objects": ["extruder", "heater_bed", "fan", "neopixel status_led"],
            "status": {"extruder": {}, "heater_bed": {}, "fan": {}, "neopixel status_led": {}},
        }
    )
    by_action = {item["action_id"]: item for item in capabilities}

    assert by_action["set_hotend_temp"]["status"] == "supported"
    assert by_action["set_bed_temp"]["status"] == "supported"
    assert by_action["set_fan"]["status"] == "supported"
    assert by_action["set_led"]["status"] == "supported"
    assert by_action["quad_gantry_level"]["status"] == "unknown"


def test_operation_action_preflight_uses_live_state_and_keeps_execution_blocked() -> None:
    preflight = build_operation_action_preflight(
        action_id="move_z",
        parameters={"distance_mm": 2, "feedrate": 900},
        preflight={
            "safe_mode": "read_only_preflight",
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
        },
        objects={"objects": ["toolhead"]},
    )

    assert preflight["safe_mode"] == "operation_action_preflight_read_only"
    assert preflight["command_preview"] == ["G91", "G0 Z2 F900", "G90"]
    assert preflight["capability"]["status"] == "supported"
    assert preflight["would_send_gcode"] is False
    assert preflight["can_execute"] is False
    assert preflight["executable"] is False
    assert preflight["blockers"] == ["Bloqueado: execução real de ação operacional ainda não implementada."]


def test_operation_action_preflight_blocks_missing_macro_and_printing() -> None:
    preflight = build_operation_action_preflight(
        action_id="quad_gantry_level",
        parameters={},
        preflight={
            "safe_mode": "read_only_preflight",
            "connected": True,
            "printing": True,
            "print_state": "printing",
            "klipper_state": "ready",
            "klippy_state": "ready",
        },
        objects={"objects": ["toolhead"]},
    )

    assert preflight["capability"]["status"] == "unknown"
    assert "Bloqueado: impressão em andamento." in preflight["blockers"]
    assert any("capacidade não confirmada" in blocker for blocker in preflight["blockers"])
    assert preflight["can_execute"] is False
