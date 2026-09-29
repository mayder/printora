from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database
from app.modules.community.contracts import (
    LibraryLicense,
    clean_discussion_text,
    clean_optional_text,
    validate_public_url,
)

ExternalSourceStatus = Literal["active", "paused", "blocked"]
ExternalImportMode = Literal["bookmark", "metadata_only"]


class ExternalSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=8, max_length=500)
    license_policy: str = Field(default="", max_length=500)
    attribution_required: bool = True

    @field_validator("base_url")
    @classmethod
    def clean_base_url(cls, value: str) -> str:
        return validate_public_url(value, field_name="base_url", allowed_hosts=None) or value


class ExternalSourceRecord(BaseModel):
    id: int
    name: str
    base_url: str
    license_policy: str
    attribution_required: bool
    status: ExternalSourceStatus
    created_at: str
    updated_at: str


class ExternalReferenceCreate(BaseModel):
    source_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=160)
    external_url: str = Field(min_length=8, max_length=500)
    author_name: str = Field(default="", max_length=160)
    license: LibraryLicense | str = Field(default="", max_length=80)
    attribution_text: str = Field(default="", max_length=500)
    checksum_sha256: str | None = Field(default=None, max_length=64)
    import_mode: ExternalImportMode = "bookmark"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("external_url")
    @classmethod
    def clean_external_url(cls, value: str) -> str:
        return validate_public_url(value, field_name="external_url", allowed_hosts=None) or value

    @field_validator("title", "author_name", "attribution_text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return clean_discussion_text(value) or ""

    @field_validator("checksum_sha256")
    @classmethod
    def clean_checksum(cls, value: str | None) -> str | None:
        if not value:
            return None
        clean = value.strip().lower()
        if len(clean) != 64 or any(char not in "0123456789abcdef" for char in clean):
            raise ValueError("checksum SHA-256 inválido")
        return clean

    @field_validator("metadata")
    @classmethod
    def bound_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_metadata_shape(value)
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > 16 * 1024:
            raise ValueError("metadados excedem 16 KiB")
        return value


def _validate_metadata_shape(value: Any, *, depth: int = 0) -> None:
    if depth > 5:
        raise ValueError("metadados excedem profundidade permitida")
    if isinstance(value, dict):
        if len(value) > 100:
            raise ValueError("metadados contêm chaves demais")
        for key, child in value.items():
            if not isinstance(key, str) or len(key) > 120:
                raise ValueError("chave de metadado inválida")
            _validate_metadata_shape(child, depth=depth + 1)
        return
    if isinstance(value, list):
        if len(value) > 100:
            raise ValueError("metadados contêm itens demais")
        for child in value:
            _validate_metadata_shape(child, depth=depth + 1)
        return
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("tipo de metadado inválido")


class ExternalReferenceRecord(BaseModel):
    id: int
    source_id: int | None
    source_name: str | None = None
    library_item_id: int | None
    title: str
    external_url: str
    author_name: str
    license: str
    attribution_text: str
    checksum_sha256: str | None
    import_mode: ExternalImportMode
    duplicate_library_file_id: int | None
    hosted_in_printora: bool
    status: Literal["active", "archived"]
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class ExternalImportPreview(BaseModel):
    title: str
    external_url: str
    source_host: str
    suggested_source_name: str
    license: str
    attribution_text: str
    import_mode: ExternalImportMode = "bookmark"
    hosted_in_printora: bool = False
    duplicate_library_file_id: int | None = None


class ExternalLibraryRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def list_sources(self, actor_user_id: int) -> list[ExternalSourceRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM external_content_sources
                WHERE owner_user_id = ? OR owner_user_id IS NULL
                ORDER BY name
                """,
                (actor_user_id,),
            ).fetchall()
        return [_source_from_row(row) for row in rows]

    def create_source(self, actor_user_id: int, payload: ExternalSourceCreate) -> ExternalSourceRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO external_content_sources (owner_user_id, name, base_url, license_policy, attribution_required)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(owner_user_id, base_url) DO UPDATE SET
                    name = excluded.name,
                    license_policy = excluded.license_policy,
                    attribution_required = excluded.attribution_required,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (actor_user_id, payload.name.strip(), payload.base_url, payload.license_policy.strip(), 1 if payload.attribution_required else 0),
            )
            source_id = int(cursor.lastrowid or connection.execute("SELECT id FROM external_content_sources WHERE owner_user_id = ? AND base_url = ?", (actor_user_id, payload.base_url)).fetchone()["id"])
            return _source_from_row(connection.execute("SELECT * FROM external_content_sources WHERE id = ?", (source_id,)).fetchone())

    def preview_import(self, actor_user_id: int, external_url: str, checksum_sha256: str | None = None) -> ExternalImportPreview:
        clean_url = validate_public_url(external_url, field_name="external_url", allowed_hosts=None)
        checksum = ExternalReferenceCreate(title="preview", external_url=clean_url, checksum_sha256=checksum_sha256).checksum_sha256
        parsed = urlparse(clean_url)
        title = _title_from_url(clean_url)
        duplicate = self._duplicate_file(actor_user_id, checksum)
        return ExternalImportPreview(
            title=title,
            external_url=clean_url,
            source_host=parsed.netloc,
            suggested_source_name=parsed.netloc.replace("www.", ""),
            license="",
            attribution_text=f"Fonte externa: {parsed.netloc}",
            duplicate_library_file_id=duplicate,
        )

    def list_references(self, actor_user_id: int) -> list[ExternalReferenceRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(REFERENCE_SQL + "WHERE r.owner_user_id = ? AND r.status = 'active' ORDER BY r.created_at DESC, r.id DESC", (actor_user_id,)).fetchall()
        return [_reference_from_row(row) for row in rows]

    def create_reference(self, actor_user_id: int, payload: ExternalReferenceCreate) -> ExternalReferenceRecord:
        with connect_database(self.database_path) as connection:
            source = self._source_row(connection, actor_user_id, payload.source_id)
            if source is not None and source["status"] != "active":
                raise ValueError("fonte externa indisponível")
            if source is not None and bool(source["attribution_required"]) and not clean_optional_text(payload.attribution_text):
                raise ValueError("fonte externa exige atribuição")
            if payload.import_mode != "bookmark" and not clean_optional_text(payload.license):
                raise ValueError("importação de metadados exige licença")
            duplicate = self._duplicate_file(actor_user_id, payload.checksum_sha256, connection=connection)
            cursor = connection.execute(
                """
                INSERT INTO external_library_references (
                    owner_user_id, source_id, title, external_url, author_name, license,
                    attribution_text, checksum_sha256, import_mode, duplicate_library_file_id, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(owner_user_id, external_url) DO UPDATE SET
                    title = excluded.title,
                    author_name = excluded.author_name,
                    license = excluded.license,
                    attribution_text = excluded.attribution_text,
                    checksum_sha256 = excluded.checksum_sha256,
                    duplicate_library_file_id = excluded.duplicate_library_file_id,
                    metadata_json = excluded.metadata_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    actor_user_id,
                    payload.source_id,
                    payload.title.strip(),
                    payload.external_url,
                    clean_optional_text(payload.author_name) or "",
                    str(payload.license or ""),
                    clean_optional_text(payload.attribution_text) or "",
                    payload.checksum_sha256,
                    payload.import_mode,
                    duplicate,
                    json.dumps(payload.metadata, ensure_ascii=False),
                ),
            )
            reference_id = int(cursor.lastrowid or connection.execute("SELECT id FROM external_library_references WHERE owner_user_id = ? AND external_url = ?", (actor_user_id, payload.external_url)).fetchone()["id"])
            row = connection.execute(REFERENCE_SQL + "WHERE r.id = ?", (reference_id,)).fetchone()
            return _reference_from_row(row)

    def _source_row(self, connection, actor_user_id: int, source_id: int | None):
        if source_id is None:
            return None
        row = connection.execute(
            "SELECT * FROM external_content_sources WHERE id = ? AND (owner_user_id = ? OR owner_user_id IS NULL)",
            (source_id, actor_user_id),
        ).fetchone()
        if row is None:
            raise ValueError("fonte externa não encontrada")
        return row

    def _duplicate_file(self, actor_user_id: int, checksum_sha256: str | None, connection=None) -> int | None:
        if not checksum_sha256:
            return None
        query = """
            SELECT lf.id
            FROM social_library_files lf
            JOIN social_library_items li ON li.id = lf.item_id
            WHERE lf.sha256 = ? AND li.owner_user_id = ?
            LIMIT 1
        """
        if connection is not None:
            row = connection.execute(query, (checksum_sha256, actor_user_id)).fetchone()
            return int(row["id"]) if row else None
        with connect_database(self.database_path) as owned_connection:
            row = owned_connection.execute(query, (checksum_sha256, actor_user_id)).fetchone()
            return int(row["id"]) if row else None


REFERENCE_SQL = """
SELECT r.*, s.name AS source_name
FROM external_library_references r
LEFT JOIN external_content_sources s ON s.id = r.source_id
"""


def _source_from_row(row) -> ExternalSourceRecord:
    return ExternalSourceRecord(
        id=int(row["id"]),
        name=str(row["name"]),
        base_url=str(row["base_url"]),
        license_policy=str(row["license_policy"] or ""),
        attribution_required=bool(row["attribution_required"]),
        status=row["status"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _reference_from_row(row) -> ExternalReferenceRecord:
    return ExternalReferenceRecord(
        id=int(row["id"]),
        source_id=row["source_id"],
        source_name=row["source_name"],
        library_item_id=row["library_item_id"],
        title=str(row["title"]),
        external_url=str(row["external_url"]),
        author_name=str(row["author_name"] or ""),
        license=str(row["license"] or ""),
        attribution_text=str(row["attribution_text"] or ""),
        checksum_sha256=row["checksum_sha256"],
        import_mode=row["import_mode"],
        duplicate_library_file_id=row["duplicate_library_file_id"],
        hosted_in_printora=row["library_item_id"] is not None,
        status=row["status"],
        metadata=_json_dict(row["metadata_json"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _title_from_url(value: str) -> str:
    path = urlparse(value).path.rstrip("/").split("/")[-1]
    return (path.replace("-", " ").replace("_", " ") or urlparse(value).netloc)[:160]


def _json_dict(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
