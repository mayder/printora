import math
from typing import Any


OPERATION_OBJECTS: dict[str, list[str]] = {
    "webhooks": ["state", "state_message"],
    "print_stats": ["state", "filename", "total_duration", "print_duration", "filament_used", "message", "current_layer", "total_layer", "info"],
    "display_status": ["progress", "message"],
    "virtual_sdcard": ["progress", "file_position", "is_active"],
    "toolhead": ["position", "homed_axes", "max_velocity", "max_accel", "estimated_print_time", "axis_minimum", "axis_maximum"],
    "gcode_move": ["gcode_position", "speed_factor", "extrude_factor"],
    "extruder": ["temperature", "target", "power", "pressure_advance", "smooth_time"],
    "heater_bed": ["temperature", "target", "power"],
}

LED_OBJECT_PREFIXES = ("led ", "neopixel ", "dotstar ", "pca9533 ", "pca9632 ")
OPTIONAL_OPERATION_OBJECT_PREFIXES = (
    "fan",
    "fan_generic ",
    "heater_fan ",
    "controller_fan ",
    "temperature_sensor ",
    "heater_generic ",
    "output_pin ",
    *LED_OBJECT_PREFIXES,
)
LOW_RISK_OPERATION_ACTIONS = {"set_fan", "set_led", "set_output_pin"}
MAX_OPERATION_GCODE_FILES = 20
GCODE_FILE_EXTENSIONS = (".gcode", ".gcode.gz", ".gco", ".g", ".gc", ".nc", ".ngc", ".tap")


def operation_action_requires_step_up(action_id: str) -> bool:
    return action_id not in LOW_RISK_OPERATION_ACTIONS


def operation_action_blocks_when_printing(action_id: str) -> bool:
    return action_id not in LOW_RISK_OPERATION_ACTIONS


def build_operation_query_objects(available_objects: list[str]) -> dict[str, list[str]]:
    objects = dict(OPERATION_OBJECTS)
    for name in available_objects:
        if name in objects:
            continue
        if name.startswith(("temperature_sensor ", "heater_generic ")):
            objects[name] = ["temperature", "target", "power"]
        elif name == "fan" or name.startswith(("fan ", "fan_generic ", "heater_fan ", "controller_fan ")):
            objects[name] = ["speed", "rpm"]
        elif name.startswith("output_pin "):
            objects[name] = ["value"]
        elif name.startswith(LED_OBJECT_PREFIXES):
            objects[name] = ["color_data"]
    return objects


def build_operation_status(
    *,
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
    objects: dict[str, Any],
    history_totals: dict[str, Any] | None = None,
    print_metadata: dict[str, Any] | None = None,
    gcode_files: list[Any] | None = None,
) -> dict[str, Any]:
    status = _object_status(objects)
    print_state = _text(_nested(status, ["print_stats", "state"]))
    klipper_state = _text(printer_info.get("state") or _nested(status, ["webhooks", "state"]))
    connected = bool(server_info.get("klippy_connected", True))

    return {
        "safe_mode": "operation_ready",
        "data_state": "live",
        "connected": connected,
        "summary": _summary(connected, klipper_state, print_state),
        "can_send_commands": connected and klipper_state == "ready",
        "system_loads": _system_loads(server_info, system_info, proc_stats),
        "temperatures": _temperatures(status),
        "temperature_history": [],
        "actions": build_operation_actions(connected=connected, print_state=print_state, objects=objects),
        "capabilities": build_operation_capabilities(objects),
        "toolhead": _toolhead(status),
        "extruder": _extruder(status),
        "miscellaneous": {
            **_miscellaneous(objects, print_metadata, gcode_files),
            "total_print_hours": _total_print_hours(history_totals),
        },
    }


def build_unreachable_operation(moonraker_url: str, error: str) -> dict[str, Any]:
    return {
        "safe_mode": "read_only",
        "data_state": "offline",
        "connected": False,
        "moonraker_url": moonraker_url,
        "summary": "Impressora desligada ou Moonraker indisponível.",
        "error": _unreachable_error_message(error),
        "can_send_commands": False,
        "system_loads": [],
        "temperatures": [],
        "temperature_history": [],
        "actions": build_operation_actions(connected=False, print_state=""),
        "capabilities": build_operation_capabilities({}),
        "toolhead": {},
        "extruder": {},
        "miscellaneous": {},
    }


def _unreachable_error_message(error: str) -> str:
    message = str(error or "").strip()
    if message[:3].isdigit() and ":" in message[:5]:
        message = message.split(":", 1)[1].strip()
    lower = message.lower()
    if "ficou enfileirado para polling" in lower:
        return "Agente online por heartbeat, mas sem confirmação do canal remoto nesta leitura. O job ficou enfileirado para polling."
    if "aguardando o agente iniciar" in lower:
        return "Agente sem confirmação de início nesta leitura. Atualize novamente quando o canal remoto responder."
    if "aguardando o agente concluir" in lower:
        return "Agente iniciou a leitura, mas não concluiu dentro da janela desta atualização."
    if "timeout aguardando resposta do agente" in lower:
        return "Agente sem resposta nesta leitura. Atualize novamente quando o serviço voltar a responder."
    return message or "Sem leitura ao vivo do agente ou Moonraker."


def build_last_known_operation(snapshot) -> dict[str, Any]:
    payload = snapshot.payload
    operation = build_operation_status(
        printer_info=_dict(payload.get("printer_info")),
        server_info=_dict(payload.get("server_info")),
        system_info=_dict(payload.get("system_info")),
        proc_stats=_dict(payload.get("proc_stats")),
        objects=_dict(payload.get("operation_objects")),
    )
    operation.update(
        {
            "data_state": "last_snapshot",
            "connected": False,
            "can_send_commands": False,
            "summary": f"Último estado conhecido do snapshot {snapshot.created_at}.",
            "moonraker_url": payload.get("moonraker_url"),
            "actions": build_operation_actions(connected=False, print_state=""),
            "last_snapshot": {
                "id": snapshot.id,
                "created_at": snapshot.created_at,
                "snapshot_type": snapshot.snapshot_type,
            },
        }
    )
    return operation


def build_temperature_history(snapshots: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snapshot in reversed(snapshots):
        payload = _dict(getattr(snapshot, "payload", {}))
        readings = _snapshot_temperatures(payload)
        if not readings:
            continue
        rows.append(
            {
                "snapshot_id": getattr(snapshot, "id", None),
                "created_at": getattr(snapshot, "created_at", ""),
                "readings": readings,
            }
        )
    return rows


def build_operation_actions(*, connected: bool, print_state: str, objects: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    printing = print_state not in {"", "standby", "complete", "cancelled", "error"}
    capabilities = {item["action_id"]: item for item in build_operation_capabilities(objects or {})}
    rows: list[dict[str, Any]] = []
    for action in _operation_action_catalog():
        blocked_by_printing = printing and operation_action_blocks_when_printing(str(action["id"]))
        rows.append(
            {
                **action,
                "capability": capabilities.get(action["id"], {"status": "unknown", "reason": "Sem dados de objetos Klipper."}),
                "enabled": connected and not blocked_by_printing and capabilities.get(action["id"], {}).get("status") == "supported",
                "confirmation_required": True,
                "block_reason": _operation_action_block_reason(connected, blocked_by_printing),
            }
        )
    return rows


def build_operation_capabilities(objects: dict[str, Any]) -> list[dict[str, str]]:
    names = _object_names(objects)
    return [
        _capability(
            "home_xyz",
            "supported" if "toolhead" in names else "unknown",
            "Objeto toolhead detectado." if "toolhead" in names else "Homing depende da cinemática e endstops configurados.",
        ),
        _capability(
            "quad_gantry_level",
            "supported" if "quad_gantry_level" in names else "unknown",
            "Macro/comando QUAD_GANTRY_LEVEL detectado." if "quad_gantry_level" in names else "Não foi possível confirmar QUAD_GANTRY_LEVEL nos objetos conhecidos.",
        ),
        _capability(
            "move_xy",
            "supported" if "toolhead" in names else "unknown",
            "Objeto toolhead detectado." if "toolhead" in names else "Movimento XY depende da cinemática configurada.",
        ),
        _capability(
            "move_absolute",
            "supported" if "toolhead" in names else "unknown",
            "Objeto toolhead detectado." if "toolhead" in names else "Movimento absoluto depende da cinemática configurada.",
        ),
        _capability(
            "move_z",
            "supported" if "toolhead" in names else "unknown",
            "Objeto toolhead detectado." if "toolhead" in names else "Movimento Z depende do eixo Z configurado.",
        ),
        _capability(
            "extrude",
            "supported" if "extruder" in names else "unknown",
            "Objeto extruder detectado." if "extruder" in names else "Objeto extruder não detectado nos dados conhecidos.",
        ),
        _capability(
            "set_hotend_temp",
            "supported" if "extruder" in names else "unknown",
            "Heater extruder detectado." if "extruder" in names else "Heater extruder não detectado nos dados conhecidos.",
        ),
        _capability(
            "set_bed_temp",
            "supported" if "heater_bed" in names else "unknown",
            "Heater heater_bed detectado." if "heater_bed" in names else "Heater heater_bed não detectado nos dados conhecidos.",
        ),
        _capability(
            "set_fan",
            "supported" if any(_is_controllable_fan(name) for name in names) else "unknown",
            "Fan controlável detectado." if any(_is_controllable_fan(name) for name in names) else "Fan controlável não detectado nos dados conhecidos.",
        ),
        _capability(
            "set_output_pin",
            "supported" if any(name.startswith("output_pin ") for name in names) else "unknown",
            "Output pin detectado." if any(name.startswith("output_pin ") for name in names) else "Output pin controlável não detectado nos dados conhecidos.",
        ),
        _capability(
            "set_led",
            "supported" if any(name.startswith(("led ", "neopixel ", "dotstar ", "pca9533 ", "pca9632 ")) for name in names) else "unknown",
            "Objeto LED detectado." if any(name.startswith(("led ", "neopixel ", "dotstar ", "pca9533 ", "pca9632 ")) for name in names) else "LED exige nome real do objeto Klipper.",
        ),
        _capability(
            "set_speed_factor",
            "supported" if "gcode_move" in names else "unknown",
            "Objeto gcode_move detectado." if "gcode_move" in names else "Speed factor depende do estado gcode_move.",
        ),
        _capability(
            "set_velocity_limit",
            "supported" if "toolhead" in names else "unknown",
            "Objeto toolhead detectado." if "toolhead" in names else "Limites de velocidade dependem do toolhead.",
        ),
        _capability(
            "set_extrusion_factor",
            "supported" if "gcode_move" in names else "unknown",
            "Objeto gcode_move detectado." if "gcode_move" in names else "Extrusion factor depende do estado gcode_move.",
        ),
        _capability(
            "set_pressure_advance",
            "supported" if "extruder" in names else "unknown",
            "Objeto extruder detectado." if "extruder" in names else "Pressure advance depende do extrusor configurado.",
        ),
        _capability(
            "save_config",
            "supported" if "webhooks" in names or names else "unknown",
            "Klipper online; SAVE_CONFIG pode salvar printer.cfg e reiniciar o firmware." if "webhooks" in names or names else "SAVE_CONFIG exige Klipper online.",
        ),
    ]


def build_operation_action_preview(
    *,
    action_id: str,
    parameters: dict[str, Any] | None = None,
    connected: bool,
    print_state: str,
) -> dict[str, Any]:
    action = _operation_action(action_id)
    if action is None:
        raise ValueError("unknown operation action")
    printing = operation_action_blocks_when_printing(action_id) and print_state not in {"", "standby", "complete", "cancelled", "error"}
    clean_parameters = _normalize_action_parameters(action_id, parameters or {})
    executable = connected and not printing
    return {
        "safe_mode": "operation_action_preview",
        "action": {
            **action,
            "enabled": executable,
            "confirmation_required": True,
            "block_reason": _operation_action_block_reason(connected, printing),
        },
        "parameters": clean_parameters,
        "expected_parameters": _operation_action_parameters(action_id),
        "command_preview": _operation_action_commands(action_id, clean_parameters),
        "would_send_gcode": executable,
        "executable": executable,
        "confirmation_phrase": f"CONFIRM_{action_id.upper()}",
        "blockers": [] if executable else [_operation_action_block_reason(connected, printing)],
        "rollback_plan": "Ação operacional enviada por G-code. Para rollback, pare a impressora pelo Mainsail/Klipper se houver movimento inesperado e zere alvos/fans quando aplicável.",
    }


def build_operation_action_preflight(
    *,
    action_id: str,
    parameters: dict[str, Any] | None,
    preflight: dict[str, Any],
    objects: dict[str, Any],
) -> dict[str, Any]:
    preview = build_operation_action_preview(
        action_id=action_id,
        parameters=parameters,
        connected=bool(preflight.get("connected")),
        print_state=str(preflight.get("print_state") or ""),
    )
    capabilities = {item["action_id"]: item for item in build_operation_capabilities(objects)}
    capability = capabilities.get(action_id, _capability(action_id, "unknown", "Sem dados de objetos Klipper."))
    klipper_state = _text(preflight.get("klipper_state"))
    klippy_state = _text(preflight.get("klippy_state"))
    blockers = _operation_action_preflight_blockers(action_id, preflight, capability, klipper_state, klippy_state)
    axis_blocker = _axis_limit_blocker(action_id, preview["parameters"], preflight)
    if axis_blocker:
        blockers.append(axis_blocker)
    return {
        "safe_mode": "operation_action_preflight",
        "action": {
            **preview["action"],
            "capability": capability,
            "enabled": not blockers,
            "block_reason": blockers[0] if blockers else "",
        },
        "parameters": preview["parameters"],
        "expected_parameters": preview["expected_parameters"],
        "command_preview": preview["command_preview"],
        "preflight": preflight,
        "capability": capability,
        "would_send_gcode": not blockers,
        "executable": not blockers,
        "can_execute": not blockers,
        "confirmation_phrase": preview["confirmation_phrase"],
        "blockers": blockers,
        "rollback_plan": [
            "Ação operacional enviada por G-code via Moonraker.",
            "Se algo sair do esperado, use Emergency Stop no Mainsail/Klipper e zere alvos/fans quando aplicável.",
        ],
    }


def build_offline_fixture_operation() -> dict[str, Any]:
    fixture = build_operation_status(
        printer_info={"state": "ready"},
        server_info={"klippy_connected": True, "klippy_state": "ready", "moonraker_version": "v0.10.0"},
        system_info={
            "system_info": {
                "cpu_info": {"cpu_desc": "Raspberry Pi 4 Model B"},
                "memory": {"available": 1_734_000_000},
            },
            "disk": {"available": 18_400_000_000},
        },
        proc_stats={"cpu_temp": 47.8, "system_load": 0.32},
        objects={
            "status": {
                "print_stats": {"state": "standby", "filename": "", "filament_used": 0},
                "display_status": {"progress": 0, "message": "offline fixture"},
                "toolhead": {"position": [175.0, 175.0, 20.0, 0], "homed_axes": "xyz", "max_velocity": 300, "max_accel": 8000},
                "gcode_move": {"speed_factor": 1.0, "extrude_factor": 0.98},
                "extruder": {"temperature": 24.7, "target": 0, "power": 0, "pressure_advance": 0.04, "smooth_time": 0.04},
                "heater_bed": {"temperature": 25.1, "target": 0, "power": 0},
                "temperature_sensor raspberry_pi": {"temperature": 47.8, "target": 0, "power": 0},
                "fan": {"speed": 0, "rpm": 0},
                "heater_fan hotend_fan": {"speed": 0, "rpm": 0},
                "controller_fan nevermore": {"speed": 0, "rpm": None},
            }
        },
    )
    fixture.update(
        {
            "data_state": "fixture",
            "connected": False,
            "can_send_commands": False,
            "moonraker_url": "fixture://voron-offline",
            "summary": "Exemplo offline para validar a tela sem impressora ligada.",
            "actions": build_operation_actions(connected=False, print_state=""),
        }
    )
    return fixture


def _operation_action_catalog() -> list[dict[str, Any]]:
    return [
        {"id": "home_xyz", "group": "movimento", "label": "Home XYZ", "command": "G28", "risk": "move_toolhead", "compatibility": ["Klipper padrão com eixos configurados"]},
        {"id": "quad_gantry_level", "group": "movimento", "label": "QGL", "command": "QUAD_GANTRY_LEVEL", "risk": "move_toolhead", "compatibility": ["requer macro/comando QUAD_GANTRY_LEVEL"]},
        {"id": "move_xy", "group": "movimento", "label": "Mover XY", "command": "G0 X/Y", "risk": "move_toolhead", "compatibility": ["Klipper padrão com cinemática XY"]},
        {"id": "move_absolute", "group": "movimento", "label": "Mover posição", "command": "G0 X/Y/Z", "risk": "move_toolhead", "compatibility": ["Klipper padrão com cinemática configurada"]},
        {"id": "move_z", "group": "movimento", "label": "Mover Z", "command": "G0 Z", "risk": "move_z", "compatibility": ["Klipper padrão com eixo Z"]},
        {"id": "extrude", "group": "extrusão", "label": "Extrudar", "command": "G1 E", "risk": "extrude_filament", "compatibility": ["extrusor configurado", "hotend aquecido para extrusão real"]},
        {"id": "set_hotend_temp", "group": "temperatura", "label": "Hotend", "command": "SET_HEATER_TEMPERATURE HEATER=extruder", "risk": "heat_toolhead", "compatibility": ["heater chamado extruder"]},
        {"id": "set_bed_temp", "group": "temperatura", "label": "Mesa", "command": "SET_HEATER_TEMPERATURE HEATER=heater_bed", "risk": "heat_bed", "compatibility": ["heater chamado heater_bed"]},
        {"id": "set_fan", "group": "fan", "label": "Fan", "command": "M106/M107", "risk": "change_fan", "compatibility": ["fan de peça padrão M106/M107"]},
        {"id": "set_output_pin", "group": "led", "label": "Output pin", "command": "SET_PIN", "risk": "change_output_pin", "compatibility": ["output_pin PWM, como caselight"]},
        {"id": "set_led", "group": "led", "label": "LED", "command": "SET_LED", "risk": "change_led", "compatibility": ["requer LED Klipper informado no parâmetro led_name"]},
        {"id": "set_speed_factor", "group": "movimento", "label": "Speed factor", "command": "M220", "risk": "change_speed_factor", "compatibility": ["gcode_move disponível"]},
        {"id": "set_velocity_limit", "group": "movimento", "label": "Limites da máquina", "command": "SET_VELOCITY_LIMIT", "risk": "change_velocity_limit", "compatibility": ["toolhead disponível"]},
        {"id": "set_extrusion_factor", "group": "extrusão", "label": "Extrusion factor", "command": "M221", "risk": "change_extrusion_factor", "compatibility": ["gcode_move disponível"]},
        {"id": "set_pressure_advance", "group": "extrusão", "label": "Pressure advance", "command": "SET_PRESSURE_ADVANCE", "risk": "change_pressure_advance", "compatibility": ["extrusor configurado"]},
        {"id": "save_config", "group": "configuração", "label": "Salvar config", "command": "SAVE_CONFIG", "risk": "restart_firmware", "compatibility": ["Klipper SAVE_CONFIG", "reinicia o firmware após salvar"]},
    ]


def _operation_action(action_id: str) -> dict[str, Any] | None:
    return next((action for action in _operation_action_catalog() if action["id"] == action_id), None)


def _operation_action_parameters(action_id: str) -> list[dict[str, Any]]:
    parameters: dict[str, list[dict[str, Any]]] = {
        "move_xy": [
            {"name": "axis", "type": "enum", "values": ["X", "Y"], "default": "X"},
            {"name": "distance_mm", "type": "number", "default": 10, "min": -50, "max": 50},
            {"name": "feedrate", "type": "number", "default": 6000, "min": 600, "max": 12000},
        ],
        "move_z": [
            {"name": "distance_mm", "type": "number", "default": 5, "min": -10, "max": 10},
            {"name": "feedrate", "type": "number", "default": 1200, "min": 120, "max": 3000},
        ],
        "move_absolute": [
            {"name": "axis", "type": "enum", "values": ["X", "Y", "Z"], "default": "X"},
            {"name": "position_mm", "type": "number", "default": 0, "min": -1000, "max": 1000},
            {"name": "feedrate", "type": "number", "default": 6000, "min": 120, "max": 12000},
        ],
        "extrude": [
            {"name": "length_mm", "type": "number", "default": 5, "min": -10, "max": 50},
            {"name": "feedrate", "type": "number", "default": 300, "min": 60, "max": 1200},
        ],
        "set_hotend_temp": [{"name": "temperature", "type": "number", "default": 0, "min": 0, "max": 300}],
        "set_bed_temp": [{"name": "temperature", "type": "number", "default": 0, "min": 0, "max": 130}],
        "set_fan": [
            {"name": "fan_name", "type": "text", "default": ""},
            {"name": "speed_percent", "type": "number", "default": 0, "min": 0, "max": 100},
        ],
        "set_output_pin": [
            {"name": "pin_name", "type": "text", "default": ""},
            {"name": "value_percent", "type": "number", "default": 0, "min": 0, "max": 100},
        ],
        "set_led": [
            {"name": "led_name", "type": "text", "default": ""},
            {"name": "brightness_percent", "type": "number", "default": 0, "min": 0, "max": 100},
        ],
        "set_speed_factor": [{"name": "speed_percent", "type": "number", "default": 100, "min": 1, "max": 300}],
        "set_velocity_limit": [
            {"name": "velocity", "type": "number", "default": 350, "min": 1, "max": 1000},
            {"name": "accel", "type": "number", "default": 10000, "min": 1, "max": 100000},
            {"name": "square_corner_velocity", "type": "number", "default": 5, "min": 0, "max": 100},
        ],
        "set_extrusion_factor": [{"name": "extrusion_percent", "type": "number", "default": 100, "min": 1, "max": 300}],
        "set_pressure_advance": [
            {"name": "advance", "type": "number", "default": 0, "min": 0, "max": 2},
            {"name": "smooth_time", "type": "number", "default": 0.04, "min": 0, "max": 1},
        ],
    }
    return parameters.get(action_id, [])


def _operation_action_commands(action_id: str, parameters: dict[str, Any]) -> list[str]:
    if action_id == "home_xyz":
        return ["G28"]
    if action_id == "quad_gantry_level":
        return ["QUAD_GANTRY_LEVEL"]
    if action_id == "move_xy":
        axis = parameters.get("axis") if parameters.get("axis") in {"X", "Y"} else "X"
        return ["G91", f"G0 {axis}{_number(parameters.get('distance_mm'), 10)} F{_number(parameters.get('feedrate'), 6000)}", "G90"]
    if action_id == "move_z":
        return ["G91", f"G0 Z{_number(parameters.get('distance_mm'), 5)} F{_number(parameters.get('feedrate'), 1200)}", "G90"]
    if action_id == "move_absolute":
        axis = parameters.get("axis") if parameters.get("axis") in {"X", "Y", "Z"} else "X"
        default_feedrate = 1200 if axis == "Z" else 6000
        return ["G90", f"G0 {axis}{_number(parameters.get('position_mm'), 0)} F{_number(parameters.get('feedrate'), default_feedrate)}"]
    if action_id == "extrude":
        return ["M83", f"G1 E{_number(parameters.get('length_mm'), 5)} F{_number(parameters.get('feedrate'), 300)}", "M82"]
    if action_id == "set_hotend_temp":
        return [f"SET_HEATER_TEMPERATURE HEATER=extruder TARGET={_number(parameters.get('temperature'), 0)}"]
    if action_id == "set_bed_temp":
        return [f"SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={_number(parameters.get('temperature'), 0)}"]
    if action_id == "set_fan":
        fan_name = _safe_gcode_identifier(_fan_config_name(str(parameters.get("fan_name") or "")))
        speed_percent = _number(parameters.get("speed_percent"), 0)
        if not fan_name or fan_name == "fan":
            return [f"M106 S{round(speed_percent * 2.55)}"]
        return [f"SET_FAN_SPEED FAN={fan_name} SPEED={speed_percent / 100:.2f}"]
    if action_id == "set_output_pin":
        pin_name = _safe_gcode_identifier(_output_pin_config_name(str(parameters.get("pin_name") or "<pin_name>")))
        return [f"SET_PIN PIN={pin_name} VALUE={_number(parameters.get('value_percent'), 0) / 100:.2f}"]
    if action_id == "set_led":
        led_name = _safe_gcode_identifier(_led_config_name(str(parameters.get("led_name") or "<led_name>")))
        return [f"SET_LED LED={led_name} WHITE={_number(parameters.get('brightness_percent'), 0) / 100:.2f}"]
    if action_id == "set_speed_factor":
        return [f"M220 S{_number(parameters.get('speed_percent'), 100)}"]
    if action_id == "set_velocity_limit":
        return [
            "SET_VELOCITY_LIMIT "
            f"VELOCITY={_number(parameters.get('velocity'), 350)} "
            f"ACCEL={_number(parameters.get('accel'), 10000)} "
            f"SQUARE_CORNER_VELOCITY={_number(parameters.get('square_corner_velocity'), 5)}"
        ]
    if action_id == "set_extrusion_factor":
        return [f"M221 S{_number(parameters.get('extrusion_percent'), 100)}"]
    if action_id == "set_pressure_advance":
        return [f"SET_PRESSURE_ADVANCE ADVANCE={_number(parameters.get('advance'), 0)} SMOOTH_TIME={_number(parameters.get('smooth_time'), 0.04)}"]
    if action_id == "save_config":
        return ["SAVE_CONFIG"]
    return []


def _normalize_action_parameters(action_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for spec in _operation_action_parameters(action_id):
        name = str(spec["name"])
        if spec.get("type") == "enum":
            values = [str(value) for value in spec.get("values", [])]
            value = str(parameters.get(name, spec.get("default", values[0] if values else "")))
            clean[name] = value if value in values else spec.get("default", values[0] if values else "")
            continue
        if spec.get("type") == "number":
            value = _number(parameters.get(name), float(spec.get("default", 0)))
            minimum = spec.get("min")
            maximum = spec.get("max")
            if isinstance(minimum, int | float):
                value = max(float(minimum), value)
            if isinstance(maximum, int | float):
                value = min(float(maximum), value)
            clean[name] = int(value) if value.is_integer() else value
        if spec.get("type") == "text":
            if action_id == "set_fan" and name == "fan_name":
                clean[name] = str(parameters.get(name, spec.get("default", "")))
                continue
            if action_id == "set_output_pin" and name == "pin_name":
                raw = str(parameters.get(name, spec.get("default", "")))
                clean[name] = raw if raw.startswith("output_pin ") else _safe_gcode_identifier(raw)
                continue
            if action_id == "set_led" and name == "led_name":
                raw = str(parameters.get(name, spec.get("default", "")))
                clean[name] = raw if raw.startswith(LED_OBJECT_PREFIXES) else _safe_gcode_identifier(raw)
                continue
            clean[name] = _safe_gcode_identifier(str(parameters.get(name, spec.get("default", ""))))
    return clean


def _operation_action_block_reason(connected: bool, printing: bool) -> str:
    if not connected:
        return "Bloqueado: exige leitura ao vivo do Moonraker."
    if printing:
        return "Bloqueado: impressão em andamento."
    return ""


def _operation_action_preflight_blockers(
    action_id: str,
    preflight: dict[str, Any],
    capability: dict[str, str],
    klipper_state: str,
    klippy_state: str,
) -> list[str]:
    blockers: list[str] = []
    if preflight.get("connected") is False:
        blockers.append("Bloqueado: exige leitura ao vivo do Moonraker.")
    if operation_action_blocks_when_printing(action_id) and preflight.get("printing") is True:
        blockers.append("Bloqueado: impressão em andamento.")
    if klipper_state != "ready":
        blockers.append(f"Bloqueado: Klipper não está ready ({klipper_state or '-'}).")
    if klippy_state != "ready":
        blockers.append(f"Bloqueado: Klippy não está ready ({klippy_state or '-'}).")
    if capability.get("status") != "supported":
        blockers.append(f"Bloqueado: capacidade não confirmada ({capability.get('reason') or 'sem evidência'}).")
    return blockers


def _axis_limit_blocker(action_id: str, parameters: dict[str, Any] | None, preflight: dict[str, Any]) -> str | None:
    if action_id != "move_absolute":
        return None
    params = parameters or {}
    axis = str(params.get("axis") or "X").upper()
    if axis not in {"X", "Y", "Z"}:
        return "Bloqueado: eixo inválido."
    target = _number(params.get("position_mm"), 0)
    toolhead = _dict(_dict(preflight.get("object_status")).get("toolhead"))
    minimum = _axis_value(toolhead.get("axis_minimum"), axis)
    maximum = _axis_value(toolhead.get("axis_maximum"), axis)
    if minimum is None or maximum is None:
        return None
    if target < minimum or target > maximum:
        return f"Bloqueado: posição {axis}{target} fora dos limites {minimum}..{maximum}."
    return None


def _capability(action_id: str, status: str, reason: str) -> dict[str, str]:
    return {"action_id": action_id, "status": status, "reason": reason}


def _object_names(objects: dict[str, Any]) -> set[str]:
    status = _object_status(objects)
    names = set(status.keys())
    object_list = objects.get("objects")
    if isinstance(object_list, list):
        names.update(str(name) for name in object_list)
    return names


def _number(value: Any, default: float) -> float:
    return value if isinstance(value, int | float) else default


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _safe_gcode_identifier(value: str) -> str:
    cleaned = "".join(character for character in value.strip() if character.isalnum() or character in {"_", "-", "<", ">"})
    return cleaned[:80]


def _fan_config_name(object_name: str) -> str:
    for prefix in ("fan_generic ", "heater_fan ", "controller_fan ", "fan "):
        if object_name.startswith(prefix):
            return object_name.removeprefix(prefix)
    return object_name


def _is_controllable_fan(object_name: str) -> bool:
    return object_name == "fan" or object_name.startswith(("fan ", "fan_generic "))


def _output_pin_config_name(object_name: str) -> str:
    return object_name.removeprefix("output_pin ") if object_name.startswith("output_pin ") else object_name


def _led_config_name(object_name: str) -> str:
    for prefix in LED_OBJECT_PREFIXES:
        if object_name.startswith(prefix):
            return object_name.removeprefix(prefix)
    return object_name


def _summary(connected: bool, klipper_state: str, print_state: str) -> str:
    if not connected:
        return "Moonraker desconectado."
    if print_state and print_state not in {"standby", "complete"}:
        return f"Operação carregada. Impressão: {print_state}."
    if klipper_state:
        return f"Operação carregada. Klipper: {klipper_state}."
    return "Operação carregada."


def _system_loads(server_info: dict[str, Any], system_info: dict[str, Any], proc_stats: dict[str, Any]) -> list[dict[str, Any]]:
    system = _nested(system_info, ["system_info"]) or system_info
    cpu_info = _nested(system, ["cpu_info"]) or {}
    memory = _nested(system, ["memory"]) or {}
    disk = _nested(system_info, ["disk"]) or _nested(system, ["disk"]) or {}
    return [
        _metric("Klipper", server_info.get("klippy_state")),
        _metric("Moonraker", server_info.get("moonraker_version")),
        _metric("CPU", cpu_info.get("cpu_desc") or cpu_info.get("model")),
        _metric("Carga", proc_stats.get("system_load") or proc_stats.get("load_average")),
        _metric("Temp. host", proc_stats.get("cpu_temp") or proc_stats.get("temperature"), "°C"),
        _metric("Memória livre", memory.get("available") or memory.get("free"), "bytes"),
        _metric("Disco livre", disk.get("available") or disk.get("free"), "bytes"),
    ]


def _temperatures(status: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, payload in status.items():
        if not isinstance(payload, dict) or "temperature" not in payload:
            continue
        rows.append(
            {
                "name": _display_name(name),
                "temperature": payload.get("temperature"),
                "target": payload.get("target"),
                "power": payload.get("power"),
            }
        )
    return sorted(rows, key=lambda row: str(row["name"]))


def _snapshot_temperatures(payload: dict[str, Any]) -> list[dict[str, Any]]:
    objects = _dict(payload.get("operation_objects"))
    readings = [
        {
            "name": item["name"],
            "temperature": item.get("temperature"),
            "target": item.get("target"),
        }
        for item in _temperatures(_object_status(objects))
        if isinstance(item.get("temperature"), int | float)
    ]
    proc_stats = _dict(payload.get("proc_stats"))
    cpu_temp = proc_stats.get("cpu_temp") or proc_stats.get("temperature")
    if isinstance(cpu_temp, int | float) and not any(item["name"] == "Host" for item in readings):
        readings.append({"name": "Host", "temperature": cpu_temp, "target": None})
    return readings


def _toolhead(status: dict[str, Any]) -> dict[str, Any]:
    toolhead = _nested(status, ["toolhead"]) or {}
    gcode_move = _nested(status, ["gcode_move"]) or {}
    return {
        "position": toolhead.get("position") or gcode_move.get("gcode_position"),
        "homed_axes": toolhead.get("homed_axes"),
        "max_velocity": toolhead.get("max_velocity"),
        "max_accel": toolhead.get("max_accel"),
        "square_corner_velocity": toolhead.get("square_corner_velocity"),
        "axis_minimum": toolhead.get("axis_minimum"),
        "axis_maximum": toolhead.get("axis_maximum"),
        "speed_factor": gcode_move.get("speed_factor"),
    }


def _extruder(status: dict[str, Any]) -> dict[str, Any]:
    extruder = _nested(status, ["extruder"]) or {}
    gcode_move = _nested(status, ["gcode_move"]) or {}
    print_stats = _nested(status, ["print_stats"]) or {}
    return {
        "pressure_advance": extruder.get("pressure_advance"),
        "smooth_time": extruder.get("smooth_time"),
        "extrusion_factor": gcode_move.get("extrude_factor"),
        "filament_used": print_stats.get("filament_used"),
    }


def _miscellaneous(objects: dict[str, Any], print_metadata: dict[str, Any] | None = None, gcode_files: list[Any] | None = None) -> dict[str, Any]:
    status = _object_status(objects)
    metadata = _dict(print_metadata)
    fans = _misc_fans(status)
    outputs = _misc_outputs(status)
    leds = _misc_leds(status)
    detected_objects = _misc_object_names(objects)
    missing_status_objects = [name for name in detected_objects if not _misc_object_has_reading(name, status)]
    collection_state = _misc_collection_state(
        has_readings=bool(fans or outputs or leds),
        has_detected_objects=bool(detected_objects),
        has_object_list=isinstance(objects.get("objects"), list),
    )
    display = _nested(status, ["display_status"]) or {}
    virtual_sdcard = _nested(status, ["virtual_sdcard"]) or {}
    print_stats = _nested(status, ["print_stats"]) or {}
    progress = _print_progress(display, virtual_sdcard)
    file_progress = _progress_fraction(virtual_sdcard.get("progress"))
    layer_info = _print_layer_info(print_stats, display, status, metadata)
    defer_layer_preview = _defer_print_layer_until_material(print_stats, display, virtual_sdcard)
    if defer_layer_preview:
        layer_info = {
            "current_layer": None,
            "total_layers": layer_info["total_layers"] or _metadata_total_layers(metadata),
            "source": "pre_print",
        }
    estimated_time = _number_or_none(metadata.get("estimated_time"))
    remaining_time = _remaining_print_time(estimated_time, _number_or_none(print_stats.get("print_duration")), file_progress)
    visuals = _dict(metadata.get("printora_visuals"))
    return {
        "fans": fans,
        "outputs": outputs,
        "leds": leds,
        "collection_state": collection_state,
        "detected_objects": detected_objects,
        "missing_status_objects": missing_status_objects,
        "progress": progress["value"],
        "progress_source": progress["source"],
        "file_progress": file_progress,
        "file_position": virtual_sdcard.get("file_position"),
        "message": print_stats.get("message") or display.get("message"),
        "print_state": print_stats.get("state"),
        "filename": print_stats.get("filename"),
        "print_duration": print_stats.get("print_duration"),
        "total_duration": print_stats.get("total_duration"),
        "estimated_time": estimated_time,
        "remaining_time": remaining_time,
        "current_layer": layer_info["current_layer"],
        "total_layers": layer_info["total_layers"],
        "layer_source": layer_info["source"],
        "thumbnail": _dict(visuals.get("thumbnail")) or None,
        "layer_preview": None if defer_layer_preview else _dict(visuals.get("layer_preview")) or None,
        "slicer": metadata.get("slicer"),
        "slicer_version": metadata.get("slicer_version"),
        "filament_total": metadata.get("filament_total"),
        "filament_weight_total": metadata.get("filament_weight_total"),
        "object_height": metadata.get("object_height"),
        "layer_height": metadata.get("layer_height"),
        "first_layer_height": metadata.get("first_layer_height"),
        "nozzle_diameter": metadata.get("nozzle_diameter"),
        "filament_type": metadata.get("filament_type"),
        "filament_name": metadata.get("filament_name"),
        "gcode_files": _gcode_files(gcode_files),
    }


def _gcode_files(value: list[Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in value or []:
        mapped = _dict(item)
        filename = _gcode_file_text(mapped.get("filename") or mapped.get("path") or mapped.get("name"))
        if not filename or not _is_gcode_filename(filename):
            continue
        rows.append(
            {
                "filename": filename,
                "path": _gcode_file_text(mapped.get("path") or filename),
                "size": _number_or_none(mapped.get("size")),
                "modified": _number_or_none(mapped.get("modified")),
                "estimated_time": _number_or_none(mapped.get("estimated_time")),
                "slicer": _gcode_file_text(mapped.get("slicer")),
                "slicer_version": _gcode_file_text(mapped.get("slicer_version")),
                "object_height": _number_or_none(mapped.get("object_height")),
                "layer_height": _number_or_none(mapped.get("layer_height")),
                "first_layer_height": _number_or_none(mapped.get("first_layer_height")),
                "nozzle_diameter": _number_or_none(mapped.get("nozzle_diameter")),
                "filament_total": _number_or_none(mapped.get("filament_total")),
                "filament_weight_total": _number_or_none(mapped.get("filament_weight_total")),
                "filament_type": _gcode_file_text(mapped.get("filament_type")),
                "filament_name": _gcode_file_text(mapped.get("filament_name")),
                "print_start_time": _number_or_none(mapped.get("print_start_time")),
                "last_print_duration": _number_or_none(mapped.get("last_print_duration")),
            }
        )
    rows.sort(key=lambda row: row["modified"] if isinstance(row.get("modified"), int | float) else 0, reverse=True)
    return rows[:MAX_OPERATION_GCODE_FILES]


def _gcode_file_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list | tuple):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return ""


def _is_gcode_filename(value: str) -> bool:
    lowered = value.strip().lower()
    return any(lowered.endswith(extension) for extension in GCODE_FILE_EXTENSIONS)


def _misc_fans(status: dict[str, Any]) -> list[dict[str, Any]]:
    fans = [
        {"name": _display_name(name), "object_name": name, "speed": payload.get("speed"), "rpm": payload.get("rpm"), "controllable": _is_controllable_fan(name)}
        for name, payload in status.items()
        if isinstance(payload, dict) and (name == "fan" or name.startswith(("fan ", "fan_generic ", "heater_fan ", "controller_fan "))) and ("speed" in payload or "rpm" in payload)
    ]
    return sorted(fans, key=lambda row: str(row["name"]))


def _misc_outputs(status: dict[str, Any]) -> list[dict[str, Any]]:
    outputs = [
        {"name": _display_name(name), "object_name": name, "value": _output_value(payload), "controllable": True}
        for name, payload in status.items()
        if isinstance(payload, dict) and name.startswith("output_pin ") and _output_value(payload) is not None
    ]
    return sorted(outputs, key=lambda row: str(row["name"]))


def _misc_leds(status: dict[str, Any]) -> list[dict[str, Any]]:
    leds = [
        {
            "name": _display_name(name),
            "object_name": name,
            "brightness": _led_brightness(payload),
            "color": _led_color(payload),
            "controllable": True,
        }
        for name, payload in status.items()
        if isinstance(payload, dict) and name.startswith(LED_OBJECT_PREFIXES)
    ]
    return sorted(leds, key=lambda row: str(row["name"]))


def _misc_object_names(objects: dict[str, Any]) -> list[str]:
    object_list = objects.get("objects")
    if not isinstance(object_list, list):
        return []
    return sorted({str(name) for name in object_list if _is_misc_object_name(str(name))})


def _is_misc_object_name(name: str) -> bool:
    return name == "fan" or name.startswith(("fan ", "fan_generic ", "heater_fan ", "controller_fan ", "output_pin ", *LED_OBJECT_PREFIXES))


def _misc_object_has_reading(name: str, status: dict[str, Any]) -> bool:
    payload = status.get(name)
    if not isinstance(payload, dict):
        return False
    if name == "fan" or name.startswith(("fan ", "fan_generic ", "heater_fan ", "controller_fan ")):
        return "speed" in payload or "rpm" in payload
    if name.startswith("output_pin "):
        return _output_value(payload) is not None
    if name.startswith(LED_OBJECT_PREFIXES):
        return "color_data" in payload
    return False


def _misc_collection_state(*, has_readings: bool, has_detected_objects: bool, has_object_list: bool) -> str:
    if has_readings:
        return "loaded"
    if has_detected_objects:
        return "objects_detected_without_status"
    if has_object_list:
        return "none_detected"
    return "objects_not_reported"


def _print_progress(display: dict[str, Any], virtual_sdcard: dict[str, Any]) -> dict[str, Any]:
    for source, payload in (("display_status", display), ("virtual_sdcard", virtual_sdcard)):
        value = _progress_fraction(payload.get("progress"))
        if value is not None:
            return {"value": value, "source": source}
    return {"value": None, "source": None}


def _defer_print_layer_until_material(print_stats: dict[str, Any], display: dict[str, Any], virtual_sdcard: dict[str, Any]) -> bool:
    state = str(print_stats.get("state") or "").strip().lower()
    if state != "printing":
        return False
    return not _has_print_material_progress(print_stats, display, virtual_sdcard)


def _has_print_material_progress(print_stats: dict[str, Any], display: dict[str, Any], virtual_sdcard: dict[str, Any]) -> bool:
    filament_used = _number_or_none(print_stats.get("filament_used"))
    display_progress = _progress_fraction(display.get("progress"))
    file_progress = _progress_fraction(virtual_sdcard.get("progress"))
    if filament_used is not None:
        if filament_used > 0.01:
            return True
        return bool(display_progress is not None and display_progress > 0.001)
    if display_progress is not None and display_progress > 0.001:
        return True
    if file_progress is not None and file_progress > 0.02:
        return not _looks_like_preprint_message(print_stats.get("message") or display.get("message"))
    return False


def _looks_like_preprint_message(value: Any) -> bool:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        return False
    return any(
        token in normalized
        for token in (
            "qgl",
            "quad_gantry_level",
            "bed_mesh",
            "homing",
            "g28",
            "z_tilt",
            "calibrate_z",
        )
    )


def _output_value(payload: dict[str, Any]) -> float | None:
    return _bounded_fraction(payload.get("value"))


def _led_brightness(payload: dict[str, Any]) -> float | None:
    channels = _led_channels(payload)
    if not channels:
        return None
    return max(channels)


def _led_color(payload: dict[str, Any]) -> str | None:
    channels = _led_channels(payload)
    if not channels:
        return None
    red = int(round(_bounded_fraction(channels[0]) * 255)) if len(channels) > 0 else 0
    green = int(round(_bounded_fraction(channels[1]) * 255)) if len(channels) > 1 else 0
    blue = int(round(_bounded_fraction(channels[2]) * 255)) if len(channels) > 2 else 0
    return f"#{red:02x}{green:02x}{blue:02x}"


def _led_channels(payload: dict[str, Any]) -> list[float] | None:
    color_data = payload.get("color_data")
    if not isinstance(color_data, list) or not color_data:
        return None
    first = color_data[0]
    if not isinstance(first, list | tuple):
        return None
    return [_bounded_fraction(value) for value in first if isinstance(value, int | float)]


def _progress_fraction(value: Any) -> float | None:
    return _bounded_fraction(value, allow_percent=True)


def _bounded_fraction(value: Any, *, allow_percent: bool = False) -> float | None:
    if not isinstance(value, int | float):
        return None
    clean_value = float(value)
    if clean_value < 0:
        return 0.0
    if clean_value <= 1:
        return clean_value
    if allow_percent and clean_value <= 100:
        return clean_value / 100.0
    return 1.0


def _print_layer_info(print_stats: dict[str, Any], display: dict[str, Any], status: dict[str, Any], metadata: dict[str, Any]) -> dict[str, int | str | None]:
    info = _dict(print_stats.get("info"))
    current_layer = _int_or_none(print_stats.get("current_layer") or info.get("current_layer"))
    direct_total_layers = _int_or_none(print_stats.get("total_layer") or info.get("total_layer") or info.get("total_layers"))
    if current_layer is not None or direct_total_layers is not None:
        return {"current_layer": current_layer, "total_layers": direct_total_layers or _metadata_total_layers(metadata), "source": "print_stats"}
    message = str(print_stats.get("message") or display.get("message") or "")
    parsed = _parse_layer_message(message)
    if parsed["current_layer"] is not None or parsed["total_layers"] is not None:
        return {**parsed, "source": "message"}
    estimated_current = _estimated_current_layer(status, metadata)
    total_layers = _metadata_total_layers(metadata)
    return {"current_layer": estimated_current, "total_layers": total_layers, "source": "metadata" if estimated_current is not None or total_layers is not None else None}


def _parse_layer_message(message: str) -> dict[str, int | None]:
    lowered = message.lower().replace("camada", "layer")
    for separator in ("/", " of "):
        if separator not in lowered:
            continue
        parts = lowered.replace("layer", "").replace(":", " ").split(separator, 1)
        if len(parts) != 2:
            continue
        current = _int_or_none(parts[0].strip().split()[-1] if parts[0].strip().split() else None)
        total = _int_or_none(parts[1].strip().split()[0] if parts[1].strip().split() else None)
        if current is not None or total is not None:
            return {"current_layer": current, "total_layers": total}
    return {"current_layer": None, "total_layers": None}


def _metadata_total_layers(metadata: dict[str, Any]) -> int | None:
    for key in ("layer_count", "total_layer", "total_layers", "layers"):
        total = _int_or_none(metadata.get(key))
        if total is not None and total > 0:
            return total
    object_height = _number_or_none(metadata.get("object_height"))
    layer_height = _number_or_none(metadata.get("layer_height"))
    first_layer_height = _number_or_none(metadata.get("first_layer_height")) or layer_height
    if object_height is None or layer_height is None or object_height <= 0 or layer_height <= 0:
        return None
    if first_layer_height is None or first_layer_height <= 0:
        return max(1, math.ceil(object_height / layer_height))
    remaining_height = max(0.0, object_height - first_layer_height)
    return max(1, 1 + math.ceil(remaining_height / layer_height))


def _estimated_current_layer(status: dict[str, Any], metadata: dict[str, Any]) -> int | None:
    current_z = _current_z(status)
    layer_height = _number_or_none(metadata.get("layer_height"))
    first_layer_height = _number_or_none(metadata.get("first_layer_height")) or layer_height
    if current_z is None or layer_height is None or layer_height <= 0 or current_z <= 0:
        return None
    if first_layer_height is None or first_layer_height <= 0:
        current = math.ceil(current_z / layer_height)
    elif current_z <= first_layer_height + layer_height * 0.25:
        current = 1
    else:
        current = 1 + math.ceil(max(0.0, current_z - first_layer_height) / layer_height)
    total = _metadata_total_layers(metadata)
    return min(max(1, current), total) if total is not None else max(1, current)


def _current_z(status: dict[str, Any]) -> float | None:
    for object_name, field in (("gcode_move", "gcode_position"), ("toolhead", "position")):
        position = _nested(status, [object_name, field])
        if isinstance(position, list | tuple) and len(position) > 2:
            return _number_or_none(position[2])
    return None


def _remaining_print_time(estimated_time: float | None, print_duration: float | None, file_progress: float | None) -> float | None:
    if estimated_time is not None and estimated_time > 0:
        if file_progress is not None and file_progress > 0:
            return max(0.0, estimated_time - estimated_time * file_progress)
        if print_duration is not None:
            return max(0.0, estimated_time - print_duration)
    if print_duration is not None and file_progress is not None and file_progress > 0:
        total_time = print_duration / file_progress
        return max(0.0, total_time - print_duration)
    return None


def _number_or_none(value: Any) -> float | None:
    return float(value) if isinstance(value, int | float) and math.isfinite(float(value)) else None


def _total_print_hours(history_totals: dict[str, Any] | None) -> float | None:
    if not history_totals:
        return None
    job_totals = history_totals.get("job_totals")
    if not isinstance(job_totals, dict):
        return None
    total_seconds = job_totals.get("total_print_time")
    if not isinstance(total_seconds, int | float):
        return None
    return round(float(total_seconds) / 3600.0, 3)


def _object_status(objects: dict[str, Any]) -> dict[str, Any]:
    status = objects.get("status", objects)
    return status if isinstance(status, dict) else {}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _metric(label: str, value: Any, unit: str | None = None) -> dict[str, Any]:
    return {"label": label, "value": value, "unit": unit}


def _nested(payload: dict[str, Any], path: list[str]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _display_name(name: str) -> str:
    clean = name
    for prefix in ("fan_generic ", "heater_fan ", "controller_fan ", "fan ", "output_pin ", "heater_generic ", *LED_OBJECT_PREFIXES):
        if clean.startswith(prefix):
            clean = clean.removeprefix(prefix)
            break
    return clean.replace("_", " ").title()


def _axis_value(values: Any, axis: str) -> float | None:
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    if not isinstance(values, list | tuple) or len(values) <= index:
        return None
    value = values[index]
    return float(value) if isinstance(value, int | float) else None
