import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.database import connect_database


class OperationActionPreviewRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    created_at: str
    action_id: str
    action_label: str
    safe_mode: str
    executable: bool
    would_send_gcode: bool
    command_preview: list[str]
    blockers: list[str]
    payload: dict[str, Any]


class OperationActionExecutionAttemptRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    preview_id: int
    created_at: str
    action_id: str
    status: str
    confirmation_matched: bool
    executable: bool
    would_send_gcode: bool
    block_reason: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class OperationActionHistoryRepository:
    database_path: Path

    def create_preview(self, printer_id: int, preview: dict[str, Any]) -> OperationActionPreviewRecord:
        action = preview.get("action") if isinstance(preview.get("action"), dict) else {}
        command_preview = preview.get("command_preview") if isinstance(preview.get("command_preview"), list) else []
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO operation_action_previews (
                    printer_id, action_id, action_label, safe_mode, executable, would_send_gcode,
                    command_preview_json, blockers_json, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    str(action.get("id") or ""),
                    str(action.get("label") or ""),
                    str(preview.get("safe_mode") or ""),
                    1 if preview.get("executable") else 0,
                    1 if preview.get("would_send_gcode") else 0,
                    json.dumps(command_preview, ensure_ascii=False),
                    json.dumps(blockers, ensure_ascii=False),
                    json.dumps(preview, ensure_ascii=False, sort_keys=True),
                ),
            )
            preview_id = int(cursor.lastrowid)
        record = self.get_preview(preview_id)
        if record is None:
            raise RuntimeError("operation action preview was not persisted")
        return record

    def list_previews(self, printer_id: int, limit: int = 20) -> list[OperationActionPreviewRecord]:
        clean_limit = min(max(limit, 1), 100)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, created_at, action_id, action_label, safe_mode,
                       executable, would_send_gcode, command_preview_json, blockers_json, payload_json
                FROM operation_action_previews
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, clean_limit),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_preview(self, preview_id: int) -> OperationActionPreviewRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, created_at, action_id, action_label, safe_mode,
                       executable, would_send_gcode, command_preview_json, blockers_json, payload_json
                FROM operation_action_previews
                WHERE id = ?
                """,
                (preview_id,),
            ).fetchone()
        return _record_from_row(row) if row else None

    def create_execution_attempt(
        self,
        *,
        printer_id: int,
        preview: OperationActionPreviewRecord,
        confirmation_phrase: str,
        preflight: dict[str, Any] | None = None,
    ) -> OperationActionExecutionAttemptRecord:
        expected_phrase = str(preview.payload.get("confirmation_phrase") or "")
        confirmation_matched = confirmation_phrase.strip() == expected_phrase
        clean_preflight = preflight or {"connected": None, "print_state": "", "summary": "Preflight não executado."}
        block_reason = _execution_block_reason(preview, confirmation_matched, clean_preflight)
        payload = {
            "safe_mode": "execution_blocked",
            "preview_id": preview.id,
            "action_id": preview.action_id,
            "preflight": clean_preflight,
            "confirmation_matched": confirmation_matched,
            "would_send_gcode": False,
            "executable": False,
            "block_reason": block_reason,
            "command_preview": preview.command_preview,
            "rollback_plan": "Nenhum rollback necessário: a execução foi bloqueada antes de chamar Moonraker.",
        }
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO operation_action_execution_attempts (
                    printer_id, preview_id, action_id, status, confirmation_matched,
                    executable, would_send_gcode, block_reason, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    preview.id,
                    preview.action_id,
                    "blocked",
                    1 if confirmation_matched else 0,
                    0,
                    0,
                    block_reason,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            attempt_id = int(cursor.lastrowid)
        attempt = self.get_execution_attempt(attempt_id)
        if attempt is None:
            raise RuntimeError("operation action execution attempt was not persisted")
        return attempt

    def create_execution_result(
        self,
        *,
        printer_id: int,
        preview: OperationActionPreviewRecord,
        confirmation_phrase: str,
        preflight: dict[str, Any],
        moonraker_response: dict[str, Any] | None,
        status: str,
        block_reason: str = "",
    ) -> OperationActionExecutionAttemptRecord:
        expected_phrase = str(preview.payload.get("confirmation_phrase") or "")
        confirmation_matched = confirmation_phrase.strip() == expected_phrase
        payload = {
            "safe_mode": "operation_action_executed" if status == "executed" else "operation_action_blocked",
            "preview_id": preview.id,
            "action_id": preview.action_id,
            "preflight": preflight,
            "confirmation_matched": confirmation_matched,
            "would_send_gcode": status == "executed",
            "executable": status == "executed",
            "block_reason": block_reason,
            "command_preview": preview.command_preview,
            "moonraker_response": moonraker_response or {},
            "rollback_plan": "Ação operacional enviada por G-code. Use Emergency Stop no Mainsail/Klipper se houver movimento inesperado.",
        }
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO operation_action_execution_attempts (
                    printer_id, preview_id, action_id, status, confirmation_matched,
                    executable, would_send_gcode, block_reason, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    preview.id,
                    preview.action_id,
                    status,
                    1 if confirmation_matched else 0,
                    1 if status == "executed" else 0,
                    1 if status == "executed" else 0,
                    block_reason,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            attempt_id = int(cursor.lastrowid)
        attempt = self.get_execution_attempt(attempt_id)
        if attempt is None:
            raise RuntimeError("operation action execution result was not persisted")
        return attempt

    def get_execution_attempt(self, attempt_id: int) -> OperationActionExecutionAttemptRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, preview_id, created_at, action_id, status,
                       confirmation_matched, executable, would_send_gcode, block_reason, payload_json
                FROM operation_action_execution_attempts
                WHERE id = ?
                """,
                (attempt_id,),
            ).fetchone()
        return _execution_attempt_from_row(row) if row else None

    def list_execution_attempts(self, printer_id: int, limit: int = 20) -> list[OperationActionExecutionAttemptRecord]:
        clean_limit = min(max(limit, 1), 100)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, preview_id, created_at, action_id, status,
                       confirmation_matched, executable, would_send_gcode, block_reason, payload_json
                FROM operation_action_execution_attempts
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, clean_limit),
            ).fetchall()
        return [_execution_attempt_from_row(row) for row in rows]


def _record_from_row(row: Any) -> OperationActionPreviewRecord:
    return OperationActionPreviewRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        created_at=str(row["created_at"]),
        action_id=str(row["action_id"]),
        action_label=str(row["action_label"]),
        safe_mode=str(row["safe_mode"]),
        executable=bool(row["executable"]),
        would_send_gcode=bool(row["would_send_gcode"]),
        command_preview=_json_list(row["command_preview_json"]),
        blockers=_json_list(row["blockers_json"]),
        payload=_json_dict(row["payload_json"]),
    )


def _execution_attempt_from_row(row: Any) -> OperationActionExecutionAttemptRecord:
    return OperationActionExecutionAttemptRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        preview_id=int(row["preview_id"]),
        created_at=str(row["created_at"]),
        action_id=str(row["action_id"]),
        status=str(row["status"]),
        confirmation_matched=bool(row["confirmation_matched"]),
        executable=bool(row["executable"]),
        would_send_gcode=bool(row["would_send_gcode"]),
        block_reason=str(row["block_reason"]),
        payload=_json_dict(row["payload_json"]),
    )


def _execution_block_reason(
    preview: OperationActionPreviewRecord,
    confirmation_matched: bool,
    preflight: dict[str, Any],
) -> str:
    if not confirmation_matched:
        return "Bloqueado: frase de confirmação inválida."
    if preflight.get("connected") is False:
        return "Bloqueado: preflight sem leitura ao vivo do Moonraker."
    if preflight.get("printing") is True:
        return "Bloqueado: preflight detectou impressão em andamento."
    if not preview.executable:
        return "Bloqueado: preview marcado como não executável."
    if not preview.would_send_gcode:
        return "Bloqueado: execução real ainda não implementada."
    return "Bloqueado: gate de execução real ainda não liberado."


def _json_list(value: str) -> list[str]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in payload] if isinstance(payload, list) else []


def _json_dict(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
