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
    operation_action_blocks_when_printing,
    operation_action_requires_step_up,
)
from app.routes.operation import _operation_status_timeout, _remote_gcode_failure_detail
from app.snapshots import SnapshotDetail


def test_operation_query_objects_adds_only_discovered_optional_objects() -> None:
    objects = build_operation_query_objects(["fan", "heater_fan hotend_fan", "temperature_sensor raspberry_pi", "output_pin caselight", "neopixel sb_leds"])

    assert objects["virtual_sdcard"] == ["progress", "file_position", "is_active"]
    assert objects["fan"] == ["speed", "rpm"]
    assert objects["heater_fan hotend_fan"] == ["speed", "rpm"]
    assert objects["temperature_sensor raspberry_pi"] == ["temperature", "target", "power"]
    assert objects["output_pin caselight"] == ["value"]
    assert objects["neopixel sb_leds"] == ["color_data"]


def test_operation_status_enables_controlled_operations_and_groups_mainsail_like_panels() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready", "moonraker_version": "v0.10.0"},
        system_info={"system_info": {"cpu_info": {"cpu_desc": "Raspberry Pi"}, "memory": {"available": 1234}}},
        proc_stats={"cpu_temp": 44.5, "system_load": 0.42},
        history_totals={"job_totals": {"total_print_time": 44100}},
        objects={
            "objects": ["fan", "fan_generic nevermore", "controller_fan controller_fan", "output_pin caselight", "neopixel display"],
            "status": {
                "print_stats": {"state": "standby", "filename": "", "filament_used": 0, "print_duration": 123, "info": {"current_layer": 4, "total_layer": 80}},
                "display_status": {"progress": 0.89},
                "virtual_sdcard": {"progress": 0.42, "file_position": 123456, "is_active": True},
                "toolhead": {"position": [1, 2, 3, 0], "homed_axes": "xyz", "max_velocity": 300, "axis_minimum": [0, 0, 0], "axis_maximum": [300, 300, 250]},
                "gcode_move": {"speed_factor": 1.0, "extrude_factor": 0.95},
                "extruder": {"temperature": 210.5, "target": 215, "pressure_advance": 0.04},
                "heater_bed": {"temperature": 60.1, "target": 60},
                "fan": {"speed": 0.75, "rpm": 4200},
                "fan_generic nevermore": {"speed": 0, "rpm": None},
                "controller_fan controller_fan": {"speed": 1, "rpm": None},
                "output_pin caselight": {"value": 0.25},
                "neopixel display": {"color_data": [[1, 0, 0, 0]]},
            }
        },
    )

    assert result["safe_mode"] == "operation_ready"
    assert result["can_send_commands"] is True
    assert result["summary"] == "Operação carregada. Klipper: ready."
    assert len(result["system_loads"]) >= 4
    assert {row["name"] for row in result["temperatures"]} == {"Extruder", "Heater Bed"}
    assert result["toolhead"]["homed_axes"] == "xyz"
    assert result["toolhead"]["axis_maximum"] == [300, 300, 250]
    assert result["extruder"]["extrusion_factor"] == 0.95
    fans = {item["object_name"]: item for item in result["miscellaneous"]["fans"]}
    assert fans["fan"]["name"] == "Fan"
    assert fans["fan"]["controllable"] is True
    assert fans["fan_generic nevermore"]["name"] == "Nevermore"
    assert fans["fan_generic nevermore"]["controllable"] is True
    assert fans["controller_fan controller_fan"]["name"] == "Controller Fan"
    assert fans["controller_fan controller_fan"]["controllable"] is False
    assert result["miscellaneous"]["outputs"] == [{"name": "Caselight", "object_name": "output_pin caselight", "value": 0.25, "controllable": True}]
    assert result["miscellaneous"]["leds"] == [{"name": "Display", "object_name": "neopixel display", "brightness": 1.0, "color": "#ff0000", "controllable": True}]
    assert result["miscellaneous"]["collection_state"] == "loaded"
    assert result["miscellaneous"]["missing_status_objects"] == []
    assert result["miscellaneous"]["total_print_hours"] == 12.25
    assert result["miscellaneous"]["print_duration"] == 123
    assert result["miscellaneous"]["progress"] == 0.89
    assert result["miscellaneous"]["progress_source"] == "display_status"
    assert result["miscellaneous"]["file_progress"] == 0.42
    assert result["miscellaneous"]["current_layer"] == 4
    assert result["miscellaneous"]["total_layers"] == 80
    assert result["actions"][0]["enabled"] is True
    assert result["actions"][0]["confirmation_required"] is True
    assert result["capabilities"]


def test_operation_status_enriches_print_metadata_and_keeps_display_progress() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready"},
        system_info={},
        proc_stats={},
        objects={
            "objects": ["print_stats", "display_status", "virtual_sdcard", "gcode_move"],
            "status": {
                "print_stats": {"state": "printing", "filename": "printora/calicat_PLA_31m5s.gcode", "print_duration": 600},
                "display_status": {"progress": 0.31},
                "virtual_sdcard": {"progress": 0.29, "file_position": 123456},
                "gcode_move": {"gcode_position": [187.89, 180.28, 6.18, 0]},
            },
        },
        print_metadata={
            "estimated_time": 3600,
            "slicer": "OrcaSlicer",
            "slicer_version": "2.3.0",
            "layer_height": 0.2,
            "first_layer_height": 0.2,
            "object_height": 38.8,
            "filament_total": 1321,
            "filament_weight_total": 9.57,
            "filament_type": "PLA",
            "printora_visuals": {
                "thumbnail": {"data_uri": "data:image/jpeg;base64,abc", "source": "moonraker_thumbnail", "width": 160, "height": 120},
                "layer_preview": {
                    "data_uri": "data:image/svg+xml;base64,def",
                    "source": "agent_gcode",
                    "current_layer": 31,
                    "total_layers": 194,
                    "scene": {"kind": "gcode_layer_scene", "printed": [[0, 0, 0.2, 10, 0, 0.2]], "current": [[0, 0, 6.2, 10, 10, 6.2]]},
                },
            },
        },
    )

    misc = result["miscellaneous"]
    assert misc["progress"] == 0.31
    assert misc["progress_source"] == "display_status"
    assert misc["file_progress"] == 0.29
    assert misc["file_position"] == 123456
    assert misc["estimated_time"] == 3600
    assert misc["remaining_time"] == 2556
    assert misc["current_layer"] == 31
    assert misc["total_layers"] == 194
    assert misc["layer_source"] == "metadata"
    assert misc["slicer"] == "OrcaSlicer"
    assert misc["filament_total"] == 1321
    assert misc["filament_weight_total"] == 9.57
    assert misc["filament_type"] == "PLA"
    assert misc["thumbnail"]["data_uri"].startswith("data:image/jpeg")
    assert misc["layer_preview"]["current_layer"] == 31
    assert misc["layer_preview"]["scene"]["printed"]


def test_operation_status_defers_layer_preview_until_material_progress() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready"},
        system_info={},
        proc_stats={},
        objects={
            "objects": ["print_stats", "display_status", "virtual_sdcard", "gcode_move"],
            "status": {
                "print_stats": {
                    "state": "printing",
                    "filename": "printora/deck.gcode",
                    "filament_used": 0,
                    "message": "QGL",
                    "info": {"current_layer": 55, "total_layer": 369},
                },
                "display_status": {"progress": 0},
                "virtual_sdcard": {"progress": 0.003, "file_position": 4200},
                "gcode_move": {"gcode_position": [187.89, 180.28, 9.9, 0]},
            },
        },
        print_metadata={
            "layer_height": 0.18,
            "first_layer_height": 0.3,
            "object_height": 66.89,
            "printora_visuals": {
                "thumbnail": {"data_uri": "data:image/jpeg;base64,abc", "source": "moonraker_thumbnail", "width": 160, "height": 120},
                "layer_preview": {"source": "agent_gcode", "current_layer": 55, "total_layers": 369},
            },
        },
    )

    misc = result["miscellaneous"]
    assert misc["current_layer"] is None
    assert misc["total_layers"] == 369
    assert misc["layer_source"] == "pre_print"
    assert misc["thumbnail"]["data_uri"].startswith("data:image/jpeg")
    assert misc["layer_preview"] is None


def test_operation_status_lists_idle_gcode_files_sorted_and_filtered() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready"},
        system_info={},
        proc_stats={},
        objects={
            "objects": ["print_stats", "display_status", "virtual_sdcard"],
            "status": {
                "print_stats": {"state": "standby", "filename": "", "filament_used": 0},
                "display_status": {"progress": 0},
                "virtual_sdcard": {"progress": 0, "file_position": 0},
            },
        },
        gcode_files=[
            {"filename": "old.gcode", "path": "folder/old.gcode", "size": 1024, "modified": 10, "layer_height": 0.2},
            {"filename": "notes.txt", "path": "folder/notes.txt", "size": 10, "modified": 30},
            {
                "filename": "new.gcode",
                "path": "folder/new.gcode",
                "size": 2048,
                "modified": 20,
                "estimated_time": 3600,
                "slicer": "OrcaSlicer",
                "slicer_version": "2.4.2",
                "object_height": 66.89,
                "nozzle_diameter": 0.6,
                "filament_total": 23145.18,
                "filament_type": ["PLA", "PLA"],
            },
        ],
    )

    files = result["miscellaneous"]["gcode_files"]
    assert [file["filename"] for file in files] == ["new.gcode", "old.gcode"]
    assert files[0]["path"] == "folder/new.gcode"
    assert files[0]["estimated_time"] == 3600
    assert files[0]["slicer"] == "OrcaSlicer"
    assert files[0]["slicer_version"] == "2.4.2"
    assert files[0]["object_height"] == 66.89
    assert files[0]["nozzle_diameter"] == 0.6
    assert files[0]["filament_total"] == 23145.18
    assert files[0]["filament_type"] == "PLA, PLA"


def test_operation_status_reports_detected_misc_objects_without_status() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready"},
        system_info={},
        proc_stats={},
        objects={
            "objects": ["toolhead", "extruder", "output_pin caselight", "fan_generic nevermore", "controller_fan controller_fan", "neopixel sb_leds"],
            "status": {
                "print_stats": {"state": "standby"},
                "toolhead": {},
                "extruder": {},
            },
        },
    )

    assert result["miscellaneous"]["fans"] == []
    assert result["miscellaneous"]["outputs"] == []
    assert result["miscellaneous"]["leds"] == []
    assert result["miscellaneous"]["collection_state"] == "objects_detected_without_status"
    assert result["miscellaneous"]["detected_objects"] == [
        "controller_fan controller_fan",
        "fan_generic nevermore",
        "neopixel sb_leds",
        "output_pin caselight",
    ]
    assert result["miscellaneous"]["missing_status_objects"] == [
        "controller_fan controller_fan",
        "fan_generic nevermore",
        "neopixel sb_leds",
        "output_pin caselight",
    ]
    capabilities = {item["action_id"]: item["status"] for item in result["capabilities"]}
    assert capabilities["set_output_pin"] == "supported"
    assert capabilities["set_fan"] == "supported"
    assert capabilities["set_led"] == "supported"


def test_operation_status_reports_missing_dynamic_object_list() -> None:
    result = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready"},
        system_info={},
        proc_stats={},
        objects={"status": {"print_stats": {"state": "standby"}, "toolhead": {}, "extruder": {}}},
    )

    assert result["miscellaneous"]["collection_state"] == "objects_not_reported"
    assert result["miscellaneous"]["detected_objects"] == []


def test_unreachable_operation_blocks_actions() -> None:
    result = build_unreachable_operation("http://voron.local:7125", "connection failed")

    assert result["connected"] is False
    assert result["data_state"] == "offline"
    assert result["can_send_commands"] is False
    assert result["temperatures"] == []
    assert result["actions"][0]["block_reason"] == "Bloqueado: exige leitura ao vivo do Moonraker."


def test_unreachable_operation_sanitizes_agent_timeout() -> None:
    result = build_unreachable_operation("agent", "504: timeout aguardando resposta do agente")

    assert result["error"] == "Agente sem resposta nesta leitura. Atualize novamente quando o serviço voltar a responder."
    assert "504" not in result["error"]


def test_unreachable_operation_explains_polling_queue_timeout() -> None:
    result = build_unreachable_operation(
        "agent",
        "timeout aguardando resposta do agente; job ficou enfileirado para polling porque o WebSocket não confirmou entrega",
    )

    assert result["error"] == "Agente online por heartbeat, mas sem confirmação do canal remoto nesta leitura. O job ficou enfileirado para polling."
    assert "timeout" not in result["error"].lower()


def test_operation_status_timeout_covers_agent_polling_window() -> None:
    settings = type("Settings", (), {"request_timeout_seconds": 5.0})()

    assert _operation_status_timeout(settings) == 25.0


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
    assert next(action for action in printing_actions if action["id"] == "set_fan")["block_reason"] == ""
    assert next(action for action in printing_actions if action["id"] == "set_output_pin")["block_reason"] == ""
    assert standby_actions[0]["block_reason"] == ""
    assert "requer macro/comando QUAD_GANTRY_LEVEL" in next(action for action in standby_actions if action["id"] == "quad_gantry_level")["compatibility"]


def test_low_risk_operation_actions_do_not_require_step_up_or_print_block() -> None:
    assert operation_action_requires_step_up("set_output_pin") is False
    assert operation_action_requires_step_up("set_fan") is False
    assert operation_action_blocks_when_printing("set_output_pin") is False
    assert operation_action_blocks_when_printing("move_z") is True


def test_operation_action_preview_keeps_gcode_blocked_when_offline() -> None:
    preview = build_operation_action_preview(
        action_id="move_z",
        parameters={"distance_mm": 2, "feedrate": 900},
        connected=False,
        print_state="",
    )

    assert preview["safe_mode"] == "operation_action_preview"
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


def test_operation_absolute_move_uses_axis_target_and_feedrate() -> None:
    preview = build_operation_action_preview(
        action_id="move_absolute",
        parameters={"axis": "Y", "position_mm": 123.4, "feedrate": 6000},
        connected=True,
        print_state="standby",
    )

    assert preview["parameters"] == {"axis": "Y", "position_mm": 123.4, "feedrate": 6000}
    assert preview["command_preview"] == ["G90", "G0 Y123.4 F6000"]
    assert preview["would_send_gcode"] is True


def test_operation_absolute_move_blocks_outside_live_axis_limits() -> None:
    preflight = build_operation_action_preflight(
        action_id="move_absolute",
        parameters={"axis": "X", "position_mm": 350, "feedrate": 6000},
        preflight={
            "safe_mode": "read_only_preflight",
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
            "object_status": {"toolhead": {"axis_minimum": [0, 0, 0], "axis_maximum": [300, 300, 250]}},
        },
        objects={"objects": ["toolhead"]},
    )

    assert preflight["can_execute"] is False
    assert "fora dos limites" in preflight["blockers"][0]


def test_operation_velocity_limit_preview_generates_klipper_command() -> None:
    preview = build_operation_action_preview(
        action_id="set_velocity_limit",
        parameters={"velocity": 320, "accel": 9000, "square_corner_velocity": 4},
        connected=True,
        print_state="standby",
    )

    assert preview["parameters"] == {"velocity": 320, "accel": 9000, "square_corner_velocity": 4}
    assert preview["command_preview"] == ["SET_VELOCITY_LIMIT VELOCITY=320 ACCEL=9000 SQUARE_CORNER_VELOCITY=4"]
    assert preview["would_send_gcode"] is True


def test_operation_pressure_advance_preview_generates_klipper_command() -> None:
    preview = build_operation_action_preview(
        action_id="set_pressure_advance",
        parameters={"advance": 0.052, "smooth_time": 0.04},
        connected=True,
        print_state="standby",
    )

    assert preview["parameters"] == {"advance": 0.052, "smooth_time": 0.04}
    assert preview["command_preview"] == ["SET_PRESSURE_ADVANCE ADVANCE=0.052 SMOOTH_TIME=0.04"]
    assert preview["would_send_gcode"] is True


def test_operation_save_config_preview_is_explicit_and_supervised() -> None:
    preview = build_operation_action_preview(
        action_id="save_config",
        parameters={},
        connected=True,
        print_state="standby",
    )

    assert preview["parameters"] == {}
    assert preview["command_preview"] == ["SAVE_CONFIG"]
    assert preview["would_send_gcode"] is True
    assert preview["action"]["risk"] == "restart_firmware"


def test_operation_failure_detail_prefers_moonraker_error_message() -> None:
    result = {
        "status": "failed",
        "detail": 'moonraker /printer/gcode/script: status 400',
        "results": [
            {
                "command": "SAVE_CONFIG",
                "accepted": False,
                "moonraker_response": {
                    "error": {
                        "message": "SAVE_CONFIG section 'extruder' option 'control' conflicts with included value",
                    },
                },
            },
        ],
    }

    assert _remote_gcode_failure_detail(result) == "SAVE_CONFIG section 'extruder' option 'control' conflicts with included value"


def test_operation_named_fan_preview_uses_set_fan_speed() -> None:
    preview = build_operation_action_preview(
        action_id="set_fan",
        parameters={"fan_name": "controller_fan nevermore", "speed_percent": 42},
        connected=True,
        print_state="standby",
    )

    assert preview["parameters"] == {"fan_name": "controller_fan nevermore", "speed_percent": 42}
    assert preview["command_preview"] == ["SET_FAN_SPEED FAN=nevermore SPEED=0.42"]
    assert preview["would_send_gcode"] is True


def test_output_pin_preview_uses_set_pin_and_allows_printing() -> None:
    preview = build_operation_action_preview(
        action_id="set_output_pin",
        parameters={"pin_name": "output_pin caselight", "value_percent": 25},
        connected=True,
        print_state="printing",
    )

    assert preview["parameters"] == {"pin_name": "output_pin caselight", "value_percent": 25}
    assert preview["command_preview"] == ["SET_PIN PIN=caselight VALUE=0.25"]
    assert preview["would_send_gcode"] is True
    assert preview["executable"] is True


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
            "objects": ["extruder", "heater_bed", "fan", "output_pin caselight", "neopixel status_led"],
            "status": {"extruder": {}, "heater_bed": {}, "fan": {}, "output_pin caselight": {}, "neopixel status_led": {}},
        }
    )
    by_action = {item["action_id"]: item for item in capabilities}

    assert by_action["set_hotend_temp"]["status"] == "supported"
    assert by_action["set_bed_temp"]["status"] == "supported"
    assert by_action["set_fan"]["status"] == "supported"
    assert by_action["set_output_pin"]["status"] == "supported"
    assert by_action["set_led"]["status"] == "supported"
    assert by_action["save_config"]["status"] == "supported"
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

    assert preflight["safe_mode"] == "operation_action_preflight"
    assert preflight["command_preview"] == ["G91", "G0 Z2 F900", "G90"]
    assert preflight["capability"]["status"] == "supported"
    assert preflight["would_send_gcode"] is True
    assert preflight["can_execute"] is True
    assert preflight["executable"] is True
    assert preflight["blockers"] == []


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


def test_operation_action_preflight_allows_output_pin_during_printing() -> None:
    preflight = build_operation_action_preflight(
        action_id="set_output_pin",
        parameters={"pin_name": "output_pin caselight", "value_percent": 25},
        preflight={
            "safe_mode": "read_only_preflight",
            "connected": True,
            "printing": True,
            "print_state": "printing",
            "klipper_state": "ready",
            "klippy_state": "ready",
        },
        objects={"objects": ["output_pin caselight"], "status": {"output_pin caselight": {"value": 0.25}}},
    )

    assert preflight["command_preview"] == ["SET_PIN PIN=caselight VALUE=0.25"]
    assert preflight["blockers"] == []
    assert preflight["can_execute"] is True
