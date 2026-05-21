import json
import shutil
import subprocess
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


class FirmwareBuildDryRunCreate(BaseModel):
    klipper_path: str = Field(default="~/klipper", min_length=1, max_length=200)
    output_root: str = Field(default="~/printer_data/firmware_builds", min_length=1, max_length=240)
    notes: str = Field(default="", max_length=1000)


class FirmwareBuildExecuteCreate(FirmwareBuildDryRunCreate):
    confirmation: str = Field(default="", max_length=80)


class FirmwareBuildRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    board_id: int
    created_at: str
    status: str
    klipper_path: str
    output_dir: str
    config_backup_path: str
    binary_output_path: str
    commands: list[str]
    checklist: list[str]
    message: str


class FirmwareBuildPreflightCheck(BaseModel):
    key: str
    label: str
    status: Literal["ok", "warning", "blocked"]
    detail: str


class FirmwareBuildPreflight(BaseModel):
    safe_mode: str
    printer_id: int
    board_id: int
    board_name: str
    klipper_path: str
    output_root: str
    config_file: str
    expected_build_output: str
    checks: list[FirmwareBuildPreflightCheck]
    commands_preview: list[str]
    blocked: bool
    can_execute_build: bool
    message: str


class FirmwareFlashDryRunCreate(BaseModel):
    build_run_id: int | None = None
    binary_path: str | None = Field(default=None, max_length=260)
    notes: str = Field(default="", max_length=1000)


class FirmwareFlashExecuteCreate(FirmwareFlashDryRunCreate):
    confirmation: str = Field(default="", max_length=100)


class FirmwareFlashRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    board_id: int
    build_run_id: int | None
    created_at: str
    status: str
    flash_method: FlashMethod
    can_uuid: str | None
    can_interface: str
    binary_path: str
    commands: list[str]
    checklist: list[str]
    message: str


class FirmwareFlashPreflightCheck(BaseModel):
    key: str
    label: str
    status: Literal["ok", "warning", "blocked"]
    detail: str


class FirmwareFlashPreflight(BaseModel):
    safe_mode: str
    printer_id: int
    board_id: int
    board_name: str
    flash_method: FlashMethod
    can_uuid: str | None
    can_interface: str
    binary_path: str
    connected: bool
    printing: bool
    print_state: str
    klipper_state: str | None
    klippy_state: str | None
    checks: list[FirmwareFlashPreflightCheck]
    commands_preview: list[str]
    rollback_plan: list[str]
    blocked: bool
    can_execute_flash: bool
    message: str


class FirmwareRecoveryPlan(BaseModel):
    safe_mode: str
    printer_id: int
    board_id: int
    board_name: str
    flash_method: FlashMethod
    can_uuid: str | None
    can_interface: str
    prerequisites: list[str]
    recovery_steps: list[str]
    validation_steps: list[str]
    rollback_notes: list[str]
    blocked: bool


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

    def build_recovery_plan(self, board_id: int) -> FirmwareRecoveryPlan:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        return FirmwareRecoveryPlan(
            safe_mode="manual_recovery_plan_only",
            printer_id=board.printer_id,
            board_id=board.id,
            board_name=board.name,
            flash_method=board.flash_method,
            can_uuid=board.can_uuid,
            can_interface=board.can_interface,
            prerequisites=[
                "Confirmar impressora parada e energia estável.",
                "Ter backup da .config e binário anterior antes de qualquer flash.",
                "Confirmar método de bootloader da placa e acesso físico se necessário.",
                "Registrar UUID/serial atual antes de alterar firmware.",
            ],
            recovery_steps=_firmware_recovery_steps(board),
            validation_steps=[
                "Validar UUID/serial após recuperação.",
                "Reiniciar Klipper somente depois de confirmar que a MCU voltou a responder.",
                "Conferir printer/info e logs antes de liberar impressão.",
            ],
            rollback_notes=[
                "Este plano não executou flash, restart, SSH nem comandos locais.",
                "Se o flash falhar, usar o binário anterior e o método de bootloader documentado para a placa.",
            ],
            blocked=True,
        )

    def create_build_dry_run(self, board_id: int, payload: FirmwareBuildDryRunCreate) -> FirmwareBuildRunRecord:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        preset = self.get_preset(board.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        plan = _build_dry_run_plan(board, preset, payload)
        return self._insert_build_run(board, "dry_run_planned", plan)

    def build_build_preflight(self, board_id: int, payload: FirmwareBuildDryRunCreate, mode: str) -> FirmwareBuildPreflight:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        preset = self.get_preset(board.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        return _build_local_build_preflight(board, preset, payload, mode)

    def execute_build_local(
        self,
        board_id: int,
        payload: FirmwareBuildExecuteCreate,
        mode: str,
        timeout_seconds: float,
    ) -> FirmwareBuildRunRecord:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        preset = self.get_preset(board.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        plan = _build_dry_run_plan(board, preset, payload)
        if mode != "local":
            plan["message"] = "Build local bloqueado: PRINTORA_FIRMWARE_BUILD_MODE não está em local."
            return self._insert_build_run(board, "blocked_build_mode_disabled", plan)
        if payload.confirmation != "EXECUTE_LOCAL_BUILD_NO_FLASH":
            raise ValueError("invalid build confirmation")
        _mark_local_build_plan(plan, board, preset, payload)

        status = "build_success"
        try:
            log_excerpt = _execute_local_build(board, preset, payload, timeout_seconds)
            plan["message"] = payload.notes.strip() or f"Build local concluído sem flash. Log: {log_excerpt}"
        except Exception as exc:
            status = "build_failed"
            plan["message"] = f"Build local falhou: {exc}"
        return self._insert_build_run(board, status, plan)

    def _insert_build_run(
        self,
        board: FirmwareBoardRecord,
        status: str,
        plan: dict[str, object],
    ) -> FirmwareBuildRunRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO firmware_build_runs (
                    printer_id, board_id, status, klipper_path, output_dir, config_backup_path,
                    binary_output_path, commands_json, checklist_json, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    board.printer_id,
                    board.id,
                    status,
                    plan["klipper_path"],
                    plan["output_dir"],
                    plan["config_backup_path"],
                    plan["binary_output_path"],
                    json.dumps(plan["commands"], ensure_ascii=False),
                    json.dumps(plan["checklist"], ensure_ascii=False),
                    plan["message"],
                ),
            )
            run_id = int(cursor.lastrowid)
        record = self.get_build_run(run_id)
        if record is None:
            raise RuntimeError("firmware build run was not persisted")
        return record

    def list_build_runs(self, printer_id: int, limit: int = 20) -> list[FirmwareBuildRunRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, board_id, created_at, status, klipper_path, output_dir,
                       config_backup_path, binary_output_path, commands_json, checklist_json, message
                FROM firmware_build_runs
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_build_run_from_row(row) for row in rows]

    def get_build_run(self, run_id: int) -> FirmwareBuildRunRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, board_id, created_at, status, klipper_path, output_dir,
                       config_backup_path, binary_output_path, commands_json, checklist_json, message
                FROM firmware_build_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        return _build_run_from_row(row) if row else None

    def create_flash_dry_run(self, board_id: int, payload: FirmwareFlashDryRunCreate) -> FirmwareFlashRunRecord:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        preset = self.get_preset(board.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        build_run = self.get_build_run(payload.build_run_id) if payload.build_run_id is not None else None
        if payload.build_run_id is not None and build_run is None:
            raise ValueError("firmware build run not found")
        if build_run is not None and (build_run.board_id != board.id or build_run.printer_id != board.printer_id):
            raise ValueError("firmware build run does not belong to this board")

        plan = _flash_dry_run_plan(board, preset, payload, build_run)
        return self._insert_flash_run(board, payload.build_run_id, "flash_dry_run_planned", plan)

    def build_flash_preflight(
        self,
        board_id: int,
        payload: FirmwareFlashDryRunCreate,
        preflight: dict[str, object],
    ) -> FirmwareFlashPreflight:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        preset = self.get_preset(board.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        build_run = self.get_build_run(payload.build_run_id) if payload.build_run_id is not None else None
        if payload.build_run_id is not None and build_run is None:
            raise ValueError("firmware build run not found")
        if build_run is not None and (build_run.board_id != board.id or build_run.printer_id != board.printer_id):
            raise ValueError("firmware build run does not belong to this board")
        return _build_flash_preflight(board, preset, payload, build_run, preflight)

    def execute_flash_blocked(self, board_id: int, payload: FirmwareFlashExecuteCreate) -> FirmwareFlashRunRecord:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError("firmware board not found")
        preset = self.get_preset(board.preset_id)
        if preset is None:
            raise ValueError("unknown board preset")
        build_run = self.get_build_run(payload.build_run_id) if payload.build_run_id is not None else None
        if payload.build_run_id is not None and build_run is None:
            raise ValueError("firmware build run not found")
        if build_run is not None and (build_run.board_id != board.id or build_run.printer_id != board.printer_id):
            raise ValueError("firmware build run does not belong to this board")
        if payload.confirmation != "BLOCK_REAL_FLASH":
            raise ValueError("invalid flash confirmation")

        plan = _flash_dry_run_plan(board, preset, payload, build_run)
        plan["message"] = (
            payload.notes.strip()
            or "Execução real de flash bloqueada por segurança. Nenhum comando foi executado."
        )
        plan["checklist"] = [
            "Gate validado: confirmação textual recebida.",
            "Execução real bloqueada nesta versão.",
            "Nenhum flash, restart, SSH ou validação ao vivo foi executado.",
            *list(plan["checklist"]),
        ]
        return self._insert_flash_run(board, payload.build_run_id, "blocked_flash_execution", plan)

    def _insert_flash_run(
        self,
        board: FirmwareBoardRecord,
        build_run_id: int | None,
        status: str,
        plan: dict[str, object],
    ) -> FirmwareFlashRunRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO firmware_flash_runs (
                    printer_id, board_id, build_run_id, status, flash_method, can_uuid,
                    can_interface, binary_path, commands_json, checklist_json, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    board.printer_id,
                    board.id,
                    build_run_id,
                    status,
                    plan["flash_method"],
                    plan["can_uuid"],
                    plan["can_interface"],
                    plan["binary_path"],
                    json.dumps(plan["commands"], ensure_ascii=False),
                    json.dumps(plan["checklist"], ensure_ascii=False),
                    plan["message"],
                ),
            )
            run_id = int(cursor.lastrowid)
        record = self.get_flash_run(run_id)
        if record is None:
            raise RuntimeError("firmware flash run was not persisted")
        return record

    def list_flash_runs(self, printer_id: int, limit: int = 20) -> list[FirmwareFlashRunRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, board_id, build_run_id, created_at, status, flash_method,
                       can_uuid, can_interface, binary_path, commands_json, checklist_json, message
                FROM firmware_flash_runs
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_flash_run_from_row(row) for row in rows]

    def get_flash_run(self, run_id: int) -> FirmwareFlashRunRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, board_id, build_run_id, created_at, status, flash_method,
                       can_uuid, can_interface, binary_path, commands_json, checklist_json, message
                FROM firmware_flash_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        return _flash_run_from_row(row) if row else None


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


def _build_run_from_row(row) -> FirmwareBuildRunRecord:
    return FirmwareBuildRunRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        board_id=int(row["board_id"]),
        created_at=str(row["created_at"]),
        status=str(row["status"]),
        klipper_path=str(row["klipper_path"]),
        output_dir=str(row["output_dir"]),
        config_backup_path=str(row["config_backup_path"]),
        binary_output_path=str(row["binary_output_path"]),
        commands=json.loads(row["commands_json"]),
        checklist=json.loads(row["checklist_json"]),
        message=str(row["message"]),
    )


def _flash_run_from_row(row) -> FirmwareFlashRunRecord:
    return FirmwareFlashRunRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        board_id=int(row["board_id"]),
        build_run_id=int(row["build_run_id"]) if row["build_run_id"] is not None else None,
        created_at=str(row["created_at"]),
        status=str(row["status"]),
        flash_method=row["flash_method"],
        can_uuid=row["can_uuid"],
        can_interface=str(row["can_interface"]),
        binary_path=str(row["binary_path"]),
        commands=json.loads(row["commands_json"]),
        checklist=json.loads(row["checklist_json"]),
        message=str(row["message"]),
    )


def _build_dry_run_plan(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
) -> dict[str, object]:
    slug = _slug(board.name)
    output_dir = f"{payload.output_root.rstrip('/')}/DRY-RUN/{slug}"
    backup_path = f"{output_dir}/.config.before-build"
    binary_path = f"{output_dir}/{Path(preset.build_output).name}"
    commands = [
        "curl -s http://127.0.0.1:7125/printer/info",
        f"mkdir -p {output_dir}",
        f"cd {payload.klipper_path}",
        f"cp .config {backup_path}",
        "make clean",
        f"cp {board.config_file} .config",
        "make",
        f"cp {preset.build_output} {binary_path}",
        f"cp {backup_path} .config",
    ]
    checklist = [
        "Confirmar que a impressora não está imprimindo.",
        "Confirmar Klipper/Moonraker conectados e sem erro.",
        f"Confirmar preset {preset.id} para {board.name}.",
        f"Confirmar MCU {preset.mcu}, arquitetura {preset.architecture} e bootloader {preset.bootloader_offset}.",
        f"Confirmar arquivo de config planejado: {board.config_file}.",
        f"Confirmar saída esperada do build: {preset.build_output}.",
        f"Confirmar UUID CAN {board.can_uuid or '-'} antes de qualquer flash futuro.",
        "Confirmar backup da .config antes de sobrescrever.",
        "Confirmar que build local só roda com modo local e confirmação explícita.",
        "Confirmar que dry-run apenas registra plano e não executou comandos.",
    ]
    return {
        "klipper_path": payload.klipper_path,
        "output_dir": output_dir,
        "config_backup_path": backup_path,
        "binary_output_path": binary_path,
        "commands": commands,
        "checklist": checklist,
        "message": payload.notes.strip()
        or "Dry-run criado. Nenhum comando foi executado; plano salvo apenas para revisão.",
    }


def _build_local_build_preflight(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
    mode: str,
) -> FirmwareBuildPreflight:
    klipper_path = Path(payload.klipper_path).expanduser()
    output_root = Path(payload.output_root).expanduser()
    source_config = Path(board.config_file).expanduser()
    if not source_config.is_absolute():
        source_config = klipper_path / source_config
    expected_output = klipper_path / preset.build_output
    plan = _build_dry_run_plan(board, preset, payload)
    checks = [
        _preflight_check(
            "build_mode",
            "Modo de build local",
            mode == "local",
            f"PRINTORA_FIRMWARE_BUILD_MODE={mode}",
            "Build real bloqueado porque o modo local não está habilitado.",
        ),
        _preflight_check(
            "make_binary",
            "Comando make disponível",
            shutil.which("make") is not None,
            shutil.which("make") or "make não encontrado no PATH",
            "Instalar toolchain/build tools no host antes de compilar.",
        ),
        _preflight_check(
            "klipper_path",
            "Diretório Klipper",
            klipper_path.is_dir(),
            str(klipper_path),
            "Diretório Klipper não encontrado neste host.",
        ),
        _preflight_check(
            "klipper_makefile",
            "Makefile do Klipper",
            (klipper_path / "Makefile").is_file(),
            str(klipper_path / "Makefile"),
            "Makefile do Klipper não encontrado.",
        ),
        _preflight_check(
            "current_config",
            ".config atual",
            (klipper_path / ".config").is_file(),
            str(klipper_path / ".config"),
            ".config atual não encontrado; build real não deve sobrescrever sem backup.",
        ),
        _preflight_check(
            "board_config",
            ".config da placa cadastrada",
            source_config.is_file(),
            str(source_config),
            "Arquivo de configuração da placa não encontrado.",
        ),
        FirmwareBuildPreflightCheck(
            key="expected_output",
            label="Saída esperada do build",
            status="warning",
            detail=f"{expected_output} será validado somente depois de make; nenhum build foi executado.",
        ),
        FirmwareBuildPreflightCheck(
            key="output_root",
            label="Diretório destino planejado",
            status="warning",
            detail=f"{output_root} não foi criado nem alterado neste preflight.",
        ),
    ]
    blocked = any(check.status == "blocked" for check in checks)
    return FirmwareBuildPreflight(
        safe_mode="local_build_preflight_read_only",
        printer_id=board.printer_id,
        board_id=board.id,
        board_name=board.name,
        klipper_path=str(klipper_path),
        output_root=str(output_root),
        config_file=str(source_config),
        expected_build_output=str(expected_output),
        checks=checks,
        commands_preview=list(plan["commands"]),
        blocked=True,
        can_execute_build=False,
        message=(
            "Preflight concluído com bloqueios; nenhum comando foi executado."
            if blocked
            else "Preflight sem bloqueios críticos, mas build real permanece bloqueado neste lote."
        ),
    )


def _preflight_check(
    key: str,
    label: str,
    ok: bool,
    ok_detail: str,
    blocked_detail: str,
) -> FirmwareBuildPreflightCheck:
    return FirmwareBuildPreflightCheck(
        key=key,
        label=label,
        status="ok" if ok else "blocked",
        detail=ok_detail if ok else blocked_detail,
    )


def _mark_local_build_plan(
    plan: dict[str, object],
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
) -> None:
    output_dir = f"{payload.output_root.rstrip('/')}/local-build/{_slug(board.name)}"
    plan["output_dir"] = output_dir
    plan["config_backup_path"] = f"{output_dir}/.config.before-build"
    plan["binary_output_path"] = f"{output_dir}/{Path(preset.build_output).name}"


def _flash_dry_run_plan(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareFlashDryRunCreate,
    build_run: FirmwareBuildRunRecord | None,
) -> dict[str, object]:
    binary_path = _flash_binary_path(board, preset, payload, build_run)
    commands = _flash_commands(board, binary_path)
    checklist = [
        "Confirmar que a impressora não está imprimindo.",
        "Confirmar hotend, mesa e câmara em condição segura.",
        "Confirmar energia estável antes de qualquer flash futuro.",
        "Confirmar que o binário foi gerado com a mesma versão do Klipper em uso.",
        "Confirmar backup da configuração de firmware e binário anterior.",
        f"Confirmar UUID CAN esperado: {board.can_uuid or '-'}; abortar se não bater.",
        f"Confirmar interface CAN esperada: {board.can_interface}.",
        f"Confirmar método de flash esperado: {board.flash_method}.",
        "Confirmar plano de recuperação caso a MCU não volte.",
        "Confirmar rollback manual antes de qualquer flash real.",
        "Confirmar que este registro é dry-run: nenhum comando foi executado.",
    ]
    return {
        "flash_method": board.flash_method,
        "can_uuid": board.can_uuid,
        "can_interface": board.can_interface,
        "binary_path": binary_path,
        "commands": commands,
        "checklist": checklist,
        "message": payload.notes.strip()
        or "Dry-run de flash criado. Nenhum comando foi executado; usar apenas para revisão.",
    }


def _build_flash_preflight(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareFlashDryRunCreate,
    build_run: FirmwareBuildRunRecord | None,
    preflight: dict[str, object],
) -> FirmwareFlashPreflight:
    binary_path = _flash_binary_path(board, preset, payload, build_run)
    connected = bool(preflight.get("connected"))
    printing = bool(preflight.get("printing"))
    print_state = str(preflight.get("print_state") or "")
    klipper_state = _optional_str(preflight.get("klipper_state"))
    klippy_state = _optional_str(preflight.get("klippy_state"))
    checks = [
        FirmwareFlashPreflightCheck(
            key="moonraker_connected",
            label="Moonraker/Klipper acessível",
            status="ok" if connected else "blocked",
            detail="Moonraker respondeu ao preflight read-only." if connected else str(preflight.get("error") or "Moonraker indisponível."),
        ),
        FirmwareFlashPreflightCheck(
            key="not_printing",
            label="Impressão parada",
            status="blocked" if printing else "ok",
            detail=f"print_stats.state={print_state or '-'}",
        ),
        FirmwareFlashPreflightCheck(
            key="klipper_ready",
            label="Klipper ready",
            status="ok" if klipper_state == "ready" else "blocked",
            detail=f"printer/info.state={klipper_state or '-'}",
        ),
        FirmwareFlashPreflightCheck(
            key="klippy_ready",
            label="Klippy ready",
            status="ok" if klippy_state == "ready" else "blocked",
            detail=f"server/info.klippy_state={klippy_state or '-'}",
        ),
        FirmwareFlashPreflightCheck(
            key="binary_selected",
            label="Binário selecionado",
            status="ok" if binary_path.strip() else "blocked",
            detail=binary_path or "Nenhum binário informado ou planejado.",
        ),
        FirmwareFlashPreflightCheck(
            key="flash_method",
            label="Método de flash cadastrado",
            status="ok",
            detail=board.flash_method,
        ),
        FirmwareFlashPreflightCheck(
            key="can_identity",
            label="Identidade CAN/USB",
            status="ok" if board.connection_type == "usb" or bool(board.can_uuid) else "blocked",
            detail=f"uuid={board.can_uuid or '-'} interface={board.can_interface}",
        ),
        FirmwareFlashPreflightCheck(
            key="execution_policy",
            label="Política de execução",
            status="blocked",
            detail="Flash real permanece bloqueado neste lote.",
        ),
    ]
    blocked = any(check.status == "blocked" for check in checks)
    return FirmwareFlashPreflight(
        safe_mode="flash_preflight_read_only",
        printer_id=board.printer_id,
        board_id=board.id,
        board_name=board.name,
        flash_method=board.flash_method,
        can_uuid=board.can_uuid,
        can_interface=board.can_interface,
        binary_path=binary_path,
        connected=connected,
        printing=printing,
        print_state=print_state,
        klipper_state=klipper_state,
        klippy_state=klippy_state,
        checks=checks,
        commands_preview=_flash_commands(board, binary_path),
        rollback_plan=[
            "Nenhum flash, restart, SSH ou comando local foi executado neste preflight.",
            "Flash real futuro deve preservar binário anterior e .config antes da execução.",
            "Flash real futuro deve validar UUID/serial antes e depois, reiniciar Klipper separadamente e confirmar printer/info ready.",
        ],
        blocked=True,
        can_execute_flash=False,
        message=(
            "Preflight de flash concluiu com bloqueios; nenhuma ação foi executada."
            if blocked
            else "Preflight sem bloqueios operacionais, mas flash real permanece bloqueado neste lote."
        ),
    )


def _flash_binary_path(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareFlashDryRunCreate,
    build_run: FirmwareBuildRunRecord | None,
) -> str:
    if payload.binary_path and payload.binary_path.strip():
        return payload.binary_path.strip()
    if build_run is not None:
        return build_run.binary_output_path
    return f"~/printer_data/firmware_builds/DRY-RUN/{_slug(board.name)}/{Path(preset.build_output).name}"


def _flash_commands(board: FirmwareBoardRecord, binary_path: str) -> list[str]:
    if board.flash_method in {"katapult_can", "katapult_usb_can"}:
        return [
            "curl -s http://127.0.0.1:7125/printer/info",
            f"python3 ~/katapult/scripts/flashtool.py -i {board.can_interface} -u {board.can_uuid} -f {binary_path}",
            "sudo systemctl restart klipper",
            "curl -s http://127.0.0.1:7125/printer/info",
        ]
    if board.flash_method == "dfu_usb":
        return [
            "curl -s http://127.0.0.1:7125/printer/info",
            f"# DFU USB exige identificar o dispositivo correto antes do flash de {binary_path}.",
            "# Exemplo futuro: make flash FLASH_DEVICE=<device> depois de validação manual.",
            "sudo systemctl restart klipper",
            "curl -s http://127.0.0.1:7125/printer/info",
        ]
    return [
        "curl -s http://127.0.0.1:7125/printer/info",
        f"# Método manual: revisar documentação da placa antes de usar {binary_path}.",
        "sudo systemctl restart klipper",
        "curl -s http://127.0.0.1:7125/printer/info",
    ]


def _firmware_recovery_steps(board: FirmwareBoardRecord) -> list[str]:
    if board.flash_method == "katapult_can":
        return [
            f"Confirmar interface CAN: {board.can_interface}.",
            f"Confirmar UUID atual/esperado: {board.can_uuid or '-'}.",
            "Colocar a placa em Katapult pelo procedimento físico/documentado.",
            "Reaplicar o binário anterior com o comando Katapult validado manualmente.",
        ]
    if board.flash_method == "katapult_usb_can":
        return [
            "Confirmar que a bridge USB-CAN continua aparecendo no host.",
            f"Confirmar interface CAN: {board.can_interface}.",
            "Colocar a placa em Katapult pelo procedimento físico/documentado.",
            "Reaplicar o binário anterior com o comando da bridge validado manualmente.",
        ]
    if board.flash_method == "dfu_usb":
        return [
            "Colocar a placa em DFU/bootloader pelo jumper ou botão documentado.",
            "Confirmar presença no host com ferramenta de listagem USB apropriada.",
            "Reaplicar o binário anterior com o comando DFU validado manualmente.",
        ]
    return [
        "Seguir o procedimento manual da placa.",
        "Usar binário anterior e .config preservados.",
        "Registrar comando, resultado e evidência antes de reiniciar Klipper.",
    ]


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value.strip()).strip("-") or "board"


def _execute_local_build(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildExecuteCreate,
    timeout_seconds: float,
) -> str:
    klipper_path = Path(payload.klipper_path).expanduser().resolve()
    output_root = Path(payload.output_root).expanduser().resolve()
    output_dir = output_root / "local-build" / _slug(board.name)
    backup_path = output_dir / ".config.before-build"
    binary_path = output_dir / Path(preset.build_output).name
    source_config = Path(board.config_file).expanduser()
    if not source_config.is_absolute():
        source_config = klipper_path / source_config
    source_config = source_config.resolve()
    klipper_config = klipper_path / ".config"
    build_output = klipper_path / preset.build_output

    if not klipper_path.is_dir():
        raise ValueError(f"klipper path not found: {klipper_path}")
    if not (klipper_path / "Makefile").is_file():
        raise ValueError("klipper path does not contain Makefile")
    if not source_config.is_file():
        raise ValueError(f"firmware config not found: {source_config}")
    if not klipper_config.is_file():
        raise ValueError("current .config not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(klipper_config, backup_path)
    restored = False
    logs: list[str] = []
    try:
        logs.append(_run_make(["make", "clean"], klipper_path, timeout_seconds))
        shutil.copy2(source_config, klipper_config)
        logs.append(_run_make(["make"], klipper_path, timeout_seconds))
        if not build_output.is_file():
            raise ValueError(f"expected build output not found: {build_output}")
        shutil.copy2(build_output, binary_path)
    finally:
        if backup_path.is_file():
            shutil.copy2(backup_path, klipper_config)
            restored = True
        if not restored:
            raise RuntimeError("failed to restore original .config")
    return _excerpt("\n".join(logs))


def _run_make(command: list[str], cwd: Path, timeout_seconds: float) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    output = result.stdout + "\n" + result.stderr
    if result.returncode != 0:
        excerpt = _excerpt(output)
        raise RuntimeError(f"{' '.join(command)} failed with exit {result.returncode}: {excerpt}")
    return output


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _excerpt(output: str, max_lines: int = 20) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:]) if lines else "sem saída relevante"
