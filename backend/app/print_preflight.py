from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agent_pairing import AgentJobCreateRequest, AgentPairingRepository
from app.auth import format_dt, utc_now
from app.database import connect_database
from app.printers import PrinterRecord
from app.slicing_pipeline import SlicingJob

PreflightStatus = Literal["approved", "blocked", "pending_remote", "failed"]


class GcodeMetadata(BaseModel):
    line_count: int
    command_count: int
    max_x_mm: float | None = None
    max_y_mm: float | None = None
    max_z_mm: float | None = None
    max_nozzle_temperature_c: int | None = None
    max_bed_temperature_c: int | None = None
    filament_type: str | None = None
    nozzle_diameter_mm: float | None = None
    estimated_time_seconds: int | None = None
    filament_used_mm: float | None = None
    checksum_sha256: str | None = None


class PrintPreflightRecord(BaseModel):
    id: int
    owner_user_id: int | None
    printer_id: int
    slicing_job_id: int
    remote_agent_job_id: int | None
    status: PreflightStatus
    local_metadata: dict[str, Any]
    remote_preflight: dict[str, Any]
    blockers: list[str]
    warnings: list[str]
    checklist: list[str]
    created_at: str
    updated_at: str
    approved_at: str | None


class PrintPreflightRepository:
    def __init__(self, database_path: Path, data_dir: Path) -> None:
        self.database_path = database_path
        self.data_dir = data_dir

    def create_preflight(self, printer: PrinterRecord, actor_user_id: int | None, slicing_job_id: int) -> PrintPreflightRecord:
        job = self._slicing_job(slicing_job_id, actor_user_id)
        blockers, warnings = self._job_blockers(printer, job)
        metadata = self._metadata_for_job(job)
        local_blockers, local_warnings, checklist = self._local_checks(job, metadata)
        blockers.extend(local_blockers)
        warnings.extend(local_warnings)
        remote_job_id: int | None = None
        status: PreflightStatus = "blocked" if blockers else "pending_remote"
        if not blockers:
            remote_job_id, remote_warning = self._create_remote_preflight(printer, actor_user_id, job, metadata)
            if remote_warning:
                blockers.append(remote_warning)
                status = "blocked"
        return self._insert_record(
            actor_user_id=actor_user_id,
            printer_id=printer.id,
            slicing_job_id=job.id,
            remote_agent_job_id=remote_job_id,
            status=status,
            metadata=metadata.model_dump(),
            remote={},
            blockers=blockers,
            warnings=warnings,
            checklist=checklist,
        )

    def refresh_preflight(self, preflight_id: int, actor_user_id: int | None) -> PrintPreflightRecord:
        record = self.get_preflight(preflight_id, actor_user_id)
        if record is None:
            raise ValueError("preflight não encontrado")
        if record.remote_agent_job_id is None or record.status != "pending_remote":
            return record
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM agent_jobs WHERE id = ? AND printer_id = ?",
                (record.remote_agent_job_id, record.printer_id),
            ).fetchone()
        if row is None or row["status"] in {"pending", "in_progress"}:
            return record
        remote = json.loads(row["result_json"] or "{}")
        blockers = list(record.blockers)
        warnings = list(record.warnings)
        if row["status"] != "succeeded":
            blockers.append(str(row["error_message"] or "preflight remoto falhou"))
        if remote.get("can_execute") is not True:
            blockers.extend([str(item) for item in remote.get("blockers", []) if str(item)])
        if remote.get("printing") is True:
            blockers.append("Impressão em andamento bloqueia envio de G-code.")
        status: PreflightStatus = "approved" if not blockers else "blocked"
        return self._update_record(record.id, status, remote, blockers, warnings)

    def list_preflights(self, actor_user_id: int | None, slicing_job_id: int | None = None) -> list[PrintPreflightRecord]:
        params: list[Any] = []
        clauses: list[str] = []
        if actor_user_id is not None:
            clauses.append("owner_user_id = ?")
            params.append(actor_user_id)
        if slicing_job_id is not None:
            clauses.append("slicing_job_id = ?")
            params.append(slicing_job_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"SELECT * FROM print_preflight_checks {where} ORDER BY created_at DESC, id DESC LIMIT 30",
                params,
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def get_preflight(self, preflight_id: int, actor_user_id: int | None) -> PrintPreflightRecord | None:
        params: list[Any] = [preflight_id]
        owner_sql = ""
        if actor_user_id is not None:
            owner_sql = "AND owner_user_id = ?"
            params.append(actor_user_id)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                f"SELECT * FROM print_preflight_checks WHERE id = ? {owner_sql}",
                params,
            ).fetchone()
        return self._record_from_row(row) if row else None

    def _slicing_job(self, job_id: int, actor_user_id: int | None) -> SlicingJob:
        from app.config import Settings
        from app.slicing_pipeline import SlicingPipelineRepository

        settings = Settings(data_dir=self.data_dir)
        job = SlicingPipelineRepository(self.database_path, settings).get_job(job_id, actor_user_id)
        if job is None:
            raise ValueError("job de fatiamento não encontrado")
        return job

    def _job_blockers(self, printer: PrinterRecord, job: SlicingJob) -> tuple[list[str], list[str]]:
        blockers: list[str] = []
        warnings: list[str] = []
        if job.status != "completed":
            blockers.append("Job de fatiamento precisa estar concluído antes do preflight.")
        if job.printer_id != printer.id:
            blockers.append("G-code pertence a outra impressora.")
        if not any(artifact.artifact_kind == "gcode" for artifact in job.artifacts):
            blockers.append("Job não possui artefato G-code rastreado.")
        if not job.model_version_reference:
            warnings.append("Versão do modelo não informada no job de fatiamento.")
        return blockers, warnings

    def _metadata_for_job(self, job: SlicingJob) -> GcodeMetadata:
        artifact = next((item for item in job.artifacts if item.artifact_kind == "gcode"), None)
        content = ""
        if artifact is not None:
            content = _read_artifact_text(self.data_dir, artifact.storage_key)
        metadata = parse_gcode_metadata(content)
        metadata.checksum_sha256 = artifact.checksum_sha256 if artifact else None
        return metadata

    def _local_checks(self, job: SlicingJob, metadata: GcodeMetadata) -> tuple[list[str], list[str], list[str]]:
        blockers: list[str] = []
        warnings: list[str] = []
        checklist = ["Conferir impressora selecionada.", "Conferir material carregado.", "Conferir mesa livre antes do envio."]
        volume = job.compatibility.get("build_volume") if isinstance(job.compatibility.get("build_volume"), dict) else {}
        for axis, value in (("X", metadata.max_x_mm), ("Y", metadata.max_y_mm), ("Z", metadata.max_z_mm)):
            max_value = _float_or_none(volume.get(axis.lower())) if volume else None
            if value is not None and max_value is not None and value > max_value:
                blockers.append(f"G-code excede volume útil no eixo {axis}.")
        material = job.input.get("material_profile", {}) if isinstance(job.input.get("material_profile"), dict) else {}
        nozzle_temp = _float_or_none(material.get("nozzle_temperature_c"))
        bed_temp = _float_or_none(material.get("bed_temperature_c"))
        if metadata.max_nozzle_temperature_c and metadata.max_nozzle_temperature_c > 320:
            blockers.append("Temperatura de nozzle acima do limite seguro do Printora.")
        if metadata.max_bed_temperature_c and metadata.max_bed_temperature_c > 140:
            blockers.append("Temperatura de mesa acima do limite seguro do Printora.")
        if nozzle_temp and metadata.max_nozzle_temperature_c and metadata.max_nozzle_temperature_c > nozzle_temp + 15:
            warnings.append("Temperatura de nozzle diverge do perfil de material.")
        if bed_temp and metadata.max_bed_temperature_c and metadata.max_bed_temperature_c > bed_temp + 15:
            warnings.append("Temperatura de mesa diverge do perfil de material.")
        if metadata.command_count == 0:
            blockers.append("Arquivo G-code sem comandos imprimíveis.")
        return blockers, warnings, checklist

    def _create_remote_preflight(self, printer: PrinterRecord, actor_user_id: int | None, job: SlicingJob, metadata: GcodeMetadata) -> tuple[int | None, str | None]:
        pairing = AgentPairingRepository(self.database_path)
        agent = pairing.latest_active_agent(printer.id)
        if agent is None:
            return None, "Preflight remoto exige agente ativo e online para a impressora."
        expires_at = format_dt(utc_now() + timedelta(minutes=10))
        remote_job = pairing.create_job(
            printer,
            AgentJobCreateRequest(
                agent_id=agent.id,
                job_type="remote_gcode_preflight",
                correlation_id=f"print_preflight_{uuid4().hex}",
                payload={
                    "safe_mode": "print_preflight_only",
                    "slicing_job_id": job.id,
                    "model_reference": job.model_reference,
                    "model_version_reference": job.model_version_reference,
                    "metadata": metadata.model_dump(),
                    "requested_by_user_id": actor_user_id,
                },
                expires_at=expires_at,
            ),
        )
        return remote_job.id, None

    def _insert_record(self, *, actor_user_id: int | None, printer_id: int, slicing_job_id: int, remote_agent_job_id: int | None, status: PreflightStatus, metadata: dict[str, Any], remote: dict[str, Any], blockers: list[str], warnings: list[str], checklist: list[str]) -> PrintPreflightRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO print_preflight_checks (
                    owner_user_id, printer_id, slicing_job_id, remote_agent_job_id, status,
                    local_metadata_json, remote_preflight_json, blockers_json, warnings_json, checklist_json, approved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? = 'approved' THEN CURRENT_TIMESTAMP ELSE NULL END)
                """,
                (actor_user_id, printer_id, slicing_job_id, remote_agent_job_id, status, json.dumps(metadata), json.dumps(remote), json.dumps(blockers), json.dumps(warnings), json.dumps(checklist), status),
            )
            row = connection.execute("SELECT * FROM print_preflight_checks WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
        return self._record_from_row(row)

    def _update_record(self, preflight_id: int, status: PreflightStatus, remote: dict[str, Any], blockers: list[str], warnings: list[str]) -> PrintPreflightRecord:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE print_preflight_checks
                SET status = ?, remote_preflight_json = ?, blockers_json = ?, warnings_json = ?,
                    approved_at = CASE WHEN ? = 'approved' THEN CURRENT_TIMESTAMP ELSE approved_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, json.dumps(remote), json.dumps(blockers), json.dumps(warnings), status, preflight_id),
            )
            row = connection.execute("SELECT * FROM print_preflight_checks WHERE id = ?", (preflight_id,)).fetchone()
        return self._record_from_row(row)

    def _record_from_row(self, row) -> PrintPreflightRecord:
        return PrintPreflightRecord(
            id=int(row["id"]),
            owner_user_id=row["owner_user_id"],
            printer_id=int(row["printer_id"]),
            slicing_job_id=int(row["slicing_job_id"]),
            remote_agent_job_id=row["remote_agent_job_id"],
            status=row["status"],
            local_metadata=json.loads(row["local_metadata_json"]),
            remote_preflight=json.loads(row["remote_preflight_json"]),
            blockers=json.loads(row["blockers_json"]),
            warnings=json.loads(row["warnings_json"]),
            checklist=json.loads(row["checklist_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            approved_at=row["approved_at"],
        )


def parse_gcode_metadata(content: str) -> GcodeMetadata:
    lines = content.splitlines()
    metadata = GcodeMetadata(line_count=len(lines), command_count=0)
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        _parse_comment(metadata, line)
        command = line.split(";", 1)[0].strip().upper()
        if not command:
            continue
        metadata.command_count += 1
        _parse_motion(metadata, command)
        _parse_temperature(metadata, command)
    return metadata


def _parse_motion(metadata: GcodeMetadata, command: str) -> None:
    if not command.startswith(("G0", "G1")):
        return
    values = dict((axis, _float_or_none(value)) for axis, value in re.findall(r"\b([XYZ])(-?\d+(?:[.]\d+)?)", command))
    if values.get("X") is not None:
        metadata.max_x_mm = max(metadata.max_x_mm or values["X"], values["X"])
    if values.get("Y") is not None:
        metadata.max_y_mm = max(metadata.max_y_mm or values["Y"], values["Y"])
    if values.get("Z") is not None:
        metadata.max_z_mm = max(metadata.max_z_mm or values["Z"], values["Z"])


def _parse_temperature(metadata: GcodeMetadata, command: str) -> None:
    match = re.search(r"\bS(-?\d+(?:[.]\d+)?)", command)
    if not match:
        return
    value = int(float(match.group(1)))
    if command.startswith(("M104", "M109")):
        metadata.max_nozzle_temperature_c = max(metadata.max_nozzle_temperature_c or value, value)
    if command.startswith(("M140", "M190")):
        metadata.max_bed_temperature_c = max(metadata.max_bed_temperature_c or value, value)


def _parse_comment(metadata: GcodeMetadata, line: str) -> None:
    lower = line.lower()
    if "filament_type" in lower or "filament type" in lower:
        metadata.filament_type = line.split("=", 1)[-1].strip(" ;")[:40]
    if "nozzle_diameter" in lower or "nozzle diameter" in lower:
        metadata.nozzle_diameter_mm = _float_or_none(line.split("=", 1)[-1])
    if "filament used" in lower or "filament_used" in lower:
        metadata.filament_used_mm = _float_or_none(line)
    if "estimated printing time" in lower or "estimated_time" in lower:
        metadata.estimated_time_seconds = _time_to_seconds(line)


def _read_artifact_text(data_dir: Path, storage_key: str) -> str:
    path = (data_dir / storage_key).resolve()
    data_root = data_dir.resolve()
    if data_root not in path.parents and path != data_root:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:[.]\d+)?", str(value))
    if not match:
        return None
    return float(match.group(0))


def _time_to_seconds(value: str) -> int | None:
    numbers = [int(item) for item in re.findall(r"\d+", value)]
    if not numbers:
        return None
    if len(numbers) >= 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    return numbers[0]
