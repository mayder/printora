from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database


PresetPart = Literal["machine", "process", "filament"]
SENSITIVE_KEY = re.compile(
    r"(^|[_-])(token|password|passwd|senha|secret|credential|moonraker|ssh|api[_-]?key|host|hostname|file[_-]?path)([_-]|$)",
    re.I,
)
SENSITIVE_VALUE = re.compile(
    r"(^/Users/|^/home/|^[A-Za-z]:\\|ssh://|https?://(?:localhost|127\.0\.0\.1|10\.|192\.168\.)|Bearer\s+|ptr_(?:agent|pair|sess)_)",
    re.I,
)


class NativeProfileBundle(BaseModel):
    machine: dict[str, Any]
    process: dict[str, Any]
    filament: dict[str, Any]


class ProfileBundleImport(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    engine_version: str = Field(min_length=1, max_length=80)
    schema_version: str = Field(default="1", min_length=1, max_length=40)
    compatibility: dict[str, str] = Field(default_factory=dict)
    native_bundle: NativeProfileBundle
    bundle_id: int | None = Field(default=None, ge=1)
    parent_revision_id: int | None = Field(default=None, ge=1)

    @field_validator("title", "engine_version", "schema_version")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if SENSITIVE_VALUE.search(cleaned):
            raise ValueError("pacote de perfil contém dado operacional sensível")
        return cleaned


class ProfileRevision(BaseModel):
    id: int
    bundle_id: int
    revision_number: int
    parent_revision_id: int | None
    sha256: str
    native_bundle: dict[str, Any]
    canonical: dict[str, Any]
    overrides: dict[str, Any]
    loss_report: list[str]
    created_at: str


class ProfileBundle(BaseModel):
    id: int
    title: str
    engine: str
    engine_version: str
    schema_version: str
    source_format: str
    compatibility: dict[str, str]
    current_revision_id: int | None
    current_sha256: str | None
    revisions: list[ProfileRevision]
    created_at: str
    updated_at: str


class ProfileDiff(BaseModel):
    from_revision_id: int
    to_revision_id: int
    added: dict[str, Any]
    changed: dict[str, dict[str, Any]]
    removed: dict[str, Any]
    loss_report: list[str] = Field(default_factory=list)


class SlicingProfileBundlesRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def list_for_owner(self, actor_user_id: int) -> list[ProfileBundle]:
        with connect_database(self.database_path) as connection:
            ids = [int(row["id"]) for row in connection.execute(
                "SELECT id FROM slicing_profile_bundles WHERE owner_user_id = ? AND status = 'active' ORDER BY updated_at DESC, id DESC",
                (actor_user_id,),
            ).fetchall()]
        return [bundle for bundle_id in ids if (bundle := self.detail(actor_user_id, bundle_id)) is not None]

    def detail(self, actor_user_id: int, bundle_id: int) -> ProfileBundle | None:
        with connect_database(self.database_path) as connection:
            bundle = connection.execute(
                "SELECT * FROM slicing_profile_bundles WHERE id = ? AND owner_user_id = ? AND status = 'active'",
                (bundle_id, actor_user_id),
            ).fetchone()
            if bundle is None:
                return None
            revisions = connection.execute(
                "SELECT * FROM slicing_profile_revisions WHERE bundle_id = ? ORDER BY revision_number DESC",
                (bundle_id,),
            ).fetchall()
        parsed = [_revision_from_row(row) for row in revisions]
        current = next((item for item in parsed if item.id == bundle["current_revision_id"]), None)
        return ProfileBundle(
            id=int(bundle["id"]), title=str(bundle["title"]), engine=str(bundle["engine"]),
            engine_version=str(bundle["engine_version"]), schema_version=str(bundle["schema_version"]),
            source_format=str(bundle["source_format"]), compatibility=_loads_dict(bundle["compatibility_json"]),
            current_revision_id=bundle["current_revision_id"], current_sha256=current.sha256 if current else None,
            revisions=parsed, created_at=str(bundle["created_at"]), updated_at=str(bundle["updated_at"]),
        )

    def import_bundle(self, actor_user_id: int, payload: ProfileBundleImport) -> ProfileBundle:
        native = _sanitize_bundle(payload.native_bundle.model_dump())
        canonical = _canonical(payload, native)
        canonical_json = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(canonical_json.encode()).hexdigest()
        with connect_database(self.database_path) as connection:
            if payload.bundle_id is None:
                duplicate = connection.execute(
                    """SELECT b.id FROM slicing_profile_bundles b JOIN slicing_profile_revisions r ON r.bundle_id = b.id
                       WHERE b.owner_user_id = ? AND r.sha256 = ? AND b.status = 'active' LIMIT 1""",
                    (actor_user_id, checksum),
                ).fetchone()
                if duplicate is not None:
                    bundle_id = int(duplicate["id"])
                else:
                    cursor = connection.execute(
                        """INSERT INTO slicing_profile_bundles
                           (owner_user_id, title, engine_version, schema_version, compatibility_json)
                           VALUES (?, ?, ?, ?, ?)""",
                        (actor_user_id, payload.title, payload.engine_version, payload.schema_version,
                         json.dumps(payload.compatibility, ensure_ascii=False, sort_keys=True)),
                    )
                    bundle_id = int(cursor.lastrowid)
                    self._insert_revision(connection, actor_user_id, bundle_id, None, native, canonical_json, checksum)
            else:
                bundle = connection.execute(
                    "SELECT * FROM slicing_profile_bundles WHERE id = ? AND owner_user_id = ? AND status = 'active'",
                    (payload.bundle_id, actor_user_id),
                ).fetchone()
                if bundle is None:
                    raise PermissionError("pacote de perfil não encontrado")
                bundle_id = int(bundle["id"])
                duplicate = connection.execute(
                    "SELECT id FROM slicing_profile_revisions WHERE bundle_id = ? AND sha256 = ?",
                    (bundle_id, checksum),
                ).fetchone()
                if duplicate is None:
                    parent_id = payload.parent_revision_id or bundle["current_revision_id"]
                    self._assert_parent(connection, bundle_id, parent_id)
                    self._insert_revision(connection, actor_user_id, bundle_id, parent_id, native, canonical_json, checksum)
                connection.execute(
                    "UPDATE slicing_profile_bundles SET title = ?, engine_version = ?, schema_version = ?, compatibility_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (payload.title, payload.engine_version, payload.schema_version,
                     json.dumps(payload.compatibility, ensure_ascii=False, sort_keys=True), bundle_id),
                )
        result = self.detail(actor_user_id, bundle_id)
        if result is None:
            raise ValueError("pacote de perfil não encontrado")
        return result

    def export_revision(self, actor_user_id: int, revision_id: int) -> dict[str, Any]:
        revision = self._owned_revision(actor_user_id, revision_id)
        if revision is None:
            raise PermissionError("revisão de perfil não encontrada")
        return {
            "format": "printora.orcaslicer-profile-bundle/v1",
            "engine": "orcaslicer",
            "sha256": revision.sha256,
            "native_bundle": revision.native_bundle,
        }

    def diff(self, actor_user_id: int, from_revision_id: int, to_revision_id: int) -> ProfileDiff:
        before = self._owned_revision(actor_user_id, from_revision_id)
        after = self._owned_revision(actor_user_id, to_revision_id)
        if before is None or after is None or before.bundle_id != after.bundle_id:
            raise PermissionError("revisões não pertencem ao mesmo pacote")
        left, right = _flatten(before.canonical), _flatten(after.canonical)
        return ProfileDiff(
            from_revision_id=before.id,
            to_revision_id=after.id,
            added={key: right[key] for key in sorted(right.keys() - left.keys())},
            changed={key: {"before": left[key], "after": right[key]} for key in sorted(left.keys() & right.keys()) if left[key] != right[key]},
            removed={key: left[key] for key in sorted(left.keys() - right.keys())},
            loss_report=after.loss_report,
        )

    def _insert_revision(self, connection, actor_user_id: int, bundle_id: int, parent_id: int | None,
                         native: dict[str, Any], canonical_json: str, checksum: str) -> None:
        number = int(connection.execute(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM slicing_profile_revisions WHERE bundle_id = ?",
            (bundle_id,),
        ).fetchone()[0])
        overrides: dict[str, Any] = {}
        if parent_id is not None:
            parent = connection.execute("SELECT canonical_json FROM slicing_profile_revisions WHERE id = ?", (parent_id,)).fetchone()
            parent_flat = _flatten(_loads_dict(parent["canonical_json"])) if parent else {}
            current_flat = _flatten(json.loads(canonical_json))
            overrides = {key: value for key, value in current_flat.items() if parent_flat.get(key) != value}
        cursor = connection.execute(
            """INSERT INTO slicing_profile_revisions
               (bundle_id, revision_number, parent_revision_id, native_bundle_json, canonical_json, sha256,
                overrides_json, created_by_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (bundle_id, number, parent_id, json.dumps(native, ensure_ascii=False, sort_keys=True), canonical_json,
             checksum, json.dumps(overrides, ensure_ascii=False, sort_keys=True), actor_user_id),
        )
        connection.execute("UPDATE slicing_profile_bundles SET current_revision_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (cursor.lastrowid, bundle_id))

    def _assert_parent(self, connection, bundle_id: int, parent_id: int | None) -> None:
        if parent_id is None:
            return
        if connection.execute("SELECT 1 FROM slicing_profile_revisions WHERE id = ? AND bundle_id = ?", (parent_id, bundle_id)).fetchone() is None:
            raise ValueError("revisão base não pertence ao pacote")

    def _owned_revision(self, actor_user_id: int, revision_id: int) -> ProfileRevision | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """SELECT r.* FROM slicing_profile_revisions r JOIN slicing_profile_bundles b ON b.id = r.bundle_id
                   WHERE r.id = ? AND b.owner_user_id = ? AND b.status = 'active'""",
                (revision_id, actor_user_id),
            ).fetchone()
        return _revision_from_row(row) if row else None


def _sanitize_bundle(value: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(value, ensure_ascii=False)
    if len(encoded.encode()) > 2 * 1024 * 1024:
        raise ValueError("pacote de perfil excede 2 MB")
    return _sanitize(value, 0)


def _sanitize(value: Any, depth: int) -> Any:
    if depth > 12:
        raise ValueError("pacote de perfil possui estrutura profunda demais")
    if isinstance(value, dict):
        if len(value) > 2000:
            raise ValueError("pacote de perfil possui configurações demais")
        cleaned: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key).strip()
            if not key or len(key) > 160 or SENSITIVE_KEY.search(key):
                raise ValueError("pacote de perfil contém chave operacional sensível")
            cleaned[key] = _sanitize(item, depth + 1)
        return cleaned
    if isinstance(value, list):
        if len(value) > 5000:
            raise ValueError("pacote de perfil possui lista grande demais")
        return [_sanitize(item, depth + 1) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    if len(text) > 10_000 or SENSITIVE_VALUE.search(text):
        raise ValueError("pacote de perfil contém valor operacional sensível")
    return text


def _canonical(payload: ProfileBundleImport, native: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": "printora.slicing-profile/v1",
        "engine": "orcaslicer",
        "engine_version": payload.engine_version,
        "schema_version": payload.schema_version,
        "compatibility": dict(sorted(payload.compatibility.items())),
        "presets": native,
    }


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key in sorted(value):
            result.update(_flatten(value[key], f"{prefix}.{key}" if prefix else key))
        return result
    if isinstance(value, list):
        result: dict[str, Any] = {}
        for index, item in enumerate(value):
            result.update(_flatten(item, f"{prefix}[{index}]"))
        return result
    return {prefix: value}


def _revision_from_row(row) -> ProfileRevision:
    return ProfileRevision(
        id=int(row["id"]), bundle_id=int(row["bundle_id"]), revision_number=int(row["revision_number"]),
        parent_revision_id=row["parent_revision_id"], sha256=str(row["sha256"]),
        native_bundle=_loads_dict(row["native_bundle_json"]), canonical=_loads_dict(row["canonical_json"]),
        overrides=_loads_dict(row["overrides_json"]), loss_report=_loads_list(row["loss_report_json"]),
        created_at=str(row["created_at"]),
    )


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _loads_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        parsed = json.loads(value or "[]")
        return [str(item) for item in parsed] if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []
