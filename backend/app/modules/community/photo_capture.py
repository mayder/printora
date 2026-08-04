from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.database import connect_database
from app.modules.community.photo_capture_contracts import (
    HeightBand,
    PhotoCaptureCreate,
    PhotoCapturePhoto,
    PhotoCaptureScaleUpdate,
    PhotoCaptureSession,
)
from app.modules.community.photo_image import inspect_photo_quality, sanitize_photo
from app.modules.community.storage_usage import personal_storage_quota, total_personal_storage_used
from app.social_storage import SocialStorageRepository


class PhotoCaptureRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.storage = SocialStorageRepository(database_path)

    def create(self, owner_user_id: int, payload: PhotoCaptureCreate) -> PhotoCaptureSession:
        if not payload.consent_confirmed:
            raise ValueError("confirme que você pode fotografar este objeto")
        with connect_database(self.database_path) as connection:
            project = connection.execute(
                "SELECT id FROM print_projects WHERE id = ? AND owner_user_id = ? AND lifecycle_status != 'archived'",
                (payload.project_id, owner_user_id),
            ).fetchone()
            if project is None:
                raise PermissionError("projeto não encontrado")
            existing = connection.execute(
                "SELECT id FROM photo_capture_sessions WHERE project_id = ? AND owner_user_id = ? AND status IN ('draft', 'review') ORDER BY id DESC LIMIT 1",
                (payload.project_id, owner_user_id),
            ).fetchone()
            if existing is not None:
                return self.get(owner_user_id, int(existing["id"]))
            cursor = connection.execute(
                "INSERT INTO photo_capture_sessions (project_id, owner_user_id, target_photo_count, consent_confirmed_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (payload.project_id, owner_user_id, payload.target_photo_count),
            )
            session_id = int(cursor.lastrowid)
        return self.get(owner_user_id, session_id)

    def list_for_owner(self, owner_user_id: int) -> list[PhotoCaptureSession]:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE photo_capture_sessions SET status = 'expired', updated_at = CURRENT_TIMESTAMP WHERE owner_user_id = ? AND status IN ('draft', 'review') AND expires_at <= CURRENT_TIMESTAMP",
                (owner_user_id,),
            )
            rows = connection.execute(
                "SELECT id FROM photo_capture_sessions WHERE owner_user_id = ? ORDER BY updated_at DESC, id DESC",
                (owner_user_id,),
            ).fetchall()
        return [self.get(owner_user_id, int(row["id"])) for row in rows]

    def get(self, owner_user_id: int, session_id: int) -> PhotoCaptureSession:
        with connect_database(self.database_path) as connection:
            session = self._owned_session(connection, owner_user_id, session_id)
            photos = connection.execute(
                "SELECT * FROM photo_capture_photos WHERE session_id = ? AND is_current = 1 ORDER BY capture_index, id",
                (session_id,),
            ).fetchall()
        return _session_model(session, photos)

    def upload(
        self,
        owner_user_id: int,
        session_id: int,
        file_name: str,
        capture_index: int,
        height_band: HeightBand,
        body: bytes,
        idempotency_key: str | None,
    ) -> PhotoCaptureSession:
        if not 1 <= capture_index <= 80:
            raise ValueError("posição da foto inválida")
        if not body or len(body) > 15 * 1024 * 1024:
            raise ValueError("cada foto deve ter até 15 MB")
        clean_name = Path(file_name).name[:180]
        cleaned, content_type, width, height = sanitize_photo(clean_name, body)
        checksum = hashlib.sha256(cleaned).hexdigest()
        issues, quality = inspect_photo_quality(cleaned, width, height)
        safe_key = _idempotency_key(idempotency_key)
        with connect_database(self.database_path) as connection:
            session = self._owned_session(connection, owner_user_id, session_id)
            if session["status"] not in {"draft", "review"}:
                raise ValueError("esta captura não aceita novas fotos")
            if capture_index > int(session["target_photo_count"]):
                raise ValueError("esta captura aceita somente as posições solicitadas")
            replay = connection.execute(
                "SELECT id FROM photo_capture_photos WHERE session_id = ? AND upload_idempotency_key IS NOT NULL AND upload_idempotency_key = ? LIMIT 1",
                (session_id, safe_key),
            ).fetchone() if safe_key is not None else None
            if replay is None:
                duplicate = connection.execute(
                    "SELECT id FROM photo_capture_photos WHERE session_id = ? AND sha256 = ? LIMIT 1",
                    (session_id, checksum),
                ).fetchone()
                if duplicate is not None:
                    raise ValueError("esta foto já foi enviada; fotografe o próximo ângulo")
                if total_personal_storage_used(connection, owner_user_id) + len(cleaned) > personal_storage_quota(connection, owner_user_id):
                    raise ValueError("cota de armazenamento insuficiente para estas fotos")
                stored = self.storage.storage.write_quarantine(checksum, Path(clean_name).suffix.lower(), cleaned)
                promoted = self.storage.storage.promote(stored)
                connection.execute(
                    "UPDATE photo_capture_photos SET is_current = 0, replaced_at = CURRENT_TIMESTAMP WHERE session_id = ? AND capture_index = ? AND is_current = 1",
                    (session_id, capture_index),
                )
                cursor = connection.execute(
                    """
                    INSERT INTO photo_capture_photos (
                        session_id, owner_user_id, capture_index, height_band, file_name,
                        storage_key, sha256, size_bytes, width, height, quality_status,
                        quality_json, upload_idempotency_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id, owner_user_id, capture_index, height_band, clean_name,
                        promoted.key, checksum, len(cleaned), width, height,
                        "needs_review" if issues else "accepted",
                        json.dumps({"issues": issues, **quality}, ensure_ascii=False), safe_key,
                    ),
                )
                self.storage.register_object(
                    connection, promoted, owner_user_id=owner_user_id,
                    reference_type="photo_capture_photo", reference_id=int(cursor.lastrowid), state="promoted",
                )
                connection.execute(
                    "UPDATE photo_capture_sessions SET status = 'review', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (session_id,),
                )
        return self.get(owner_user_id, session_id)

    def update_scale(self, owner_user_id: int, session_id: int, payload: PhotoCaptureScaleUpdate) -> PhotoCaptureSession:
        with connect_database(self.database_path) as connection:
            session = self._owned_session(connection, owner_user_id, session_id)
            if session["status"] not in {"draft", "review"}:
                raise ValueError("a escala desta captura não pode mais ser alterada")
            connection.execute(
                "UPDATE photo_capture_sessions SET scale_method = ?, scale_value_mm = ?, scale_uncertainty_mm = ?, scale_confirmed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (payload.method, payload.value_mm, payload.uncertainty_mm, session_id),
            )
        return self.get(owner_user_id, session_id)

    def complete(self, owner_user_id: int, session_id: int) -> PhotoCaptureSession:
        current = self.get(owner_user_id, session_id)
        if not current.can_complete:
            raise ValueError("revise as fotos indicadas antes de concluir")
        with connect_database(self.database_path) as connection:
            self._owned_session(connection, owner_user_id, session_id)
            connection.execute(
                "UPDATE photo_capture_sessions SET status = 'ready', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )
        return self.get(owner_user_id, session_id)

    def cancel(self, owner_user_id: int, session_id: int) -> PhotoCaptureSession:
        with connect_database(self.database_path) as connection:
            self._owned_session(connection, owner_user_id, session_id)
            connection.execute(
                "UPDATE photo_capture_sessions SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status != 'ready'",
                (session_id,),
            )
        return self.get(owner_user_id, session_id)

    @staticmethod
    def _owned_session(connection, owner_user_id: int, session_id: int):
        connection.execute(
            "UPDATE photo_capture_sessions SET status = 'expired', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND owner_user_id = ? AND status IN ('draft', 'review') AND expires_at <= CURRENT_TIMESTAMP",
            (session_id, owner_user_id),
        )
        row = connection.execute(
            "SELECT * FROM photo_capture_sessions WHERE id = ? AND owner_user_id = ?",
            (session_id, owner_user_id),
        ).fetchone()
        if row is None:
            raise PermissionError("captura não encontrada")
        return row


def _session_model(session, rows) -> PhotoCaptureSession:
    photos = [
        PhotoCapturePhoto(
            id=int(row["id"]), capture_index=int(row["capture_index"]), height_band=row["height_band"],
            file_name=row["file_name"], sha256=row["sha256"], size_bytes=int(row["size_bytes"]),
            width=int(row["width"]), height=int(row["height"]), quality_status=row["quality_status"],
            issues=json.loads(row["quality_json"] or "{}").get("issues", []),
        )
        for row in rows
    ]
    accepted = [photo for photo in photos if photo.quality_status == "accepted"]
    target = int(session["target_photo_count"])
    accepted_by_band = {
        band: sum(photo.height_band == band for photo in accepted)
        for band in ("low", "middle", "high")
    }
    base, remainder = divmod(target, 3)
    required_by_band = {
        "low": base,
        "middle": base + (1 if remainder >= 1 else 0),
        "high": base + (1 if remainder >= 2 else 0),
    }
    covered_photo_count = sum(
        min(accepted_by_band[band], required_by_band[band])
        for band in ("low", "middle", "high")
    )
    missing = [
        band for band in ("low", "middle", "high")
        if accepted_by_band[band] < required_by_band[band]
    ]
    actions: list[str] = []
    labels = {"low": "De baixo", "middle": "Na altura do objeto", "high": "De cima"}
    for band in ("middle", "high", "low"):
        remaining = required_by_band[band] - accepted_by_band[band]
        if remaining > 0:
            actions.append(f"{labels[band]}: faça mais {remaining} foto(s) durante a volta.")
    if any(photo.quality_status == "needs_review" for photo in photos):
        actions.append("Refaça as fotos marcadas para revisão.")
    scale_confirmed = session["scale_confirmed_at"] is not None
    if not scale_confirmed:
        actions.append("Informe uma medida ou confirme que o tamanho real será definido depois.")
    return PhotoCaptureSession(
        id=int(session["id"]), project_id=int(session["project_id"]), status=session["status"],
        target_photo_count=target, scale_method=session["scale_method"], scale_value_mm=session["scale_value_mm"],
        scale_uncertainty_mm=session["scale_uncertainty_mm"], scale_confirmed=scale_confirmed,
        consent_confirmed=session["consent_confirmed_at"] is not None,
        expires_at=str(session["expires_at"]), created_at=str(session["created_at"]), updated_at=str(session["updated_at"]),
        photos=photos, accepted_photo_count=len(accepted), covered_photo_count=covered_photo_count,
        accepted_by_height_band=accepted_by_band,
        required_by_height_band=required_by_band, missing_height_bands=missing,
        next_actions=actions, can_complete=(
            len(accepted) >= target and not missing and len(accepted) == len(photos) and scale_confirmed
        ),
    )


def _idempotency_key(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    cleaned = value.strip()
    if len(cleaned) > 120 or any(character in cleaned for character in "\r\n\0"):
        raise ValueError("chave de repetição inválida")
    return cleaned
