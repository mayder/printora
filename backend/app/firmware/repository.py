import json
from dataclasses import dataclass
from pathlib import Path

from app.database import connect_database
from app.firmware.build_service import (
    _build_dry_run_plan,
    _build_local_build_preflight,
    _execute_local_build,
    _mark_local_build_plan,
)
from app.firmware.flash_service import _build_flash_preflight, _flash_dry_run_plan
from app.firmware.models import (
    BoardPreset,
    FirmwareBoardCreate,
    FirmwareBoardRecord,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareBuildPreflight,
    FirmwareBuildRunRecord,
    FirmwareFlashDryRunCreate,
    FirmwareFlashExecuteCreate,
    FirmwareFlashPreflight,
    FirmwareFlashRunRecord,
    FirmwareRecoveryPlan,
)
from app.firmware.presets import BOARD_PRESETS
from app.firmware.recovery_service import build_firmware_recovery_plan
from app.firmware.utils import _clean_optional



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
            existing = self._find_existing_board(connection, printer_id, name, can_uuid)
            if existing is not None:
                return existing
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

    def _find_existing_board(self, connection, printer_id: int, name: str, can_uuid: str | None) -> FirmwareBoardRecord | None:
        if can_uuid:
            row = connection.execute(
                """
                SELECT id, printer_id, name, preset_id, can_uuid, can_interface, connection_type,
                       mcu, flash_method, config_file, notes, is_active, created_at, updated_at
                FROM firmware_boards
                WHERE printer_id = ? AND is_active = 1 AND can_uuid = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (printer_id, can_uuid),
            ).fetchone()
            if row:
                return _record_from_row(row)
        row = connection.execute(
            """
            SELECT id, printer_id, name, preset_id, can_uuid, can_interface, connection_type,
                   mcu, flash_method, config_file, notes, is_active, created_at, updated_at
            FROM firmware_boards
            WHERE printer_id = ? AND is_active = 1 AND lower(name) = lower(?)
            ORDER BY id ASC
            LIMIT 1
            """,
            (printer_id, name),
        ).fetchone()
        return _record_from_row(row) if row else None

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
        return build_firmware_recovery_plan(board)

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
