from pathlib import Path
from types import SimpleNamespace
from collections import Counter

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.firmware import (
    BoardPreset,
    FirmwareBoardCreate,
    FirmwareBoardRepository,
    FirmwareBuildConfig,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareFlashDryRunCreate,
    FirmwareFlashExecuteCreate,
)
from app.firmware.config_generator import generate_firmware_config_preview
from app.firmware.presets import BOARD_PRESETS
from app.firmware_catalog import (
    FirmwareCatalog,
    build_firmware_hardware_inventory,
    catalog_counts,
    catalog_hardware_without_local_preset,
    firmware_catalog_json_schema,
    load_firmware_catalog,
    match_catalog_for_mcu,
)
from app.main import app
from app.printers import PrinterCreate, PrinterRepository


def test_list_board_presets_contains_common_voron_boards(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = FirmwareBoardRepository(database_path)

    preset_ids = {preset.id for preset in repository.list_presets()}

    assert "btt_octopus_pro_f446_usb_can" in preset_ids
    assert "btt_ebb36_g0b1_can" in preset_ids
    assert "btt_sb2209_rp2040_can" in preset_ids
    assert "mellow_fly_sht36_v2_g0b1_can" in preset_ids
    assert "fysetc_spider_f446_usb" in preset_ids


def test_board_presets_endpoint_contains_pkg33_catalog_presets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.get("/api/firmware/board-presets")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    presets = {preset["id"]: preset for preset in response.json()["presets"]}
    expected_ids = {
        "btt_kraken_h723_usb_can",
        "btt_manta_m5p_g0b1_usb_can",
        "btt_manta_m8p_v2_h723_usb_can",
        "btt_skr_3_h743_usb_can",
        "fysetc_spider_v2_2_f446_usb_can",
        "fysetc_spider_v2_3_f446_usb_can",
        "fysetc_spider_v3_h723_usb_can",
        "fysetc_h36_g0b1_can",
        "fysetc_sb_combo_v2_f072_can",
        "mellow_fly_super8_pro_h723_usb_can",
        "mellow_fly_sb2040_v3_rp2040_can",
        "mellow_fly_sht36_v3_rp2040_can",
    }

    assert expected_ids <= presets.keys()
    for preset_id in expected_ids:
        preset = presets[preset_id]
        assert preset["mcu"]
        assert preset["architecture"]
        assert preset["communication"]
        assert preset["connection_type"] in {"can", "usb_can_bridge"}
        assert preset["config_file"] == f"firmware/{preset_id}.config"
        assert preset["build_output"] in {"out/klipper.bin", "out/klipper.uf2"}
        assert preset["default_flash_method"] in {"katapult_can", "katapult_usb_can"}
        assert preset["build_config_status"] == "complete"
        assert preset["build_config_validation"] == {
            "status": "complete",
            "missing_fields": [],
            "invalid_fields": [],
        }
        assert preset["build_config"]["schema_version"] == 1
        assert preset["build_config"]["mcu"] == preset["mcu"]
        assert preset["build_config"]["config_file"] == preset["config_file"]
        assert preset["build_config"]["build_output"] == preset["build_output"]


def test_firmware_build_config_classifies_complete_missing_and_invalid_presets() -> None:
    complete = BOARD_PRESETS["btt_kraken_h723_usb_can"]
    missing = BoardPreset(
        id="test_missing_config",
        vendor="Test",
        name="Test Missing Config",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        config_file="firmware/test_missing_config.config",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        build_config=FirmwareBuildConfig.model_construct(
            schema_version=1,
            architecture="stm32",
            mcu="stm32g0b1",
            processor_model="",
            bootloader_offset="8KiB",
            clock_reference="8 MHz crystal",
            communication_interface="CAN bus",
            connection_type="can",
            canbus_pins="PB0/PB1",
            usb_pins=None,
            serial_pins=None,
            config_file="firmware/test_missing_config.config",
            build_output="out/klipper.bin",
        ),
        notes="Fixture local de teste.",
    )
    invalid = BoardPreset(
        id="test_invalid_config",
        vendor="Test",
        name="Test Invalid Config",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        config_file="firmware/test_invalid_config.config",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        build_config=FirmwareBuildConfig(
            architecture="rp2040",
            mcu="rp2040",
            processor_model="RP2040",
            bootloader_offset="none",
            clock_reference="12 MHz crystal",
            communication_interface="CAN bus",
            connection_type="can",
            config_file="firmware/test_invalid_config.config",
            build_output="out/klipper.bin",
        ),
        notes="Fixture local de teste.",
    )

    assert complete.build_config_status == "complete"
    assert missing.build_config_status == "missing_data"
    assert missing.build_config_validation.missing_fields == ["processor_model"]
    assert invalid.build_config_status == "invalid"
    assert invalid.build_config_validation.invalid_fields == ["architecture", "mcu", "bootloader_offset"]


def test_firmware_build_config_schema_invalid_fails_with_clear_error() -> None:
    with pytest.raises(ValueError, match="config_file must end with .config"):
        FirmwareBuildConfig(
            architecture="stm32",
            mcu="stm32g0b1",
            processor_model="STM32G0B1",
            bootloader_offset="8KiB",
            clock_reference="8 MHz crystal",
            communication_interface="CAN bus",
            connection_type="can",
            config_file="firmware/test.txt",
            build_output="out/klipper.bin",
        )

    with pytest.raises(ValueError, match="build_output must end with .bin or .uf2"):
        FirmwareBuildConfig(
            architecture="stm32",
            mcu="stm32g0b1",
            processor_model="STM32G0B1",
            bootloader_offset="8KiB",
            clock_reference="8 MHz crystal",
            communication_interface="CAN bus",
            connection_type="can",
            config_file="firmware/test.config",
            build_output="out/klipper.hex",
        )


def test_firmware_config_preview_is_deterministic_for_stm32_snapshot() -> None:
    preview = generate_firmware_config_preview(BOARD_PRESETS["btt_kraken_h723_usb_can"])

    assert preview.safe_mode == "config_preview_only_no_write"
    assert preview.artifact_saved is False
    assert preview.artifact_path is None
    assert preview.content == """# Printora firmware .config preview
# preset_id=btt_kraken_h723_usb_can
# preset_name=BTT Kraken STM32H723 USB-CAN bridge
# schema_version=1
CONFIG_LOW_LEVEL_OPTIONS=y
CONFIG_MACH_STM32=y
CONFIG_MCU="stm32h723"
CONFIG_PROCESSOR_MODEL="STM32H723"
CONFIG_BOOTLOADER_OFFSET="128KiB"
CONFIG_CLOCK_REFERENCE="25 MHz crystal"
CONFIG_COMMUNICATION_INTERFACE="USB to CAN bus bridge"
CONFIG_CONNECTION_TYPE="usb_can_bridge"
CONFIG_CANBUS_PINS="PD0/PD1"
CONFIG_USB_PINS="PA11/PA12"
CONFIG_PRINTORA_CONFIG_FILE="firmware/btt_kraken_h723_usb_can.config"
CONFIG_PRINTORA_BUILD_OUTPUT="out/klipper.bin"
CONFIG_PRINTORA_FLASH_AUTOMATICO=n
"""


def test_firmware_config_preview_is_deterministic_for_rp2040_snapshot() -> None:
    preview = generate_firmware_config_preview(BOARD_PRESETS["mellow_fly_sb2040_v3_rp2040_can"])

    assert preview.content == """# Printora firmware .config preview
# preset_id=mellow_fly_sb2040_v3_rp2040_can
# preset_name=Mellow Fly SB2040 v3 RP2040 CAN
# schema_version=1
CONFIG_LOW_LEVEL_OPTIONS=y
CONFIG_MACH_RP2040=y
CONFIG_MCU="rp2040"
CONFIG_PROCESSOR_MODEL="RP2040"
CONFIG_BOOTLOADER_OFFSET="none"
CONFIG_CLOCK_REFERENCE="12 MHz crystal"
CONFIG_COMMUNICATION_INTERFACE="CAN bus"
CONFIG_CONNECTION_TYPE="can"
CONFIG_PRINTORA_CONFIG_FILE="firmware/mellow_fly_sb2040_v3_rp2040_can.config"
CONFIG_PRINTORA_BUILD_OUTPUT="out/klipper.uf2"
CONFIG_PRINTORA_FLASH_AUTOMATICO=n
"""
    assert preview.lines == preview.content.rstrip("\n").splitlines()


def test_firmware_config_preview_blocks_incomplete_preset() -> None:
    preset = BoardPreset(
        id="test_missing_config_preview",
        vendor="Test",
        name="Test Missing Config Preview",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        config_file="firmware/test_missing_config_preview.config",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        build_config=FirmwareBuildConfig.model_construct(
            schema_version=1,
            architecture="stm32",
            mcu="stm32g0b1",
            processor_model="",
            bootloader_offset="8KiB",
            clock_reference="8 MHz crystal",
            communication_interface="CAN bus",
            connection_type="can",
            canbus_pins="PB0/PB1",
            usb_pins=None,
            serial_pins=None,
            config_file="firmware/test_missing_config_preview.config",
            build_output="out/klipper.bin",
        ),
        notes="Fixture local de teste.",
    )

    with pytest.raises(ValueError, match="preset build config is missing_data: processor_model"):
        generate_firmware_config_preview(preset)


def test_firmware_config_preview_endpoint_does_not_execute_external_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    def fail_subprocess_run(*_args, **_kwargs):
        raise AssertionError("config preview must not execute commands")

    monkeypatch.setattr("subprocess.run", fail_subprocess_run)
    try:
        with TestClient(app) as client:
            response = client.get("/api/firmware/board-presets/btt_kraken_h723_usb_can/config-preview")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["preset_id"] == "btt_kraken_h723_usb_can"
    assert payload["artifact_saved"] is False
    assert payload["artifact_path"] is None
    assert payload["content"].endswith("CONFIG_PRINTORA_FLASH_AUTOMATICO=n\n")


def test_pkg33_presets_are_metadata_only() -> None:
    forbidden_tokens = ("make", "flash", "ssh", "restart", "reboot", "shutdown", "systemctl")
    pkg33_ids = {
        preset_id
        for preset_id in BOARD_PRESETS
        if preset_id.startswith(("btt_kraken", "btt_manta", "btt_skr_3", "fysetc_spider_v2", "fysetc_spider_v3", "fysetc_h36", "fysetc_sb_combo", "mellow_fly_super8", "mellow_fly_sb2040_v3", "mellow_fly_sht36_v3"))
    }

    assert pkg33_ids
    for preset_id in pkg33_ids:
        preset = BOARD_PRESETS[preset_id]
        serialized = " ".join([preset.id, preset.name, preset.notes]).lower()
        assert not any(token in serialized for token in forbidden_tokens)


def test_esoterical_catalog_contains_core_can_hardware() -> None:
    counts = catalog_counts()

    assert counts["hardware_with_guides"] >= 10
    assert match_catalog_for_mcu(mcu_name="EBBCan", mcu_version="stm32g0b1 firmware")[0].role == "toolhead"
    assert any(match.id == "bigtreetech_octopus" for match in match_catalog_for_mcu(mcu_name="mcu", mcu_version="stm32f446 firmware"))


def test_firmware_catalog_matches_official_schema() -> None:
    catalog = FirmwareCatalog.model_validate(load_firmware_catalog())
    schema = firmware_catalog_json_schema()

    assert catalog.schema_version == 1
    assert catalog.manifest.total_pages == 83
    assert catalog.generation_metadata.manifest_path == "backend/app/data/firmware_canbus_manifest.json"
    assert catalog.update_flows
    assert catalog.katapult.guide_url == "https://canbus.esoterical.online/katapult_updating.html"
    assert catalog.can_speed.guide_url == "https://canbus.esoterical.online/updating_can_speed.html"
    assert {"source", "manifest", "workflows", "hardware", "troubleshooting", "update_flows", "katapult", "can_speed", "known_hardware_without_local_preset", "generation_metadata"} <= set(schema["properties"])
    hardware_schema = schema["$defs"]["FirmwareCatalogHardware"]["properties"]
    assert {"id", "vendor", "modelo", "role", "connection", "guide_url", "known_mcus", "flash_method", "bootloader", "katapult", "validation_commands", "safety_notes", "preset_ids", "catalog_status"} <= set(hardware_schema)


def test_firmware_catalog_normalizes_manifest_categories() -> None:
    catalog = FirmwareCatalog.model_validate(load_firmware_catalog())
    roles = Counter(item.role for item in catalog.hardware)

    assert len(catalog.hardware) == 56
    assert roles["can_adapter"] == 3
    assert roles["mainboard"] == 28
    assert roles["toolhead"] == 25
    assert len(catalog.workflows) == 9
    assert len(catalog.update_flows) == 5
    assert len(catalog.troubleshooting) == 12
    assert catalog.manifest.total_pages == 83
    assert catalog.manifest.pages
    assert all(item.catalog_status == "catalogada" for item in catalog.hardware)
    assert all(item.safety_notes for item in catalog.hardware)
    assert any(item.vendor == "BigTreeTech" and item.name == "Octopus" for item in catalog.hardware)
    assert "can_adapters" in catalog.known_hardware_without_local_preset
    assert catalog.can_speed.supported_bitrates


def test_firmware_catalog_maps_local_presets_and_missing_hardware() -> None:
    catalog = FirmwareCatalog.model_validate(load_firmware_catalog())
    by_label = {f"{item.vendor} {item.name}": item for item in catalog.hardware}
    missing = catalog_hardware_without_local_preset()
    counts = catalog_counts()

    assert by_label["BigTreeTech Octopus"].preset_ids == ["btt_octopus_v1_1_f446_usb_can"]
    assert by_label["BigTreeTech Octopus Pro v1.1"].preset_ids == [
        "btt_octopus_pro_f446_usb_can",
        "btt_octopus_pro_h723_usb_can",
    ]
    assert by_label["BigTreeTech SB2209 and SB2240"].preset_ids == [
        "btt_sb2209_rp2040_can",
        "btt_sb2240_rp2040_can",
    ]
    assert by_label["Fysetc Spider V1.0"].preset_ids == ["fysetc_spider_f446_usb"]
    assert by_label["BigTreeTech Kraken"].preset_ids == ["btt_kraken_h723_usb_can"]
    assert by_label["BigTreeTech Manta M5P V1.0"].preset_ids == ["btt_manta_m5p_g0b1_usb_can"]
    assert by_label["BigTreeTech Manta M8P V2.0"].preset_ids == ["btt_manta_m8p_v2_h723_usb_can"]
    assert by_label["BigTreeTech SKR-3"].preset_ids == ["btt_skr_3_h743_usb_can"]
    assert by_label["Fysetc Spider v2.2"].preset_ids == ["fysetc_spider_v2_2_f446_usb_can"]
    assert by_label["Fysetc Spider v2.3"].preset_ids == ["fysetc_spider_v2_3_f446_usb_can"]
    assert by_label["Fysetc Spider v3.0 H7"].preset_ids == ["fysetc_spider_v3_h723_usb_can"]
    assert by_label["Fysetc H36"].preset_ids == ["fysetc_h36_g0b1_can"]
    assert by_label["Fysetc SB Combo V2"].preset_ids == ["fysetc_sb_combo_v2_f072_can"]
    assert by_label["Mellow Fly-Super8 Pro H723"].preset_ids == ["mellow_fly_super8_pro_h723_usb_can"]
    assert by_label["Mellow Fly SB2040v3"].preset_ids == ["mellow_fly_sb2040_v3_rp2040_can"]
    assert by_label["Mellow Fly SHT36v3"].preset_ids == ["mellow_fly_sht36_v3_rp2040_can"]
    assert by_label["BigTreeTech Octopus Max EZ"].preset_ids == []
    assert "BigTreeTech Octopus Max EZ" in missing["mainboards"]
    assert "BigTreeTech Octopus Pro v1.1" not in missing["mainboards"]
    assert "BigTreeTech Kraken" not in missing["mainboards"]
    assert "Mellow Fly SHT36v3" not in missing["toolheads"]
    assert counts["hardware_with_local_preset"] == 23
    assert counts["hardware_without_local_preset"] == 33


def test_firmware_catalog_summary_endpoint_is_local_read_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("runtime must not fetch external CANBus site")

    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)
    try:
        with TestClient(app) as client:
            response = client.get("/api/firmware/catalog")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["safe_mode"] == "local_catalog_read_only"
    assert payload["manifest_total_pages"] == 83
    assert payload["category_counts"]["mainboard"] == 28
    assert payload["status_counts"]["catalogada"] == 83
    assert payload["hardware_role_counts"] == {"mainboard": 28, "toolhead": 25, "can_adapter": 3, "unknown": 0}
    assert payload["catalog_counts"]["hardware_with_local_preset"] == 23
    assert payload["catalog_counts"]["hardware_without_local_preset"] == 33
    assert "BigTreeTech Octopus Max EZ" in payload["hardware_without_local_preset"]["mainboards"]
    assert "hardware" not in payload


def test_firmware_inventory_api_enriches_registered_and_detected_boards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    async def fake_agent_run(self, printer, *, job_type, payload=None, timeout_seconds=12.0, require_online=True):
        assert job_type == "remote_firmware_inventory"
        return SimpleNamespace(
            result={
                "objects_list": ["mcu", "mcu EBBCan", "configfile"],
                "object_payload": {
                    "result": {
                        "status": {
                            "mcu": {"mcu_version": "stm32f446 firmware"},
                            "mcu EBBCan": {"mcu_version": "stm32g0b1 firmware"},
                            "configfile": {
                                "settings": {
                                    "mcu": {"canbus_uuid": "abc123"},
                                    "mcu EBBCan": {"canbus_uuid": "def456", "canbus_interface": "can0"},
                                }
                            },
                        }
                    }
                },
            }
        )

    monkeypatch.setattr("app.routes.firmware.AgentCommandExecutor.run", fake_agent_run)
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://127.0.0.1:7125",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200
            printer_id = created.json()["id"]
            board = client.post(
                f"/api/printers/{printer_id}/firmware/boards",
                json={
                    "name": "EBBCan",
                    "preset_id": "btt_ebb36_g0b1_can",
                    "can_uuid": "def456",
                    "config_file": "firmware/ebbcan.config",
                },
            )
            assert board.status_code == 200
            response = client.get(f"/api/printers/{printer_id}/firmware/hardware-inventory")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog_counts"]["hardware_with_guides"] == 56
    assert payload["catalog_hardware_without_local_preset"]["can_adapters"]
    registered = next(item for item in payload["items"] if item["status"] == "registered")
    detected_main = next(item for item in payload["items"] if item["name"] == "MCU principal")
    assert registered["matched_preset_ids"] == ["btt_ebb36_g0b1_can"]
    assert registered["catalog_references"][0]["label"].startswith("BigTreeTech EBB36")
    assert detected_main["matched_catalog_ids"]
    assert any(reference["guide_url"].startswith("https://canbus.esoterical.online/") for reference in detected_main["catalog_references"])
    assert all(item["name"] != "EBBCan" or item["status"] == "registered" for item in payload["items"])


def test_firmware_inventory_detects_klipper_mcus_without_manual_board() -> None:
    inventory = build_firmware_hardware_inventory(
        printer_id=1,
        registered_boards=[],
        object_names=["mcu", "mcu EBBCan", "configfile"],
        object_payload={
            "status": {
                "mcu": {"mcu_version": "stm32f446"},
                "mcu EBBCan": {"mcu_version": "stm32g0b1"},
                "configfile": {
                    "settings": {
                        "mcu": {"canbus_uuid": "abc123"},
                        "mcu EBBCan": {"canbus_uuid": "def456", "canbus_interface": "can0"},
                    }
                },
            }
        },
    )

    assert inventory.items[0].role == "mainboard"
    assert any(item.name == "EBBCan" and item.can_uuid == "def456" for item in inventory.items)
    assert "BigTreeTech Octopus Max EZ" in inventory.catalog_hardware_without_local_preset["mainboards"]
    assert inventory.catalog_counts["hardware_with_local_preset"] == 23
    assert "detectada" in inventory.summary


def test_firmware_inventory_does_not_duplicate_registered_detected_mcu() -> None:
    inventory = build_firmware_hardware_inventory(
        printer_id=1,
        registered_boards=[
            SimpleNamespace(
                id=10,
                printer_id=1,
                name="EBBCan",
                preset_id="btt_ebb36_g0b1_can",
                can_uuid="def456",
                can_interface="can0",
                connection_type="can",
                mcu="stm32g0b1",
                flash_method="katapult_can",
                config_file="firmware/ebbcan.config",
                notes="",
                is_active=True,
                created_at="2026-05-26T00:00:00",
                updated_at="2026-05-26T00:00:00",
            )
        ],
        object_names=["mcu EBBCan", "configfile"],
        object_payload={
            "status": {
                "mcu EBBCan": {"mcu_version": "stm32g0b1"},
                "configfile": {"settings": {"mcu EBBCan": {"canbus_uuid": "def456", "canbus_interface": "can0"}}},
            }
        },
    )

    assert [item.name for item in inventory.items] == ["EBBCan"]
    assert inventory.items[0].status == "registered"
    assert inventory.summary == "1 cadastrada(s), 0 detectada(s) pelo Klipper."


def test_create_firmware_board_from_preset(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)

    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    assert board.name == "EBB T0"
    assert board.mcu == "stm32g0b1"
    assert board.connection_type == "can"
    assert board.flash_method == "katapult_can"
    assert board.config_file == "firmware/ebb_t0.config"


def test_create_firmware_board_is_idempotent_for_same_can_uuid(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)

    first = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBBCan",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )
    second = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBBCan",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    assert second.id == first.id
    assert len(repository.list_boards(printer.id)) == 1


def test_firmware_recovery_plan_is_manual_and_blocked(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    plan = repository.build_recovery_plan(board.id)

    assert plan.safe_mode == "manual_recovery_plan_only"
    assert plan.blocked is True
    assert plan.board_id == board.id
    assert any("Katapult" in step for step in plan.recovery_steps)
    assert any("não executou flash" in note for note in plan.rollback_notes)


def test_can_board_requires_uuid(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)

    with pytest.raises(ValueError, match="can_uuid is required"):
        repository.create_board(
            printer.id,
            FirmwareBoardCreate(name="EBB T0", preset_id="btt_ebb36_g0b1_can"),
        )


def test_firmware_boards_are_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Other", moonraker_url="http://other.local:7125"))
    repository = FirmwareBoardRepository(database_path)

    repository.create_board(
        first.id,
        FirmwareBoardCreate(name="Octopus", preset_id="btt_octopus_pro_f446_usb_can", can_uuid="862bb5a4c690"),
    )
    repository.create_board(
        second.id,
        FirmwareBoardCreate(name="EBB", preset_id="btt_ebb36_g0b1_can", can_uuid="fd7bbba1e6aa"),
    )

    assert len(repository.list_boards(first.id)) == 1
    assert repository.list_boards(first.id)[0].name == "Octopus"


def test_create_firmware_build_dry_run_generates_safe_artifact_plan(tmp_path: Path, monkeypatch) -> None:
    import app.firmware.build_service as build_service

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("dry-run must not execute external commands")

    monkeypatch.setattr(build_service.subprocess, "run", fail_if_called)
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    run = repository.create_build_dry_run(
        board.id,
        FirmwareBuildDryRunCreate(
            klipper_path="~/klipper",
            output_root="~/printer_data/firmware_builds",
        ),
    )

    assert run.status == "dry_run_planned"
    assert run.printer_id == printer.id
    assert run.board_id == board.id
    assert run.preset_id == "btt_ebb36_g0b1_can"
    assert run.preset_build_config_status == "complete"
    assert run.generated_config_path.endswith("/DRY-RUN/ebb-t0/generated/ebb_t0.config")
    assert run.config_backup_path.endswith("/DRY-RUN/ebb-t0/.config.before-build")
    assert run.work_dir == "~/klipper"
    assert run.expected_build_output == "~/klipper/out/klipper.bin"
    assert run.binary_output_path.endswith("/klipper.bin")
    assert run.log_path.endswith("/DRY-RUN/ebb-t0/logs/build.log")
    assert "PLAN make clean" in run.commands
    assert "PLAN make" in run.commands
    assert all(command.startswith("PLAN ") for command in run.commands)
    assert any("não executou comandos" in item for item in run.checklist)
    history = repository.list_build_runs(printer.id)
    assert len(history) == 1
    assert history[0].board_id == board.id
    assert history[0].preset_id == run.preset_id
    assert history[0].generated_config_path == run.generated_config_path


def test_build_dry_run_rejects_incomplete_preset_without_external_command(
    tmp_path: Path, monkeypatch
) -> None:
    import app.firmware.build_service as build_service

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("dry-run must not execute external commands")

    incomplete_preset = BoardPreset.model_construct(
        id="test_incomplete_usb",
        vendor="Test",
        name="Incomplete USB",
        mcu="stm32f446",
        architecture="stm32",
        connection_type="usb",
        communication="USB",
        bootloader_offset="32KiB",
        canbus_pins=None,
        config_file="firmware/test_incomplete.config",
        build_output="out/klipper.bin",
        default_flash_method="dfu_usb",
        build_config=None,
        notes="Fixture incompleta para validar bloqueio de dry-run.",
    )
    monkeypatch.setattr(build_service.subprocess, "run", fail_if_called)
    monkeypatch.setitem(BOARD_PRESETS, incomplete_preset.id, incomplete_preset)
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(name="Incomplete", preset_id=incomplete_preset.id),
    )

    with pytest.raises(ValueError, match="preset build config is missing_data"):
        repository.create_build_dry_run(board.id, FirmwareBuildDryRunCreate())

    assert repository.list_build_runs(printer.id) == []


def test_build_dry_run_api_returns_planned_artifact_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    def fail_subprocess_run(*_args, **_kwargs):
        raise AssertionError("dry-run API must not execute commands")

    monkeypatch.setattr("subprocess.run", fail_subprocess_run)
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://127.0.0.1:7125",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200
            printer_id = created.json()["id"]
            board = client.post(
                f"/api/printers/{printer_id}/firmware/boards",
                json={
                    "name": "EBB T0",
                    "preset_id": "btt_ebb36_g0b1_can",
                    "can_uuid": "fd7bbba1e6aa",
                    "config_file": "firmware/ebb_t0.config",
                },
            )
            assert board.status_code == 200
            board_id = board.json()["id"]

            response = client.post(
                f"/api/firmware/boards/{board_id}/build-runs/dry-run",
                json={
                    "klipper_path": "~/klipper",
                    "output_root": "~/printer_data/firmware_builds",
                },
            )
            history = client.get(f"/api/printers/{printer_id}/firmware/build-runs")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["preset_id"] == "btt_ebb36_g0b1_can"
    assert payload["preset_build_config_status"] == "complete"
    assert payload["generated_config_path"].endswith("/DRY-RUN/ebb-t0/generated/ebb_t0.config")
    assert payload["config_backup_path"].endswith("/DRY-RUN/ebb-t0/.config.before-build")
    assert payload["work_dir"] == "~/klipper"
    assert payload["expected_build_output"] == "~/klipper/out/klipper.bin"
    assert payload["log_path"].endswith("/DRY-RUN/ebb-t0/logs/build.log")
    assert all(command.startswith("PLAN ") for command in payload["commands"])
    assert history.status_code == 200
    assert history.json()["runs"][0]["board_id"] == board_id
    assert history.json()["runs"][0]["generated_config_path"] == payload["generated_config_path"]


def test_build_dry_run_requires_existing_board(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = FirmwareBoardRepository(database_path)

    with pytest.raises(ValueError, match="firmware board not found"):
        repository.create_build_dry_run(999, FirmwareBuildDryRunCreate())


def test_local_build_preflight_is_read_only_and_blocked_by_default(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    klipper_path = tmp_path / "klipper"
    firmware_dir = klipper_path / "firmware"
    firmware_dir.mkdir(parents=True)
    (klipper_path / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
    (klipper_path / ".config").write_text("CURRENT\n", encoding="utf-8")
    (firmware_dir / "ebb_t0.config").write_text("BOARD\n", encoding="utf-8")
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    preflight = repository.build_build_preflight(
        board.id,
        FirmwareBuildDryRunCreate(klipper_path=str(klipper_path), output_root=str(tmp_path / "builds")),
        mode="disabled",
    )

    assert preflight.safe_mode == "local_build_preflight_read_only"
    assert preflight.blocked is True
    assert preflight.can_execute_build is False
    assert any(check.key == "build_mode" and check.status == "blocked" for check in preflight.checks)
    assert not (tmp_path / "builds").exists()


def test_local_build_preflight_reports_ready_but_keeps_execution_blocked(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    klipper_path = tmp_path / "klipper"
    firmware_dir = klipper_path / "firmware"
    firmware_dir.mkdir(parents=True)
    (klipper_path / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
    (klipper_path / ".config").write_text("CURRENT\n", encoding="utf-8")
    (firmware_dir / "ebb_t0.config").write_text("BOARD\n", encoding="utf-8")
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    preflight = repository.build_build_preflight(
        board.id,
        FirmwareBuildDryRunCreate(klipper_path=str(klipper_path), output_root=str(tmp_path / "builds")),
        mode="local",
    )

    blocking_checks = [check for check in preflight.checks if check.status == "blocked"]
    assert blocking_checks == []
    assert preflight.blocked is True
    assert preflight.can_execute_build is False
    assert "make" in "\n".join(preflight.commands_preview)


def test_local_build_is_blocked_when_mode_disabled(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    run = repository.execute_build_local(
        board.id,
        FirmwareBuildExecuteCreate(confirmation="EXECUTE_LOCAL_BUILD_NO_FLASH"),
        mode="disabled",
        timeout_seconds=1,
    )

    assert run.status == "blocked_build_mode_disabled"
    assert "bloqueado" in run.message
    assert len(repository.list_build_runs(printer.id)) == 1


def test_local_build_blocks_and_records_missing_confirmation(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    run = repository.execute_build_local(
        board.id,
        FirmwareBuildExecuteCreate(confirmation="wrong"),
        mode="local",
        timeout_seconds=1,
    )

    assert run.status == "blocked_invalid_build_confirmation"
    assert "confirmação textual" in run.message
    assert len(repository.list_build_runs(printer.id)) == 1


def test_local_build_restores_config_and_copies_binary(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    klipper_path = tmp_path / "klipper"
    output_root = tmp_path / "builds"
    klipper_path.mkdir(parents=True)
    (klipper_path / ".config").write_text("ORIGINAL_CONFIG\n")
    (klipper_path / "Makefile").write_text(
        ".DEFAULT_GOAL := all\n\nclean:\n\t@rm -rf out\n\nall:\n\t@grep -q CONFIG_PRINTORA_FLASH_AUTOMATICO .config\n\t@mkdir -p out\n\t@printf 'bin' > out/klipper.bin\n\t@echo build-ok\n",
        encoding="utf-8",
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    run = repository.execute_build_local(
        board.id,
        FirmwareBuildExecuteCreate(
            klipper_path=str(klipper_path),
            output_root=str(output_root),
            confirmation="EXECUTE_LOCAL_BUILD_NO_FLASH",
        ),
        mode="local",
        timeout_seconds=10,
    )

    assert run.status == "build_success"
    assert (klipper_path / ".config").read_text() == "ORIGINAL_CONFIG\n"
    assert Path(run.generated_config_path).read_text().endswith("CONFIG_PRINTORA_FLASH_AUTOMATICO=n\n")
    assert Path(run.binary_output_path).read_text() == "bin"
    assert Path(run.config_backup_path).read_text() == "ORIGINAL_CONFIG\n"
    assert Path(run.log_path).is_file()
    assert "build-ok" in run.message
    assert run.preset_id == "btt_ebb36_g0b1_can"
    unsafe_plan = "\n".join(run.commands).lower()
    assert "ssh" not in unsafe_plan
    assert "flashtool.py" not in unsafe_plan
    assert "restart" not in unsafe_plan


def test_local_build_restores_config_and_records_failure(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    klipper_path = tmp_path / "klipper"
    output_root = tmp_path / "builds"
    klipper_path.mkdir(parents=True)
    (klipper_path / ".config").write_text("ORIGINAL_CONFIG\n", encoding="utf-8")
    (klipper_path / "Makefile").write_text(
        ".DEFAULT_GOAL := all\n\nclean:\n\t@true\n\nall:\n\t@echo build-failed\n\t@exit 2\n",
        encoding="utf-8",
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )

    run = repository.execute_build_local(
        board.id,
        FirmwareBuildExecuteCreate(
            klipper_path=str(klipper_path),
            output_root=str(output_root),
            confirmation="EXECUTE_LOCAL_BUILD_NO_FLASH",
        ),
        mode="local",
        timeout_seconds=10,
    )

    assert run.status == "build_failed"
    assert (klipper_path / ".config").read_text() == "ORIGINAL_CONFIG\n"
    assert Path(run.generated_config_path).is_file()
    assert Path(run.config_backup_path).read_text() == "ORIGINAL_CONFIG\n"
    assert "build-failed" in Path(run.log_path).read_text()
    assert not Path(run.binary_output_path).exists()


def test_create_firmware_flash_dry_run_uses_latest_build_plan(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
            config_file="firmware/ebb_t0.config",
        ),
    )
    build_run = repository.create_build_dry_run(board.id, FirmwareBuildDryRunCreate())

    flash_run = repository.create_flash_dry_run(board.id, FirmwareFlashDryRunCreate(build_run_id=build_run.id))

    assert flash_run.status == "flash_dry_run_planned"
    assert flash_run.build_run_id == build_run.id
    assert flash_run.binary_path == build_run.binary_output_path
    assert flash_run.can_uuid == "fd7bbba1e6aa"
    assert any("flashtool.py" in command for command in flash_run.commands)
    assert any("nenhum comando foi executado" in item for item in flash_run.checklist)
    assert len(repository.list_flash_runs(printer.id)) == 1


def test_flash_dry_run_rejects_build_run_from_other_board(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    first_board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="Octopus",
            preset_id="btt_octopus_pro_f446_usb_can",
            can_uuid="862bb5a4c690",
        ),
    )
    second_board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
        ),
    )
    build_run = repository.create_build_dry_run(first_board.id, FirmwareBuildDryRunCreate())

    with pytest.raises(ValueError, match="does not belong"):
        repository.create_flash_dry_run(second_board.id, FirmwareFlashDryRunCreate(build_run_id=build_run.id))


def test_flash_preflight_is_read_only_and_always_blocks_execution(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
        ),
    )

    preflight = repository.build_flash_preflight(
        board.id,
        FirmwareFlashDryRunCreate(binary_path="/tmp/klipper.bin"),
        {
            "connected": True,
            "printing": False,
            "print_state": "standby",
            "klipper_state": "ready",
            "klippy_state": "ready",
        },
    )

    assert preflight.safe_mode == "flash_preflight_read_only"
    assert preflight.blocked is True
    assert preflight.can_execute_flash is False
    assert preflight.printing is False
    assert preflight.binary_path == "/tmp/klipper.bin"
    assert any(check.key == "execution_policy" and check.status == "blocked" for check in preflight.checks)
    assert any("flashtool.py" in command for command in preflight.commands_preview)


def test_flash_preflight_blocks_while_printing(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
        ),
    )

    preflight = repository.build_flash_preflight(
        board.id,
        FirmwareFlashDryRunCreate(),
        {
            "connected": True,
            "printing": True,
            "print_state": "printing",
            "klipper_state": "ready",
            "klippy_state": "ready",
        },
    )

    assert preflight.printing is True
    assert any(check.key == "not_printing" and check.status == "blocked" for check in preflight.checks)
    assert preflight.can_execute_flash is False


def test_flash_execution_gate_is_always_blocked(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
        ),
    )

    run = repository.execute_flash_blocked(
        board.id,
        FirmwareFlashExecuteCreate(confirmation="BLOCK_REAL_FLASH"),
    )

    assert run.status == "blocked_flash_execution"
    assert "bloqueada" in run.message
    assert any("Nenhum flash" in item for item in run.checklist)
    assert len(repository.list_flash_runs(printer.id)) == 1


def test_flash_execution_gate_requires_confirmation(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = FirmwareBoardRepository(database_path)
    board = repository.create_board(
        printer.id,
        FirmwareBoardCreate(
            name="EBB T0",
            preset_id="btt_ebb36_g0b1_can",
            can_uuid="fd7bbba1e6aa",
        ),
    )

    with pytest.raises(ValueError, match="invalid flash confirmation"):
        repository.execute_flash_blocked(board.id, FirmwareFlashExecuteCreate(confirmation="wrong"))
