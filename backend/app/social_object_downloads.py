from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel

from app.database import connect_database
from app.object_storage import ObjectReader, build_object_storage


TOKEN_TTL_SECONDS = 60


class ObjectDownloadToken(BaseModel):
    download_url: str
    authorization_token: str
    expires_at: str
    single_use: bool = True


@dataclass(frozen=True)
class DownloadGrant:
    object_id: int
    object_key: str
    file_name: str


class SocialObjectDownloadRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.storage = build_object_storage(database_path)

    def issue_social_file_token(self, file_id: int, actor_user_id: int, is_admin: bool) -> ObjectDownloadToken:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT lf.id, lf.file_name, lf.validation_status, li.owner_user_id,
                       li.visibility, li.status AS item_status, li.content_class,
                       li.commercial_status, object.id AS object_id
                FROM social_library_files lf
                JOIN social_library_items li ON li.id = lf.item_id
                JOIN cloud_object_references reference
                  ON reference.reference_type = 'social_library_file' AND reference.reference_id = lf.id
                JOIN cloud_objects object ON object.id = reference.object_id
                WHERE lf.id = ? AND object.state = 'promoted'
                """,
                (file_id,),
            ).fetchone()
            if row is None:
                raise ValueError("arquivo promovido não encontrado")
            owns = int(row["owner_user_id"]) == actor_user_id
            publicly_eligible = (
                row["visibility"] == "public"
                and row["item_status"] == "active"
                and (row["content_class"] in {"community", "curated"} or row["commercial_status"] == "approved")
            )
            if not (owns or is_admin or publicly_eligible):
                raise PermissionError("download não autorizado")
            return self._issue(connection, int(row["object_id"]), actor_user_id, "social_library_file", file_id)

    def issue_project_file_token(self, file_id: int, actor_user_id: int, is_admin: bool) -> ObjectDownloadToken:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT pf.id, pp.owner_user_id, pp.visibility, pp.lifecycle_status,
                       pp.publication_status, object.id AS object_id
                FROM print_project_files pf
                JOIN print_projects pp ON pp.id = pf.project_id
                JOIN cloud_object_references reference
                  ON reference.reference_type = 'print_project_file' AND reference.reference_id = pf.id
                JOIN cloud_objects object ON object.id = reference.object_id
                WHERE pf.id = ? AND object.state = 'promoted'
                """,
                (file_id,),
            ).fetchone()
            if row is None:
                raise ValueError("arquivo promovido não encontrado")
            owns = row["owner_user_id"] is not None and int(row["owner_user_id"]) == actor_user_id
            publicly_eligible = row["visibility"] == "public" and row["lifecycle_status"] == "active" and row["publication_status"] == "approved"
            if not (owns or is_admin or publicly_eligible):
                raise PermissionError("download não autorizado")
            return self._issue(connection, int(row["object_id"]), actor_user_id, "print_project_file", file_id)

    def consume(self, token: str) -> tuple[ObjectReader, str]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = _timestamp(datetime.now(timezone.utc))
        with connect_database(self.database_path) as connection:
            consumed = connection.execute(
                """
                UPDATE cloud_object_download_tokens
                SET status = 'used', used_at = CURRENT_TIMESTAMP
                WHERE token_sha256 = ? AND status = 'active' AND expires_at > ?
                RETURNING object_id, reference_type, reference_id
                """,
                (token_hash, now),
            ).fetchone()
            if consumed is None:
                raise PermissionError("token inválido, expirado ou já utilizado")
            object_row = connection.execute(
                """
                SELECT object_key, size_bytes, content_type, state
                FROM cloud_objects
                WHERE id = ?
                """,
                (consumed["object_id"],),
            ).fetchone()
            if object_row is None or object_row["state"] != "promoted":
                raise PermissionError("objeto não disponível")
            file_name = self._file_name(connection, str(consumed["reference_type"]), int(consumed["reference_id"]))
        reader = self.storage.open_promoted(str(object_row["object_key"]))
        if reader.size_bytes != int(object_row["size_bytes"]):
            reader.body.close()
            raise RuntimeError("tamanho do objeto divergiu do metadado")
        return reader, file_name

    def _issue(self, connection, object_id: int, actor_user_id: int, reference_type: str, reference_id: int) -> ObjectDownloadToken:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_TTL_SECONDS)
        expires_at = _timestamp(expires)
        connection.execute(
            """
            INSERT INTO cloud_object_download_tokens (
                token_sha256, object_id, issued_to_user_id, reference_type, reference_id, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (hashlib.sha256(token.encode()).hexdigest(), object_id, actor_user_id, reference_type, reference_id, expires_at),
        )
        return ObjectDownloadToken(download_url="/api/storage/download", authorization_token=token, expires_at=expires_at)

    @staticmethod
    def _file_name(connection, reference_type: str, reference_id: int) -> str:
        if reference_type == "social_library_file":
            row = connection.execute("SELECT file_name FROM social_library_files WHERE id = ?", (reference_id,)).fetchone()
        elif reference_type == "print_project_file":
            row = connection.execute("SELECT file_name FROM print_project_files WHERE id = ?", (reference_id,)).fetchone()
        else:
            raise PermissionError("referência de download inválida")
        if row is None:
            raise PermissionError("referência de download ausente")
        return str(row["file_name"]).replace('"', "").replace("\r", "").replace("\n", "")


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
