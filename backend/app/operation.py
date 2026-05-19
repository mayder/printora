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
        "toolhead": {},
        "extruder": {},
        "miscellaneous": {},
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
        }
    )
    return fixture


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
