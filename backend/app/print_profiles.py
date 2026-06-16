from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database


ProfileVisibility = Literal["private", "community", "public"]
SlicingGoal = Literal["quality", "strength", "speed", "prototype"]


class SlicingProfilePayload(BaseModel):
    layer_height_mm: float | None = Field(default=None, gt=0, le=1.0)
    speed_mm_s: int | None = Field(default=None, ge=1, le=1000)
    infill_percent: int | None = Field(default=None, ge=0, le=100)
    supports_enabled: bool = False
    goal: SlicingGoal = "quality"
    settings: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @field_validator("settings")
    @classmethod
    def clean_settings(cls, value: dict[str, str | int | float | bool]) -> dict[str, str | int | float | bool]:
        if len(value) > 80:
            raise ValueError("limite de configurações excedido")
        return {_clean_key(key): item for key, item in value.items() if _clean_key(key)}


class MaterialProfilePayload(BaseModel):
    printer_id: int | None = Field(default=None, ge=1)
    catalog_variant_id: int | None = Field(default=None, ge=1)
    community_slug: str | None = Field(default=None, max_length=160)
    linked_library_item_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=2, max_length=120)
    visibility: ProfileVisibility = "private"
    material_brand: str = Field(default="", max_length=80)
    material_type: str = Field(min_length=2, max_length=40)
    nozzle_diameter_mm: float | None = Field(default=None, gt=0, le=3.0)
    bed_temperature_c: int | None = Field(default=None, ge=0, le=160)
    nozzle_temperature_c: int | None = Field(default=None, ge=0, le=400)
    flow_percent: float | None = Field(default=None, gt=0, le=200)
    notes: str = Field(default="", max_length=2000)
    version_label: str = Field(default="v1", min_length=1, max_length=40)
    compatibility: dict[str, str] = Field(default_factory=dict)
    slicing: SlicingProfilePayload = Field(default_factory=SlicingProfilePayload)

    @field_validator("title", "material_brand", "material_type", "notes", "version_label")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if any(term in cleaned.lower() for term in ("token", "senha", "password", "moonraker", "ssh", "host", "ip", "path")):
            raise ValueError("perfil compartilhável não pode conter dado operacional sensível")
        return cleaned

    @field_validator("community_slug")
    @classmethod
    def clean_slug(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else None

    @field_validator("compatibility")
    @classmethod
    def clean_compatibility(cls, value: dict[str, str]) -> dict[str, str]:
        return {_clean_key(key): " ".join(str(item).strip().split())[:120] for key, item in value.items() if _clean_key(key)}


class SlicingProfile(BaseModel):
    id: int
    material_profile_id: int
    layer_height_mm: float | None
    speed_mm_s: int | None
    infill_percent: int | None
    supports_enabled: bool
    goal: SlicingGoal
    settings: dict[str, str | int | float | bool]
    created_at: str
    updated_at: str


class MaterialProfile(BaseModel):
    id: int
    owner_user_id: int
    owner_slug: str | None = None
    owner_display_name: str | None = None
    printer_id: int | None = None
    printer_public_name: str | None = None
    catalog_variant_id: int | None = None
    manufacturer_name: str | None = None
    model_name: str | None = None
    variant_name: str | None = None
    community_slug: str | None = None
    community_id: int | None = None
    community_name: str | None = None
    linked_library_item_id: int | None = None
    title: str
    visibility: ProfileVisibility
    material_brand: str
    material_type: str
    nozzle_diameter_mm: float | None
    bed_temperature_c: int | None
    nozzle_temperature_c: int | None
    flow_percent: float | None
    notes: str
    version_label: str
    compatibility: dict[str, str]
    slicing: SlicingProfile
    status: str
    created_at: str
    updated_at: str


class MaterialProfileExport(BaseModel):
    format: str = "printora.material-profile.v1"
    profile: MaterialProfile


class PrintProfilesRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def create_profile(self, actor_user_id: int, payload: MaterialProfilePayload) -> MaterialProfile:
        community_id = self._community_id(payload.community_slug) if payload.community_slug else None
        printer = self._printer_for_owner(payload.printer_id, actor_user_id) if payload.printer_id else None
        catalog_variant_id = payload.catalog_variant_id or (printer["catalog_variant_id"] if printer else None)
        if payload.visibility == "community" and community_id is None:
            raise ValueError("perfil comunitário exige comunidade")
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO social_material_profiles (
                    owner_user_id, printer_id, catalog_variant_id, community_id, linked_library_item_id,
                    title, visibility, material_brand, material_type, nozzle_diameter_mm,
                    bed_temperature_c, nozzle_temperature_c, flow_percent, notes, version_label,
                    compatibility_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor_user_id,
                    payload.printer_id,
                    catalog_variant_id,
                    community_id,
                    payload.linked_library_item_id,
                    payload.title,
                    payload.visibility,
                    payload.material_brand,
                    payload.material_type.upper(),
                    payload.nozzle_diameter_mm,
                    payload.bed_temperature_c,
                    payload.nozzle_temperature_c,
                    payload.flow_percent,
                    payload.notes,
                    payload.version_label,
                    json.dumps(payload.compatibility, ensure_ascii=False),
                ),
            )
            profile_id = int(cursor.lastrowid)
            self._upsert_slicing(connection, profile_id, payload.slicing)
        profile = self.profile(profile_id, actor_user_id)
        if profile is None:
            raise ValueError("perfil não encontrado")
        return profile

    def update_profile(self, profile_id: int, actor_user_id: int, payload: MaterialProfilePayload) -> MaterialProfile:
        if self._owned_profile(profile_id, actor_user_id) is None:
            raise ValueError("perfil não encontrado")
        community_id = self._community_id(payload.community_slug) if payload.community_slug else None
        printer = self._printer_for_owner(payload.printer_id, actor_user_id) if payload.printer_id else None
        catalog_variant_id = payload.catalog_variant_id or (printer["catalog_variant_id"] if printer else None)
        if payload.visibility == "community" and community_id is None:
            raise ValueError("perfil comunitário exige comunidade")
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE social_material_profiles
                SET printer_id = ?, catalog_variant_id = ?, community_id = ?, linked_library_item_id = ?,
                    title = ?, visibility = ?, material_brand = ?, material_type = ?, nozzle_diameter_mm = ?,
                    bed_temperature_c = ?, nozzle_temperature_c = ?, flow_percent = ?, notes = ?,
                    version_label = ?, compatibility_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (
                    payload.printer_id,
                    catalog_variant_id,
                    community_id,
                    payload.linked_library_item_id,
                    payload.title,
                    payload.visibility,
                    payload.material_brand,
                    payload.material_type.upper(),
                    payload.nozzle_diameter_mm,
                    payload.bed_temperature_c,
                    payload.nozzle_temperature_c,
                    payload.flow_percent,
                    payload.notes,
                    payload.version_label,
                    json.dumps(payload.compatibility, ensure_ascii=False),
                    profile_id,
                    actor_user_id,
                ),
            )
            self._upsert_slicing(connection, profile_id, payload.slicing)
        profile = self.profile(profile_id, actor_user_id)
        if profile is None:
            raise ValueError("perfil não encontrado")
        return profile

    def archive_profile(self, profile_id: int, actor_user_id: int) -> None:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE social_material_profiles
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (profile_id, actor_user_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("perfil não encontrado")

    def my_profiles(self, actor_user_id: int) -> list[MaterialProfile]:
        return self._list_profiles("mp.owner_user_id = ? AND mp.status = 'active'", (actor_user_id,), actor_user_id)

    def community_profiles(self, slug: str, viewer_user_id: int | None = None) -> list[MaterialProfile]:
        return self._list_profiles(
            "sc.slug = ? AND mp.status = 'active' AND mp.visibility IN ('community', 'public')",
            (slug,),
            viewer_user_id,
        )

    def profile(self, profile_id: int, viewer_user_id: int | None = None) -> MaterialProfile | None:
        profiles = self._list_profiles(
            "mp.id = ? AND mp.status = 'active' AND (mp.visibility IN ('community', 'public') OR mp.owner_user_id = ?)",
            (profile_id, viewer_user_id or -1),
            viewer_user_id,
        )
        return profiles[0] if profiles else None

    def export_profile(self, profile_id: int, viewer_user_id: int | None = None) -> MaterialProfileExport:
        profile = self.profile(profile_id, viewer_user_id)
        if profile is None:
            raise ValueError("perfil não encontrado")
        return MaterialProfileExport(profile=profile)

    def import_profile(self, actor_user_id: int, payload: MaterialProfileExport) -> MaterialProfile:
        profile = payload.profile
        return self.create_profile(
            actor_user_id,
            MaterialProfilePayload(
                printer_id=profile.printer_id,
                catalog_variant_id=profile.catalog_variant_id,
                community_slug=profile.community_slug,
                linked_library_item_id=profile.linked_library_item_id,
                title=f"{profile.title} importado",
                visibility="private",
                material_brand=profile.material_brand,
                material_type=profile.material_type,
                nozzle_diameter_mm=profile.nozzle_diameter_mm,
                bed_temperature_c=profile.bed_temperature_c,
                nozzle_temperature_c=profile.nozzle_temperature_c,
                flow_percent=profile.flow_percent,
                notes=profile.notes,
                version_label=profile.version_label,
                compatibility=profile.compatibility,
                slicing=SlicingProfilePayload(**profile.slicing.model_dump(exclude={"id", "material_profile_id", "created_at", "updated_at"})),
            ),
        )

    def _list_profiles(self, where_sql: str, params: tuple[object, ...], viewer_user_id: int | None) -> list[MaterialProfile]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT mp.*, sp.slug AS owner_slug, sp.display_name AS owner_display_name,
                       sc.slug AS community_slug, sc.name AS community_name,
                       p.public_name AS printer_public_name,
                       cm.name AS manufacturer_name, cpm.name AS model_name, cpv.name AS variant_name,
                       sl.id AS slicing_id, sl.layer_height_mm, sl.speed_mm_s, sl.infill_percent,
                       sl.supports_enabled, sl.goal, sl.settings_json,
                       sl.created_at AS slicing_created_at, sl.updated_at AS slicing_updated_at
                FROM social_material_profiles mp
                JOIN social_slicing_profiles sl ON sl.material_profile_id = mp.id
                LEFT JOIN social_profiles sp ON sp.user_id = mp.owner_user_id
                LEFT JOIN social_communities sc ON sc.id = mp.community_id
                LEFT JOIN printers p ON p.id = mp.printer_id
                LEFT JOIN catalog_printer_variants cpv ON cpv.id = mp.catalog_variant_id
                LEFT JOIN catalog_printer_models cpm ON cpm.id = cpv.model_id
                LEFT JOIN catalog_manufacturers cm ON cm.id = cpm.manufacturer_id
                WHERE {where_sql}
                ORDER BY mp.updated_at DESC, mp.id DESC
                """,
                params,
            ).fetchall()
        return [_row_to_profile(row) for row in rows]

    def _upsert_slicing(self, connection, profile_id: int, payload: SlicingProfilePayload) -> None:
        connection.execute(
            """
            INSERT INTO social_slicing_profiles (
                material_profile_id, layer_height_mm, speed_mm_s, infill_percent,
                supports_enabled, goal, settings_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(material_profile_id) DO UPDATE SET
                layer_height_mm = excluded.layer_height_mm,
                speed_mm_s = excluded.speed_mm_s,
                infill_percent = excluded.infill_percent,
                supports_enabled = excluded.supports_enabled,
                goal = excluded.goal,
                settings_json = excluded.settings_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                profile_id,
                payload.layer_height_mm,
                payload.speed_mm_s,
                payload.infill_percent,
                1 if payload.supports_enabled else 0,
                payload.goal,
                json.dumps(payload.settings, ensure_ascii=False),
            ),
        )

    def _owned_profile(self, profile_id: int, actor_user_id: int):
        with connect_database(self.database_path) as connection:
            return connection.execute(
                "SELECT id FROM social_material_profiles WHERE id = ? AND owner_user_id = ? AND status = 'active'",
                (profile_id, actor_user_id),
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


def _row_to_profile(row) -> MaterialProfile:
    slicing = SlicingProfile(
        id=row["slicing_id"],
        material_profile_id=row["id"],
        layer_height_mm=row["layer_height_mm"],
        speed_mm_s=row["speed_mm_s"],
        infill_percent=row["infill_percent"],
        supports_enabled=bool(row["supports_enabled"]),
        goal=row["goal"],
        settings=json.loads(row["settings_json"] or "{}"),
        created_at=row["slicing_created_at"],
        updated_at=row["slicing_updated_at"],
    )
    return MaterialProfile(
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
        material_brand=row["material_brand"],
        material_type=row["material_type"],
        nozzle_diameter_mm=row["nozzle_diameter_mm"],
        bed_temperature_c=row["bed_temperature_c"],
        nozzle_temperature_c=row["nozzle_temperature_c"],
        flow_percent=row["flow_percent"],
        notes=row["notes"],
        version_label=row["version_label"],
        compatibility=json.loads(row["compatibility_json"] or "{}"),
        slicing=slicing,
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _clean_key(value: object) -> str:
    key = " ".join(str(value).strip().split())[:60]
    if any(term in key.lower() for term in ("token", "senha", "password", "moonraker", "ssh", "host", "ip", "path")):
        raise ValueError("perfil compartilhável não pode conter dado operacional sensível")
    return key
