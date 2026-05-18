from pathlib import Path

import pytest

from app.database import initialize_database
from app.firmware import (
    FirmwareBoardCreate,
    FirmwareBoardRepository,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareFlashDryRunCreate,
)
from app.printers import PrinterCreate, PrinterRepository


def test_list_board_presets_contains_common_voron_boards(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = FirmwareBoardRepository(database_path)

    preset_ids = {preset.id for preset in repository.list_presets()}

    assert "btt_octopus_pro_f446_usb_can" in preset_ids
    assert "btt_ebb36_g0b1_can" in preset_ids
    assert "btt_sb2209_rp2040_can" in preset_ids
    assert "mellow_fly_sht36_v2_g0b1_can" in preset_ids
    assert "fysetc_spider_f446_usb" in preset_ids


def test_create_firmware_board_from_preset(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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


def test_can_board_requires_uuid(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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
    database_path = tmp_path / "mayderprintlab.db"
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


def test_create_firmware_build_dry_run_does_not_execute_commands(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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
    assert run.binary_output_path.endswith("/klipper.bin")
    assert "make clean" in run.commands
    assert "make" in run.commands
    assert any("não executou comandos" in item for item in run.checklist)
    assert len(repository.list_build_runs(printer.id)) == 1


def test_build_dry_run_requires_existing_board(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = FirmwareBoardRepository(database_path)

    with pytest.raises(ValueError, match="firmware board not found"):
        repository.create_build_dry_run(999, FirmwareBuildDryRunCreate())


def test_local_build_is_blocked_when_mode_disabled(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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


def test_local_build_requires_confirmation_when_enabled(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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

    with pytest.raises(ValueError, match="invalid build confirmation"):
        repository.execute_build_local(
            board.id,
            FirmwareBuildExecuteCreate(confirmation="wrong"),
            mode="local",
            timeout_seconds=1,
        )


def test_create_firmware_flash_dry_run_uses_latest_build_plan(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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
    database_path = tmp_path / "mayderprintlab.db"
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
