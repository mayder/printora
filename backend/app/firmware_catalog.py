import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel


FirmwareHardwareRole = Literal["mainboard", "toolhead", "can_adapter", "unknown"]
FirmwareHardwareConnection = Literal["can", "usb", "usb_can_bridge", "dedicated_usb_can", "unknown"]
FirmwareHardwareStatus = Literal["detected", "registered", "needs_mapping"]


class FirmwareCatalogSource(BaseModel):
    name: str
    url: str
    retrieved_at: str
    notes: list[str]


class FirmwareCatalogHardware(BaseModel):
    id: str
    vendor: str
    name: str
    role: FirmwareHardwareRole
    connection: FirmwareHardwareConnection
    guide_url: str
    known_mcus: list[str]
    preset_ids: list[str]


class FirmwareHardwareItem(BaseModel):
    id: str
    name: str
    role: FirmwareHardwareRole
    status: FirmwareHardwareStatus
    source: str
    connection: FirmwareHardwareConnection
    mcu_name: str | None = None
    current_version: str | None = None
    can_uuid: str | None = None
    can_interface: str | None = None
    registered_board_id: int | None = None
    matched_catalog_ids: list[str]
    matched_preset_ids: list[str]
    guide_url: str | None = None
    action_label: str
    detail: str


class FirmwareHardwareInventory(BaseModel):
    printer_id: int
    safe_mode: str
    source: str
    summary: str
    catalog_source: FirmwareCatalogSource
    catalog_counts: dict[str, int]
    items: list[FirmwareHardwareItem]


@lru_cache(maxsize=1)
def load_firmware_catalog() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "data" / "firmware_hardware_catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_source() -> FirmwareCatalogSource:
    return FirmwareCatalogSource(**load_firmware_catalog()["source"])


def catalog_counts() -> dict[str, int]:
    catalog = load_firmware_catalog()
    hardware = _catalog_hardware()
    known_without_preset = catalog.get("known_hardware_without_local_preset", {})
    return {
        "hardware_with_guides": len(hardware),
        "mainboards_without_local_preset": len(known_without_preset.get("mainboards", [])),
        "toolheads_without_local_preset": len(known_without_preset.get("toolheads", [])),
        "troubleshooting_guides": len(catalog.get("troubleshooting", [])),
    }


def match_catalog_for_mcu(*, mcu_name: str, mcu_version: str | None) -> list[FirmwareCatalogHardware]:
    normalized_name = _normalize(mcu_name)
    normalized_version = _normalize(mcu_version or "")
    matches = []
    for item in _catalog_hardware():
        if normalized_name and normalized_name in _normalize(item.name):
            matches.append(item)
            continue
        if normalized_version and any(_normalize(mcu) in normalized_version for mcu in item.known_mcus):
            matches.append(item)
    return matches


def build_firmware_hardware_inventory(
    *,
    printer_id: int,
    registered_boards: list[Any],
    object_names: list[str],
    object_payload: dict[str, Any],
) -> FirmwareHardwareInventory:
    items = [_registered_board_item(board) for board in registered_boards]
    registered_mcu_names = {_normalize(item.mcu_name or item.name) for item in items}
    for mcu_name in _mcu_object_names(object_names):
        if _normalize(mcu_name) in registered_mcu_names:
            continue
        item = _detected_mcu_item(mcu_name, object_payload)
        items.append(item)
    items = sorted(items, key=lambda item: (_role_order(item.role), item.name.lower()))
    detected_count = sum(1 for item in items if item.status == "detected")
    registered_count = sum(1 for item in items if item.status == "registered")
    summary = f"{registered_count} cadastrada(s), {detected_count} detectada(s) pelo Klipper."
    return FirmwareHardwareInventory(
        printer_id=printer_id,
        safe_mode="read_only_moonraker_inventory",
        source="moonraker_printer_objects",
        summary=summary,
        catalog_source=catalog_source(),
        catalog_counts=catalog_counts(),
        items=items,
    )


def _catalog_hardware() -> list[FirmwareCatalogHardware]:
    return [FirmwareCatalogHardware(**item) for item in load_firmware_catalog().get("hardware", [])]


def _registered_board_item(board: Any) -> FirmwareHardwareItem:
    matches = [item for item in _catalog_hardware() if board.preset_id in item.preset_ids]
    first = matches[0] if matches else None
    return FirmwareHardwareItem(
        id=f"registered-{board.id}",
        name=board.name,
        role=first.role if first else _role_from_connection(board.connection_type),
        status="registered",
        source="printora_firmware_boards",
        connection=board.connection_type,
        mcu_name=board.mcu,
        current_version=None,
        can_uuid=board.can_uuid,
        can_interface=board.can_interface,
        registered_board_id=board.id,
        matched_catalog_ids=[item.id for item in matches],
        matched_preset_ids=[board.preset_id],
        guide_url=first.guide_url if first else None,
        action_label="Gerar build",
        detail=f"Placa cadastrada com preset {board.preset_id}.",
    )


def _detected_mcu_item(mcu_name: str, object_payload: dict[str, Any]) -> FirmwareHardwareItem:
    mcu_status = _object_status(object_payload).get(_mcu_object_key(mcu_name), {})
    version = _optional_text(mcu_status.get("mcu_version") or mcu_status.get("mcu_build_versions"))
    settings = _configfile_settings(object_payload).get(_mcu_config_key(mcu_name), {})
    can_uuid = _optional_text(settings.get("canbus_uuid"))
    serial = _optional_text(settings.get("serial"))
    can_interface = _optional_text(settings.get("canbus_interface")) or "can0"
    matches = match_catalog_for_mcu(mcu_name=mcu_name, mcu_version=version)
    first = matches[0] if matches else None
    role = _role_from_mcu_name(mcu_name) if first is None else first.role
    connection = "can" if can_uuid else "usb" if serial else first.connection if first else "unknown"
    return FirmwareHardwareItem(
        id=f"detected-{_slug(mcu_name)}",
        name=_display_mcu_name(mcu_name),
        role=role,
        status="detected",
        source="klipper_configfile" if settings else "klipper_object_list",
        connection=connection,
        mcu_name=mcu_name,
        current_version=version,
        can_uuid=can_uuid,
        can_interface=can_interface if can_uuid else None,
        matched_catalog_ids=[item.id for item in matches],
        matched_preset_ids=_unique_preset_ids(matches),
        guide_url=first.guide_url if first else None,
        action_label="Associar modelo",
        detail=_detected_detail(can_uuid=can_uuid, serial=serial, matches=matches),
    )


def _mcu_object_names(object_names: list[str]) -> list[str]:
    names = []
    for name in object_names:
        if name == "mcu":
            names.append("mcu")
        elif name.startswith("mcu "):
            names.append(name.removeprefix("mcu ").strip())
    return names


def _mcu_object_key(mcu_name: str) -> str:
    return "mcu" if mcu_name == "mcu" else f"mcu {mcu_name}"


def _mcu_config_key(mcu_name: str) -> str:
    return "mcu" if mcu_name == "mcu" else f"mcu {mcu_name}"


def _object_status(object_payload: dict[str, Any]) -> dict[str, Any]:
    status = object_payload.get("status")
    return status if isinstance(status, dict) else {}


def _configfile_settings(object_payload: dict[str, Any]) -> dict[str, Any]:
    configfile = _object_status(object_payload).get("configfile")
    if not isinstance(configfile, dict):
        return {}
    settings = configfile.get("settings")
    return settings if isinstance(settings, dict) else {}


def _display_mcu_name(mcu_name: str) -> str:
    if mcu_name == "mcu":
        return "MCU principal"
    return mcu_name


def _role_from_mcu_name(mcu_name: str) -> FirmwareHardwareRole:
    lowered = mcu_name.lower()
    if any(token in lowered for token in ["ebb", "sb", "tool", "head", "can"]):
        return "toolhead"
    if mcu_name == "mcu":
        return "mainboard"
    return "unknown"


def _role_from_connection(connection: str) -> FirmwareHardwareRole:
    if connection == "usb_can_bridge":
        return "mainboard"
    if connection == "can":
        return "toolhead"
    return "unknown"


def _detected_detail(*, can_uuid: str | None, serial: str | None, matches: list[FirmwareCatalogHardware]) -> str:
    identity = f"UUID CAN {can_uuid}" if can_uuid else f"serial {serial}" if serial else "identidade sem UUID/serial no configfile"
    if matches:
        return f"Detectada no Klipper com {identity}; {len(matches)} modelo(s) compatível(is) no catálogo."
    return f"Detectada no Klipper com {identity}; modelo físico ainda não classificado no catálogo."


def _unique_preset_ids(matches: list[FirmwareCatalogHardware]) -> list[str]:
    values: list[str] = []
    for item in matches:
        for preset_id in item.preset_ids:
            if preset_id not in values:
                values.append(preset_id)
    return values


def _role_order(role: FirmwareHardwareRole) -> int:
    return {"mainboard": 0, "can_adapter": 1, "toolhead": 2, "unknown": 3}[role]


def _normalize(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "mcu"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
