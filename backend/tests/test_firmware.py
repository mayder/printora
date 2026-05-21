from pathlib import Path

import pytest

from app.database import initialize_database
from app.firmware import (
    FirmwareBoardCreate,
    FirmwareBoardRepository,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareFlashDryRunCreate,
    FirmwareFlashExecuteCreate,
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


def test_firmware_recovery_plan_is_manual_and_blocked(tmp_path: Path) -> None:
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

    plan = repository.build_recovery_plan(board.id)

    assert plan.safe_mode == "manual_recovery_plan_only"
    assert plan.blocked is True
    assert plan.board_id == board.id
    assert any("Katapult" in step for step in plan.recovery_steps)
    assert any("não executou flash" in note for note in plan.rollback_notes)


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


def test_local_build_preflight_is_read_only_and_blocked_by_default(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
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
    database_path = tmp_path / "mayderprintlab.db"
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


def test_local_build_restores_config_and_copies_binary(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    klipper_path = tmp_path / "klipper"
    firmware_dir = klipper_path / "firmware"
    output_root = tmp_path / "builds"
    firmware_dir.mkdir(parents=True)
    (klipper_path / ".config").write_text("ORIGINAL_CONFIG\n")
    (firmware_dir / "ebb_t0.config").write_text("BUILD_CONFIG\n")
    (klipper_path / "Makefile").write_text(
        ".DEFAULT_GOAL := all\n\nclean:\n\t@rm -rf out\n\nall:\n\t@mkdir -p out\n\t@printf 'bin' > out/klipper.bin\n\t@echo build-ok\n"
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
    assert Path(run.binary_output_path).read_text() == "bin"
    assert Path(run.config_backup_path).read_text() == "ORIGINAL_CONFIG\n"
    assert "build-ok" in run.message


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


def test_flash_preflight_is_read_only_and_always_blocks_execution(tmp_path: Path) -> None:
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
        ),
    )

    with pytest.raises(ValueError, match="invalid flash confirmation"):
        repository.execute_flash_blocked(board.id, FirmwareFlashExecuteCreate(confirmation="wrong"))
