from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.database import connect_database
from app.print_preflight import PrintPreflightRecord, _read_artifact_text
from app.slicing_pipeline import SlicingJob

DeliveryMode = Literal["save_only", "save_and_print"]
DeliveryStatus = Literal[
    "pending_remote",
    "saved",
    "printing",
    "blocked",
    "failed",
    "canceled",
    "rollback_pending",
    "rolled_back",
    "rollback_failed",
]

PREFLIGHT_MAX_AGE_SECONDS = 15 * 60


class PrintDeliveryCreate(BaseModel):
    preflight_id: int = Field(ge=1)
    mode: DeliveryMode = "save_only"
    confirmation_phrase: str = Field(default="", max_length=120)
    step_up_token: str | None = Field(default=None, max_length=240)


class PrintDeliveryRecord(BaseModel):
    id: int
    owner_user_id: int | None
    printer_id: int
    slicing_job_id: int
    preflight_id: int
    remote_agent_job_id: int | None
    rollback_agent_job_id: int | None
    mode: DeliveryMode
    status: DeliveryStatus
    remote_filename: str
    gcode_checksum_sha256: str
    gcode_size_bytes: int
    confirmation_phrase: str
    confirmation_matched: bool
    preflight_snapshot: dict[str, Any]
    remote_result: dict[str, Any]
    rollback_result: dict[str, Any]
    blockers: list[str]
    audit: dict[str, Any]
    created_at: str
    updated_at: str
    completed_at: str | None
    canceled_at: str | None
    rolled_back_at: str | None


class PreparedGcodeDelivery(BaseModel):
    delivery: PrintDeliveryRecord
    gcode_content: str
    payload: dict[str, Any]


class PrintDeliveryRepository:
    def __init__(self, database_path: Path, data_dir: Path) -> None:
        self.database_path = database_path
        self.data_dir = data_dir

    def prepare_delivery(
        self,
        *,
        actor_user_id: int | None,
        preflight: PrintPreflightRecord,
        job: SlicingJob,
        payload: PrintDeliveryCreate,
        step_up_authorized: bool = False,
    ) -> PreparedGcodeDelivery:
        blockers = self._delivery_blockers(preflight, job, payload)
        artifact = next((item for item in job.artifacts if item.artifact_kind == "gcode"), None)
        gcode_content = _read_artifact_text(self.data_dir, artifact.storage_key) if artifact else ""
        checksum = str(artifact.checksum_sha256 or preflight.local_metadata.get("checksum_sha256") or "") if artifact else ""
        remote_filename = _remote_filename(job)
        confirmation_expected = _confirmation_phrase(preflight)
        confirmation_matched = payload.confirmation_phrase.strip() == confirmation_expected if payload.mode == "save_and_print" else bool(payload.confirmation_phrase.strip())
        if payload.mode == "save_and_print" and not confirmation_matched and not step_up_authorized:
            blockers.append("Iniciar impressão exige confirmação textual ou autenticação reforçada.")
        audit = {
            "model_reference": job.model_reference,
            "model_version_reference": job.model_version_reference,
            "quality_reference": job.quality_reference,
            "profile_reference": job.input.get("profile_reference"),
            "artifact_id": artifact.id if artifact else None,
            "artifact_storage_key": artifact.storage_key if artifact else None,
            "confirmation_expected": confirmation_expected if payload.mode == "save_and_print" else "",
            "step_up_authorized": step_up_authorized,
        }
        if blockers:
            delivery = self._insert_delivery(
                actor_user_id=actor_user_id,
                preflight=preflight,
                mode=payload.mode,
                status="blocked",
                remote_filename=remote_filename,
                checksum=checksum,
                size_bytes=len(gcode_content.encode("utf-8")),
                confirmation_phrase=payload.confirmation_phrase,
                confirmation_matched=confirmation_matched,
                preflight_snapshot=preflight.model_dump(),
                remote_result={},
                blockers=blockers,
                audit=audit,
            )
            return PreparedGcodeDelivery(delivery=delivery, gcode_content="", payload={})
        try:
            delivery = self._insert_delivery(
                actor_user_id=actor_user_id,
                preflight=preflight,
                mode=payload.mode,
                status="pending_remote",
                remote_filename=remote_filename,
                checksum=checksum,
                size_bytes=len(gcode_content.encode("utf-8")),
                confirmation_phrase=payload.confirmation_phrase,
                confirmation_matched=confirmation_matched,
                preflight_snapshot=preflight.model_dump(),
                remote_result={},
                blockers=[],
                audit=audit,
            )
        except Exception as exc:
            if "idx_print_delivery_active_preflight" in str(exc) or "UNIQUE constraint failed" in str(exc):
                raise ValueError("preflight já utilizado por outro envio") from exc
            raise
        remote_payload = {
            "safe_mode": "print_gcode_delivery",
            "delivery_id": delivery.id,
            "slicing_job_id": job.id,
            "preflight_id": preflight.id,
            "mode": payload.mode,
            "remote_filename": remote_filename,
            "gcode_content": gcode_content,
            "checksum_sha256": checksum,
            "start_print": payload.mode == "save_and_print",
            "metadata": preflight.local_metadata,
            "audit": audit,
        }
        return PreparedGcodeDelivery(delivery=delivery, gcode_content=gcode_content, payload=remote_payload)

    def mark_remote_job(self, delivery_id: int, remote_agent_job_id: int) -> PrintDeliveryRecord:
        with connect_database(self.database_path) as connection:
            updated = connection.execute(
                """
                UPDATE print_gcode_deliveries
                SET remote_agent_job_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending_remote'
                """,
                (remote_agent_job_id, delivery_id),
            )
            if updated.rowcount == 0:
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'canceled', error_message = 'envio cancelado antes do vínculo',
                        finished_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'pending'
                    """,
                    (remote_agent_job_id,),
                )
            row = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
        return self._record_from_row(row)

    def complete_delivery(self, delivery_id: int, result: dict[str, Any]) -> PrintDeliveryRecord:
        status: DeliveryStatus = "saved"
        if result.get("status") in {"failed", "blocked"}:
            status = "failed"
        elif result.get("started") is True or result.get("status") == "started":
            status = "printing"
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE print_gcode_deliveries
                SET status = ?, remote_result_json = ?, updated_at = CURRENT_TIMESTAMP,
                    completed_at = CASE WHEN ? IN ('saved', 'printing') THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = ? AND status = 'pending_remote'
                """,
                (status, json.dumps(result, ensure_ascii=False), status, delivery_id),
            )
            row = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
        return self._record_from_row(row)

    def fail_delivery(self, delivery_id: int, detail: str, result: dict[str, Any] | None = None) -> PrintDeliveryRecord:
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT blockers_json FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
            blockers = json.loads(row["blockers_json"]) if row else []
            blockers.append(detail)
            connection.execute(
                """
                UPDATE print_gcode_deliveries
                SET status = 'failed', blockers_json = ?, remote_result_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(blockers, ensure_ascii=False), json.dumps(result or {}, ensure_ascii=False), delivery_id),
            )
            updated = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
        return self._record_from_row(updated)

    def list_deliveries(self, actor_user_id: int | None, preflight_id: int | None = None) -> list[PrintDeliveryRecord]:
        params: list[Any] = []
        clauses: list[str] = []
        if actor_user_id is not None:
            clauses.append("owner_user_id = ?")
            params.append(actor_user_id)
        if preflight_id is not None:
            clauses.append("preflight_id = ?")
            params.append(preflight_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"SELECT * FROM print_gcode_deliveries {where} ORDER BY created_at DESC, id DESC LIMIT 30",
                params,
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def get_delivery(self, delivery_id: int, actor_user_id: int | None) -> PrintDeliveryRecord | None:
        params: list[Any] = [delivery_id]
        owner_sql = ""
        if actor_user_id is not None:
            owner_sql = "AND owner_user_id = ?"
            params.append(actor_user_id)
        with connect_database(self.database_path) as connection:
            row = connection.execute(f"SELECT * FROM print_gcode_deliveries WHERE id = ? {owner_sql}", params).fetchone()
        return self._record_from_row(row) if row else None

    def cancel_delivery(self, delivery_id: int, actor_user_id: int | None) -> PrintDeliveryRecord:
        record = self.get_delivery(delivery_id, actor_user_id)
        if record is None:
            raise ValueError("envio não encontrado")
        if record.status != "pending_remote":
            raise ValueError("somente envio pendente pode ser cancelado")
        with connect_database(self.database_path) as connection:
            if record.remote_agent_job_id:
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'canceled', error_message = 'envio cancelado antes da execução',
                        finished_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND printer_id = ? AND status = 'pending'
                    """,
                    (record.remote_agent_job_id, record.printer_id),
                )
            connection.execute(
                """
                UPDATE print_gcode_deliveries
                SET status = 'canceled', canceled_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (delivery_id,),
            )
            row = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
        return self._record_from_row(row)

    def mark_rollback_job(self, delivery_id: int, rollback_agent_job_id: int) -> PrintDeliveryRecord:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE print_gcode_deliveries
                SET status = 'rollback_pending', rollback_agent_job_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (rollback_agent_job_id, delivery_id),
            )
            row = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
        return self._record_from_row(row)

    def complete_rollback(self, delivery_id: int, result: dict[str, Any]) -> PrintDeliveryRecord:
        status: DeliveryStatus = "rolled_back" if result.get("status") == "deleted" else "rollback_failed"
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE print_gcode_deliveries
                SET status = ?, rollback_result_json = ?, rolled_back_at = CASE WHEN ? = 'rolled_back' THEN CURRENT_TIMESTAMP ELSE rolled_back_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, json.dumps(result, ensure_ascii=False), status, delivery_id),
            )
            row = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (delivery_id,)).fetchone()
        return self._record_from_row(row)

    def _delivery_blockers(self, preflight: PrintPreflightRecord, job: SlicingJob, payload: PrintDeliveryCreate) -> list[str]:
        blockers: list[str] = []
        if preflight.status != "approved":
            blockers.append("Envio exige preflight aprovado.")
        if not _is_recent(preflight.approved_at):
            blockers.append("Preflight aprovado expirou; gere um novo preflight antes do envio.")
        if job.id != preflight.slicing_job_id or job.printer_id != preflight.printer_id:
            blockers.append("Preflight não pertence ao job e à impressora selecionados.")
        if not any(artifact.artifact_kind == "gcode" for artifact in job.artifacts):
            blockers.append("Job não possui artefato G-code rastreado.")
        checksum = next((item.checksum_sha256 for item in job.artifacts if item.artifact_kind == "gcode"), None)
        if preflight.local_metadata.get("checksum_sha256") and checksum and preflight.local_metadata["checksum_sha256"] != checksum:
            blockers.append("Checksum do G-code mudou depois do preflight.")
        return blockers

    def _insert_delivery(
        self,
        *,
        actor_user_id: int | None,
        preflight: PrintPreflightRecord,
        mode: DeliveryMode,
        status: DeliveryStatus,
        remote_filename: str,
        checksum: str,
        size_bytes: int,
        confirmation_phrase: str,
        confirmation_matched: bool,
        preflight_snapshot: dict[str, Any],
        remote_result: dict[str, Any],
        blockers: list[str],
        audit: dict[str, Any],
    ) -> PrintDeliveryRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO print_gcode_deliveries (
                    owner_user_id, printer_id, slicing_job_id, preflight_id, mode, status, remote_filename,
                    gcode_checksum_sha256, gcode_size_bytes, confirmation_phrase, confirmation_matched,
                    preflight_snapshot_json, remote_result_json, blockers_json, audit_json,
                    completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? IN ('blocked', 'failed') THEN CURRENT_TIMESTAMP ELSE NULL END)
                """,
                (
                    actor_user_id,
                    preflight.printer_id,
                    preflight.slicing_job_id,
                    preflight.id,
                    mode,
                    status,
                    remote_filename,
                    checksum,
                    size_bytes,
                    confirmation_phrase.strip(),
                    1 if confirmation_matched else 0,
                    json.dumps(preflight_snapshot, ensure_ascii=False),
                    json.dumps(remote_result, ensure_ascii=False),
                    json.dumps(blockers, ensure_ascii=False),
                    json.dumps(audit, ensure_ascii=False),
                    status,
                ),
            )
            row = connection.execute("SELECT * FROM print_gcode_deliveries WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
        return self._record_from_row(row)

    def _record_from_row(self, row) -> PrintDeliveryRecord:
        return PrintDeliveryRecord(
            id=int(row["id"]),
            owner_user_id=row["owner_user_id"],
            printer_id=int(row["printer_id"]),
            slicing_job_id=int(row["slicing_job_id"]),
            preflight_id=int(row["preflight_id"]),
            remote_agent_job_id=row["remote_agent_job_id"],
            rollback_agent_job_id=row["rollback_agent_job_id"],
            mode=row["mode"],
            status=row["status"],
            remote_filename=row["remote_filename"],
            gcode_checksum_sha256=row["gcode_checksum_sha256"],
            gcode_size_bytes=int(row["gcode_size_bytes"]),
            confirmation_phrase=row["confirmation_phrase"],
            confirmation_matched=bool(row["confirmation_matched"]),
            preflight_snapshot=json.loads(row["preflight_snapshot_json"]),
            remote_result=json.loads(row["remote_result_json"]),
            rollback_result=json.loads(row["rollback_result_json"]),
            blockers=json.loads(row["blockers_json"]),
            audit=json.loads(row["audit_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            canceled_at=row["canceled_at"],
            rolled_back_at=row["rolled_back_at"],
        )


def _remote_filename(job: SlicingJob) -> str:
    base = job.model_reference.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].rsplit(".", 1)[0]
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("._-")[:80] or "printora_job"
    return f"printora/{clean}_job_{job.id}.gcode"


def _confirmation_phrase(preflight: PrintPreflightRecord) -> str:
    return f"IMPRIMIR {preflight.printer_id}-{preflight.id}"


def _is_recent(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed).total_seconds() <= PREFLIGHT_MAX_AGE_SECONDS
