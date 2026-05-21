from typing import Any


OPERATION_OBJECTS: dict[str, list[str]] = {
    "webhooks": ["state", "state_message"],
    "print_stats": ["state", "filename", "total_duration", "print_duration", "filament_used"],
    "display_status": ["progress", "message"],
    "toolhead": ["position", "homed_axes", "max_velocity", "max_accel", "estimated_print_time"],
    "gcode_move": ["gcode_position", "speed_factor", "extrude_factor"],
    "extruder": ["temperature", "target", "power", "pressure_advance", "smooth_time"],
    "heater_bed": ["temperature", "target", "power"],
}

OPTIONAL_OPERATION_OBJECT_PREFIXES = ("fan", "heater_fan ", "controller_fan ", "temperature_sensor ", "heater_generic ")


def build_operation_query_objects(available_objects: list[str]) -> dict[str, list[str]]:
    objects = dict(OPERATION_OBJECTS)
    for name in available_objects:
        if name in objects:
            continue
        if name.startswith(("temperature_sensor ", "heater_generic ")):
            objects[name] = ["temperature", "target", "power"]
        elif name == "fan" or name.startswith(("fan ", "heater_fan ", "controller_fan ")):
            objects[name] = ["speed", "rpm"]
    return objects


def build_operation_status(
    *,
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
    objects: dict[str, Any],
) -> dict[str, Any]:
    status = _object_status(objects)
    print_state = _text(_nested(status, ["print_stats", "state"]))
    klipper_state = _text(printer_info.get("state") or _nested(status, ["webhooks", "state"]))
    connected = bool(server_info.get("klippy_connected", True))

    return {
        "safe_mode": "read_only",
        "data_state": "live",
        "connected": connected,
        "summary": _summary(connected, klipper_state, print_state),
        "can_send_commands": False,
        "system_loads": _system_loads(server_info, system_info, proc_stats),
        "temperatures": _temperatures(status),
        "temperature_history": [],
        "actions": build_operation_actions(connected=connected, print_state=print_state, objects=objects),
        "capabilities": build_operation_capabilities(objects),
        "toolhead": _toolhead(status),
        "extruder": _extruder(status),
        "miscellaneous": _miscellaneous(status),
    }


def build_unreachable_operation(moonraker_url: str, error: str) -> dict[str, Any]:
    return {
        "safe_mode": "read_only",
        "data_state": "offline",
        "connected": False,
        "moonraker_url": moonraker_url,
        "summary": "Impressora desligada ou Moonraker indisponível.",
        "error": error,
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
        rows.append(
            {
                **action,
                "capability": capabilities.get(action["id"], {"status": "unknown", "reason": "Sem dados de objetos Klipper."}),
                "enabled": False,
                "confirmation_required": True,
                "block_reason": _operation_action_block_reason(connected, printing),
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
            "supported" if any(name == "fan" or name.startswith("fan ") for name in names) else "unknown",
            "Fan padrão detectado." if any(name == "fan" or name.startswith("fan ") for name in names) else "Fan padrão não detectado nos dados conhecidos.",
        ),
        _capability(
            "set_led",
            "supported" if any(name.startswith(("led ", "neopixel ", "dotstar ", "pca9533 ", "pca9632 ")) for name in names) else "unknown",
            "Objeto LED detectado." if any(name.startswith(("led ", "neopixel ", "dotstar ", "pca9533 ", "pca9632 ")) for name in names) else "LED exige nome real do objeto Klipper.",
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
    printing = print_state not in {"", "standby", "complete", "cancelled", "error"}
    clean_parameters = _normalize_action_parameters(action_id, parameters or {})
    return {
        "safe_mode": "dry_run_only",
        "action": {
            **action,
            "enabled": False,
            "confirmation_required": True,
            "block_reason": _operation_action_block_reason(connected, printing),
        },
        "parameters": clean_parameters,
        "expected_parameters": _operation_action_parameters(action_id),
        "command_preview": _operation_action_commands(action_id, clean_parameters),
        "would_send_gcode": False,
        "executable": False,
        "confirmation_phrase": f"CONFIRM_{action_id.upper()}",
        "blockers": [
            _operation_action_block_reason(connected, printing),
            "Execução real de ação operacional ainda não implementada.",
        ],
        "rollback_plan": "Nenhum rollback necessário: este preview não chama Moonraker e não envia G-code.",
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
    blockers = _operation_action_preflight_blockers(preflight, capability, klipper_state, klippy_state)
    return {
        "safe_mode": "operation_action_preflight_read_only",
        "action": {
            **preview["action"],
            "capability": capability,
            "block_reason": blockers[0] if blockers else "Bloqueado: execução real ainda não liberada.",
        },
        "parameters": preview["parameters"],
        "expected_parameters": preview["expected_parameters"],
        "command_preview": preview["command_preview"],
        "preflight": preflight,
        "capability": capability,
        "would_send_gcode": False,
        "executable": False,
        "can_execute": False,
        "confirmation_phrase": preview["confirmation_phrase"],
        "blockers": blockers or ["Bloqueado: execução real de ação operacional ainda não implementada."],
        "rollback_plan": [
            "Nenhum rollback necessário: este preflight não chama endpoint de execução do Moonraker.",
            "Execução real futura deve registrar comando enviado, resposta do Moonraker e estado posterior.",
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
        {"id": "move_z", "group": "movimento", "label": "Mover Z", "command": "G0 Z", "risk": "move_z", "compatibility": ["Klipper padrão com eixo Z"]},
        {"id": "extrude", "group": "extrusão", "label": "Extrudar", "command": "G1 E", "risk": "extrude_filament", "compatibility": ["extrusor configurado", "hotend aquecido para extrusão real"]},
        {"id": "set_hotend_temp", "group": "temperatura", "label": "Hotend", "command": "SET_HEATER_TEMPERATURE HEATER=extruder", "risk": "heat_toolhead", "compatibility": ["heater chamado extruder"]},
        {"id": "set_bed_temp", "group": "temperatura", "label": "Mesa", "command": "SET_HEATER_TEMPERATURE HEATER=heater_bed", "risk": "heat_bed", "compatibility": ["heater chamado heater_bed"]},
        {"id": "set_fan", "group": "fan", "label": "Fan", "command": "M106/M107", "risk": "change_fan", "compatibility": ["fan de peça padrão M106/M107"]},
        {"id": "set_led", "group": "led", "label": "LED", "command": "SET_LED", "risk": "change_led", "compatibility": ["requer LED Klipper informado no parâmetro led_name"]},
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
        "extrude": [
            {"name": "length_mm", "type": "number", "default": 5, "min": -10, "max": 50},
            {"name": "feedrate", "type": "number", "default": 300, "min": 60, "max": 1200},
        ],
        "set_hotend_temp": [{"name": "temperature", "type": "number", "default": 0, "min": 0, "max": 300}],
        "set_bed_temp": [{"name": "temperature", "type": "number", "default": 0, "min": 0, "max": 130}],
        "set_fan": [{"name": "speed_percent", "type": "number", "default": 0, "min": 0, "max": 100}],
        "set_led": [
            {"name": "led_name", "type": "text", "default": ""},
            {"name": "brightness_percent", "type": "number", "default": 0, "min": 0, "max": 100},
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
    if action_id == "extrude":
        return ["M83", f"G1 E{_number(parameters.get('length_mm'), 5)} F{_number(parameters.get('feedrate'), 300)}", "M82"]
    if action_id == "set_hotend_temp":
        return [f"SET_HEATER_TEMPERATURE HEATER=extruder TARGET={_number(parameters.get('temperature'), 0)}"]
    if action_id == "set_bed_temp":
        return [f"SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={_number(parameters.get('temperature'), 0)}"]
    if action_id == "set_fan":
        return [f"M106 S{round(_number(parameters.get('speed_percent'), 0) * 2.55)}"]
    if action_id == "set_led":
        led_name = _safe_gcode_identifier(str(parameters.get("led_name") or "<led_name>"))
        return [f"SET_LED LED={led_name} WHITE={_number(parameters.get('brightness_percent'), 0) / 100:.2f}"]
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
            clean[name] = _safe_gcode_identifier(str(parameters.get(name, spec.get("default", ""))))
    return clean


def _operation_action_block_reason(connected: bool, printing: bool) -> str:
    if not connected:
        return "Bloqueado: exige leitura ao vivo do Moonraker."
    if printing:
        return "Bloqueado: impressão em andamento."
    return "Bloqueado: operação mutável ainda não implementada."


def _operation_action_preflight_blockers(
    preflight: dict[str, Any],
    capability: dict[str, str],
    klipper_state: str,
    klippy_state: str,
) -> list[str]:
    blockers: list[str] = []
    if preflight.get("connected") is False:
        blockers.append("Bloqueado: exige leitura ao vivo do Moonraker.")
    if preflight.get("printing") is True:
        blockers.append("Bloqueado: impressão em andamento.")
    if klipper_state != "ready":
        blockers.append(f"Bloqueado: Klipper não está ready ({klipper_state or '-'}).")
    if klippy_state != "ready":
        blockers.append(f"Bloqueado: Klippy não está ready ({klippy_state or '-'}).")
    if capability.get("status") != "supported":
        blockers.append(f"Bloqueado: capacidade não confirmada ({capability.get('reason') or 'sem evidência'}).")
    blockers.append("Bloqueado: execução real de ação operacional ainda não implementada.")
    return blockers


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


def _safe_gcode_identifier(value: str) -> str:
    cleaned = "".join(character for character in value.strip() if character.isalnum() or character in {"_", "-", "<", ">"})
    return cleaned[:80]


def _summary(connected: bool, klipper_state: str, print_state: str) -> str:
    if not connected:
        return "Moonraker desconectado."
    if print_state and print_state not in {"standby", "complete"}:
        return f"Operação read-only carregada. Impressão: {print_state}."
    if klipper_state:
        return f"Operação read-only carregada. Klipper: {klipper_state}."
    return "Operação read-only carregada."


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


def _miscellaneous(status: dict[str, Any]) -> dict[str, Any]:
    fans = [
        {"name": _display_name(name), "speed": payload.get("speed"), "rpm": payload.get("rpm")}
        for name, payload in status.items()
        if isinstance(payload, dict) and "fan" in name and ("speed" in payload or "rpm" in payload)
    ]
    display = _nested(status, ["display_status"]) or {}
    print_stats = _nested(status, ["print_stats"]) or {}
    return {
        "fans": fans,
        "progress": display.get("progress"),
        "message": display.get("message"),
        "print_state": print_stats.get("state"),
        "filename": print_stats.get("filename"),
    }


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
    return name.replace("_", " ").replace("heater generic ", "").title()
