from pathlib import Path

from app.database import initialize_database
from app.setup_firmware import (
    FIRMWARE_REMOTE_BUILD_CONFIRMATION,
    SetupFirmwareBuildRequest,
    SetupFirmwareRequest,
    SetupFirmwareRunRepository,
    build_setup_firmware_plan,
)
from app.setup_wizard import SetupSshTarget


def test_firmware_plan_blocks_without_variant_confirmation() -> None:
    request = SetupFirmwareRequest(
        target=SetupSshTarget(host="btt-pi.local", username="pi"),
        preset_id="btt_octopus_pro_h723_usb_can",
        board_name="Octopus Pro H723",
        board_role="mainboard",
        variant_confirmed=False,
    )

    plan = build_setup_firmware_plan(request)

    assert plan.status == "blocked"
    assert "Variante física ainda não confirmada." in plan.blocked_reasons
    assert plan.config_preview.startswith("# Printora firmware .config preview")
    assert all(command.command.startswith("PLAN ") for step in plan.steps for command in step.commands)


def test_firmware_plan_links_confirmed_hardware_to_preset_and_artifacts() -> None:
    request = SetupFirmwareRequest(
        target=SetupSshTarget(host="btt-pi.local", username="pi"),
        preset_id="btt_ebb36_g0b1_can",
        board_name="EBB36 v1.2",
        board_role="toolhead",
        variant_confirmed=True,
    )

    plan = build_setup_firmware_plan(request)

    assert plan.status == "ok"
    assert plan.preset_id == "btt_ebb36_g0b1_can"
    assert plan.board_name == "EBB36 v1.2"
    assert plan.board_role == "toolhead"
    assert plan.expected_binary_path.endswith("/klipper.bin")
    assert "CONFIG_PRINTORA_FLASH_AUTOMATICO=n" in plan.config_preview
    assert not any("flash" in command.command.lower() for step in plan.steps for command in step.commands)


def test_firmware_history_does_not_store_key_path(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SetupFirmwareRunRepository(database_path)
    request = SetupFirmwareRequest(
        target=SetupSshTarget(
            host="btt-pi.local",
            username="pi",
            auth_method="key_path",
            key_path="/Users/local/.ssh/id_ed25519",
        ),
        preset_id="btt_ebb36_g0b1_can",
        board_name="EBB36 v1.2",
        board_role="toolhead",
        variant_confirmed=True,
    )
    plan = build_setup_firmware_plan(request)

    history_id = repository.create_plan(request, plan)
    records = repository.list_runs()

    assert history_id > 0
    assert records[0].preset_id == "btt_ebb36_g0b1_can"
    assert "/Users/local/.ssh/id_ed25519" not in records[0].model_dump_json()


def test_firmware_build_request_requires_no_flash_confirmation() -> None:
    request = SetupFirmwareBuildRequest(
        target=SetupSshTarget(host="btt-pi.local", username="pi"),
        preset_id="btt_ebb36_g0b1_can",
        board_name="EBB36 v1.2",
        variant_confirmed=True,
        confirmation=FIRMWARE_REMOTE_BUILD_CONFIRMATION,
    )

    assert request.confirmation == "BUILD_FIRMWARE_NO_FLASH"
