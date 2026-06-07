import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


FirmwareHardwareRole = Literal["mainboard", "toolhead", "can_adapter", "unknown"]
FirmwareHardwareConnection = Literal["can", "usb", "usb_can_bridge", "dedicated_usb_can", "unknown"]
FirmwareHardwareStatus = Literal["detected", "registered", "needs_mapping"]
FirmwareCatalogStatus = Literal["catalogada", "ignorada_com_motivo", "bloqueada_com_motivo"]
FirmwareCatalogFlashMethod = Literal["katapult_can", "katapult_usb_can", "dfu_usb", "manual", "unknown"]


class FirmwareCatalogManifestPage(BaseModel):
    url: str
    title: str
    category: str
    menu_order: int
    content_hash: str | None = None
    status: FirmwareCatalogStatus
    reason: str | None = None


class FirmwareCatalogManifest(BaseModel):
    schema_version: int = 1
    source_url: str = "https://canbus.esoterical.online/"
    retrieved_at: str | None = None
    total_pages: int = 0
    pages: list[FirmwareCatalogManifestPage] = Field(default_factory=list)


class FirmwareCatalogSource(BaseModel):
    name: str
    url: str
    retrieved_at: str
    notes: list[str]


class FirmwareCatalogWorkflow(BaseModel):
    id: str
    title: str
    url: str
    steps: list[str] = Field(default_factory=list)


class FirmwareCatalogHardware(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    vendor: str
    name: str = Field(alias="modelo")
    role: FirmwareHardwareRole
    connection: FirmwareHardwareConnection
    guide_url: str
    known_mcus: list[str] = Field(default_factory=list)
    flash_method: FirmwareCatalogFlashMethod | None = None
    bootloader: str | None = None
    katapult: bool | None = None
    validation_commands: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    preset_ids: list[str] = Field(default_factory=list)
    catalog_status: FirmwareCatalogStatus = "catalogada"


class FirmwareCatalogReference(BaseModel):
    id: str
    label: str
    role: FirmwareHardwareRole
    connection: FirmwareHardwareConnection
    guide_url: str
    preset_ids: list[str] = Field(default_factory=list)
    known_mcus: list[str] = Field(default_factory=list)
    flash_method: FirmwareCatalogFlashMethod | None = None
    bootloader: str | None = None
    safety_notes: list[str] = Field(default_factory=list)


class FirmwareCatalogGuide(BaseModel):
    id: str
    title: str
    url: str
    summary: str | None = None
    validation_commands: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    catalog_status: FirmwareCatalogStatus = "catalogada"


class FirmwareCatalogKatapult(BaseModel):
    guide_url: str | None = None
    required: bool | None = None
    notes: list[str] = Field(default_factory=list)


class FirmwareCatalogCanSpeed(BaseModel):
    guide_url: str | None = None
    default_bitrate: int | None = None
    supported_bitrates: list[int] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class FirmwareCatalogGenerationMetadata(BaseModel):
    generated_by: str | None = None
    generated_at: str | None = None
    manifest_path: str = "backend/app/data/firmware_canbus_manifest.json"
    source_manifest_hash: str | None = None


class FirmwareCatalog(BaseModel):
    schema_version: int = 1
    source: FirmwareCatalogSource
    manifest: FirmwareCatalogManifest = Field(default_factory=FirmwareCatalogManifest)
    workflows: list[FirmwareCatalogWorkflow] = Field(default_factory=list)
    hardware: list[FirmwareCatalogHardware] = Field(default_factory=list)
    troubleshooting: list[FirmwareCatalogGuide] = Field(default_factory=list)
    update_flows: list[FirmwareCatalogGuide] = Field(default_factory=list)
    katapult: FirmwareCatalogKatapult = Field(default_factory=FirmwareCatalogKatapult)
    can_speed: FirmwareCatalogCanSpeed = Field(default_factory=FirmwareCatalogCanSpeed)
    known_hardware_without_local_preset: dict[str, list[str]] = Field(default_factory=dict)
    generation_metadata: FirmwareCatalogGenerationMetadata = Field(default_factory=FirmwareCatalogGenerationMetadata)


class FirmwareCatalogSummary(BaseModel):
    safe_mode: str
    source: FirmwareCatalogSource
    generated_at: str | None = None
    manifest_total_pages: int
    catalog_counts: dict[str, int]
    category_counts: dict[str, int]
    status_counts: dict[str, int]
    hardware_role_counts: dict[str, int]
    hardware_without_local_preset: dict[str, list[str]]


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
    catalog_references: list[FirmwareCatalogReference] = Field(default_factory=list)
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
    catalog_hardware_without_local_preset: dict[str, list[str]] = Field(default_factory=dict)
    items: list[FirmwareHardwareItem]


@lru_cache(maxsize=1)
def load_firmware_catalog() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "data" / "firmware_hardware_catalog.json"
    catalog = FirmwareCatalog.model_validate(json.loads(path.read_text(encoding="utf-8")))
    return catalog.model_dump(mode="json")


def firmware_catalog_json_schema() -> dict[str, Any]:
    return FirmwareCatalog.model_json_schema(by_alias=True)


def firmware_catalog_summary() -> FirmwareCatalogSummary:
    catalog = FirmwareCatalog.model_validate(load_firmware_catalog())
    return FirmwareCatalogSummary(
        safe_mode="local_catalog_read_only",
        source=catalog.source,
        generated_at=catalog.generation_metadata.generated_at,
        manifest_total_pages=catalog.manifest.total_pages,
        catalog_counts=catalog_counts(),
        category_counts=_manifest_category_counts(catalog),
        status_counts=_manifest_status_counts(catalog),
        hardware_role_counts=_hardware_role_counts(catalog),
        hardware_without_local_preset=catalog_hardware_without_local_preset(),
    )


def catalog_source() -> FirmwareCatalogSource:
    return FirmwareCatalogSource(**load_firmware_catalog()["source"])


def catalog_counts() -> dict[str, int]:
    catalog = load_firmware_catalog()
    hardware = _catalog_hardware()
    known_without_preset = catalog.get("known_hardware_without_local_preset", {})
    without_preset_total = sum(len(values) for values in known_without_preset.values())
    return {
        "hardware_with_guides": len(hardware),
        "hardware_with_local_preset": sum(1 for item in hardware if item.preset_ids),
        "hardware_without_local_preset": without_preset_total,
        "can_adapters_without_local_preset": len(known_without_preset.get("can_adapters", [])),
        "mainboards_without_local_preset": len(known_without_preset.get("mainboards", [])),
        "toolheads_without_local_preset": len(known_without_preset.get("toolheads", [])),
        "troubleshooting_guides": len(catalog.get("troubleshooting", [])),
    }


def catalog_hardware_without_local_preset() -> dict[str, list[str]]:
    catalog = load_firmware_catalog()
    values = catalog.get("known_hardware_without_local_preset", {})
    return {
        "can_adapters": list(values.get("can_adapters", [])),
        "mainboards": list(values.get("mainboards", [])),
        "toolheads": list(values.get("toolheads", [])),
    }


def match_catalog_for_mcu(*, mcu_name: str, mcu_version: str | None) -> list[FirmwareCatalogHardware]:
    normalized_name = _normalize(mcu_name)
    normalized_version = _normalize(mcu_version or "")
    matches = []
    expected_role = _role_from_mcu_name(mcu_name)
    for item in _catalog_hardware():
        if normalized_name and normalized_name in _normalize(item.name):
            matches.append(item)
            continue
        if normalized_version and any(_normalize(mcu) in normalized_version for mcu in item.known_mcus):
            matches.append(item)
    return sorted(matches, key=lambda item: (0 if item.role == expected_role else 1, _role_order(item.role), item.name.lower()))


def build_firmware_hardware_inventory(
    *,
    printer_id: int,
    registered_boards: list[Any],
    object_names: list[str],
    object_payload: dict[str, Any],
) -> FirmwareHardwareInventory:
    items = [_registered_board_item(board) for board in registered_boards]
    registered_identities = _registered_identity_keys(items)
    for mcu_name in _mcu_object_names(object_names):
        item = _detected_mcu_item(mcu_name, object_payload)
        if _hardware_identity_keys(item) & registered_identities:
            continue
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
        catalog_hardware_without_local_preset=catalog_hardware_without_local_preset(),
        items=items,
    )


def build_firmware_hardware_inventory_unavailable(*, printer_id: int, reason: str) -> FirmwareHardwareInventory:
    return FirmwareHardwareInventory(
        printer_id=printer_id,
        safe_mode="read_only_moonraker_inventory_unavailable",
        source="agent_unavailable",
        summary=f"Não foi possível ler as MCUs agora. {reason}",
        catalog_source=catalog_source(),
        catalog_counts=catalog_counts(),
        catalog_hardware_without_local_preset=catalog_hardware_without_local_preset(),
        items=[],
    )


def _registered_identity_keys(items: list[FirmwareHardwareItem]) -> set[str]:
    identities: set[str] = set()
    for item in items:
        identities.update(_hardware_identity_keys(item))
    return identities


def _hardware_identity_keys(item: FirmwareHardwareItem) -> set[str]:
    identities = {f"name:{_normalize(item.name)}"}
    if item.mcu_name:
        identities.add(f"mcu:{_normalize(item.mcu_name)}")
        identities.add(f"name:{_normalize(_display_mcu_name(item.mcu_name))}")
    if item.can_uuid:
        identities.add(f"can:{_normalize(item.can_uuid)}")
    return {identity for identity in identities if not identity.endswith(":")}


def _catalog_hardware() -> list[FirmwareCatalogHardware]:
    return [FirmwareCatalogHardware(**item) for item in load_firmware_catalog().get("hardware", [])]


def _catalog_reference(item: FirmwareCatalogHardware) -> FirmwareCatalogReference:
    return FirmwareCatalogReference(
        id=item.id,
        label=f"{item.vendor} {item.name}".strip(),
        role=item.role,
        connection=item.connection,
        guide_url=item.guide_url,
        preset_ids=item.preset_ids,
        known_mcus=item.known_mcus,
        flash_method=item.flash_method,
        bootloader=item.bootloader,
        safety_notes=item.safety_notes,
    )


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
        catalog_references=[_catalog_reference(item) for item in matches],
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
        catalog_references=[_catalog_reference(item) for item in matches],
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


def _manifest_category_counts(catalog: FirmwareCatalog) -> dict[str, int]:
    counts: dict[str, int] = {}
    for page in catalog.manifest.pages:
        counts[page.category] = counts.get(page.category, 0) + 1
    return dict(sorted(counts.items()))


def _manifest_status_counts(catalog: FirmwareCatalog) -> dict[str, int]:
    counts = {"catalogada": 0, "ignorada_com_motivo": 0, "bloqueada_com_motivo": 0}
    for page in catalog.manifest.pages:
        counts[page.status] = counts.get(page.status, 0) + 1
    return counts


def _hardware_role_counts(catalog: FirmwareCatalog) -> dict[str, int]:
    counts = {"mainboard": 0, "toolhead": 0, "can_adapter": 0, "unknown": 0}
    for item in catalog.hardware:
        counts[item.role] = counts.get(item.role, 0) + 1
    return counts


def _normalize(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "mcu"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
