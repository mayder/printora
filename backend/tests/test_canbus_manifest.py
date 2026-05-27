import importlib.util
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "backend" / "app" / "data" / "firmware_canbus_manifest.json"
CATALOG_PATH = PROJECT_ROOT / "backend" / "app" / "data" / "firmware_hardware_catalog.json"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build_canbus_manifest.py"
CATALOG_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build_firmware_catalog.py"
ALLOWED_STATUSES = {"catalogada", "ignorada_com_motivo", "bloqueada_com_motivo"}
HARDWARE_CATEGORIES = {"can_adapter", "mainboard", "toolhead"}
WORKFLOW_CATEGORIES = {
    "home",
    "getting_started",
    "can_adapter_overview",
    "usb_can_bridge_overview",
    "mainboard_overview",
    "toolhead_overview",
    "final_steps",
}
EXPECTED_MENU_URLS = {
    "https://canbus.esoterical.online/",
    "https://canbus.esoterical.online/Getting_Started.html",
    "https://canbus.esoterical.online/Dedicated_USB_Can_Device.html",
    "https://canbus.esoterical.online/can_adapter/common_can_adapters.html",
    "https://canbus.esoterical.online/can_adapter/BigTreeTech%20U2C%20v2.1/README.html",
    "https://canbus.esoterical.online/can_adapter/Makerbase%20UTC%201.0/README.html",
    "https://canbus.esoterical.online/can_adapter/Mellow%20Fly%20UTOC-1%20and%20UTOC-3/README.html",
    "https://canbus.esoterical.online/USB_CAN_Bridge_Mainboard.html",
    "https://canbus.esoterical.online/mainboard_flashing.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Kraken/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Manta%20E3EZ/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Manta%20M5P%20V1.0/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Manta%20M8P%20v1.1/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Manta%20M8P%20v2.0/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Octopus/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Octopus%20Max%20EZ/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Octopus%20Pro%20v1.1/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20Octopus%20X7/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20SKR%20Pico/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20SKR-3/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20SKR-3%20EZ/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/BigTreeTech%20SKRat%20v1.0/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Hexa%20Distro%20Fusion/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20King/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20Pro/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20v1.0/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20v2.2/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20v2.3/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20v3.0/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Fysetc%20Spider%20v3.0%20H7/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/LDO%20Leviathan%20v1.2/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/LDO%20Leviathan%20v1.3/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/MKS%20Monster8%20v2/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Mellow%20Fly-D5P/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Mellow%20Fly-Micro4/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Mellow%20Fly-Super8/README.html",
    "https://canbus.esoterical.online/mainboard_flashing/common_hardware/Mellow%20Fly-Super8%20Pro%20H723/README.html",
    "https://canbus.esoterical.online/toolhead_flashing.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/AFC-Lite/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/AFC-Pro/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20EBB36%20Gen2/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20EBB36%20V1.2/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20EBB42%20Gen2/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20EBB42%20V1.2/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20Eddy%20Duo/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20MMB%20CAN%20V1.0/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20MMB%20CAN%20v2.0/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20SB2209%20(RP2040)/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20SB2209%20and%20SB2240/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/DragonDinghy/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Fysetc%20H36/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Fysetc%20H36%20V2.0/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Fysetc%20PITB%20V1.0/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Fysetc%20PITB%20V2.0/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Fysetc%20SB%20Combo%20V2/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Fysetc%20SB-CAN-TH/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/MKS%20THR36%20V1.0/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Mellow%20Fly%20ERCF/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Mellow%20Fly%20SB2040/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Mellow%20Fly%20SB2040v3/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Mellow%20Fly%20SHT36%20and%20SHT42/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Mellow%20Fly%20SHT36v2/README.html",
    "https://canbus.esoterical.online/toolhead_flashing/common_hardware/Mellow%20Fly%20SHT36v3/README.html",
    "https://canbus.esoterical.online/Final_Steps.html",
    "https://canbus.esoterical.online/Updating.html",
    "https://canbus.esoterical.online/toolhead_klipper_updating.html",
    "https://canbus.esoterical.online/mainboard_klipper_updating.html",
    "https://canbus.esoterical.online/katapult_updating.html",
    "https://canbus.esoterical.online/updating_can_speed.html",
    "https://canbus.esoterical.online/troubleshooting.html",
    "https://canbus.esoterical.online/troubleshooting/no_can0.html",
    "https://canbus.esoterical.online/troubleshooting/no_uuid.html",
    "https://canbus.esoterical.online/troubleshooting/klipper_fail_to_start.html",
    "https://canbus.esoterical.online/troubleshooting/timeout_during_homing_probing.html",
    "https://canbus.esoterical.online/troubleshooting/lost_communication_to_mcu.html",
    "https://canbus.esoterical.online/troubleshooting/timer_too_close.html",
    "https://canbus.esoterical.online/troubleshooting/debugging/README.html",
    "https://canbus.esoterical.online/troubleshooting/multiple_can_networks.html",
    "https://canbus.esoterical.online/troubleshooting/other_errors.html",
    "https://canbus.esoterical.online/troubleshooting/tmc_reset_undervoltage.html",
    "https://canbus.esoterical.online/troubleshooting/termination_resistor_info.html",
}


def test_canbus_manifest_covers_known_public_menu_pages() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    urls = {page["url"] for page in manifest["pages"]}

    assert EXPECTED_MENU_URLS <= urls
    assert manifest["summary"]["total_pages"] == len(manifest["pages"])
    assert manifest["summary"]["total_pages"] >= len(EXPECTED_MENU_URLS)


def test_canbus_manifest_page_contract_is_safe_and_versioned() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["source"]["domain"] == "canbus.esoterical.online"
    assert manifest["safe_mode"]["dry_run_default"] is True
    assert manifest["safe_mode"]["mutating_commands_executed"] is False
    for page in manifest["pages"]:
        assert page["url"].startswith("https://canbus.esoterical.online/")
        assert page["title"]
        assert page["category"]
        assert page["status"] in ALLOWED_STATUSES
        if page["status"] == "catalogada":
            assert len(page["content_hash"]) == 64
            assert page["reason"] is None
        else:
            assert page["reason"]


def test_canbus_catalog_represents_every_public_menu_page() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    manifest_pages = manifest["pages"]
    catalog_manifest_pages = catalog["manifest"]["pages"]
    assert len(catalog_manifest_pages) == len(manifest_pages)
    assert [page["url"] for page in catalog_manifest_pages] == [page["url"] for page in manifest_pages]
    for page in catalog_manifest_pages:
        assert page["status"] in ALLOWED_STATUSES
        if page["status"] == "catalogada":
            assert page["content_hash"]
            assert page["title"]
            assert page["category"]
        else:
            assert page["reason"]

    hardware_urls = {item["guide_url"] for item in catalog["hardware"]}
    workflow_urls = {item["url"] for item in catalog["workflows"]}
    update_urls = {item["url"] for item in catalog["update_flows"]}
    troubleshooting_urls = {item["url"] for item in catalog["troubleshooting"]}
    coverage_by_category: dict[str, int] = {}
    for page in catalog_manifest_pages:
        coverage_by_category[page["category"]] = coverage_by_category.get(page["category"], 0) + 1
        if page["status"] != "catalogada":
            continue
        if page["category"] in HARDWARE_CATEGORIES and page["url"].endswith("/README.html"):
            assert page["url"] in hardware_urls
        elif page["category"] == "updating":
            assert page["url"] in update_urls
        elif page["category"] == "troubleshooting":
            assert page["url"] in troubleshooting_urls
        elif page["category"] in WORKFLOW_CATEGORIES:
            assert page["url"] in workflow_urls

    assert coverage_by_category == {
        "can_adapter": 4,
        "can_adapter_overview": 1,
        "final_steps": 1,
        "getting_started": 1,
        "home": 1,
        "mainboard": 28,
        "mainboard_overview": 2,
        "toolhead": 25,
        "toolhead_overview": 2,
        "troubleshooting": 12,
        "updating": 5,
        "usb_can_bridge_overview": 1,
    }


def test_canbus_manifest_parser_reads_nav_links_from_fixture() -> None:
    module = _load_manifest_script()
    html = """
    <nav id="site-nav">
      <ul class="nav-list">
        <li><a href="/" class="nav-list-link">Home</a></li>
        <li><a href="/toolhead_flashing/common_hardware/BigTreeTech%20EBB36%20Gen2/README.html" class="nav-list-link">EBB36</a></li>
      </ul>
    </nav>
    <main><a href="https://example.com">fora</a></main>
    """

    links = module.parse_menu_links(html)

    assert [link.url for link in links] == [
        "https://canbus.esoterical.online/",
        "https://canbus.esoterical.online/toolhead_flashing/common_hardware/BigTreeTech%20EBB36%20Gen2/README.html",
    ]
    assert links[1].category == "toolhead"


def test_canbus_manifest_script_is_dry_run_by_default(tmp_path, capsys, monkeypatch) -> None:
    module = _load_manifest_script()
    output_path = tmp_path / "manifest.json"
    manifest = {
        "schema_version": 1,
        "source": {"domain": "canbus.esoterical.online"},
        "safe_mode": {"dry_run_default": True, "mutating_commands_executed": False},
        "summary": {"total_pages": 0},
        "pages": [],
    }
    monkeypatch.setattr(module, "build_manifest", lambda **_kwargs: manifest)

    result = module.main(["--output", str(output_path), "--retrieved-at", "2026-05-27"])

    assert result == 0
    assert output_path.exists() is False
    assert json.loads(capsys.readouterr().out) == manifest


def test_canbus_manifest_rejects_urls_outside_allowed_domain() -> None:
    module = _load_manifest_script()

    for url in ["https://example.com/", "https://canbus.esoterical.online.evil.test/", "ftp://canbus.esoterical.online/"]:
        try:
            module.assert_allowed_domain(url)
        except ValueError as exc:
            assert "URL fora do domínio permitido" in str(exc)
        else:
            raise AssertionError(f"URL fora do domínio deveria ser bloqueada: {url}")


def test_firmware_catalog_script_is_dry_run_by_default(tmp_path, capsys, monkeypatch) -> None:
    module = _load_catalog_script()
    manifest_path = tmp_path / "manifest.json"
    output_path = tmp_path / "catalog.json"
    manifest_path.write_text("{}", encoding="utf-8")
    catalog = {
        "schema_version": 1,
        "source": {"name": "Esoterical CANBus Guide", "url": "https://canbus.esoterical.online/", "retrieved_at": "2026-05-27", "notes": []},
        "manifest": {"total_pages": 0, "pages": []},
        "workflows": [],
        "hardware": [],
        "known_hardware_without_local_preset": {},
        "troubleshooting": [],
        "update_flows": [],
        "katapult": {},
        "can_speed": {},
        "generation_metadata": {},
    }
    monkeypatch.setattr(module, "build_catalog", lambda **_kwargs: catalog)

    result = module.main(["--manifest", str(manifest_path), "--output", str(output_path), "--generated-at", "2026-05-27"])

    assert result == 0
    assert output_path.exists() is False
    assert json.loads(capsys.readouterr().out) == catalog


def test_firmware_catalog_excludes_mutating_commands_from_references() -> None:
    module = _load_catalog_script()
    commands = module.extract_validation_commands(
        [
            """
            python3 ~/klipper/scripts/canbus_query.py can0
            make flash FLASH_DEVICE=0483:df11
            dfu-util -a 0 -s 0x08000000:leave -D klipper.bin
            sudo reboot
            shutdown now
            lsusb
            grep can0 /etc/network/interfaces
            """
        ]
    )

    assert commands == [
        "python3 ~/klipper/scripts/canbus_query.py can0",
        "lsusb",
        "grep can0 /etc/network/interfaces",
    ]
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    serialized_commands = "\n".join(
        command
        for collection in [catalog["hardware"], catalog["troubleshooting"], catalog["update_flows"]]
        for item in collection
        for command in item.get("validation_commands", [])
    ).lower()
    for forbidden in ["make flash", "dfu-util", "reboot", "shutdown", "firmware_restart"]:
        assert forbidden not in serialized_commands


def _load_manifest_script():
    spec = importlib.util.spec_from_file_location("build_canbus_manifest", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_canbus_manifest"] = module
    spec.loader.exec_module(module)
    return module


def _load_catalog_script():
    spec = importlib.util.spec_from_file_location("build_firmware_catalog", CATALOG_SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_firmware_catalog"] = module
    spec.loader.exec_module(module)
    return module
