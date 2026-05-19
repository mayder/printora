from app.operation import (
    build_offline_fixture_operation,
    build_operation_query_objects,
    build_operation_status,
    build_unreachable_operation,
)


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


def test_unreachable_operation_blocks_actions() -> None:
    result = build_unreachable_operation("http://voron.local:7125", "connection failed")

    assert result["connected"] is False
    assert result["data_state"] == "offline"
    assert result["can_send_commands"] is False
    assert result["temperatures"] == []


def test_offline_fixture_populates_panels_without_enabling_commands() -> None:
    result = build_offline_fixture_operation()

    assert result["data_state"] == "fixture"
    assert result["connected"] is False
    assert result["can_send_commands"] is False
    assert result["temperatures"]
    assert result["miscellaneous"]["fans"]
    assert result["toolhead"]["homed_axes"] == "xyz"
