from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.database import connect_database
from app.modules.community.storage_usage import personal_storage_quota, total_personal_storage_used
from app.modules.operations.reconstruction.adapters import (
    ReconstructionAdapterInput,
    ReconstructionAdapterResult,
    ReconstructionPhotoInput,
    ReconstructionUnavailableError,
)
from app.modules.operations.reconstruction.contracts import ReconstructionCreate, ReconstructionJob
from app.modules.operations.reconstruction.models import reconstruction_job_model
from app.modules.operations.mesh_qualification import qualify_mesh
from app.modules.platform.durable_execution import DurableExecutionRepository, QueueSaturatedError
from app.social_storage import SocialStorageRepository


class ReconstructionRepository:
    def __init__(self, database_path: Path, settings: Settings) -> None:
        self.database_path = database_path
        self.settings = settings
        self.durable = DurableExecutionRepository(database_path)
        self.storage = SocialStorageRepository(database_path)

    def create(
        self,
        owner_user_id: int,
        payload: ReconstructionCreate,
        idempotency_key: str,
    ) -> ReconstructionJob:
        safe_key = _idempotency_key(idempotency_key)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT id, capture_session_id FROM photo_reconstruction_jobs WHERE owner_user_id = ? AND idempotency_key = ?",
                (owner_user_id, safe_key),
            ).fetchone()
            if existing is not None:
                if int(existing["capture_session_id"]) != payload.capture_session_id:
                    raise ValueError("chave de repetição já usada em outra captura")
                job_id = int(existing["id"])
            else:
                capture = connection.execute(
                    "SELECT id, project_id FROM photo_capture_sessions WHERE id = ? AND owner_user_id = ? AND status = 'ready'",
                    (payload.capture_session_id, owner_user_id),
                ).fetchone()
                if capture is None:
                    raise PermissionError("captura pronta não encontrada")
                prior = connection.execute(
                    "SELECT id FROM photo_reconstruction_jobs WHERE capture_session_id = ? AND owner_user_id = ?",
                    (payload.capture_session_id, owner_user_id),
                ).fetchone()
                if prior is not None:
                    job_id = int(prior["id"])
                else:
                    active = int(connection.execute(
                        "SELECT COUNT(*) FROM photo_reconstruction_jobs WHERE owner_user_id = ? AND status IN ('queued', 'processing')",
                        (owner_user_id,),
                    ).fetchone()[0])
                    if active >= max(1, min(self.settings.reconstruction_max_active_per_user, 10)):
                        raise QueueSaturatedError("aguarde uma reconstrução terminar antes de iniciar outra")
                    correlation_id = uuid4().hex
                    cursor = connection.execute(
                        """
                        INSERT INTO photo_reconstruction_jobs (
                            capture_session_id, project_id, owner_user_id, engine_policy,
                            idempotency_key, correlation_id
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            payload.capture_session_id,
                            int(capture["project_id"]),
                            owner_user_id,
                            payload.engine_policy,
                            safe_key,
                            correlation_id,
                        ),
                    )
                    job_id = int(cursor.lastrowid)
                    durable = self.durable.enqueue_job(
                        job_key=f"photo-reconstruction:{job_id}:1",
                        queue_name="bulk",
                        job_type="photo.reconstruction.execute",
                        payload={"reconstruction_job_id": job_id},
                        ordering_key=f"photo-reconstruction:{job_id}",
                        owner_type="user",
                        owner_id=str(owner_user_id),
                        priority=70,
                        max_attempts=3,
                        connection=connection,
                    )
                    connection.execute(
                        "UPDATE photo_reconstruction_jobs SET durable_job_id = ? WHERE id = ?",
                        (durable.id, job_id),
                    )
        return self.get(owner_user_id, job_id)

    def list_for_owner(self, owner_user_id: int, capture_session_id: int | None = None) -> list[ReconstructionJob]:
        with connect_database(self.database_path) as connection:
            statement = "SELECT id FROM photo_reconstruction_jobs WHERE owner_user_id = ?"
            parameters: tuple[object, ...] = (owner_user_id,)
            if capture_session_id is not None:
                statement += " AND capture_session_id = ?"
                parameters = (owner_user_id, capture_session_id)
            statement += " ORDER BY updated_at DESC, id DESC"
            rows = connection.execute(statement, parameters).fetchall()
        return [self.get(owner_user_id, int(row["id"])) for row in rows]

    def get(self, owner_user_id: int, job_id: int) -> ReconstructionJob:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM photo_reconstruction_jobs WHERE id = ? AND owner_user_id = ?",
                (job_id, owner_user_id),
            ).fetchone()
            if row is None:
                raise PermissionError("reconstrução não encontrada")
            attempts = connection.execute(
                "SELECT * FROM photo_reconstruction_attempts WHERE reconstruction_job_id = ? ORDER BY attempt_number, id",
                (job_id,),
            ).fetchall()
            artifacts = connection.execute(
                "SELECT * FROM photo_reconstruction_artifacts WHERE reconstruction_job_id = ? AND is_canonical = 1 ORDER BY id",
                (job_id,),
            ).fetchall()
            qualification = connection.execute(
                """
                SELECT mq.*
                FROM mesh_qualifications mq
                JOIN photo_reconstruction_artifacts ra ON ra.id = mq.reconstruction_artifact_id
                WHERE ra.reconstruction_job_id = ? AND ra.is_canonical = 1
                ORDER BY mq.id DESC LIMIT 1
                """,
                (job_id,),
            ).fetchone()
        return reconstruction_job_model(row, attempts, artifacts, qualification)

    def cancel(self, owner_user_id: int, job_id: int) -> ReconstructionJob:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT durable_job_id, status FROM photo_reconstruction_jobs WHERE id = ? AND owner_user_id = ?",
                (job_id, owner_user_id),
            ).fetchone()
            if row is None:
                raise PermissionError("reconstrução não encontrada")
            if row["status"] in {"queued", "processing"}:
                connection.execute(
                    "UPDATE photo_reconstruction_jobs SET status = 'cancelled', stage = 'cancelled', progress_percent = NULL, active_attempt_id = NULL, cancel_requested_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (job_id,),
                )
                if row["durable_job_id"] is not None:
                    connection.execute(
                        "UPDATE durable_jobs SET status = 'canceled', completed_at = CURRENT_TIMESTAMP, lease_owner = NULL, lease_token = NULL, lease_expires_at = NULL, heartbeat_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('queued', 'leased')",
                        (int(row["durable_job_id"]),),
                    )
        return self.get(owner_user_id, job_id)

    def open_artifact(self, owner_user_id: int, job_id: int, artifact_id: int):
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT ra.storage_key, ra.file_format
                FROM photo_reconstruction_artifacts ra
                JOIN photo_reconstruction_jobs rj ON rj.id = ra.reconstruction_job_id
                WHERE ra.id = ? AND rj.id = ? AND rj.owner_user_id = ? AND ra.is_canonical = 1
                """,
                (artifact_id, job_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise PermissionError("artefato não encontrado")
        return self.storage.storage.open_promoted(str(row["storage_key"])), str(row["file_format"])

    def retry(self, owner_user_id: int, job_id: int, idempotency_key: str) -> ReconstructionJob:
        safe_key = _idempotency_key(idempotency_key)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM photo_reconstruction_jobs WHERE id = ? AND owner_user_id = ?",
                (job_id, owner_user_id),
            ).fetchone()
            if row is None:
                raise PermissionError("reconstrução não encontrada")
            if row["status"] not in {"failed", "cancelled"}:
                pass
            else:
                generation = int(row["run_generation"]) + 1
                durable = self.durable.enqueue_job(
                    job_key=f"photo-reconstruction:{job_id}:{generation}:{safe_key}",
                    queue_name="bulk",
                    job_type="photo.reconstruction.execute",
                    payload={"reconstruction_job_id": job_id},
                    ordering_key=f"photo-reconstruction:{job_id}",
                    owner_type="user",
                    owner_id=str(owner_user_id),
                    priority=70,
                    max_attempts=3,
                    connection=connection,
                )
                connection.execute(
                    """
                    UPDATE photo_reconstruction_jobs
                    SET durable_job_id = ?, run_generation = ?, status = 'queued', stage = 'waiting',
                        progress_percent = NULL, active_attempt_id = NULL, error_code = NULL, error_message = NULL,
                        cancel_requested_at = NULL, completed_at = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (durable.id, generation, job_id),
                )
        return self.get(owner_user_id, job_id)

    def begin_attempt(self, job_id: int, engine_key: str, adapter_version: str) -> tuple[int, ReconstructionAdapterInput]:
        with connect_database(self.database_path) as connection:
            job = connection.execute(
                "SELECT * FROM photo_reconstruction_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if job is None or job["status"] == "cancelled":
                raise ValueError("reconstrução cancelada ou ausente")
            capture = connection.execute(
                "SELECT * FROM photo_capture_sessions WHERE id = ? AND status = 'ready'",
                (int(job["capture_session_id"]),),
            ).fetchone()
            if capture is None:
                raise ValueError("captura não está pronta")
            photos = connection.execute(
                "SELECT * FROM photo_capture_photos WHERE session_id = ? AND is_current = 1 AND quality_status = 'accepted' ORDER BY capture_index, id",
                (int(job["capture_session_id"]),),
            ).fetchall()
            if len(photos) < int(capture["target_photo_count"]):
                raise ValueError("captura ficou incompleta")
            attempt_number = int(connection.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM photo_reconstruction_attempts WHERE reconstruction_job_id = ?",
                (job_id,),
            ).fetchone()[0])
            cursor = connection.execute(
                "INSERT INTO photo_reconstruction_attempts (reconstruction_job_id, attempt_number, engine_key, adapter_version) VALUES (?, ?, ?, ?)",
                (job_id, attempt_number, engine_key, adapter_version),
            )
            attempt_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE photo_reconstruction_jobs SET status = 'processing', stage = 'preparing', progress_percent = NULL, engine_key = ?, active_attempt_id = ?, started_at = COALESCE(started_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (engine_key, attempt_id, job_id),
            )
        return attempt_id, ReconstructionAdapterInput(
            job_id=job_id,
            correlation_id=str(job["correlation_id"]),
            scale_method=str(capture["scale_method"]),
            scale_value_mm=capture["scale_value_mm"],
            scale_uncertainty_mm=capture["scale_uncertainty_mm"],
            photos=tuple(
                ReconstructionPhotoInput(
                    capture_index=int(photo["capture_index"]),
                    height_band=str(photo["height_band"]),
                    storage_key=str(photo["storage_key"]),
                    sha256=str(photo["sha256"]),
                    width=int(photo["width"]),
                    height=int(photo["height"]),
                )
                for photo in photos
            ),
        )

    def engine_policy_for_worker(self, job_id: int) -> str:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT engine_policy FROM photo_reconstruction_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            raise ValueError("reconstrução ausente")
        return str(row["engine_policy"])

    def ensure_engine_available(self, engine_key: str) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT circuit_open_until FROM photo_reconstruction_engine_health WHERE engine_key = ?",
                (engine_key,),
            ).fetchone()
        if row is not None and row["circuit_open_until"] is not None and str(row["circuit_open_until"]) > now:
            raise ReconstructionUnavailableError("O processador está temporariamente pausado após falhas repetidas.")

    def record_engine_success(self, engine_key: str) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO photo_reconstruction_engine_health (engine_key, consecutive_failures, last_success_at)
                VALUES (?, 0, CURRENT_TIMESTAMP)
                ON CONFLICT(engine_key) DO UPDATE SET consecutive_failures = 0,
                    circuit_open_until = NULL, last_success_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (engine_key,),
            )

    def record_engine_failure(self, engine_key: str) -> None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT consecutive_failures FROM photo_reconstruction_engine_health WHERE engine_key = ?",
                (engine_key,),
            ).fetchone()
            failures = int(row["consecutive_failures"] if row else 0) + 1
            open_until = (
                (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S.%f")
                if failures >= 3
                else None
            )
            connection.execute(
                """
                INSERT INTO photo_reconstruction_engine_health (
                    engine_key, consecutive_failures, circuit_open_until, last_failure_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(engine_key) DO UPDATE SET consecutive_failures = excluded.consecutive_failures,
                    circuit_open_until = excluded.circuit_open_until,
                    last_failure_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                """,
                (engine_key, failures, open_until),
            )

    def update_stage(self, job_id: int, attempt_id: int, stage: str) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE photo_reconstruction_jobs SET stage = ?, progress_percent = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'processing'",
                (stage, job_id),
            )
            connection.execute(
                "UPDATE photo_reconstruction_attempts SET stage = ? WHERE id = ? AND reconstruction_job_id = ? AND status = 'processing'",
                (stage, attempt_id, job_id),
            )

    def is_cancel_requested(self, job_id: int, attempt_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT status, active_attempt_id, cancel_requested_at FROM photo_reconstruction_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        return (
            row is None
            or row["status"] == "cancelled"
            or row["cancel_requested_at"] is not None
            or int(row["active_attempt_id"] or 0) != attempt_id
        )

    def cancel_from_worker(self, job_id: int, attempt_id: int | None) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE photo_reconstruction_attempts SET status = 'cancelled', stage = 'cancelled', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND reconstruction_job_id = ? AND status = 'processing'",
                (attempt_id, job_id),
            )
            connection.execute(
                "UPDATE photo_reconstruction_jobs SET status = 'cancelled', stage = 'cancelled', progress_percent = NULL, active_attempt_id = NULL, cancel_requested_at = COALESCE(cancel_requested_at, CURRENT_TIMESTAMP), completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('queued', 'processing')",
                (job_id,),
            )

    def succeed(self, job_id: int, attempt_id: int, result: ReconstructionAdapterResult) -> ReconstructionJob:
        checksum = hashlib.sha256(result.mesh_bytes).hexdigest()
        with connect_database(self.database_path) as connection:
            job = connection.execute("SELECT * FROM photo_reconstruction_jobs WHERE id = ?", (job_id,)).fetchone()
            if job is None or job["status"] == "cancelled" or int(job["active_attempt_id"] or 0) != attempt_id:
                raise ValueError("reconstrução cancelada, ausente ou tentativa não é mais ativa")
            if total_personal_storage_used(connection, int(job["owner_user_id"])) + len(result.mesh_bytes) > personal_storage_quota(connection, int(job["owner_user_id"])):
                raise ValueError("cota de armazenamento insuficiente para a malha reconstruída")
            stored = self.storage.storage.write_quarantine(checksum, f".{result.mesh_format}", result.mesh_bytes)
            promoted = self.storage.storage.promote(stored)
            provenance = {
                **result.provenance,
                "schema": "printora.reconstruction-provenance/v1",
                "engine": result.engine_key,
                "adapter_version": result.adapter_version,
                "model_version": result.model_version,
                "source_checksums": [photo.sha256 for photo in self._photo_inputs(connection, int(job["capture_session_id"]))],
                "parameters": result.parameters,
            }
            connection.execute(
                "UPDATE photo_reconstruction_artifacts SET is_canonical = 0 WHERE reconstruction_job_id = ? AND artifact_type = 'raw_mesh' AND is_canonical = 1",
                (job_id,),
            )
            cursor = connection.execute(
                """
                INSERT INTO photo_reconstruction_artifacts (
                    reconstruction_job_id, attempt_id, artifact_type, file_format,
                    storage_key, sha256, size_bytes, unit, observed_ratio,
                    inferred_ratio, provenance_json
                ) VALUES (?, ?, 'raw_mesh', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id, attempt_id, result.mesh_format, promoted.key, checksum,
                    len(result.mesh_bytes), result.unit, result.observed_ratio,
                    result.inferred_ratio, json.dumps(provenance, ensure_ascii=False, sort_keys=True),
                ),
            )
            artifact_id = int(cursor.lastrowid)
            qualification = qualify_mesh(result.mesh_bytes, result.mesh_format, result.unit)
            connection.execute(
                """
                INSERT INTO mesh_qualifications (
                    reconstruction_artifact_id, source_sha256, analyzer_version,
                    status, report_json
                ) VALUES (?, ?, 'deterministic-v1', ?, ?)
                """,
                (
                    artifact_id,
                    checksum,
                    str(qualification["status"]),
                    json.dumps(qualification, ensure_ascii=False, sort_keys=True),
                ),
            )
            self.storage.register_object(
                connection,
                promoted,
                owner_user_id=int(job["owner_user_id"]),
                reference_type="photo_reconstruction_artifact",
                reference_id=artifact_id,
                state="promoted",
            )
            connection.execute(
                "UPDATE photo_reconstruction_attempts SET status = 'succeeded', stage = 'ready', provenance_json = ?, actual_cost_cents = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(provenance, ensure_ascii=False, sort_keys=True), result.actual_cost_cents, attempt_id),
            )
            connection.execute(
                "UPDATE photo_reconstruction_jobs SET status = 'succeeded', stage = 'ready', progress_percent = 100, engine_key = ?, actual_cost_cents = ?, active_attempt_id = NULL, error_code = NULL, error_message = NULL, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (result.engine_key, result.actual_cost_cents, job_id),
            )
            owner_user_id = int(job["owner_user_id"])
        return self.get(owner_user_id, job_id)

    def fail(self, job_id: int, attempt_id: int | None, *, retryable: bool, code: str, message: str) -> None:
        safe_message = message[:400]
        with connect_database(self.database_path) as connection:
            job = connection.execute("SELECT status, active_attempt_id FROM photo_reconstruction_jobs WHERE id = ?", (job_id,)).fetchone()
            if job is None or job["status"] == "cancelled" or (attempt_id is not None and int(job["active_attempt_id"] or 0) != attempt_id):
                return
            status = "queued" if retryable else "failed"
            stage = "waiting" if retryable else "failed"
            connection.execute(
                "UPDATE photo_reconstruction_jobs SET status = ?, stage = ?, progress_percent = NULL, active_attempt_id = NULL, error_code = ?, error_message = ?, completed_at = CASE WHEN ? = 'failed' THEN CURRENT_TIMESTAMP ELSE NULL END, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, stage, code[:80], safe_message, status, job_id),
            )
            if attempt_id is not None:
                connection.execute(
                    "UPDATE photo_reconstruction_attempts SET status = 'failed', stage = 'failed', error_code = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (code[:80], safe_message, attempt_id),
                )

    @staticmethod
    def _photo_inputs(connection, capture_session_id: int) -> tuple[ReconstructionPhotoInput, ...]:
        rows = connection.execute(
            "SELECT * FROM photo_capture_photos WHERE session_id = ? AND is_current = 1 AND quality_status = 'accepted' ORDER BY capture_index, id",
            (capture_session_id,),
        ).fetchall()
        return tuple(
            ReconstructionPhotoInput(
                capture_index=int(row["capture_index"]), height_band=str(row["height_band"]),
                storage_key=str(row["storage_key"]), sha256=str(row["sha256"]),
                width=int(row["width"]), height=int(row["height"]),
            )
            for row in rows
        )


def _idempotency_key(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 120 or any(character in cleaned for character in "\r\n\0"):
        raise ValueError("chave de repetição inválida")
    return cleaned
