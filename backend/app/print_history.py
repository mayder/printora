from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database
from app.print_delivery import PrintDeliveryRecord
from app.slicing_pipeline import SlicingJob
from app.modules.operations.mesh_qualification.physical_validation import (
    MeshPhysicalValidation,
    MeshPhysicalValidationRepository,
)

PrintHistoryStatus = Literal["sent", "started", "completed", "failed", "canceled"]
PrintFeedbackOutcome = Literal["worked", "failed", "needs_adjustment"]
PrintVisibility = Literal["private", "public"]


class PrintFeedbackCreate(BaseModel):
    outcome: PrintFeedbackOutcome
    visibility: PrintVisibility = "private"
    note: str = Field(default="", max_length=500)
    photo_url: str | None = Field(default=None, max_length=500)

    @field_validator("photo_url")
    @classmethod
    def clean_photo_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        clean = value.strip()
        if not re.match(r"^https://", clean):
            raise ValueError("foto pública exige URL HTTPS")
        return clean


class PrintJobHistoryEvent(BaseModel):
    status: PrintHistoryStatus
    telemetry: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class PrintJobFeedback(BaseModel):
    id: int
    history_id: int
    outcome: PrintFeedbackOutcome
    visibility: PrintVisibility
    note: str
    photo_url: str | None
    created_at: str
    updated_at: str


class PrintJobHistoryRecord(BaseModel):
    id: int
    owner_user_id: int | None
    printer_id: int | None = None
    slicing_job_id: int | None
    delivery_id: int | None
    library_item_id: int | None
    model_reference: str
    model_version_reference: str
    profile_reference: str | None
    quality_reference: str
    status: PrintHistoryStatus
    visibility: PrintVisibility
    telemetry: dict[str, Any]
    result: dict[str, Any]
    retention_days: int
    started_at: str | None
    completed_at: str | None
    created_at: str
    updated_at: str
    feedback: list[PrintJobFeedback] = Field(default_factory=list)
    mesh_physical_validation: MeshPhysicalValidation | None = None


class PrintHistoryRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def list_history(self, actor_user_id: int | None, *, include_public: bool = False) -> list[PrintJobHistoryRecord]:
        params: list[Any] = []
        if actor_user_id is None:
            where = "WHERE h.visibility = 'public'" if include_public else "WHERE 1 = 0"
        else:
            where = "WHERE h.owner_user_id = ?"
            params.append(actor_user_id)
            if include_public:
                where += " OR h.visibility = 'public'"
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT h.*
                FROM print_job_history h
                {where}
                ORDER BY h.created_at DESC, h.id DESC
                LIMIT 50
                """,
                params,
            ).fetchall()
            return [self._record_from_row(connection, row, actor_user_id) for row in rows]

    def upsert_from_delivery(self, *, delivery: PrintDeliveryRecord, job: SlicingJob, status: PrintHistoryStatus | None = None) -> PrintJobHistoryRecord:
        next_status = status or _status_from_delivery(delivery.status)
        audit = delivery.audit or {}
        library_item_id = _library_item_id(job.model_reference)
        telemetry = _safe_telemetry(delivery.remote_result)
        result = _safe_result(delivery.remote_result)
        now = datetime.now(timezone.utc).isoformat()
        started_at = now if next_status in {"started", "completed"} else None
        completed_at = now if next_status in {"completed", "failed", "canceled"} else None
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO print_job_history (
                    owner_user_id, printer_id, slicing_job_id, delivery_id, library_item_id,
                    model_reference, model_version_reference, profile_reference, quality_reference,
                    status, telemetry_json, result_json, started_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(delivery_id) DO UPDATE SET
                    status = excluded.status,
                    telemetry_json = excluded.telemetry_json,
                    result_json = excluded.result_json,
                    started_at = COALESCE(print_job_history.started_at, excluded.started_at),
                    completed_at = COALESCE(excluded.completed_at, print_job_history.completed_at),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    delivery.owner_user_id,
                    delivery.printer_id,
                    delivery.slicing_job_id,
                    delivery.id,
                    library_item_id,
                    job.model_reference,
                    job.model_version_reference,
                    str(audit.get("profile_reference") or job.input.get("profile_reference") or ""),
                    job.quality_reference,
                    next_status,
                    json.dumps(telemetry, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False),
                    started_at,
                    completed_at,
                ),
            )
            row = connection.execute("SELECT * FROM print_job_history WHERE delivery_id = ?", (delivery.id,)).fetchone()
            return self._record_from_row(connection, row, delivery.owner_user_id)

    def record_event(self, history_id: int, actor_user_id: int | None, payload: PrintJobHistoryEvent) -> PrintJobHistoryRecord:
        telemetry = _safe_telemetry(payload.telemetry)
        result = _safe_result(payload.result)
        with connect_database(self.database_path) as connection:
            row = self._owned_row(connection, history_id, actor_user_id)
            if row is None:
                raise ValueError("histórico não encontrado")
            merged_telemetry = {**_json_dict(row["telemetry_json"]), **telemetry}
            merged_result = {**_json_dict(row["result_json"]), **result}
            connection.execute(
                """
                UPDATE print_job_history
                SET status = ?, telemetry_json = ?, result_json = ?,
                    started_at = CASE WHEN ? IN ('started', 'completed') THEN COALESCE(started_at, CURRENT_TIMESTAMP) ELSE started_at END,
                    completed_at = CASE WHEN ? IN ('completed', 'failed', 'canceled') THEN CURRENT_TIMESTAMP ELSE completed_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload.status,
                    json.dumps(merged_telemetry, ensure_ascii=False),
                    json.dumps(merged_result, ensure_ascii=False),
                    payload.status,
                    payload.status,
                    history_id,
                ),
            )
            updated = connection.execute("SELECT * FROM print_job_history WHERE id = ?", (history_id,)).fetchone()
            return self._record_from_row(connection, updated, actor_user_id)

    def add_feedback(self, history_id: int, actor_user_id: int | None, payload: PrintFeedbackCreate) -> PrintJobHistoryRecord:
        with connect_database(self.database_path) as connection:
            row = self._owned_row(connection, history_id, actor_user_id)
            if row is None:
                raise ValueError("histórico não encontrado")
            connection.execute(
                """
                INSERT INTO print_job_feedback (history_id, owner_user_id, outcome, visibility, note, photo_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (history_id, actor_user_id, payload.outcome, payload.visibility, payload.note.strip(), payload.photo_url),
            )
            if payload.visibility == "public":
                connection.execute("UPDATE print_job_history SET visibility = 'public', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (history_id,))
            self._upsert_quality_signal(connection, row, actor_user_id, payload)
            updated = connection.execute("SELECT * FROM print_job_history WHERE id = ?", (history_id,)).fetchone()
            return self._record_from_row(connection, updated, actor_user_id)

    def _owned_row(self, connection, history_id: int, actor_user_id: int | None):
        if actor_user_id is None:
            return None
        return connection.execute(
            "SELECT * FROM print_job_history WHERE id = ? AND owner_user_id = ?",
            (history_id, actor_user_id),
        ).fetchone()

    def _upsert_quality_signal(self, connection, row, actor_user_id: int | None, payload: PrintFeedbackCreate) -> None:
        library_item_id = row["library_item_id"]
        if library_item_id is None:
            return
        if payload.outcome == "worked":
            signal_type, weight, reason = "print_success", 10, "Resultado de impressão confirmado"
        elif payload.outcome == "needs_adjustment":
            signal_type, weight, reason = "report", -3, "Impressão exigiu ajuste"
        else:
            signal_type, weight, reason = "report", -6, "Falha de impressão informada"
        connection.execute(
            """
            INSERT INTO social_quality_signals (
                entity_type, entity_id, signal_type, actor_user_id, target_user_id,
                source_table, source_id, weight, reason
            )
            VALUES ('library_item', ?, ?, ?, NULL, 'print_job_feedback', ?, ?, ?)
            ON CONFLICT(signal_type, source_table, source_id) DO UPDATE SET
                weight = excluded.weight,
                reason = excluded.reason
            """,
            (library_item_id, signal_type, actor_user_id, str(row["id"]), weight, reason),
        )
        connection.execute("DELETE FROM social_materialization_state WHERE name = 'social_quality_signals'")

    def _record_from_row(self, connection, row, actor_user_id: int | None) -> PrintJobHistoryRecord:
        feedback_rows = connection.execute(
            """
            SELECT id, history_id, outcome, visibility, note, photo_url, created_at, updated_at
            FROM print_job_feedback
            WHERE history_id = ? AND (? = owner_user_id OR visibility = 'public')
            ORDER BY created_at DESC, id DESC
            """,
            (row["id"], actor_user_id),
        ).fetchall()
        is_owner = actor_user_id is not None and row["owner_user_id"] == actor_user_id
        return PrintJobHistoryRecord(
            id=int(row["id"]),
            owner_user_id=row["owner_user_id"],
            printer_id=int(row["printer_id"]) if is_owner else None,
            slicing_job_id=row["slicing_job_id"],
            delivery_id=row["delivery_id"],
            library_item_id=row["library_item_id"],
            model_reference=str(row["model_reference"]),
            model_version_reference=str(row["model_version_reference"] or ""),
            profile_reference=row["profile_reference"],
            quality_reference=str(row["quality_reference"] or ""),
            status=row["status"],
            visibility=row["visibility"],
            telemetry=_json_dict(row["telemetry_json"]) if is_owner else _public_telemetry(row["telemetry_json"]),
            result=_json_dict(row["result_json"]) if is_owner else _public_result(row["result_json"]),
            retention_days=int(row["retention_days"] or 180),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            feedback=[
                PrintJobFeedback(
                    id=int(feedback["id"]),
                    history_id=int(feedback["history_id"]),
                    outcome=feedback["outcome"],
                    visibility=feedback["visibility"],
                    note=str(feedback["note"] or ""),
                    photo_url=feedback["photo_url"],
                    created_at=str(feedback["created_at"]),
                    updated_at=str(feedback["updated_at"]),
                )
                for feedback in feedback_rows
            ],
            mesh_physical_validation=(
                MeshPhysicalValidationRepository(self.database_path).get_for_history(int(row["owner_user_id"]), int(row["id"]))
                if is_owner else None
            ),
        )


def _status_from_delivery(status: str) -> PrintHistoryStatus:
    if status == "printing":
        return "started"
    if status in {"failed", "blocked", "rollback_failed"}:
        return "failed"
    if status in {"canceled", "rolled_back"}:
        return "canceled"
    return "sent"


def _library_item_id(model_reference: str) -> int | None:
    match = re.match(r"^library:(?://)?(\d+)(?:/|$)", model_reference.strip())
    return int(match.group(1)) if match else None


def _safe_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = ("duration_seconds", "filament_used_mm", "filament_used_g", "layer_count", "progress", "temperature_target")
    return {key: payload[key] for key in allowed if key in payload and payload[key] is not None}


def _safe_result(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = ("status", "started", "message", "error_code")
    return {key: payload[key] for key in allowed if key in payload and payload[key] is not None}


def _public_telemetry(raw: str) -> dict[str, Any]:
    telemetry = _json_dict(raw)
    return {key: telemetry[key] for key in ("duration_seconds", "filament_used_g", "layer_count") if key in telemetry}


def _public_result(raw: str) -> dict[str, Any]:
    result = _json_dict(raw)
    return {key: result[key] for key in ("status", "message") if key in result}


def _json_dict(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
