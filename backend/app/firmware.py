from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


ConnectionType = Literal["usb", "can", "usb_can_bridge"]
FlashMethod = Literal["katapult_can", "katapult_usb_can", "dfu_usb", "manual"]


class BoardPreset(BaseModel):
    id: str
    vendor: str
    name: str
    mcu: str
    architecture: str
    connection_type: ConnectionType
    communication: str
    bootloader_offset: str
    canbus_pins: str | None
    build_output: str
    default_flash_method: FlashMethod
    notes: str


class FirmwareBoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    preset_id: str = Field(min_length=1, max_length=120)
    can_uuid: str | None = Field(default=None, max_length=64)
    can_interface: str = Field(default="can0", min_length=1, max_length=40)
    config_file: str | None = Field(default=None, max_length=160)
    notes: str = Field(default="", max_length=1000)


class FirmwareBoardRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    preset_id: str
    can_uuid: str | None
    can_interface: str
    connection_type: ConnectionType
    mcu: str
    flash_method: FlashMethod
    config_file: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


BOARD_PRESETS: dict[str, BoardPreset] = {
    "btt_octopus_pro_f446_usb_can": BoardPreset(
        id="btt_octopus_pro_f446_usb_can",
        vendor="BigTreeTech",
        name="BTT Octopus Pro STM32F446 USB-CAN bridge",
        mcu="stm32f446",
        architecture="stm32",
        connection_type="usb_can_bridge",
        communication="USB to CAN bus bridge",
        bootloader_offset="32KiB",
        canbus_pins="PD0/PD1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_usb_can",
        notes="Preset inicial para Octopus/Octopus Pro F446 atuando como bridge USB-CAN.",
    ),
    "btt_octopus_v1_1_f446_usb_can": BoardPreset(
        id="btt_octopus_v1_1_f446_usb_can",
        vendor="BigTreeTech",
        name="BTT Octopus v1.1 STM32F446 USB-CAN bridge",
        mcu="stm32f446",
        architecture="stm32",
        connection_type="usb_can_bridge",
        communication="USB to CAN bus bridge",
        bootloader_offset="32KiB",
        canbus_pins="PD0/PD1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_usb_can",
        notes="Preset comum para Voron 2.4 com Octopus F446 em bridge.",
    ),
    "btt_octopus_pro_h723_usb_can": BoardPreset(
        id="btt_octopus_pro_h723_usb_can",
        vendor="BigTreeTech",
        name="BTT Octopus Pro STM32H723 USB-CAN bridge",
        mcu="stm32h723",
        architecture="stm32",
        connection_type="usb_can_bridge",
        communication="USB to CAN bus bridge",
        bootloader_offset="128KiB",
        canbus_pins="PD0/PD1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_usb_can",
        notes="Preset para variantes H723; validar bootloader e clock antes de build.",
    ),
    "btt_ebb36_g0b1_can": BoardPreset(
        id="btt_ebb36_g0b1_can",
        vendor="BigTreeTech",
        name="BTT EBB36 STM32G0B1 CAN",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        notes="Preset comum para toolhead CAN EBB36 G0B1.",
    ),
    "btt_ebb42_g0b1_can": BoardPreset(
        id="btt_ebb42_g0b1_can",
        vendor="BigTreeTech",
        name="BTT EBB42 STM32G0B1 CAN",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        notes="Preset comum para toolhead CAN EBB42 G0B1.",
    ),
    "btt_sb2209_rp2040_can": BoardPreset(
        id="btt_sb2209_rp2040_can",
        vendor="BigTreeTech",
        name="BTT SB2209 RP2040 CAN",
        mcu="rp2040",
        architecture="rp2040",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="none",
        canbus_pins=None,
        build_output="out/klipper.uf2",
        default_flash_method="katapult_can",
        notes="Preset inicial; validar documentação da placa antes de build.",
    ),
    "btt_sb2240_rp2040_can": BoardPreset(
        id="btt_sb2240_rp2040_can",
        vendor="BigTreeTech",
        name="BTT SB2240 RP2040 CAN",
        mcu="rp2040",
        architecture="rp2040",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="none",
        canbus_pins=None,
        build_output="out/klipper.uf2",
        default_flash_method="katapult_can",
        notes="Preset inicial; validar documentação da placa antes de build.",
    ),
    "mellow_fly_sht36_v2_g0b1_can": BoardPreset(
        id="mellow_fly_sht36_v2_g0b1_can",
        vendor="Mellow",
        name="Mellow Fly SHT36 v2 STM32G0B1 CAN",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        notes="Preset inicial para toolhead CAN Mellow SHT36.",
    ),
    "mellow_fly_sb2040_rp2040_can": BoardPreset(
        id="mellow_fly_sb2040_rp2040_can",
        vendor="Mellow",
        name="Mellow Fly SB2040 RP2040 CAN",
        mcu="rp2040",
        architecture="rp2040",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="none",
        canbus_pins=None,
        build_output="out/klipper.uf2",
        default_flash_method="katapult_can",
        notes="Preset inicial para toolhead CAN Mellow SB2040.",
    ),
    "fysetc_spider_f446_usb": BoardPreset(
        id="fysetc_spider_f446_usb",
        vendor="Fysetc",
        name="Fysetc Spider STM32F446 USB",
        mcu="stm32f446",
        architecture="stm32",
        connection_type="usb",
        communication="USB",
        bootloader_offset="32KiB",
        canbus_pins=None,
        build_output="out/klipper.bin",
        default_flash_method="dfu_usb",
        notes="Preset inicial para Spider F446 via USB.",
    ),
    "fysetc_sb_can_g0b1": BoardPreset(
        id="fysetc_sb_can_g0b1",
        vendor="Fysetc",
        name="Fysetc SB CAN STM32G0B1",
        mcu="stm32g0b1",
        architecture="stm32",
        connection_type="can",
        communication="CAN bus",
        bootloader_offset="8KiB",
        canbus_pins="PB0/PB1",
        build_output="out/klipper.bin",
        default_flash_method="katapult_can",
        notes="Preset inicial para toolhead CAN Fysetc.",
    ),
}


@dataclass(frozen=True)
class FirmwareBoardRepository:
    database_path: Path

    def list_presets(self) -> list[BoardPreset]:
        return sorted(BOARD_PRESETS.values(), key=lambda preset: (preset.vendor, preset.name))

    def get_preset(self, preset_id: str) -> BoardPreset | None:
        return BOARD_PRESETS.get(preset_id)

    def create_board(self, printer_id: int, payload: FirmwareBoardCreate) -> FirmwareBoardRecord:
        preset = self.get_preset(payload.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        name = payload.name.strip()
        config_file = payload.config_file.strip() if payload.config_file else f"firmware/{payload.preset_id}.config"
        can_uuid = _clean_optional(payload.can_uuid)
        if preset.connection_type in {"can", "usb_can_bridge"} and not can_uuid:
            raise ValueError("can_uuid is required for CAN boards")
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO firmware_boards (
                    printer_id, name, preset_id, can_uuid, can_interface, connection_type,
                    mcu, flash_method, config_file, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    name,
                    preset.id,
                    can_uuid,
                    payload.can_interface.strip(),
                    preset.connection_type,
                    preset.mcu,
                    preset.default_flash_method,
                    config_file,
                    payload.notes.strip(),
                ),
            )
            board_id = int(cursor.lastrowid)
        record = self.get_board(board_id)
        if record is None:
            raise RuntimeError("firmware board was not persisted")
        return record

    def list_boards(self, printer_id: int) -> list[FirmwareBoardRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, name, preset_id, can_uuid, can_interface, connection_type,
                       mcu, flash_method, config_file, notes, is_active, created_at, updated_at
                FROM firmware_boards
                WHERE printer_id = ?
                ORDER BY is_active DESC, name ASC
                """,
                (printer_id,),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_board(self, board_id: int) -> FirmwareBoardRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, name, preset_id, can_uuid, can_interface, connection_type,
                       mcu, flash_method, config_file, notes, is_active, created_at, updated_at
                FROM firmware_boards
                WHERE id = ?
                """,
                (board_id,),
            ).fetchone()
        return _record_from_row(row) if row else None


def _record_from_row(row) -> FirmwareBoardRecord:
    return FirmwareBoardRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        name=str(row["name"]),
        preset_id=str(row["preset_id"]),
        can_uuid=row["can_uuid"],
        can_interface=str(row["can_interface"]),
        connection_type=row["connection_type"],
        mcu=str(row["mcu"]),
        flash_method=row["flash_method"],
        config_file=str(row["config_file"]),
        notes=str(row["notes"]),
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None
