from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

from app.database import connect_database
from app.modules.community.contracts import clean_library_file_name
from app.modules.community.project_assets import inspect_project_asset
from app.social_catalog import _validate_library_upload
from app.social_storage import SocialStorageRepository
from app.modules.community.storage_usage import personal_storage_quota, total_personal_storage_used


class ProjectAssetOwner(Protocol):
    database_path: Path

    def detail(self, slug: str, viewer_user_id: int | None = None) -> Any: ...
    def _owned_project(self, connection, actor_user_id: int, project_id: int): ...
    def _create_snapshot(self, connection, project_id: int, actor_user_id: int, label: str, changelog: str) -> None: ...


class ProjectAssetOperations:
    def __init__(self, owner: ProjectAssetOwner) -> None:
        self.owner = owner

    def upload(
        self,
        actor_user_id: int,
        project_id: int,
        file_name: str,
        file_role: str,
        body: bytes,
        idempotency_key: str | None,
    ) -> Any:
        if file_role == "external_reference":
            raise ValueError("use link externo para referência sem arquivo local")
        clean_name = clean_library_file_name(file_name)
        if len(body) > 25 * 1024 * 1024:
            raise ValueError("arquivo excede limite de 25 MB")
        file_kind = _file_kind(clean_name)
        checksum = hashlib.sha256(body).hexdigest()
        safe_key = _clean_idempotency_key(idempotency_key)
        validation_status = "quarantined"
        rejection_reason = None
        can_slice = file_role in {"primary", "printable", "optional_part"}
        try:
            _validate_library_upload(clean_name, "bundle" if file_kind == "zip" else file_kind, body)
        except ValueError as exc:
            validation_status = "rejected"
            rejection_reason = str(exc)
            can_slice = False
        storage = SocialStorageRepository(self.owner.database_path)
        with connect_database(self.owner.database_path) as connection:
            project = self.owner._owned_project(connection, actor_user_id, project_id)
            duplicate = connection.execute(
                """
                SELECT id FROM print_project_files
                WHERE project_id = ?
                  AND ((upload_idempotency_key IS NOT NULL AND upload_idempotency_key = ?)
                       OR (sha256 = ? AND file_name = ? AND file_role = ?))
                ORDER BY id LIMIT 1
                """,
                (project_id, safe_key, checksum, clean_name, file_role),
            ).fetchone()
            if duplicate is not None:
                detail = self.owner.detail(str(project["slug"]), actor_user_id)
                if detail is None:
                    raise ValueError("projeto não encontrado")
                return detail
            storage.ensure_upload_allowed(connection, actor_user_id, len(body))
            if total_personal_storage_used(connection, actor_user_id) + len(body) > personal_storage_quota(connection, actor_user_id):
                raise ValueError("cota de armazenamento insuficiente para este arquivo")
            stored = storage.storage.write_quarantine(checksum, Path(clean_name).suffix.lower(), body)
            display_order = int(connection.execute("SELECT COUNT(*) FROM print_project_files WHERE project_id = ?", (project_id,)).fetchone()[0])
            cursor = connection.execute(
                """
                INSERT INTO print_project_files (
                    project_id, file_kind, file_role, file_name, storage_path, size_bytes,
                    sha256, validation_status, can_slice, quarantine_key, uploaded_size_bytes,
                    uploaded_at, rejection_reason, is_primary_preview, inspection_status,
                    inspection_json, upload_idempotency_key, piece_name, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, file_kind, file_role, clean_name, stored.key, len(body), checksum,
                    validation_status, 1 if can_slice else 0, stored.key, len(body), rejection_reason,
                    1 if file_role in {"primary", "preview"} else 0,
                    "pending" if validation_status == "quarantined" else "failed", "{}", safe_key,
                    Path(clean_name).stem[:160], display_order,
                ),
            )
            file_id = int(cursor.lastrowid)
            storage.register_object(connection, stored, owner_user_id=actor_user_id, reference_type="print_project_file", reference_id=file_id, state=validation_status)
            if validation_status == "quarantined":
                inspection = inspect_project_asset(clean_name, body)
                promoted = storage.storage.promote(stored)
                storage.register_object(connection, promoted, owner_user_id=actor_user_id, reference_type="print_project_file", reference_id=file_id, state="promoted")
                connection.execute(
                    "UPDATE print_project_files SET storage_path = ?, validation_status = 'validated', inspection_status = ?, inspection_json = ? WHERE id = ?",
                    (promoted.key, inspection["status"], json.dumps(inspection, ensure_ascii=False, sort_keys=True), file_id),
                )
            if file_role == "primary" or project["primary_file_id"] is None:
                connection.execute("UPDATE print_projects SET primary_file_id = ? WHERE id = ?", (file_id, project_id))
            connection.execute("UPDATE print_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))
            self.owner._create_snapshot(connection, project_id, actor_user_id, "arquivo", f"Arquivo {clean_name} adicionado")
            slug = str(project["slug"])
        detail = self.owner.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail

    def update_structure(self, actor_user_id: int, project_id: int, file_id: int, payload: Any) -> Any:
        with connect_database(self.owner.database_path) as connection:
            project = self.owner._owned_project(connection, actor_user_id, project_id)
            updated = connection.execute(
                "UPDATE print_project_files SET piece_name = ?, variant_name = ?, assembly_name = ?, display_order = ?, unit = ? WHERE id = ? AND project_id = ?",
                (payload.piece_name.strip(), payload.variant_name.strip(), payload.assembly_name.strip(), payload.display_order, payload.unit, file_id, project_id),
            )
            if updated.rowcount != 1:
                raise ValueError("arquivo não encontrado")
            connection.execute("UPDATE print_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))
            self.owner._create_snapshot(connection, project_id, actor_user_id, "organização", "Estrutura das peças atualizada")
            slug = str(project["slug"])
        detail = self.owner.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail


def _file_kind(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix in {".stl", ".3mf", ".zip"}:
        return suffix.removeprefix(".")
    raise ValueError("projeto aceita STL, 3MF ou ZIP")


def _clean_idempotency_key(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    cleaned = value.strip()
    if len(cleaned) > 120 or any(character in cleaned for character in "\r\n\0"):
        raise ValueError("chave de repetição inválida")
    return cleaned
