from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.database import connect_database
from app.modules.operations.mesh_qualification.review_contracts import MeshReviewCreate, MeshRevisionReview
from app.print_projects import PrintProjectsRepository


MAX_DIMENSION_DEVIATION_PERCENT = 3.0


class MeshReviewRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.projects = PrintProjectsRepository(database_path)

    def create(
        self,
        owner_user_id: int,
        job_id: int,
        revision_id: int,
        payload: MeshReviewCreate,
        idempotency_key: str,
    ) -> MeshRevisionReview:
        safe_key = _idempotency_key(idempotency_key)
        request_hash = _request_hash(job_id, revision_id, payload)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM mesh_revision_reviews WHERE owner_user_id = ? AND idempotency_key = ?",
                (owner_user_id, safe_key),
            ).fetchone()
            if existing is not None:
                if str(existing["request_hash"]) != request_hash:
                    raise ValueError("chave de repetição já usada em outra revisão")
                return _model(existing)
            revision = self._revision(connection, owner_user_id, job_id, revision_id)
            if payload.decision == "reject":
                review_id = self._insert_rejection(connection, revision, payload, safe_key, request_hash)
            else:
                prior = connection.execute(
                    "SELECT * FROM mesh_revision_reviews WHERE revision_id = ? AND decision = 'approved_for_slicing'",
                    (revision_id,),
                ).fetchone()
                if prior is not None:
                    return _model(prior)
                review_id = self._approve(connection, revision, payload, safe_key, request_hash)
            row = connection.execute("SELECT * FROM mesh_revision_reviews WHERE id = ?", (review_id,)).fetchone()
        if row is None:
            raise RuntimeError("a revisão humana não foi persistida")
        return _model(row)

    def list(self, owner_user_id: int, job_id: int) -> list[MeshRevisionReview]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM mesh_revision_reviews WHERE owner_user_id = ? AND reconstruction_job_id = ? ORDER BY created_at, id",
                (owner_user_id, job_id),
            ).fetchall()
        return [_model(row) for row in rows]

    def _approve(self, connection, revision, payload: MeshReviewCreate, safe_key: str, request_hash: str) -> int:
        if payload.intended_use == "mechanical":
            raise ValueError("Uso mecânico exige CAD, dimensões críticas e validação física específica.")
        qualification = json.loads(revision["qualification_json"] or "{}")
        _validate_topology(qualification)
        if str(revision["unit"]).lower() not in {"mm", "millimeter", "millimetre"}:
            raise ValueError("Confirme a escala em milímetros antes de continuar.")
        if revision["output_format"] not in {"stl", "3mf"}:
            raise ValueError("Crie primeiro uma versão final STL ou 3MF.")
        dimensions = qualification.get("dimensions") or {}
        model_dimension = float(dimensions.get(payload.known_axis or "", 0))
        known_dimension = float(payload.known_dimension_mm or 0)
        deviation = abs(model_dimension - known_dimension) / known_dimension * 100 if known_dimension else 100.0
        if model_dimension <= 0 or deviation > MAX_DIMENSION_DEVIATION_PERCENT:
            raise ValueError(
                f"A medida do modelo difere {deviation:.1f}% do objeto. Ajuste a escala e confira novamente."
            )
        project = connection.execute(
            "SELECT p.* FROM print_projects p JOIN photo_reconstruction_jobs job ON job.project_id = p.id WHERE job.id = ? AND job.owner_user_id = ? AND p.owner_user_id = ?",
            (int(revision["reconstruction_job_id"]), int(revision["owner_user_id"]), int(revision["owner_user_id"])),
        ).fetchone()
        if project is None:
            raise PermissionError("projeto privado não encontrado")
        chain = _revision_chain(connection, revision)
        manifest = _review_manifest(revision, payload, qualification, model_dimension, deviation, chain, int(project["id"]))
        file_id = self._create_project_file(connection, project, revision, qualification)
        cursor = connection.execute(
            """
            INSERT INTO mesh_revision_reviews (
                revision_id, reconstruction_job_id, owner_user_id, decision, intended_use,
                known_axis, known_dimension_mm, model_dimension_mm, deviation_percent,
                revision_sha256, review_manifest_json, qualification_json, project_file_id,
                idempotency_key, request_hash, note
            ) VALUES (?, ?, ?, 'approved_for_slicing', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(revision["id"]), int(revision["reconstruction_job_id"]), int(revision["owner_user_id"]),
                payload.intended_use, payload.known_axis, known_dimension, model_dimension, round(deviation, 4),
                str(revision["sha256"]), json.dumps(manifest, ensure_ascii=False, sort_keys=True),
                json.dumps(qualification, ensure_ascii=False, sort_keys=True), file_id, safe_key, request_hash,
                payload.note.strip(),
            ),
        )
        review_id = int(cursor.lastrowid)
        _copy_object_reference(connection, int(revision["id"]), file_id)
        self.projects._create_snapshot(
            connection, int(project["id"]), int(revision["owner_user_id"]),
            "modelo revisado", "Modelo 3D aprovado para seguir ao fatiamento",
        )
        return review_id

    @staticmethod
    def _create_project_file(connection, project, revision, qualification: dict[str, object]) -> int:
        role = "primary" if project["primary_file_id"] is None else "printable"
        file_name = f"modelo-revisado-{int(revision['id'])}.{revision['output_format']}"
        inspection = _project_inspection(qualification)
        cursor = connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, storage_path, size_bytes,
                sha256, validation_status, can_slice, uploaded_size_bytes, uploaded_at,
                piece_name, display_order, unit, inspection_status, inspection_json,
                upload_idempotency_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'validated', 1, ?, CURRENT_TIMESTAMP, ?, ?, 'mm', 'limited', ?, ?)
            """,
            (
                int(project["id"]), str(revision["output_format"]), role, file_name,
                str(revision["storage_key"]), int(revision["size_bytes"]), str(revision["sha256"]),
                int(revision["size_bytes"]), "Modelo revisado", _next_display_order(connection, int(project["id"])),
                json.dumps(inspection, ensure_ascii=False, sort_keys=True), f"mesh-review-{int(revision['id'])}",
            ),
        )
        file_id = int(cursor.lastrowid)
        if project["primary_file_id"] is None:
            connection.execute("UPDATE print_projects SET primary_file_id = ? WHERE id = ?", (file_id, int(project["id"])))
        connection.execute("UPDATE print_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (int(project["id"]),))
        return file_id

    @staticmethod
    def _insert_rejection(connection, revision, payload: MeshReviewCreate, safe_key: str, request_hash: str) -> int:
        cursor = connection.execute(
            """
            INSERT INTO mesh_revision_reviews (
                revision_id, reconstruction_job_id, owner_user_id, decision, intended_use,
                revision_sha256, review_manifest_json, qualification_json,
                idempotency_key, request_hash, note
            ) VALUES (?, ?, ?, 'rejected', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(revision["id"]), int(revision["reconstruction_job_id"]), int(revision["owner_user_id"]),
                payload.intended_use, str(revision["sha256"]),
                json.dumps({"schema": "printora.mesh-review/v1", "shape_reviewed": payload.shape_reviewed}, sort_keys=True),
                str(revision["qualification_json"]), safe_key, request_hash, payload.note.strip(),
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _revision(connection, owner_user_id: int, job_id: int, revision_id: int):
        row = connection.execute(
            "SELECT * FROM mesh_revisions WHERE id = ? AND reconstruction_job_id = ? AND owner_user_id = ? AND status = 'succeeded'",
            (revision_id, job_id, owner_user_id),
        ).fetchone()
        if row is None:
            raise PermissionError("versão revisada pronta não encontrada")
        return row


def _validate_topology(qualification: dict[str, object]) -> None:
    checks = qualification.get("checks") or {}
    if not isinstance(checks, dict):
        raise ValueError("A conferência geométrica está incompleta.")
    required = {
        "watertight": True,
        "non_manifold_edge_count": 0,
        "winding_conflict_count": 0,
        "degenerate_triangle_count": 0,
        "component_count": 1,
        "self_intersection_count": 0,
    }
    if any(checks.get(key) != expected for key, expected in required.items()):
        raise ValueError("A malha ainda possui bloqueios geométricos e não pode seguir ao fatiamento.")


def _revision_chain(connection, revision) -> list[dict[str, object]]:
    chain: list[dict[str, object]] = []
    current = revision
    for _ in range(64):
        chain.append({"id": int(current["id"]), "operation": str(current["operation"]), "sha256": current["sha256"]})
        parent_id = current["parent_revision_id"]
        if parent_id is None:
            break
        current = connection.execute("SELECT * FROM mesh_revisions WHERE id = ?", (int(parent_id),)).fetchone()
        if current is None:
            raise ValueError("O histórico da versão está incompleto.")
    else:
        raise ValueError("O histórico da versão excede o limite seguro.")
    return list(reversed(chain))


def _review_manifest(revision, payload, qualification, model_dimension, deviation, chain, project_id) -> dict[str, object]:
    return {
        "schema": "printora.mesh-review/v1",
        "decision": "approved_for_slicing",
        "scope": "slicing_only",
        "project_id": project_id,
        "revision_id": int(revision["id"]),
        "revision_sha256": str(revision["sha256"]),
        "intended_use": payload.intended_use,
        "shape_reviewed": payload.shape_reviewed,
        "limitations_accepted": payload.limitations_accepted,
        "known_measurement": {"axis": payload.known_axis, "physical_mm": payload.known_dimension_mm, "model_mm": model_dimension, "deviation_percent": round(deviation, 4)},
        "qualification_sha256": hashlib.sha256(json.dumps(qualification, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "revision_chain": chain,
    }


def _copy_object_reference(connection, revision_id: int, file_id: int) -> None:
    row = connection.execute(
        "SELECT object_id FROM cloud_object_references WHERE reference_type = 'mesh_revision' AND reference_id = ?",
        (revision_id,),
    ).fetchone()
    if row is None:
        raise ValueError("O objeto da versão não está reconciliado.")
    connection.execute(
        "INSERT INTO cloud_object_references (object_id, reference_type, reference_id) VALUES (?, 'print_project_file', ?) ON CONFLICT(reference_type, reference_id) DO UPDATE SET object_id = excluded.object_id",
        (int(row["object_id"]), file_id),
    )


def _next_display_order(connection, project_id: int) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM print_project_files WHERE project_id = ?", (project_id,)).fetchone()[0])


def _project_inspection(qualification: dict[str, object]) -> dict[str, object]:
    """Translate mesh qualification facts to the stable project-file inspection contract."""
    dimensions = qualification.get("dimensions")
    checks = qualification.get("checks")
    blockers = qualification.get("blockers")
    preview = qualification.get("preview_triangles")
    safe_dimensions = dimensions if isinstance(dimensions, dict) else {}
    safe_checks = checks if isinstance(checks, dict) else {}
    safe_blockers = blockers if isinstance(blockers, list) else []
    safe_preview = preview if isinstance(preview, list) else []
    component_count = int(safe_checks.get("component_count", 0) or 0)
    return {
        "status": "limited" if safe_blockers else "ready",
        "format": "mesh",
        "source_unit": str(qualification.get("source_unit") or "mm"),
        "display_unit": "mm",
        "triangle_count": int(qualification.get("triangle_count", 0) or 0),
        "vertex_count": int(qualification.get("vertex_count", 0) or 0),
        "dimensions_mm": {
            axis: float(safe_dimensions.get(axis, 0) or 0)
            for axis in ("x", "y", "z")
        },
        "shell_count": component_count,
        "possible_islands": max(component_count - 1, 0),
        "degenerate_triangles": int(safe_checks.get("degenerate_triangle_count", 0) or 0),
        "preview_supported": bool(safe_preview),
        "preview_triangles": safe_preview,
        "warnings": [str(item) for item in safe_blockers],
    }


def _request_hash(job_id: int, revision_id: int, payload: MeshReviewCreate) -> str:
    value = json.dumps({"job_id": job_id, "revision_id": revision_id, **payload.model_dump()}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


def _idempotency_key(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 120 or any(character in cleaned for character in "\r\n\0"):
        raise ValueError("chave de repetição inválida")
    return cleaned


def _model(row) -> MeshRevisionReview:
    return MeshRevisionReview(
        id=int(row["id"]), revision_id=int(row["revision_id"]),
        reconstruction_job_id=int(row["reconstruction_job_id"]), decision=str(row["decision"]),
        intended_use=str(row["intended_use"]), known_axis=row["known_axis"],
        known_dimension_mm=row["known_dimension_mm"], model_dimension_mm=row["model_dimension_mm"],
        deviation_percent=row["deviation_percent"], revision_sha256=str(row["revision_sha256"]),
        review_manifest=json.loads(row["review_manifest_json"] or "{}"),
        qualification=json.loads(row["qualification_json"] or "{}"),
        project_file_id=row["project_file_id"], note=str(row["note"]), created_at=str(row["created_at"]),
    )
