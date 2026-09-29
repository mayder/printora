from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.database import connect_database


class MeshPhysicalValidationCreate(BaseModel):
    outcome: Literal["passed", "needs_adjustment", "failed"]
    instrument_label: str = Field(min_length=2, max_length=120)
    measured_x_mm: float | None = Field(default=None, gt=0, le=2_000)
    measured_y_mm: float | None = Field(default=None, gt=0, le=2_000)
    measured_z_mm: float | None = Field(default=None, gt=0, le=2_000)
    note: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def require_measurement(self) -> "MeshPhysicalValidationCreate":
        if all(value is None for value in (self.measured_x_mm, self.measured_y_mm, self.measured_z_mm)):
            raise ValueError("Informe ao menos uma medida da peça impressa.")
        return self


class MeshPhysicalValidation(BaseModel):
    id: int
    review_id: int
    history_id: int
    outcome: Literal["passed", "needs_adjustment", "failed"]
    instrument_label: str
    expected_dimensions_mm: dict[str, float | None]
    measured_dimensions_mm: dict[str, float | None]
    error_percent: dict[str, float | None]
    max_error_percent: float
    printer_snapshot: dict[str, object]
    material_snapshot: dict[str, object]
    profile_snapshot: dict[str, object]
    revision_sha256: str
    note: str
    created_at: str


class MeshPhysicalValidationRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def get_for_history(self, owner_user_id: int, history_id: int) -> MeshPhysicalValidation | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM mesh_physical_validations WHERE history_id = ? AND owner_user_id = ?",
                (history_id, owner_user_id),
            ).fetchone()
        return _model(row) if row is not None else None

    def create(self, owner_user_id: int, history_id: int, payload: MeshPhysicalValidationCreate, idempotency_key: str) -> MeshPhysicalValidation:
        safe_key = _safe_key(idempotency_key)
        request_hash = hashlib.sha256(json.dumps(payload.model_dump(), sort_keys=True).encode()).hexdigest()
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM mesh_physical_validations WHERE owner_user_id = ? AND idempotency_key = ?",
                (owner_user_id, safe_key),
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise ValueError("chave de repetição já usada com outras medidas")
                return _model(existing)
            context = _eligible_context(connection, owner_user_id, history_id)
            expected = _expected_dimensions(context["qualification_json"])
            measured = {"x": payload.measured_x_mm, "y": payload.measured_y_mm, "z": payload.measured_z_mm}
            errors = {axis: _error(expected[axis], measured[axis]) for axis in ("x", "y", "z")}
            comparable_errors = [value for value in errors.values() if value is not None]
            if not comparable_errors:
                raise ValueError("As medidas informadas não correspondem às dimensões qualificadas.")
            max_error = max(comparable_errors)
            if payload.outcome == "passed" and max_error > 3:
                raise ValueError("A diferença passou de 3%. Marque que precisa ajuste e revise a escala.")
            input_payload = json.loads(context["input_json"] or "{}")
            cursor = connection.execute(
                """INSERT INTO mesh_physical_validations (
                    review_id, history_id, owner_user_id, outcome, instrument_label,
                    expected_x_mm, expected_y_mm, expected_z_mm, measured_x_mm, measured_y_mm,
                    measured_z_mm, error_x_percent, error_y_percent, error_z_percent,
                    max_error_percent, printer_snapshot_json, material_snapshot_json,
                    profile_snapshot_json, revision_sha256, note, idempotency_key, request_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    context["review_id"], history_id, owner_user_id, payload.outcome, payload.instrument_label.strip(),
                    expected["x"], expected["y"], expected["z"], measured["x"], measured["y"], measured["z"],
                    errors["x"], errors["y"], errors["z"], max_error,
                    json.dumps(input_payload.get("printer") or {}, sort_keys=True),
                    json.dumps(input_payload.get("material_spool") or input_payload.get("material_profile") or {}, sort_keys=True),
                    json.dumps(input_payload.get("slicing_profile_revision") or {"quality": context["quality_reference"]}, sort_keys=True),
                    context["revision_sha256"], payload.note.strip(), safe_key, request_hash,
                ),
            )
            row = connection.execute("SELECT * FROM mesh_physical_validations WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
        return _model(row)


def _eligible_context(connection, owner_user_id: int, history_id: int):
    context = connection.execute(
        """SELECT h.status, h.quality_reference, sj.selected_project_files_json, sj.input_json
           FROM print_job_history h JOIN slicing_jobs sj ON sj.id = h.slicing_job_id
           WHERE h.id = ? AND h.owner_user_id = ? AND sj.owner_user_id = ?""",
        (history_id, owner_user_id, owner_user_id),
    ).fetchone()
    if context is None or context["status"] not in {"completed", "failed"}:
        raise ValueError("Conclua a impressão antes de registrar as medidas.")
    selected = json.loads(context["selected_project_files_json"] or "[]")
    file_ids = [int(item["id"]) for item in selected if isinstance(item, dict) and item.get("id")]
    if not file_ids:
        raise ValueError("Este histórico não usa um modelo criado por fotos.")
    placeholders = ",".join("?" for _ in file_ids)
    review = connection.execute(
        f"""SELECT id AS review_id, qualification_json, revision_sha256
            FROM mesh_revision_reviews WHERE owner_user_id = ? AND decision = 'approved_for_slicing'
            AND project_file_id IN ({placeholders}) ORDER BY id DESC LIMIT 1""",
        (owner_user_id, *file_ids),
    ).fetchone()
    if review is None:
        raise ValueError("Este histórico não usa um modelo criado por fotos.")
    return {**dict(context), **dict(review)}


def _expected_dimensions(raw: str) -> dict[str, float | None]:
    qualification = json.loads(raw or "{}")
    dimensions = qualification.get("dimensions") or {}
    return {axis: float(dimensions[axis]) if dimensions.get(axis) else None for axis in ("x", "y", "z")}


def _error(expected: float | None, measured: float | None) -> float | None:
    if expected is None or measured is None:
        return None
    return round(abs(measured - expected) / expected * 100, 4)


def _safe_key(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 120 or any(character in cleaned for character in "\r\n\0"):
        raise ValueError("chave de repetição inválida")
    return cleaned


def _model(row) -> MeshPhysicalValidation:
    return MeshPhysicalValidation(
        id=int(row["id"]), review_id=int(row["review_id"]), history_id=int(row["history_id"]),
        outcome=row["outcome"], instrument_label=str(row["instrument_label"]),
        expected_dimensions_mm={axis: row[f"expected_{axis}_mm"] for axis in ("x", "y", "z")},
        measured_dimensions_mm={axis: row[f"measured_{axis}_mm"] for axis in ("x", "y", "z")},
        error_percent={axis: row[f"error_{axis}_percent"] for axis in ("x", "y", "z")},
        max_error_percent=float(row["max_error_percent"]), printer_snapshot=json.loads(row["printer_snapshot_json"]),
        material_snapshot=json.loads(row["material_snapshot_json"]), profile_snapshot=json.loads(row["profile_snapshot_json"]),
        revision_sha256=str(row["revision_sha256"]), note=str(row["note"]), created_at=str(row["created_at"]),
    )
