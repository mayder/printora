from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.database import connect_database
from app.modules.community.storage_usage import personal_storage_quota, total_personal_storage_used
from app.modules.operations.mesh_qualification.analyzer import qualify_mesh
from app.modules.operations.mesh_qualification.contracts import MeshRepairCreate, MeshRevision
from app.modules.operations.mesh_qualification.repair import MeshRepairResult
from app.modules.platform.durable_execution import DurableExecutionRepository, QueueSaturatedError
from app.social_storage import SocialStorageRepository


@dataclass(frozen=True)
class MeshRepairInput:
    revision_id: int
    source_key: str
    source_format: str
    source_unit: str
    operation: str
    parameters: dict[str, object]


class MeshRevisionRepository:
    def __init__(self, database_path: Path, settings: Settings) -> None:
        self.database_path = database_path
        self.settings = settings
        self.durable = DurableExecutionRepository(database_path)
        self.storage = SocialStorageRepository(database_path)

    def create(self, owner_user_id: int, job_id: int, payload: MeshRepairCreate, idempotency_key: str) -> MeshRevision:
        safe_key = _idempotency_key(idempotency_key)
        request_hash = _request_hash(job_id, payload)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT id, request_hash FROM mesh_revisions WHERE owner_user_id = ? AND idempotency_key = ?",
                (owner_user_id, safe_key),
            ).fetchone()
            if existing is not None:
                if str(existing["request_hash"]) != request_hash:
                    raise ValueError("chave de repetição já usada em outra correção")
                revision_id = int(existing["id"])
            else:
                active = int(connection.execute(
                    "SELECT COUNT(*) FROM mesh_revisions WHERE owner_user_id = ? AND status IN ('queued', 'processing')",
                    (owner_user_id,),
                ).fetchone()[0])
                if active >= 3:
                    raise QueueSaturatedError("aguarde uma correção terminar antes de iniciar outra")
                source = self._source(connection, owner_user_id, job_id, payload.source_revision_id)
                cursor = connection.execute(
                    """
                    INSERT INTO mesh_revisions (
                        reconstruction_job_id, source_artifact_id, parent_revision_id,
                        owner_user_id, operation, parameters_json, request_hash,
                        idempotency_key, unit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id, int(source["source_artifact_id"]), payload.source_revision_id,
                        owner_user_id, payload.operation,
                        json.dumps(payload.parameters, ensure_ascii=False, sort_keys=True),
                        request_hash, safe_key, str(source["unit"]),
                    ),
                )
                revision_id = int(cursor.lastrowid)
                durable = self.durable.enqueue_job(
                    job_key=f"mesh-repair:{revision_id}", queue_name="bulk",
                    job_type="mesh.repair.execute", payload={"mesh_revision_id": revision_id},
                    ordering_key=f"mesh-repair:{job_id}", owner_type="user",
                    owner_id=str(owner_user_id), priority=75, max_attempts=3,
                    connection=connection,
                )
                connection.execute(
                    "UPDATE mesh_revisions SET durable_job_id = ? WHERE id = ?",
                    (durable.id, revision_id),
                )
        return self.get(owner_user_id, job_id, revision_id)

    def list(self, owner_user_id: int, job_id: int) -> list[MeshRevision]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM mesh_revisions WHERE reconstruction_job_id = ? AND owner_user_id = ? ORDER BY created_at, id",
                (job_id, owner_user_id),
            ).fetchall()
        return [_model(row) for row in rows]

    def get(self, owner_user_id: int, job_id: int, revision_id: int) -> MeshRevision:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM mesh_revisions WHERE id = ? AND reconstruction_job_id = ? AND owner_user_id = ?",
                (revision_id, job_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise PermissionError("correção não encontrada")
        return _model(row)

    def begin(self, revision_id: int, durable_job_id: int) -> MeshRepairInput:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM mesh_revisions WHERE id = ? AND durable_job_id = ? AND status IN ('queued', 'processing')",
                (revision_id, durable_job_id),
            ).fetchone()
            if row is None:
                raise ValueError("correção cancelada, concluída ou substituída")
            source = self._source_for_worker(connection, row)
            connection.execute(
                "UPDATE mesh_revisions SET status = 'processing', error_message = NULL, started_at = COALESCE(started_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (revision_id,),
            )
        return MeshRepairInput(
            revision_id=revision_id, source_key=str(source["storage_key"]),
            source_format=str(source["file_format"]), source_unit=str(row["unit"]),
            operation=str(row["operation"]), parameters=json.loads(row["parameters_json"] or "{}"),
        )

    def read_source(self, source: MeshRepairInput) -> bytes:
        reader = self.storage.storage.open_promoted(source.source_key)
        if reader.size_bytes > 500 * 1024 * 1024:
            reader.body.close()
            raise ValueError("A malha excede o limite seguro de reparo.")
        try:
            return reader.body.read()
        finally:
            reader.body.close()

    def succeed(self, source: MeshRepairInput, durable_job_id: int, result: MeshRepairResult) -> MeshRevision:
        qualification = qualify_mesh(result.body, result.file_format, result.unit)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM mesh_revisions WHERE id = ? AND durable_job_id = ? AND status = 'processing'",
                (source.revision_id, durable_job_id),
            ).fetchone()
            if row is None:
                raise ValueError("correção cancelada ou substituída")
            owner_user_id = int(row["owner_user_id"])
            if total_personal_storage_used(connection, owner_user_id) + len(result.body) > personal_storage_quota(connection, owner_user_id):
                raise ValueError("cota de armazenamento insuficiente para a nova versão")
            stored = self.storage.storage.write_quarantine(result.sha256, f".{result.file_format}", result.body)
            promoted = self.storage.storage.promote(stored)
            connection.execute(
                """
                UPDATE mesh_revisions SET status = 'succeeded', output_format = ?,
                    storage_key = ?, sha256 = ?, size_bytes = ?, manifest_json = ?,
                    qualification_json = ?, unit = ?, error_message = NULL,
                    completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    result.file_format, promoted.key, result.sha256, len(result.body),
                    json.dumps(result.manifest, ensure_ascii=False, sort_keys=True),
                    json.dumps(qualification, ensure_ascii=False, sort_keys=True), result.unit,
                    source.revision_id,
                ),
            )
            self.storage.register_object(
                connection, promoted, owner_user_id=owner_user_id,
                reference_type="mesh_revision", reference_id=source.revision_id,
                state="promoted",
            )
            job_id = int(row["reconstruction_job_id"])
        return self.get(owner_user_id, job_id, source.revision_id)

    def fail(self, revision_id: int, durable_job_id: int, message: str, retryable: bool) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE mesh_revisions SET status = ?, error_message = ?, completed_at = CASE WHEN ? = 'failed' THEN CURRENT_TIMESTAMP ELSE NULL END, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND durable_job_id = ? AND status = 'processing'",
                ("queued" if retryable else "failed", message[:400], "queued" if retryable else "failed", revision_id, durable_job_id),
            )

    def cancel(self, owner_user_id: int, job_id: int, revision_id: int) -> MeshRevision:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT durable_job_id, status FROM mesh_revisions WHERE id = ? AND reconstruction_job_id = ? AND owner_user_id = ?",
                (revision_id, job_id, owner_user_id),
            ).fetchone()
            if row is None:
                raise PermissionError("correção não encontrada")
            if row["status"] in {"queued", "processing"}:
                connection.execute(
                    "UPDATE mesh_revisions SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (revision_id,),
                )
                connection.execute(
                    "UPDATE durable_jobs SET status = 'canceled', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN ('queued', 'leased')",
                    (int(row["durable_job_id"]),),
                )
        return self.get(owner_user_id, job_id, revision_id)

    def open(self, owner_user_id: int, job_id: int, revision_id: int):
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT storage_key, output_format FROM mesh_revisions WHERE id = ? AND reconstruction_job_id = ? AND owner_user_id = ? AND status = 'succeeded'",
                (revision_id, job_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise PermissionError("versão pronta não encontrada")
        return self.storage.storage.open_promoted(str(row["storage_key"])), str(row["output_format"])

    @staticmethod
    def _source(connection, owner_user_id: int, job_id: int, parent_revision_id: int | None):
        if parent_revision_id is not None:
            row = connection.execute(
                "SELECT source_artifact_id, unit FROM mesh_revisions WHERE id = ? AND reconstruction_job_id = ? AND owner_user_id = ? AND status = 'succeeded'",
                (parent_revision_id, job_id, owner_user_id),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT ra.id AS source_artifact_id, ra.unit FROM photo_reconstruction_artifacts ra JOIN photo_reconstruction_jobs rj ON rj.id = ra.reconstruction_job_id WHERE rj.id = ? AND rj.owner_user_id = ? AND rj.status = 'succeeded' AND ra.artifact_type = 'raw_mesh' AND ra.is_canonical = 1",
                (job_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise PermissionError("malha de origem pronta não encontrada")
        return row

    @staticmethod
    def _source_for_worker(connection, revision):
        if revision["parent_revision_id"] is not None:
            row = connection.execute(
                "SELECT storage_key, output_format AS file_format FROM mesh_revisions WHERE id = ? AND status = 'succeeded'",
                (int(revision["parent_revision_id"]),),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT storage_key, file_format FROM photo_reconstruction_artifacts WHERE id = ?",
                (int(revision["source_artifact_id"]),),
            ).fetchone()
        if row is None:
            raise ValueError("malha de origem indisponível")
        return row


def _model(row) -> MeshRevision:
    status = str(row["status"])
    return MeshRevision(
        id=int(row["id"]), reconstruction_job_id=int(row["reconstruction_job_id"]),
        source_artifact_id=int(row["source_artifact_id"]), parent_revision_id=row["parent_revision_id"],
        operation=str(row["operation"]), parameters=json.loads(row["parameters_json"] or "{}"), status=status,
        output_format=row["output_format"], sha256=row["sha256"], size_bytes=row["size_bytes"], unit=str(row["unit"]),
        manifest=json.loads(row["manifest_json"] or "{}"), qualification=json.loads(row["qualification_json"] or "{}"),
        error_message=row["error_message"], can_cancel=status in {"queued", "processing"},
        next_action={"queued": "A correção está na fila.", "processing": "A nova versão está sendo preparada.", "succeeded": "A nova versão está pronta para revisão.", "failed": "Revise o problema e tente outra correção.", "cancelled": "A malha original continua preservada."}[status],
        created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
    )


def _request_hash(job_id: int, payload: MeshRepairCreate) -> str:
    body = json.dumps({"job_id": job_id, **payload.model_dump()}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def _idempotency_key(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 120 or any(character in cleaned for character in "\r\n\0"):
        raise ValueError("chave de repetição inválida")
    return cleaned
