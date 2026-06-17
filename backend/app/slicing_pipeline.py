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
    engine: SlicerEngine
    model_reference: str
    model_version_reference: str
    model_dimensions: dict[str, Any]
    quality_reference: str
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
        }
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO slicing_jobs (
                    owner_user_id, printer_id, material_profile_id, engine, model_reference,
                    model_version_reference, model_dimensions_json, quality_reference, compatibility_json, input_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
            job_id = int(cursor.lastrowid)
        job = self.get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        return job

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
            engine=row["engine"],
            model_reference=row["model_reference"],
            model_version_reference=row["model_version_reference"],
            model_dimensions=json.loads(row["model_dimensions_json"]),
            quality_reference=row["quality_reference"],
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
