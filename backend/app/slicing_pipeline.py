from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.config import Settings
from app.database import connect_database
from app.modules.platform.durable_execution import DurableExecutionRepository
from app.slicing import SlicerEngine, SlicingEngineBridge, SlicingRequest

SlicingJobStatus = Literal["planned", "running", "completed", "failed", "canceled"]
ArtifactKind = Literal["gcode", "log", "metadata", "preview"]


class ModelDimensions(BaseModel):
    x_mm: float | None = Field(default=None, gt=0, le=2000)
    y_mm: float | None = Field(default=None, gt=0, le=2000)
    z_mm: float | None = Field(default=None, gt=0, le=2000)


class SlicingJobCreate(BaseModel):
    printer_id: int = Field(ge=1)
    material_profile_id: int | None = Field(default=None, ge=1)
    slicing_profile_revision_id: int | None = Field(default=None, ge=1)
    engine: SlicerEngine = "orcaslicer"
    model_reference: str = Field(min_length=1, max_length=240)
    model_version_reference: str = Field(default="", max_length=120)
    model_dimensions: ModelDimensions = Field(default_factory=ModelDimensions)
    quality_reference: str = Field(min_length=1, max_length=120)
    profile_reference: str | None = Field(default=None, max_length=160)

    @field_validator("model_reference", "model_version_reference", "quality_reference", "profile_reference")
    @classmethod
    def clean_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        lower = cleaned.lower()
        if any(marker in lower for marker in ("token", "secret", "password", "passwd", "ptr_agent_", "ptr_pair_", "ptr_sess_")):
            raise ValueError("referência contém dado sensível")
        return cleaned


class ProjectSlicingJobCreate(BaseModel):
    project_id: int = Field(ge=1)
    selected_file_ids: list[int] = Field(default_factory=list, min_length=1, max_length=20)
    file_quantities: dict[int, int] = Field(default_factory=dict)
    printer_id: int = Field(ge=1)
    spool_id: int | None = Field(default=None, ge=1)
    material_profile_id: int | None = Field(default=None, ge=1)
    slicing_profile_revision_id: int | None = Field(default=None, ge=1)
    engine: SlicerEngine = "orcaslicer"
    model_dimensions: ModelDimensions = Field(default_factory=ModelDimensions)
    quality_reference: str = Field(default="quality", min_length=1, max_length=120)
    profile_reference: str | None = Field(default=None, max_length=160)

    @field_validator("quality_reference", "profile_reference")
    @classmethod
    def clean_reference(cls, value: str | None) -> str | None:
        return SlicingJobCreate.clean_reference(value)

    @field_validator("file_quantities")
    @classmethod
    def validate_quantities(cls, value: dict[int, int]) -> dict[int, int]:
        if len(value) > 20 or any(file_id < 1 or quantity < 1 or quantity > 100 for file_id, quantity in value.items()):
            raise ValueError("quantidades devem ficar entre 1 e 100 para cada arquivo")
        return value


class SlicingArtifact(BaseModel):
    id: int
    job_id: int
    artifact_kind: ArtifactKind
    storage_key: str
    checksum_sha256: str | None
    size_bytes: int
    payload: dict[str, Any]
    created_at: str


class SlicingJob(BaseModel):
    id: int
    owner_user_id: int | None
    printer_id: int | None
    material_profile_id: int | None
    slicing_profile_revision_id: int | None = None
    slicing_profile_sha256: str | None = None
    slicing_profile_engine_version: str | None = None
    engine: SlicerEngine
    model_reference: str
    model_version_reference: str
    model_dimensions: dict[str, Any]
    quality_reference: str
    print_project_id: int | None = None
    print_project_version_id: int | None = None
    selected_project_files: list[dict[str, Any]] = Field(default_factory=list)
    project_snapshot: dict[str, Any] = Field(default_factory=dict)
    gcode_approved_at: str | None = None
    gcode_approved_checksum: str | None = None
    reprint_of_job_id: int | None = None
    status: SlicingJobStatus
    compatibility: dict[str, Any]
    input: dict[str, Any]
    output: dict[str, Any]
    error_message: str | None
    artifacts: list[SlicingArtifact] = Field(default_factory=list)
    created_at: str
    updated_at: str
    completed_at: str | None
    canceled_at: str | None


class SlicingPipelineRepository:
    def __init__(self, database_path: Path, settings: Settings):
        self.database_path = database_path
        self.settings = settings

    def create_job(self, actor_user_id: int | None, payload: SlicingJobCreate) -> SlicingJob:
        printer = self._printer_for_actor(payload.printer_id, actor_user_id)
        profile = self._material_profile(payload.material_profile_id, actor_user_id) if payload.material_profile_id else None
        executable_profile = self._profile_revision(payload.slicing_profile_revision_id, actor_user_id)
        self._validate_profile_engine(executable_profile, payload.engine)
        compatibility = self._validate_compatibility(printer, profile, payload)
        input_payload = {
            "printer": {"id": printer["id"], "name": printer["name"], "catalog_variant_id": printer["catalog_variant_id"]},
            "material_profile": _profile_summary(profile),
            "model": {
                "reference": payload.model_reference,
                "version": payload.model_version_reference,
                "dimensions": payload.model_dimensions.model_dump(),
            },
            "quality": payload.quality_reference,
            "profile_reference": payload.profile_reference,
            "slicing_profile_revision": _profile_revision_summary(executable_profile),
        }
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO slicing_jobs (
                    owner_user_id, printer_id, material_profile_id, engine, model_reference,
                    model_version_reference, model_dimensions_json, quality_reference, compatibility_json, input_json,
                    slicing_profile_revision_id, slicing_profile_sha256, slicing_profile_engine_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor_user_id,
                    payload.printer_id,
                    payload.material_profile_id,
                    payload.engine,
                    payload.model_reference,
                    payload.model_version_reference,
                    json.dumps(payload.model_dimensions.model_dump(), ensure_ascii=False),
                    payload.quality_reference,
                    json.dumps(compatibility, ensure_ascii=False),
                    json.dumps(input_payload, ensure_ascii=False),
                    payload.slicing_profile_revision_id,
                    executable_profile["sha256"] if executable_profile else None,
                    executable_profile["engine_version"] if executable_profile else None,
                ),
            )
            job_id = int(cursor.lastrowid)
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        return job

    def create_project_job(self, actor_user_id: int, payload: ProjectSlicingJobCreate) -> SlicingJob:
        project, version, selected_files = self._project_selection_for_actor(actor_user_id, payload)
        model_reference = f"project://{project['slug']}?files={','.join(str(file['id']) for file in selected_files)}"
        model_version_reference = f"project-version:{version['id']}"
        legacy_payload = SlicingJobCreate(
            printer_id=payload.printer_id,
            material_profile_id=payload.material_profile_id,
            slicing_profile_revision_id=payload.slicing_profile_revision_id,
            engine=payload.engine,
            model_reference=model_reference,
            model_version_reference=model_version_reference,
            model_dimensions=payload.model_dimensions,
            quality_reference=payload.quality_reference,
            profile_reference=payload.profile_reference,
        )
        printer = self._printer_for_actor(payload.printer_id, actor_user_id)
        spool = self._spool_for_actor(payload.spool_id, actor_user_id) if payload.spool_id else None
        if spool is not None and payload.material_profile_id and spool["material_profile_id"] != payload.material_profile_id:
            raise ValueError("o spool selecionado não pertence ao perfil de material escolhido")
        profile = self._material_profile(payload.material_profile_id, actor_user_id) if payload.material_profile_id else None
        executable_profile = self._profile_revision(payload.slicing_profile_revision_id, actor_user_id)
        self._validate_profile_engine(executable_profile, payload.engine)
        compatibility = self._validate_compatibility(printer, profile, legacy_payload)
        project_snapshot = _loads_dict(version["project_snapshot_json"])
        selected_ids = set(payload.selected_file_ids)
        unknown_quantity_ids = set(payload.file_quantities) - selected_ids
        if unknown_quantity_ids:
            raise ValueError("quantidade informada para arquivo não selecionado")
        selected_files_snapshot = [
            _file_snapshot(file, payload.file_quantities.get(int(file["id"]), 1)) for file in selected_files
        ]
        input_payload = {
            "printer": {"id": printer["id"], "name": printer["name"], "catalog_variant_id": printer["catalog_variant_id"]},
            "material_profile": _profile_summary(profile),
            "material_spool": _spool_summary(spool),
            "project": project_snapshot,
            "selected_files": selected_files_snapshot,
            "quality": payload.quality_reference,
            "profile_reference": payload.profile_reference,
            "slicing_profile_revision": _profile_revision_summary(executable_profile),
        }
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO slicing_jobs (
                    owner_user_id, printer_id, material_profile_id, engine, model_reference,
                    model_version_reference, model_dimensions_json, quality_reference, compatibility_json,
                    input_json, print_project_id, print_project_version_id, selected_project_files_json,
                    project_snapshot_json, slicing_profile_revision_id, slicing_profile_sha256,
                    slicing_profile_engine_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor_user_id,
                    payload.printer_id,
                    payload.material_profile_id,
                    payload.engine,
                    model_reference,
                    model_version_reference,
                    json.dumps(payload.model_dimensions.model_dump(), ensure_ascii=False),
                    payload.quality_reference,
                    json.dumps(compatibility, ensure_ascii=False),
                    json.dumps(input_payload, ensure_ascii=False),
                    payload.project_id,
                    int(version["id"]),
                    json.dumps(selected_files_snapshot, ensure_ascii=False),
                    json.dumps(project_snapshot, ensure_ascii=False),
                    payload.slicing_profile_revision_id,
                    executable_profile["sha256"] if executable_profile else None,
                    executable_profile["engine_version"] if executable_profile else None,
                ),
            )
            job_id = int(cursor.lastrowid)
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        return job

    def approve_gcode(self, job_id: int, actor_user_id: int) -> SlicingJob:
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        if job.status != "completed":
            raise ValueError("conclua o fatiamento antes de aprovar a prévia")
        artifact = next((item for item in job.artifacts if item.artifact_kind == "gcode"), None)
        if artifact is None or not artifact.checksum_sha256:
            raise ValueError("G-code rastreado não encontrado")
        with connect_database(self.database_path) as connection:
            connection.execute(
                """UPDATE slicing_jobs
                   SET gcode_approved_at = CURRENT_TIMESTAMP, gcode_approved_checksum = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND owner_user_id = ?""",
                (artifact.checksum_sha256, job_id, actor_user_id),
            )
        return self.get_job(job_id, actor_user_id)  # type: ignore[return-value]

    def create_reprint_job(self, job_id: int, actor_user_id: int) -> SlicingJob:
        source = self.get_job(job_id, actor_user_id)
        if source is None:
            raise ValueError("job original não encontrado")
        if source.print_project_id is None or source.print_project_version_id is None:
            raise ValueError("reimpressão reproduzível exige um job criado a partir de projeto")
        if source.status != "completed":
            raise ValueError("reimpressão exige um fatiamento original concluído")
        input_payload = {**source.input, "reprint_of_job_id": source.id}
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """INSERT INTO slicing_jobs (
                       owner_user_id, printer_id, material_profile_id, engine, model_reference,
                       model_version_reference, model_dimensions_json, quality_reference, compatibility_json,
                       input_json, print_project_id, print_project_version_id, selected_project_files_json,
                       project_snapshot_json, slicing_profile_revision_id, slicing_profile_sha256,
                       slicing_profile_engine_version, reprint_of_job_id
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    actor_user_id, source.printer_id, source.material_profile_id, source.engine,
                    source.model_reference, source.model_version_reference,
                    json.dumps(source.model_dimensions, ensure_ascii=False), source.quality_reference,
                    json.dumps(source.compatibility, ensure_ascii=False), json.dumps(input_payload, ensure_ascii=False),
                    source.print_project_id, source.print_project_version_id,
                    json.dumps(source.selected_project_files, ensure_ascii=False),
                    json.dumps(source.project_snapshot, ensure_ascii=False), source.slicing_profile_revision_id,
                    source.slicing_profile_sha256, source.slicing_profile_engine_version, source.id,
                ),
            )
            new_id = int(cursor.lastrowid)
        return self.get_job(new_id, actor_user_id)  # type: ignore[return-value]

    def run_job(self, job_id: int, actor_user_id: int | None) -> SlicingJob:
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        if job.status == "canceled":
            return job
        if job.status not in {"planned", "failed"}:
            raise ValueError("job de fatiamento não está pronto para execução")
        self._update_status(job.id, "running")
        bridge = SlicingEngineBridge(self.settings)
        material_reference = str(job.input.get("material_profile", {}).get("material_type") or "material")
        dry_run = bridge.dry_run(
            SlicingRequest(
                model_reference=job.model_reference,
                printer_reference=str(job.input.get("printer", {}).get("name") or job.printer_id),
                material_reference=material_reference,
                quality_reference=job.quality_reference,
                profile_reference=str(job.input.get("profile_reference") or job.material_profile_id or "perfil"),
                engine=job.engine,
            )
        )
        if dry_run.status != "ready":
            self._finish_failed(job.id, dry_run.sanitized_log)
            self._record_artifact(job.id, "log", "engine-blocked.log", dry_run.sanitized_log.encode(), {"warnings": dry_run.warnings})
            return self.get_job(job.id, actor_user_id)  # type: ignore[return-value]
        try:
            output = self._execute_worker(job, dry_run.command_preview)
        except RuntimeError as exc:
            self._finish_failed(job.id, str(exc))
            self._record_artifact(job.id, "log", "worker-failed.log", str(exc).encode(), {"command_preview": dry_run.command_preview})
            return self.get_job(job.id, actor_user_id)  # type: ignore[return-value]
        self._finish_completed(job.id, output)
        return self.get_job(job.id, actor_user_id)  # type: ignore[return-value]

    def schedule_job(self, job_id: int, actor_user_id: int | None) -> SlicingJob:
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        if job.status == "canceled":
            return job
        if job.status not in {"planned", "failed"}:
            raise ValueError("job de fatiamento não está pronto para execução")
        with connect_database(self.database_path) as connection:
            active = connection.execute(
                """
                SELECT id FROM durable_jobs
                WHERE owner_type = 'slicing_job' AND owner_id = ? AND status IN ('queued', 'leased')
                LIMIT 1
                """,
                (str(job.id),),
            ).fetchone()
            if active is not None:
                return job
            previous = connection.execute(
                "SELECT COUNT(*) AS total FROM durable_jobs WHERE owner_type = 'slicing_job' AND owner_id = ?",
                (str(job.id),),
            ).fetchone()
            generation = int(previous["total"]) + 1
            DurableExecutionRepository(self.database_path).enqueue_job(
                job_key=f"slicing:{job.id}:execute:{generation}",
                queue_name="bulk",
                job_type="slicing.execute",
                payload={"slicing_job_id": job.id, "actor_user_id": actor_user_id},
                owner_type="slicing_job",
                owner_id=str(job.id),
                priority=100,
                max_attempts=3,
                connection=connection,
            )
            if job.status == "failed":
                connection.execute(
                    """
                    UPDATE slicing_jobs
                    SET status = 'planned', error_message = NULL, completed_at = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'failed'
                    """,
                    (job.id,),
                )
        return self.get_job(job.id, actor_user_id)  # type: ignore[return-value]

    def cancel_job(self, job_id: int, actor_user_id: int | None) -> SlicingJob:
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        if job.status in {"completed", "canceled"}:
            return job
        self._update_status(job.id, "canceled")
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE slicing_jobs SET canceled_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (job.id,),
            )
            connection.execute(
                """
                UPDATE durable_jobs
                SET status = 'canceled', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE owner_type = 'slicing_job' AND owner_id = ? AND status = 'queued'
                """,
                (str(job.id),),
            )
        return self.get_job(job.id, actor_user_id)  # type: ignore[return-value]

    def list_jobs(self, actor_user_id: int | None, limit: int = 20) -> list[SlicingJob]:
        params: list[Any] = []
        where = ""
        if actor_user_id is not None:
            where = "WHERE owner_user_id = ?"
            params.append(actor_user_id)
        params.append(max(1, min(limit, 100)))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM slicing_jobs
                {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._job_from_row(row) for row in rows]

    def list_project_jobs(self, actor_user_id: int, project_id: int, limit: int = 20) -> list[SlicingJob]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM slicing_jobs
                WHERE owner_user_id = ? AND print_project_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (actor_user_id, project_id, max(1, min(limit, 100))),
            ).fetchall()
        return [self._job_from_row(row) for row in rows]

    def get_job(self, job_id: int, actor_user_id: int | None) -> SlicingJob | None:
        params: list[Any] = [job_id]
        visibility = ""
        if actor_user_id is not None:
            visibility = "AND owner_user_id = ?"
            params.append(actor_user_id)
        with connect_database(self.database_path) as connection:
            row = connection.execute(f"SELECT * FROM slicing_jobs WHERE id = ? {visibility}", params).fetchone()
        return self._job_from_row(row) if row else None

    def _printer_for_actor(self, printer_id: int, actor_user_id: int | None):
        with connect_database(self.database_path) as connection:
            if actor_user_id is None:
                row = connection.execute("SELECT * FROM printers WHERE id = ? AND is_active = 1", (printer_id,)).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM printers
                    WHERE id = ? AND is_active = 1
                      AND (owner_user_id = ? OR owner_user_id IS NULL)
                    """,
                    (printer_id, actor_user_id),
                ).fetchone()
        if row is None:
            raise ValueError("impressora não encontrada")
        return row

    def _material_profile(self, profile_id: int | None, actor_user_id: int | None):
        if profile_id is None:
            return None
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT mp.*, sp.layer_height_mm, sp.speed_mm_s, sp.infill_percent, sp.supports_enabled,
                       sp.goal, sp.settings_json
                FROM social_material_profiles mp
                JOIN social_slicing_profiles sp ON sp.material_profile_id = mp.id
                WHERE mp.id = ? AND mp.status = 'active'
                  AND (mp.owner_user_id = ? OR mp.visibility IN ('community', 'public'))
                """,
                (profile_id, actor_user_id or -1),
            ).fetchone()
        if row is None:
            raise ValueError("perfil de material não encontrado")
        return row

    def _spool_for_actor(self, spool_id: int, actor_user_id: int):
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """SELECT id, material_profile_id, name, material_type, brand, color_name,
                          remaining_weight_g, storage_state, revision
                   FROM material_spools
                   WHERE id = ? AND owner_user_id = ? AND status = 'active'""",
                (spool_id, actor_user_id),
            ).fetchone()
        if row is None:
            raise ValueError("spool de material não encontrado")
        return row

    def _profile_revision(self, revision_id: int | None, actor_user_id: int | None):
        if revision_id is None:
            return None
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """SELECT r.id, r.sha256, r.canonical_json, b.engine, b.engine_version, b.schema_version
                   FROM slicing_profile_revisions r
                   JOIN slicing_profile_bundles b ON b.id = r.bundle_id
                   WHERE r.id = ? AND b.owner_user_id = ? AND b.status = 'active'""",
                (revision_id, actor_user_id or -1),
            ).fetchone()
        if row is None:
            raise ValueError("revisão executável de perfil não encontrada")
        return row

    @staticmethod
    def _validate_profile_engine(revision, engine: SlicerEngine) -> None:
        if revision is not None and revision["engine"] != engine:
            raise ValueError("perfil executável incompatível com a engine selecionada")

    def _validate_compatibility(self, printer, profile, payload: SlicingJobCreate) -> dict[str, Any]:
        volume = self._variant_build_volume(printer["catalog_variant_id"])
        dimensions = payload.model_dimensions.model_dump()
        blockers: list[str] = []
        warnings: list[str] = []
        if volume:
            for key, axis in (("x_mm", "x"), ("y_mm", "y"), ("z_mm", "z")):
                model_value = dimensions.get(key)
                max_value = _float_or_none(volume.get(axis))
                if model_value is not None and max_value is not None and float(model_value) > max_value:
                    blockers.append(f"Modelo excede volume útil no eixo {axis.upper()}.")
        else:
            warnings.append("Volume útil da impressora não está catalogado; validação dimensional ficou limitada.")
        if profile is not None and printer["catalog_variant_id"] and profile["catalog_variant_id"]:
            if int(profile["catalog_variant_id"]) != int(printer["catalog_variant_id"]):
                blockers.append("Perfil de material não pertence à variação catalogada da impressora.")
        if blockers:
            raise ValueError(" ".join(blockers))
        return {"status": "compatible", "warnings": warnings, "build_volume": volume or {}, "model_dimensions": dimensions}

    def _variant_build_volume(self, catalog_variant_id: int | None) -> dict[str, Any]:
        if catalog_variant_id is None:
            return {}
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT build_volume_json FROM catalog_printer_variants WHERE id = ?",
                (catalog_variant_id,),
            ).fetchone()
        return json.loads(row["build_volume_json"]) if row else {}

    def _project_selection_for_actor(self, actor_user_id: int, payload: ProjectSlicingJobCreate):
        with connect_database(self.database_path) as connection:
            project = connection.execute(
                """
                SELECT *
                FROM print_projects p
                WHERE p.id = ?
                  AND p.lifecycle_status != 'archived'
                  AND (
                    p.owner_user_id = ?
                    OR EXISTS (
                        SELECT 1
                        FROM print_project_saves ps
                        WHERE ps.project_id = p.id AND ps.owner_user_id = ? AND ps.status = 'active'
                    )
                  )
                """,
                (payload.project_id, actor_user_id, actor_user_id),
            ).fetchone()
            if project is None:
                raise ValueError("projeto não encontrado ou não salvo pelo usuário")
            version_id = project["current_version_id"]
            if version_id is None:
                raise ValueError("projeto precisa de snapshot antes de fatiar")
            version = connection.execute(
                "SELECT * FROM print_project_versions WHERE id = ? AND project_id = ?",
                (version_id, payload.project_id),
            ).fetchone()
            if version is None:
                raise ValueError("snapshot do projeto não encontrado")
            placeholders = ",".join("?" for _ in payload.selected_file_ids)
            files = connection.execute(
                f"""
                SELECT *
                FROM print_project_files
                WHERE project_id = ? AND id IN ({placeholders})
                ORDER BY id
                """,
                (payload.project_id, *payload.selected_file_ids),
            ).fetchall()
        if len(files) != len(set(payload.selected_file_ids)):
            raise ValueError("seleção contém arquivo inexistente no projeto")
        blocked = [
            str(file["file_name"])
            for file in files
            if int(file["can_slice"] or 0) != 1 or file["file_role"] == "external_reference"
        ]
        if blocked:
            raise ValueError("arquivos sem arquivo local validado não podem ser fatiados: " + ", ".join(blocked))
        return project, version, files

    def _execute_worker(self, job: SlicingJob, command_preview: list[str]) -> dict[str, Any]:
        executable = _resolve_engine_path(self.settings, job.engine)
        if executable is None:
            raise RuntimeError("Engine detectada no dry-run, mas indisponível para execução.")
        job_dir = (self.settings.slicer_engine_work_dir or self.settings.data_dir / "slicing_jobs") / str(job.id)
        job_dir.mkdir(parents=True, exist_ok=True)
        output_path = job_dir / "output.gcode"
        log_path = job_dir / "engine.log"
        command = ["<engine>"] + command_preview[1:]
        raw_command = [executable] + command_preview[1:]
        raw_command = [str(output_path) if item == "<artefato-printora>/output.gcode" else item for item in raw_command]
        try:
            completed = subprocess.run(
                raw_command,
                cwd=job_dir,
                capture_output=True,
                text=True,
                timeout=self.settings.slicer_engine_timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Falha ao executar worker de fatiamento: {exc}") from exc
        log_text = _compact("\n".join(part for part in (completed.stdout, completed.stderr) if part).strip())
        log_text = log_text or f"Engine finalizada com exit_code={completed.returncode}."
        if completed.returncode != 0:
            raise RuntimeError(f"Engine retornou erro no fatiamento: exit_code={completed.returncode}. {_compact(log_text)}")
        if not output_path.exists():
            output_path.write_text("; Printora slicing artifact\n; Engine did not create output file; metadata-only artifact.\n", encoding="utf-8")
        gcode_bytes = output_path.read_bytes()
        self._record_artifact(job.id, "gcode", _storage_key(output_path, self.settings.data_dir), gcode_bytes, {"command_preview": command})
        self._record_artifact(job.id, "log", _storage_key(log_path, self.settings.data_dir), log_text.encode(), {"exit_code": completed.returncode})
        log_path.write_text(log_text, encoding="utf-8")
        output = {
            "gcode_storage_key": _storage_key(output_path, self.settings.data_dir),
            "log_storage_key": _storage_key(log_path, self.settings.data_dir),
            "command_preview": command,
            "estimated_time": None,
            "estimated_weight": None,
            "warnings": [],
        }
        self._record_artifact(job.id, "metadata", "metadata.json", json.dumps(output, ensure_ascii=False).encode(), output)
        return output

    def _record_artifact(self, job_id: int, kind: ArtifactKind, storage_key: str, content: bytes, payload: dict[str, Any]) -> None:
        checksum = hashlib.sha256(content).hexdigest() if content else None
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO slicing_job_artifacts (job_id, artifact_kind, storage_key, checksum_sha256, size_bytes, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, kind, storage_key, checksum, len(content), json.dumps(payload, ensure_ascii=False)),
            )

    def _update_status(self, job_id: int, status: SlicingJobStatus) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE slicing_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, job_id),
            )

    def _finish_failed(self, job_id: int, message: str) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE slicing_jobs
                SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (_compact(message), job_id),
            )

    def _finish_completed(self, job_id: int, output: dict[str, Any]) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE slicing_jobs
                SET status = 'completed', output_json = ?, updated_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(output, ensure_ascii=False), job_id),
            )

    def _job_from_row(self, row) -> SlicingJob:
        with connect_database(self.database_path) as connection:
            artifact_rows = connection.execute(
                "SELECT * FROM slicing_job_artifacts WHERE job_id = ? ORDER BY id",
                (row["id"],),
            ).fetchall()
        return SlicingJob(
            id=int(row["id"]),
            owner_user_id=row["owner_user_id"],
            printer_id=row["printer_id"],
            material_profile_id=row["material_profile_id"],
            slicing_profile_revision_id=row["slicing_profile_revision_id"] if "slicing_profile_revision_id" in row.keys() else None,
            slicing_profile_sha256=row["slicing_profile_sha256"] if "slicing_profile_sha256" in row.keys() else None,
            slicing_profile_engine_version=row["slicing_profile_engine_version"] if "slicing_profile_engine_version" in row.keys() else None,
            engine=row["engine"],
            model_reference=row["model_reference"],
            model_version_reference=row["model_version_reference"],
            model_dimensions=json.loads(row["model_dimensions_json"]),
            quality_reference=row["quality_reference"],
            print_project_id=row["print_project_id"] if "print_project_id" in row.keys() else None,
            print_project_version_id=row["print_project_version_id"] if "print_project_version_id" in row.keys() else None,
            selected_project_files=_loads_dict_list(row["selected_project_files_json"]) if "selected_project_files_json" in row.keys() else [],
            project_snapshot=_loads_dict(row["project_snapshot_json"]) if "project_snapshot_json" in row.keys() else {},
            gcode_approved_at=row["gcode_approved_at"] if "gcode_approved_at" in row.keys() else None,
            gcode_approved_checksum=row["gcode_approved_checksum"] if "gcode_approved_checksum" in row.keys() else None,
            reprint_of_job_id=row["reprint_of_job_id"] if "reprint_of_job_id" in row.keys() else None,
            status=row["status"],
            compatibility=json.loads(row["compatibility_json"]),
            input=json.loads(row["input_json"]),
            output=json.loads(row["output_json"]),
            error_message=row["error_message"],
            artifacts=[
                SlicingArtifact(
                    id=int(artifact["id"]),
                    job_id=int(artifact["job_id"]),
                    artifact_kind=artifact["artifact_kind"],
                    storage_key=artifact["storage_key"],
                    checksum_sha256=artifact["checksum_sha256"],
                    size_bytes=int(artifact["size_bytes"]),
                    payload=json.loads(artifact["payload_json"]),
                    created_at=artifact["created_at"],
                )
                for artifact in artifact_rows
            ],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            canceled_at=row["canceled_at"],
        )


def _resolve_engine_path(settings: Settings, engine: SlicerEngine) -> str | None:
    if settings.slicer_engine_path and settings.slicer_engine_path.is_file() and os.access(settings.slicer_engine_path, os.X_OK):
        return str(settings.slicer_engine_path)
    names = ("orcaslicer", "OrcaSlicer") if engine == "orcaslicer" else ("prusaslicer", "prusa-slicer", "PrusaSlicer")
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _profile_summary(profile) -> dict[str, Any]:
    if profile is None:
        return {}
    return {
        "id": profile["id"],
        "title": profile["title"],
        "material_type": profile["material_type"],
        "nozzle_diameter_mm": profile["nozzle_diameter_mm"],
        "bed_temperature_c": profile["bed_temperature_c"],
        "nozzle_temperature_c": profile["nozzle_temperature_c"],
        "slicing": {
            "layer_height_mm": profile["layer_height_mm"],
            "speed_mm_s": profile["speed_mm_s"],
            "infill_percent": profile["infill_percent"],
            "supports_enabled": bool(profile["supports_enabled"]),
            "goal": profile["goal"],
            "settings": json.loads(profile["settings_json"]),
        },
    }


def _profile_revision_summary(revision) -> dict[str, Any]:
    if revision is None:
        return {}
    return {
        "id": int(revision["id"]),
        "engine": revision["engine"],
        "engine_version": revision["engine_version"],
        "schema_version": revision["schema_version"],
        "sha256": revision["sha256"],
        "canonical": _loads_dict(revision["canonical_json"]),
    }


def _spool_summary(spool) -> dict[str, Any]:
    if spool is None:
        return {}
    return {
        "id": int(spool["id"]),
        "material_profile_id": spool["material_profile_id"],
        "name": spool["name"],
        "material_type": spool["material_type"],
        "brand": spool["brand"],
        "color_name": spool["color_name"],
        "remaining_weight_g": spool["remaining_weight_g"],
        "storage_state": spool["storage_state"],
        "revision": int(spool["revision"]),
    }


def _file_snapshot(file, quantity: int = 1) -> dict[str, Any]:
    return {
        "id": int(file["id"]),
        "file_name": file["file_name"],
        "file_kind": file["file_kind"],
        "file_role": file["file_role"],
        "size_bytes": file["size_bytes"],
        "sha256": file["sha256"],
        "validation_status": file["validation_status"],
        "can_slice": bool(file["can_slice"]),
        "quantity": quantity,
    }


def _loads_dict(value: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _loads_dict_list(value: str | None) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact(value: str) -> str:
    return " ".join(value.replace(str(Path.home()), "<home>").split())[:500]


def _storage_key(path: Path, data_dir: Path) -> str:
    try:
        return str(path.relative_to(data_dir))
    except ValueError:
        return path.name
