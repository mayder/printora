from __future__ import annotations

from typing import Any

from app.agent_executor import unwrap_moonraker_list, unwrap_moonraker_result


def status_payload(result: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    payload = result or {}
    return (
        unwrap_moonraker_result(payload.get("printer_info")),
        unwrap_moonraker_result(payload.get("server_info")),
        unwrap_moonraker_result(payload.get("system_info")),
        unwrap_moonraker_result(payload.get("proc_stats")),
        unwrap_moonraker_result(payload.get("update_status")),
    )


def operation_payload(result: dict[str, Any] | None) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any] | None,
    dict[str, Any] | None,
    list[Any],
]:
    payload = result or {}
    printer_info, server_info, system_info, proc_stats, _update_status = status_payload(payload)
    objects = unwrap_moonraker_result(payload.get("operation_objects"))
    objects["objects"] = unwrap_moonraker_list({"result": {"objects": payload.get("objects_list") or []}}, "objects")
    history_totals = unwrap_moonraker_result(payload.get("history_totals")) if payload.get("history_totals") else None
    file_metadata = unwrap_moonraker_result(payload.get("file_metadata")) if payload.get("file_metadata") else None
    gcode_files = _unwrap_moonraker_items(payload.get("gcode_files"))
    return printer_info, server_info, system_info, proc_stats, objects, history_totals, file_metadata, gcode_files


def calibration_capabilities_payload(result: dict[str, Any] | None) -> tuple[list[str], dict[str, Any], bool]:
    payload = result or {}
    objects = [str(item) for item in payload.get("objects_list") or [] if str(item)]
    toolhead = unwrap_moonraker_result(payload.get("toolhead"))
    object_status = toolhead.get("status", toolhead) if isinstance(toolhead, dict) else {}
    if isinstance(object_status, dict) and object_status and "toolhead" not in object_status:
        object_status = {"toolhead": object_status}
    if not objects and isinstance(object_status, dict):
        objects = [str(name) for name in object_status.keys()]
    connected = bool(objects or object_status) and not _has_capability_connection_error(payload)
    return objects, object_status if isinstance(object_status, dict) else {}, connected


def firmware_inventory_payload(result: dict[str, Any] | None) -> tuple[list[str], dict[str, Any]]:
    payload = result or {}
    objects = [str(item) for item in payload.get("objects_list") or [] if str(item)]
    object_payload = unwrap_moonraker_result(payload.get("object_payload"))
    return objects, object_payload


def agent_preflight_payload(result: dict[str, Any] | None) -> dict[str, Any]:
    payload = result or {}
    objects = [str(item) for item in payload.get("objects_list") or [] if str(item)]
    object_payload = unwrap_moonraker_result(payload.get("object_status"))
    object_status = object_payload.get("status", object_payload) if isinstance(object_payload, dict) else {}
    if not objects and isinstance(object_status, dict):
        objects = [str(name) for name in object_status.keys()]
    return {
        "connected": payload.get("connected") is not False and not _has_error(payload),
        "printing": payload.get("printing") is True,
        "print_state": payload.get("print_state"),
        "klipper_state": payload.get("klipper_state"),
        "klippy_state": payload.get("klippy_state"),
        "blockers": payload.get("blockers") or [],
        "available_objects": objects,
        "object_status": object_status,
        "source": "agent",
    }


def _has_error(payload: dict[str, Any]) -> bool:
    return any(str(key).endswith("_error") for key in payload)


def _has_capability_connection_error(payload: dict[str, Any]) -> bool:
    return any(str(key).endswith("_error") and key != "toolhead_error" for key in payload)


def _unwrap_moonraker_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        items: list[Any] = []
        for item in value:
            if isinstance(item, dict):
                items.extend(_unwrap_moonraker_items(item.get("children")))
            items.append(item)
        return items
    if isinstance(value, dict):
        result = value.get("result")
        if isinstance(result, list):
            return _unwrap_moonraker_items(result)
        if isinstance(result, dict):
            for key in ("files", "items"):
                items = result.get(key)
                if isinstance(items, list):
                    return _unwrap_moonraker_items(items)
        for key in ("files", "items"):
            items = value.get(key)
            if isinstance(items, list):
                return _unwrap_moonraker_items(items)
        children = _unwrap_moonraker_items(value.get("children"))
        if children:
            return children
    return []
