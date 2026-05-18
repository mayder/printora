from pathlib import Path

import pytest

from app.database import initialize_database
from app.firmware import FirmwareBoardCreate, FirmwareBoardRepository
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
