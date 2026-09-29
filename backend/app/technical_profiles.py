from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database


ConfigVisibility = Literal["private", "community", "public"]

SENSITIVE_PATTERN = re.compile(
    r"(token|secret|password|senha|moonraker|ssh|host|ip|url|path|agent|credential|credencial)",
    re.IGNORECASE,
)


class TechnicalPrinterConfigPayload(BaseModel):
    printer_id: int | None = Field(default=None, ge=1)
    catalog_variant_id: int | None = Field(default=None, ge=1)
    community_slug: str | None = Field(default=None, max_length=160)
    linked_library_item_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=2, max_length=120)
    visibility: ConfigVisibility = "private"
    mods: list[str] = Field(default_factory=list, max_length=40)
    components: dict[str, str] = Field(default_factory=dict)
    calibrations: dict[str, str] = Field(default_factory=dict)
    notes: str = Field(default="", max_length=2000)

    @field_validator("mods")
    @classmethod
    def clean_mods(cls, value: list[str]) -> list[str]:
        return [_clean_public_text(item, 80) for item in value if _clean_public_text(item, 80)]

    @field_validator("components", "calibrations")
    @classmethod
    def clean_public_map(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for key, item in value.items():
            clean_key = _clean_public_text(str(key), 60)
            clean_item = _clean_public_text(str(item), 140)
            if not clean_key or not clean_item:
                continue
            _reject_sensitive(clean_key)
            _reject_sensitive(clean_item)
            cleaned[clean_key] = clean_item
        if len(cleaned) > 80:
            raise ValueError("limite de campos técnicos excedido")
        return cleaned

    @field_validator("title", "notes")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = _clean_public_text(value, 2000)
        _reject_sensitive(cleaned)
        return cleaned

    @field_validator("community_slug")
    @classmethod
    def clean_slug(cls, value: str | None) -> str | None:
        return _clean_public_text(value, 160).lower() if value else None


class TechnicalPrinterConfig(TechnicalPrinterConfigPayload):
    id: int
    owner_user_id: int
    owner_slug: str | None = None
    owner_display_name: str | None = None
    community_id: int | None = None
    community_name: str | None = None
    catalog_variant_id: int | None = None
    manufacturer_name: str | None = None
    model_name: str | None = None
    variant_name: str | None = None
    printer_public_name: str | None = None
    status: str
    created_at: str
    updated_at: str


class TechnicalConfigComparison(BaseModel):
    community_slug: str
    community_name: str
    configs: list[TechnicalPrinterConfig]
    normalized_components: dict[str, list[str]]
    normalized_calibrations: dict[str, list[str]]


class TechnicalProfilesRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def create_config(self, actor_user_id: int, payload: TechnicalPrinterConfigPayload) -> TechnicalPrinterConfig:
        community_id = self._community_id(payload.community_slug) if payload.community_slug else None
        printer = self._printer_for_owner(payload.printer_id, actor_user_id) if payload.printer_id else None
        catalog_variant_id = payload.catalog_variant_id or (printer["catalog_variant_id"] if printer else None)
        if payload.visibility == "community" and community_id is None:
            raise ValueError("perfil comunitário exige comunidade")
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO social_technical_printer_configs (
                    owner_user_id, printer_id, catalog_variant_id, community_id, linked_library_item_id,
                    title, visibility, mods_json, components_json, calibrations_json, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor_user_id,
                    payload.printer_id,
                    catalog_variant_id,
                    community_id,
                    payload.linked_library_item_id,
                    payload.title,
                    payload.visibility,
                    json.dumps(payload.mods, ensure_ascii=False),
                    json.dumps(payload.components, ensure_ascii=False),
                    json.dumps(payload.calibrations, ensure_ascii=False),
                    payload.notes,
                ),
            )
            config_id = int(cursor.lastrowid)
        config = self.config(config_id, actor_user_id)
        if config is None:
            raise ValueError("configuração técnica não encontrada")
        return config

    def update_config(self, config_id: int, actor_user_id: int, payload: TechnicalPrinterConfigPayload) -> TechnicalPrinterConfig:
        existing = self._owned_config(config_id, actor_user_id)
        if existing is None:
            raise ValueError("configuração técnica não encontrada")
        community_id = self._community_id(payload.community_slug) if payload.community_slug else None
        printer = self._printer_for_owner(payload.printer_id, actor_user_id) if payload.printer_id else None
        catalog_variant_id = payload.catalog_variant_id or (printer["catalog_variant_id"] if printer else None)
        if payload.visibility == "community" and community_id is None:
            raise ValueError("perfil comunitário exige comunidade")
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE social_technical_printer_configs
                SET printer_id = ?, catalog_variant_id = ?, community_id = ?, linked_library_item_id = ?,
                    title = ?, visibility = ?, mods_json = ?, components_json = ?, calibrations_json = ?,
                    notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (
                    payload.printer_id,
                    catalog_variant_id,
                    community_id,
                    payload.linked_library_item_id,
                    payload.title,
                    payload.visibility,
                    json.dumps(payload.mods, ensure_ascii=False),
                    json.dumps(payload.components, ensure_ascii=False),
                    json.dumps(payload.calibrations, ensure_ascii=False),
                    payload.notes,
                    config_id,
                    actor_user_id,
                ),
            )
        config = self.config(config_id, actor_user_id)
        if config is None:
            raise ValueError("configuração técnica não encontrada")
        return config

    def archive_config(self, config_id: int, actor_user_id: int) -> None:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE social_technical_printer_configs
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (config_id, actor_user_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("configuração técnica não encontrada")

    def my_configs(self, actor_user_id: int) -> list[TechnicalPrinterConfig]:
        return self._list_configs("c.owner_user_id = ? AND c.status = 'active'", (actor_user_id,), actor_user_id)

    def community_configs(self, slug: str, viewer_user_id: int | None = None) -> list[TechnicalPrinterConfig]:
        return self._list_configs(
            """
            sc.slug = ?
            AND c.status = 'active'
            AND c.visibility IN ('community', 'public')
            """,
            (slug,),
            viewer_user_id,
        )

    def profile_configs(self, slug: str, viewer_user_id: int | None = None) -> list[TechnicalPrinterConfig]:
        return self._list_configs(
            """
            sp.slug = ?
            AND sp.visibility IN ('public', 'unlisted')
            AND c.status = 'active'
            AND c.visibility = 'public'
            AND NOT EXISTS (
                SELECT 1 FROM social_relationships r
                WHERE r.relation_type = 'block'
                  AND r.status = 'active'
                  AND ((r.actor_user_id = c.owner_user_id AND r.target_user_id = ?)
                    OR (r.actor_user_id = ? AND r.target_user_id = c.owner_user_id))
            )
            """,
            (slug, viewer_user_id or -1, viewer_user_id or -1),
            viewer_user_id,
        )

    def config(self, config_id: int, viewer_user_id: int | None = None) -> TechnicalPrinterConfig | None:
        configs = self._list_configs(
            """
            c.id = ?
            AND c.status = 'active'
            AND (c.visibility IN ('community', 'public') OR c.owner_user_id = ?)
            """,
            (config_id, viewer_user_id or -1),
            viewer_user_id,
        )
        return configs[0] if configs else None

    def compare_community(self, slug: str, viewer_user_id: int | None = None) -> TechnicalConfigComparison:
        configs = self.community_configs(slug, viewer_user_id)
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT slug, name FROM social_communities WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            raise ValueError("comunidade não encontrada")
        return TechnicalConfigComparison(
            community_slug=row["slug"],
            community_name=row["name"],
            configs=configs,
            normalized_components=_normalize_maps([item.components for item in configs]),
            normalized_calibrations=_normalize_maps([item.calibrations for item in configs]),
        )

    def _list_configs(self, where_sql: str, params: tuple[object, ...], viewer_user_id: int | None) -> list[TechnicalPrinterConfig]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT c.*, sc.slug AS community_slug, sc.name AS community_name,
                       sp.slug AS owner_slug, sp.display_name AS owner_display_name,
                       p.public_name AS printer_public_name,
                       cm.name AS manufacturer_name, cpm.name AS model_name, cpv.name AS variant_name
                FROM social_technical_printer_configs c
                LEFT JOIN social_communities sc ON sc.id = c.community_id
                LEFT JOIN social_profiles sp ON sp.user_id = c.owner_user_id
                LEFT JOIN printers p ON p.id = c.printer_id
                LEFT JOIN catalog_printer_variants cpv ON cpv.id = c.catalog_variant_id
                LEFT JOIN catalog_printer_models cpm ON cpm.id = cpv.model_id
                LEFT JOIN catalog_manufacturers cm ON cm.id = cpm.manufacturer_id
                WHERE {where_sql}
                ORDER BY c.updated_at DESC, c.id DESC
                """,
                params,
            ).fetchall()
        return [_row_to_config(row) for row in rows]

    def _owned_config(self, config_id: int, actor_user_id: int):
        with connect_database(self.database_path) as connection:
            return connection.execute(
                "SELECT id FROM social_technical_printer_configs WHERE id = ? AND owner_user_id = ? AND status = 'active'",
                (config_id, actor_user_id),
            ).fetchone()

    def _printer_for_owner(self, printer_id: int, actor_user_id: int):
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT id, catalog_variant_id FROM printers WHERE id = ? AND owner_user_id = ?",
                (printer_id, actor_user_id),
            ).fetchone()
        if row is None:
            raise ValueError("impressora não encontrada para o usuário")
        return row

    def _community_id(self, slug: str) -> int:
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT id FROM social_communities WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            raise ValueError("comunidade não encontrada")
        return int(row["id"])


def _row_to_config(row) -> TechnicalPrinterConfig:
    return TechnicalPrinterConfig(
        id=row["id"],
        owner_user_id=row["owner_user_id"],
        owner_slug=row["owner_slug"],
        owner_display_name=row["owner_display_name"],
        printer_id=row["printer_id"],
        printer_public_name=row["printer_public_name"],
        catalog_variant_id=row["catalog_variant_id"],
        manufacturer_name=row["manufacturer_name"],
        model_name=row["model_name"],
        variant_name=row["variant_name"],
        community_slug=row["community_slug"],
        community_id=row["community_id"],
        community_name=row["community_name"],
        linked_library_item_id=row["linked_library_item_id"],
        title=row["title"],
        visibility=row["visibility"],
        mods=json.loads(row["mods_json"] or "[]"),
        components=json.loads(row["components_json"] or "{}"),
        calibrations=json.loads(row["calibrations_json"] or "{}"),
        notes=row["notes"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _normalize_maps(maps: list[dict[str, str]]) -> dict[str, list[str]]:
    normalized: dict[str, set[str]] = {}
    for payload in maps:
        for key, value in payload.items():
            normalized.setdefault(key.strip().lower(), set()).add(value)
    return {key: sorted(values) for key, values in sorted(normalized.items())}


def _clean_public_text(value: str | None, max_length: int) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().split())[:max_length]


def _reject_sensitive(value: str) -> None:
    if SENSITIVE_PATTERN.search(value):
        raise ValueError("configuração pública não pode conter dado operacional sensível")
