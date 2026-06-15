from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import connect_database


TrustState = Literal["official", "community", "draft", "obsolete", "blocked"]
ProfileVisibility = Literal["public", "unlisted", "private"]
CommunityStatus = Literal["active", "uncurated", "obsolete", "merged"]
RelationshipType = Literal["follow", "friend", "block"]
RelationshipStatus = Literal["active", "pending", "accepted", "ended"]


class CatalogVariant(BaseModel):
    id: int
    slug: str
    name: str
    build_volume: dict[str, object]
    components: dict[str, object]
    firmware_family: str | None
    trust_state: TrustState
    source: str


class CatalogVariantDetail(CatalogVariant):
    manufacturer_id: int
    manufacturer_slug: str
    manufacturer_name: str
    model_id: int
    model_slug: str
    model_name: str
    kinematics: str


class CatalogModelAdmin(BaseModel):
    id: int
    slug: str
    name: str
    kinematics: str
    trust_state: TrustState
    manufacturer_id: int
    manufacturer_slug: str
    manufacturer_name: str
    manufacturer_website_url: str | None = None
    manufacturer_repository_url: str | None = None
    manufacturer_documentation_url: str | None = None
    website_url: str | None = None
    repository_url: str | None = None
    documentation_url: str | None = None
    bom_url: str | None = None
    description: str | None = None
    variants: list[CatalogVariant] = Field(default_factory=list)


class CatalogModel(BaseModel):
    id: int
    slug: str
    name: str
    kinematics: str
    trust_state: TrustState
    source: str
    variants: list[CatalogVariant] = Field(default_factory=list)


class CatalogManufacturer(BaseModel):
    id: int
    slug: str
    name: str
    trust_state: TrustState
    source: str
    models: list[CatalogModel] = Field(default_factory=list)


class CatalogSummary(BaseModel):
    manufacturers: list[CatalogManufacturer]


class CatalogAdminSummary(BaseModel):
    models: list[CatalogModelAdmin]
    manufacturer_count: int
    model_count: int
    variant_count: int


class CatalogVariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    build_volume: dict[str, object] | None = None
    components: dict[str, object] | None = None
    firmware_family: str | None = Field(default=None, max_length=80)
    trust_state: TrustState | None = None
    source: str | None = Field(default=None, max_length=120)


class CatalogManufacturerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    trust_state: TrustState = "draft"
    source: str = Field(default="admin", max_length=120)


class CatalogModelCreate(BaseModel):
    manufacturer_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    kinematics: str = Field(min_length=1, max_length=80)
    trust_state: TrustState = "draft"
    source: str = Field(default="admin", max_length=120)


class CatalogVariantCreate(BaseModel):
    model_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=120)
    build_volume: dict[str, object] = Field(default_factory=dict)
    components: dict[str, object] = Field(default_factory=dict)
    firmware_family: str | None = Field(default=None, max_length=80)
    trust_state: TrustState = "draft"
    source: str = Field(default="admin", max_length=120)


class PublicProfileUpdate(BaseModel):
    slug: str | None = Field(default=None, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=280)
    avatar_url: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=120)
    social_links: dict[str, str | None] = Field(default_factory=dict)
    visibility: ProfileVisibility = "public"

    @field_validator("slug")
    @classmethod
    def clean_slug(cls, value: str | None) -> str | None:
        return normalize_slug(value) if value else None


class PublicProfile(BaseModel):
    user_id: int
    slug: str
    display_name: str
    bio: str | None
    avatar_url: str | None
    location: str | None
    social_links: dict[str, str | None]
    visibility: ProfileVisibility
    created_at: str
    updated_at: str
    viewer_blocked: bool = False


class PrinterPublicUpdate(BaseModel):
    public_profile_enabled: bool = False
    catalog_variant_id: int | None = Field(default=None, ge=1)
    public_name: str | None = Field(default=None, max_length=120)
    public_description: str | None = Field(default=None, max_length=500)
    public_mods: list[str] = Field(default_factory=list, max_length=20)
    public_images: list[str] = Field(default_factory=list, max_length=12)


class PublicPrinter(BaseModel):
    id: int
    owner_user_id: int
    owner_slug: str | None
    owner_display_name: str | None
    public_name: str
    public_description: str | None
    public_mods: list[str]
    public_images: list[str]
    catalog_variant_id: int
    manufacturer_name: str
    model_name: str
    variant_name: str
    variant_slug: str
    updated_at: str


class Community(BaseModel):
    id: int
    slug: str
    name: str
    scope: Literal["manufacturer", "model", "variant"]
    status: CommunityStatus
    manufacturer_id: int | None
    model_id: int | None
    variant_id: int | None
    member_count: int
    printer_count: int


class CommunityDetail(Community):
    members: list[PublicProfile] = Field(default_factory=list)
    printers: list[PublicPrinter] = Field(default_factory=list)


class RelationshipRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_user_id: int
    target_slug: str | None
    target_display_name: str | None
    relation_type: RelationshipType
    status: RelationshipStatus
    created_at: str
    updated_at: str


class RelationshipSummary(BaseModel):
    following: list[RelationshipRecord]
    followers: list[RelationshipRecord]
    friends: list[RelationshipRecord]
    blocked: list[RelationshipRecord]
    pending_friend_requests: list[RelationshipRecord]


@dataclass(frozen=True)
class SocialCatalogRepository:
    database_path: Path

    def list_catalog(self, *, include_blocked: bool = False, include_obsolete: bool = True) -> CatalogSummary:
        state_filter = _catalog_state_filter("trust_state", include_blocked, include_obsolete)
        with connect_database(self.database_path) as connection:
            manufacturers = connection.execute(
                f"""
                SELECT id, slug, name, trust_state, source
                FROM catalog_manufacturers
                WHERE {state_filter}
                ORDER BY name
                """
            ).fetchall()
            models = connection.execute(
                f"""
                SELECT id, manufacturer_id, slug, name, kinematics, trust_state, source
                FROM catalog_printer_models
                WHERE {state_filter}
                ORDER BY name
                """
            ).fetchall()
            variants = connection.execute(
                f"""
                SELECT id, model_id, slug, name, build_volume_json, components_json,
                       firmware_family, trust_state, source
                FROM catalog_printer_variants
                WHERE {state_filter}
                ORDER BY name
                """
            ).fetchall()
        variants_by_model: dict[int, list[CatalogVariant]] = {}
        for row in variants:
            variants_by_model.setdefault(int(row["model_id"]), []).append(_variant_from_row(row))
        models_by_manufacturer: dict[int, list[CatalogModel]] = {}
        for row in models:
            model = CatalogModel(
                id=int(row["id"]),
                slug=str(row["slug"]),
                name=str(row["name"]),
                kinematics=str(row["kinematics"]),
                trust_state=row["trust_state"],
                source=str(row["source"]),
                variants=variants_by_model.get(int(row["id"]), []),
            )
            models_by_manufacturer.setdefault(int(row["manufacturer_id"]), []).append(model)
        return CatalogSummary(
            manufacturers=[
                CatalogManufacturer(
                    id=int(row["id"]),
                    slug=str(row["slug"]),
                    name=str(row["name"]),
                    trust_state=row["trust_state"],
                    source=str(row["source"]),
                    models=models_by_manufacturer.get(int(row["id"]), []),
                )
                for row in manufacturers
            ]
        )

    def search_catalog_admin(
        self,
        *,
        manufacturer: str | None = None,
        model: str | None = None,
        variant: str | None = None,
        component: str | None = None,
        kinematics: str | None = None,
        firmware_family: str | None = None,
        trust_state: TrustState | None = None,
    ) -> CatalogAdminSummary:
        clauses = ["1 = 1"]
        parameters: list[object] = []
        like_filters = [
            ("mf.name || ' ' || mf.slug", manufacturer),
            ("m.name || ' ' || m.slug", model),
            ("v.name || ' ' || v.slug", variant),
            ("v.components_json", component),
            ("m.kinematics", kinematics),
            ("COALESCE(v.firmware_family, '')", firmware_family),
        ]
        for expression, value in like_filters:
            cleaned = clean_optional_text(value)
            if cleaned:
                clauses.append(f"LOWER({expression}) LIKE ?")
                parameters.append(f"%{cleaned.lower()}%")
        if trust_state:
            clauses.append("v.trust_state = ?")
            parameters.append(trust_state)
        else:
            clauses.append("v.trust_state != 'blocked'")
            clauses.append("m.trust_state != 'blocked'")
            clauses.append("mf.trust_state != 'blocked'")
        where_sql = " AND ".join(clauses)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT v.id, v.slug, v.name, v.build_volume_json, v.components_json,
                       v.firmware_family, v.trust_state, v.source,
                       m.id AS model_id, m.slug AS model_slug, m.name AS model_name, m.kinematics,
                       m.trust_state AS model_trust_state, m.website_url AS model_website_url,
                       m.repository_url AS model_repository_url, m.documentation_url AS model_documentation_url,
                       m.bom_url AS model_bom_url, m.description AS model_description,
                       mf.id AS manufacturer_id, mf.slug AS manufacturer_slug, mf.name AS manufacturer_name,
                       mf.website_url AS manufacturer_website_url,
                       mf.repository_url AS manufacturer_repository_url,
                       mf.documentation_url AS manufacturer_documentation_url
                FROM catalog_printer_variants v
                JOIN catalog_printer_models m ON m.id = v.model_id
                JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
                WHERE {where_sql}
                ORDER BY mf.name, m.name, v.name
                """,
                tuple(parameters),
            ).fetchall()
        models_by_id: dict[int, CatalogModelAdmin] = {}
        manufacturers: set[int] = set()
        variant_count = 0
        for row in rows:
            model_id = int(row["model_id"])
            manufacturers.add(int(row["manufacturer_id"]))
            if model_id not in models_by_id:
                models_by_id[model_id] = CatalogModelAdmin(
                    id=model_id,
                    slug=str(row["model_slug"]),
                    name=str(row["model_name"]),
                    kinematics=str(row["kinematics"]),
                    trust_state=row["model_trust_state"],
                    manufacturer_id=int(row["manufacturer_id"]),
                    manufacturer_slug=str(row["manufacturer_slug"]),
                    manufacturer_name=str(row["manufacturer_name"]),
                    manufacturer_website_url=clean_optional_text(row["manufacturer_website_url"]),
                    manufacturer_repository_url=clean_optional_text(row["manufacturer_repository_url"]),
                    manufacturer_documentation_url=clean_optional_text(row["manufacturer_documentation_url"]),
                    website_url=clean_optional_text(row["model_website_url"]),
                    repository_url=clean_optional_text(row["model_repository_url"]),
                    documentation_url=clean_optional_text(row["model_documentation_url"]),
                    bom_url=clean_optional_text(row["model_bom_url"]),
                    description=clean_optional_text(row["model_description"]),
                    variants=[],
                )
            models_by_id[model_id].variants.append(_variant_from_row(row))
            variant_count += 1
        models = list(models_by_id.values())
        return CatalogAdminSummary(
            models=models,
            manufacturer_count=len(manufacturers),
            model_count=len(models),
            variant_count=variant_count,
        )

    def create_manufacturer(self, payload: CatalogManufacturerCreate, actor_user_id: int) -> CatalogManufacturer:
        slug = normalize_slug(payload.slug or payload.name)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO catalog_manufacturers (slug, name, trust_state, source, created_by_user_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (slug, payload.name.strip(), payload.trust_state, payload.source.strip(), actor_user_id),
            )
            entity_id = int(cursor.lastrowid)
            self._audit(connection, "manufacturer", entity_id, "create", actor_user_id, payload.model_dump())
        return self._get_manufacturer(entity_id)

    def create_model(self, payload: CatalogModelCreate, actor_user_id: int) -> CatalogModel:
        slug = normalize_slug(payload.slug or payload.name)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO catalog_printer_models (
                    manufacturer_id, slug, name, kinematics, trust_state, source, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.manufacturer_id,
                    slug,
                    payload.name.strip(),
                    payload.kinematics.strip(),
                    payload.trust_state,
                    payload.source.strip(),
                    actor_user_id,
                ),
            )
            entity_id = int(cursor.lastrowid)
            self._audit(connection, "model", entity_id, "create", actor_user_id, payload.model_dump())
        return self._get_model(entity_id)

    def create_variant(self, payload: CatalogVariantCreate, actor_user_id: int) -> CatalogVariant:
        slug = normalize_slug(payload.slug or payload.name)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO catalog_printer_variants (
                    model_id, slug, name, build_volume_json, components_json,
                    firmware_family, trust_state, source, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.model_id,
                    slug,
                    payload.name.strip(),
                    json.dumps(payload.build_volume, ensure_ascii=False, sort_keys=True),
                    json.dumps(payload.components, ensure_ascii=False, sort_keys=True),
                    clean_optional_text(payload.firmware_family),
                    payload.trust_state,
                    payload.source.strip(),
                    actor_user_id,
                ),
            )
            entity_id = int(cursor.lastrowid)
            self._audit(connection, "variant", entity_id, "create", actor_user_id, payload.model_dump())
        return self._get_variant(entity_id)

    def update_variant(self, variant_id: int, payload: CatalogVariantUpdate, actor_user_id: int) -> CatalogVariant:
        updates: list[str] = []
        parameters: list[object] = []
        payload_dump = payload.model_dump(exclude_unset=True)
        if "name" in payload_dump and payload.name is not None:
            updates.append("name = ?")
            parameters.append(payload.name.strip())
        if "build_volume" in payload_dump and payload.build_volume is not None:
            updates.append("build_volume_json = ?")
            parameters.append(json.dumps(payload.build_volume, ensure_ascii=False, sort_keys=True))
        if "components" in payload_dump and payload.components is not None:
            updates.append("components_json = ?")
            parameters.append(json.dumps(payload.components, ensure_ascii=False, sort_keys=True))
        if "firmware_family" in payload_dump:
            updates.append("firmware_family = ?")
            parameters.append(clean_optional_text(payload.firmware_family))
        if "trust_state" in payload_dump and payload.trust_state is not None:
            updates.append("trust_state = ?")
            parameters.append(payload.trust_state)
        if "source" in payload_dump and payload.source is not None:
            updates.append("source = ?")
            parameters.append(payload.source.strip())
        if not updates:
            return self._get_variant(variant_id)
        updates.append("updated_at = CURRENT_TIMESTAMP")
        with connect_database(self.database_path) as connection:
            existing = connection.execute("SELECT id FROM catalog_printer_variants WHERE id = ?", (variant_id,)).fetchone()
            if existing is None:
                raise ValueError("variante de catálogo não encontrada")
            connection.execute(
                f"UPDATE catalog_printer_variants SET {', '.join(updates)} WHERE id = ?",
                (*parameters, variant_id),
            )
            self._audit(connection, "variant", variant_id, "update", actor_user_id, payload_dump)
        return self._get_variant(variant_id)

    def get_or_create_profile(self, user_id: int) -> PublicProfile:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM social_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                user = connection.execute(
                    "SELECT email, display_name FROM auth_users WHERE id = ?",
                    (user_id,),
                ).fetchone()
                if user is None:
                    raise ValueError("usuário não encontrado")
                display_name = clean_optional_text(user["display_name"]) or str(user["email"]).split("@")[0]
                slug = self._unique_slug(connection, display_name, user_id)
                connection.execute(
                    """
                    INSERT INTO social_profiles (user_id, slug, display_name)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, slug, display_name),
                )
                row = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
        return _profile_from_row(row)

    def update_profile(self, user_id: int, payload: PublicProfileUpdate) -> PublicProfile:
        with connect_database(self.database_path) as connection:
            current = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
            if current is None:
                self.get_or_create_profile(user_id)
                current = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
            slug = payload.slug or str(current["slug"])
            if slug != current["slug"]:
                reserved = connection.execute(
                    """
                    SELECT 1 FROM social_profile_slug_history
                    WHERE slug = ? AND user_id != ?
                    """,
                    (slug, user_id),
                ).fetchone()
                if reserved is not None:
                    raise ValueError("slug já usado anteriormente")
                connection.execute(
                    "INSERT OR IGNORE INTO social_profile_slug_history (user_id, slug) VALUES (?, ?)",
                    (user_id, current["slug"]),
                )
            connection.execute(
                """
                UPDATE social_profiles
                SET slug = ?, display_name = ?, bio = ?, avatar_url = ?, location = ?,
                    social_links_json = ?, visibility = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (
                    slug,
                    payload.display_name.strip(),
                    clean_optional_text(payload.bio),
                    clean_optional_text(payload.avatar_url),
                    clean_optional_text(payload.location),
                    json.dumps(_clean_social_links(payload.social_links), ensure_ascii=False, sort_keys=True),
                    payload.visibility,
                    user_id,
                ),
            )
            row = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
        return _profile_from_row(row)

    def public_profile_by_slug(self, slug: str, viewer_user_id: int | None = None) -> PublicProfile | None:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT * FROM social_profiles WHERE slug = ?", (clean_slug,)).fetchone()
            if row is None or row["visibility"] == "private":
                return None
            viewer_blocked = False
            if viewer_user_id is not None:
                viewer_blocked = self._is_blocked(connection, int(row["user_id"]), viewer_user_id)
        profile = _profile_from_row(row)
        return profile.model_copy(update={"viewer_blocked": viewer_blocked})

    def update_printer_public(self, printer_id: int, owner_user_id: int, payload: PrinterPublicUpdate) -> PublicPrinter | None:
        with connect_database(self.database_path) as connection:
            printer = connection.execute(
                "SELECT id, name, owner_user_id FROM printers WHERE id = ? AND owner_user_id = ?",
                (printer_id, owner_user_id),
            ).fetchone()
            if printer is None:
                return None
            if payload.public_profile_enabled and payload.catalog_variant_id is None:
                raise ValueError("impressora pública exige variante do catálogo")
            if payload.catalog_variant_id is not None:
                variant = connection.execute(
                    """
                    SELECT id FROM catalog_printer_variants
                    WHERE id = ? AND trust_state NOT IN ('blocked', 'obsolete')
                    """,
                    (payload.catalog_variant_id,),
                ).fetchone()
                if variant is None:
                    raise ValueError("variante de catálogo inválida para publicação")
            connection.execute(
                """
                UPDATE printers
                SET public_profile_enabled = ?, catalog_variant_id = ?, public_name = ?,
                    public_description = ?, public_mods_json = ?, public_images_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    1 if payload.public_profile_enabled else 0,
                    payload.catalog_variant_id,
                    clean_optional_text(payload.public_name) or str(printer["name"]),
                    clean_optional_text(payload.public_description),
                    json.dumps(clean_text_list(payload.public_mods, 80), ensure_ascii=False),
                    json.dumps(clean_text_list(payload.public_images, 500), ensure_ascii=False),
                    printer_id,
                ),
            )
            self.sync_communities_for_user(connection, owner_user_id)
        return self.public_printer(printer_id)

    def public_printer(self, printer_id: int) -> PublicPrinter | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(PUBLIC_PRINTER_SQL + " WHERE p.id = ? AND p.public_profile_enabled = 1", (printer_id,)).fetchone()
        return _public_printer_from_row(row) if row else None

    def list_public_printers_for_profile(self, slug: str) -> list[PublicPrinter]:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                PUBLIC_PRINTER_SQL
                + """
                WHERE sp.slug = ? AND sp.visibility != 'private' AND p.public_profile_enabled = 1
                ORDER BY p.updated_at DESC, p.id DESC
                """,
                (clean_slug,),
            ).fetchall()
        return [_public_printer_from_row(row) for row in rows]

    def list_communities(self) -> list[Community]:
        with connect_database(self.database_path) as connection:
            self.sync_all_communities(connection)
            rows = connection.execute(COMMUNITY_SQL + COMMUNITY_GROUP_SQL + " ORDER BY c.scope, c.name").fetchall()
        return [_community_from_row(row) for row in rows]

    def community_detail(self, slug: str) -> CommunityDetail | None:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            self.sync_all_communities(connection)
            row = connection.execute(COMMUNITY_SQL + " WHERE c.slug = ?" + COMMUNITY_GROUP_SQL, (clean_slug,)).fetchone()
            if row is None:
                return None
            member_rows = connection.execute(
                """
                SELECT sp.*
                FROM social_community_members cm
                JOIN social_profiles sp ON sp.user_id = cm.user_id
                WHERE cm.community_id = ? AND cm.active = 1 AND sp.visibility = 'public'
                GROUP BY sp.user_id
                ORDER BY sp.display_name
                """,
                (row["id"],),
            ).fetchall()
            printer_rows = connection.execute(
                PUBLIC_PRINTER_SQL
                + """
                JOIN social_community_members cm ON cm.printer_id = p.id
                WHERE cm.community_id = ? AND cm.active = 1 AND p.public_profile_enabled = 1
                ORDER BY p.updated_at DESC
                """,
                (row["id"],),
            ).fetchall()
        community = _community_from_row(row)
        return CommunityDetail(
            **community.model_dump(),
            members=[_profile_from_row(member_row) for member_row in member_rows],
            printers=[_public_printer_from_row(printer_row) for printer_row in printer_rows],
        )

    def set_relationship(self, actor_user_id: int, target_user_id: int, relation_type: RelationshipType, status: RelationshipStatus) -> RelationshipRecord:
        if actor_user_id == target_user_id:
            raise ValueError("relação consigo mesmo não é permitida")
        with connect_database(self.database_path) as connection:
            if relation_type != "block" and self._is_blocked(connection, actor_user_id, target_user_id):
                raise PermissionError("relação bloqueada por bloqueio social")
            if relation_type == "block":
                connection.execute(
                    """
                    UPDATE social_relationships
                    SET status = 'ended', ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
                      AND relation_type IN ('follow', 'friend')
                      AND status != 'ended'
                    """,
                    (actor_user_id, target_user_id, target_user_id, actor_user_id),
                )
            connection.execute(
                """
                INSERT INTO social_relationships (actor_user_id, target_user_id, relation_type, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(actor_user_id, target_user_id, relation_type) DO UPDATE SET
                    status = excluded.status,
                    ended_at = CASE WHEN excluded.status = 'ended' THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (actor_user_id, target_user_id, relation_type, status),
            )
        return self._relationship(actor_user_id, target_user_id, relation_type)

    def accept_friend(self, actor_user_id: int, requester_user_id: int) -> RelationshipRecord:
        with connect_database(self.database_path) as connection:
            pending = connection.execute(
                """
                SELECT 1 FROM social_relationships
                WHERE actor_user_id = ? AND target_user_id = ? AND relation_type = 'friend' AND status = 'pending'
                """,
                (requester_user_id, actor_user_id),
            ).fetchone()
            if pending is None:
                raise ValueError("solicitação de amizade não encontrada")
            connection.execute(
                """
                UPDATE social_relationships
                SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
                WHERE actor_user_id = ? AND target_user_id = ? AND relation_type = 'friend'
                """,
                (requester_user_id, actor_user_id),
            )
            connection.execute(
                """
                INSERT INTO social_relationships (actor_user_id, target_user_id, relation_type, status)
                VALUES (?, ?, 'friend', 'accepted')
                ON CONFLICT(actor_user_id, target_user_id, relation_type) DO UPDATE SET
                    status = 'accepted', ended_at = NULL, updated_at = CURRENT_TIMESTAMP
                """,
                (actor_user_id, requester_user_id),
            )
        return self._relationship(actor_user_id, requester_user_id, "friend")

    def relationship_summary(self, user_id: int) -> RelationshipSummary:
        with connect_database(self.database_path) as connection:
            outgoing = connection.execute(RELATIONSHIP_SQL + " WHERE r.actor_user_id = ? AND r.status != 'ended'", (user_id,)).fetchall()
            incoming = connection.execute(
                RELATIONSHIP_INCOMING_SQL + " WHERE r.target_user_id = ? AND r.status != 'ended'",
                (user_id,),
            ).fetchall()
        outgoing_records = [_relationship_from_row(row) for row in outgoing]
        incoming_records = [_relationship_from_row(row) for row in incoming]
        return RelationshipSummary(
            following=[item for item in outgoing_records if item.relation_type == "follow" and item.status == "active"],
            followers=[item for item in incoming_records if item.relation_type == "follow" and item.status == "active"],
            friends=[item for item in outgoing_records if item.relation_type == "friend" and item.status == "accepted"],
            blocked=[item for item in outgoing_records if item.relation_type == "block" and item.status == "active"],
            pending_friend_requests=[item for item in incoming_records if item.relation_type == "friend" and item.status == "pending"],
        )

    def sync_all_communities(self, connection) -> None:
        manufacturer_rows = connection.execute("SELECT id, slug, name FROM catalog_manufacturers WHERE trust_state != 'blocked'").fetchall()
        model_rows = connection.execute(
            """
            SELECT m.id, m.slug, m.name, mf.id AS manufacturer_id, mf.slug AS manufacturer_slug, mf.name AS manufacturer_name
            FROM catalog_printer_models m
            JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
            WHERE m.trust_state != 'blocked'
            """
        ).fetchall()
        variant_rows = connection.execute(
            """
            SELECT v.id, v.slug, v.name, m.id AS model_id, mf.id AS manufacturer_id,
                   m.slug AS model_slug, mf.slug AS manufacturer_slug
            FROM catalog_printer_variants v
            JOIN catalog_printer_models m ON m.id = v.model_id
            JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
            WHERE v.trust_state != 'blocked'
            """
        ).fetchall()
        for row in manufacturer_rows:
            self._upsert_community(connection, f"maker-{row['slug']}", str(row["name"]), "manufacturer", row["id"], None, None)
        for row in model_rows:
            self._upsert_community(connection, f"model-{row['manufacturer_slug']}-{row['slug']}", f"{row['manufacturer_name']} {row['name']}", "model", row["manufacturer_id"], row["id"], None)
        for row in variant_rows:
            self._upsert_community(connection, f"variant-{row['manufacturer_slug']}-{row['model_slug']}-{row['slug']}", str(row["name"]), "variant", row["manufacturer_id"], row["model_id"], row["id"])

    def sync_communities_for_user(self, connection, user_id: int) -> None:
        self.sync_all_communities(connection)
        connection.execute(
            """
            UPDATE social_community_members
            SET active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        rows = connection.execute(
            """
            SELECT p.id AS printer_id, v.id AS variant_id, m.id AS model_id, mf.id AS manufacturer_id
            FROM printers p
            JOIN catalog_printer_variants v ON v.id = p.catalog_variant_id
            JOIN catalog_printer_models m ON m.id = v.model_id
            JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
            WHERE p.owner_user_id = ? AND p.public_profile_enabled = 1
            """,
            (user_id,),
        ).fetchall()
        for row in rows:
            community_rows = connection.execute(
                """
                SELECT id FROM social_communities
                WHERE manufacturer_id = ?
                  AND (model_id IS NULL OR model_id = ?)
                  AND (variant_id IS NULL OR variant_id = ?)
                """,
                (row["manufacturer_id"], row["model_id"], row["variant_id"]),
            ).fetchall()
            for community in community_rows:
                connection.execute(
                    """
                    INSERT INTO social_community_members (community_id, user_id, printer_id, source, active)
                    VALUES (?, ?, ?, 'public_printer', 1)
                    ON CONFLICT(community_id, user_id, printer_id) DO UPDATE SET
                        active = 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (community["id"], user_id, row["printer_id"]),
                )

    def _upsert_community(self, connection, slug: str, name: str, scope: str, manufacturer_id: int | None, model_id: int | None, variant_id: int | None) -> None:
        connection.execute(
            """
            INSERT INTO social_communities (slug, name, scope, manufacturer_id, model_id, variant_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                status = CASE WHEN social_communities.status = 'merged' THEN social_communities.status ELSE 'active' END,
                updated_at = CURRENT_TIMESTAMP
            """,
            (slug, name, scope, manufacturer_id, model_id, variant_id),
        )

    def _relationship(self, actor_user_id: int, target_user_id: int, relation_type: RelationshipType) -> RelationshipRecord:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                RELATIONSHIP_SQL + " WHERE r.actor_user_id = ? AND r.target_user_id = ? AND r.relation_type = ?",
                (actor_user_id, target_user_id, relation_type),
            ).fetchone()
        if row is None:
            raise RuntimeError("relação social não persistida")
        return _relationship_from_row(row)

    def _unique_slug(self, connection, value: str, user_id: int) -> str:
        base = normalize_slug(value)
        slug = base
        suffix = 2
        while connection.execute("SELECT 1 FROM social_profiles WHERE slug = ? AND user_id != ?", (slug, user_id)).fetchone():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _is_blocked(self, connection, left_user_id: int, right_user_id: int) -> bool:
        row = connection.execute(
            """
            SELECT 1 FROM social_relationships
            WHERE relation_type = 'block'
              AND status = 'active'
              AND ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
            """,
            (left_user_id, right_user_id, right_user_id, left_user_id),
        ).fetchone()
        return row is not None

    def _audit(self, connection, entity_type: str, entity_id: int, action: str, actor_user_id: int, payload: dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO catalog_audit_events (entity_type, entity_id, action, actor_user_id, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entity_type, entity_id, action, actor_user_id, json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)),
        )

    def _get_manufacturer(self, entity_id: int) -> CatalogManufacturer:
        for manufacturer in self.list_catalog().manufacturers:
            if manufacturer.id == entity_id:
                return manufacturer
        raise RuntimeError("fabricante não persistido")

    def _get_model(self, entity_id: int) -> CatalogModel:
        for manufacturer in self.list_catalog().manufacturers:
            for model in manufacturer.models:
                if model.id == entity_id:
                    return model
        raise RuntimeError("modelo não persistido")

    def _get_variant(self, entity_id: int) -> CatalogVariant:
        for manufacturer in self.list_catalog(include_blocked=True).manufacturers:
            for model in manufacturer.models:
                for variant in model.variants:
                    if variant.id == entity_id:
                        return variant
        raise RuntimeError("variante não persistida")


PUBLIC_PRINTER_SQL = """
SELECT p.id, p.owner_user_id, sp.slug AS owner_slug, sp.display_name AS owner_display_name,
       COALESCE(p.public_name, p.name) AS public_name, p.public_description,
       p.public_mods_json, p.public_images_json, p.catalog_variant_id,
       mf.name AS manufacturer_name, m.name AS model_name, v.name AS variant_name,
       v.slug AS variant_slug, p.updated_at
FROM printers p
JOIN social_profiles sp ON sp.user_id = p.owner_user_id
JOIN catalog_printer_variants v ON v.id = p.catalog_variant_id
JOIN catalog_printer_models m ON m.id = v.model_id
JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
"""

COMMUNITY_SQL = """
SELECT c.id, c.slug, c.name, c.scope, c.status, c.manufacturer_id, c.model_id, c.variant_id,
       COUNT(DISTINCT CASE WHEN cm.active = 1 THEN cm.user_id END) AS member_count,
       COUNT(DISTINCT CASE WHEN cm.active = 1 THEN cm.printer_id END) AS printer_count
FROM social_communities c
LEFT JOIN social_community_members cm ON cm.community_id = c.id
"""

COMMUNITY_GROUP_SQL = """
GROUP BY c.id, c.slug, c.name, c.scope, c.status, c.manufacturer_id, c.model_id, c.variant_id
"""

RELATIONSHIP_SQL = """
SELECT r.target_user_id, sp.slug AS target_slug, sp.display_name AS target_display_name,
       r.relation_type, r.status, r.created_at, r.updated_at
FROM social_relationships r
LEFT JOIN social_profiles sp ON sp.user_id = r.target_user_id
"""

RELATIONSHIP_INCOMING_SQL = """
SELECT r.actor_user_id AS target_user_id, sp.slug AS target_slug, sp.display_name AS target_display_name,
       r.relation_type, r.status, r.created_at, r.updated_at
FROM social_relationships r
LEFT JOIN social_profiles sp ON sp.user_id = r.actor_user_id
"""


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = slug.strip("-")
    if not slug:
        raise ValueError("slug inválido")
    return slug[:80]


def clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def clean_text_list(values: list[str], max_length: int) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        cleaned.append(item[:max_length])
        seen.add(item)
    return cleaned


def _clean_social_links(values: dict[str, str | None]) -> dict[str, str | None]:
    allowed = {"website", "github", "instagram", "youtube", "x", "printables", "makerworld"}
    return {key: clean_optional_text(value) for key, value in values.items() if key in allowed}


def _json_dict(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _variant_from_row(row) -> CatalogVariant:
    return CatalogVariant(
        id=int(row["id"]),
        slug=str(row["slug"]),
        name=str(row["name"]),
        build_volume=_json_dict(row["build_volume_json"]),
        components=_json_dict(row["components_json"]),
        firmware_family=row["firmware_family"],
        trust_state=row["trust_state"],
        source=str(row["source"]),
    )


def _variant_detail_from_row(row) -> CatalogVariantDetail:
    variant = _variant_from_row(row)
    return CatalogVariantDetail(
        **variant.model_dump(),
        manufacturer_id=int(row["manufacturer_id"]),
        manufacturer_slug=str(row["manufacturer_slug"]),
        manufacturer_name=str(row["manufacturer_name"]),
        model_id=int(row["model_id"]),
        model_slug=str(row["model_slug"]),
        model_name=str(row["model_name"]),
        kinematics=str(row["kinematics"]),
    )


def _catalog_state_filter(column: str, include_blocked: bool, include_obsolete: bool) -> str:
    blocked = "1 = 1" if include_blocked else f"{column} != 'blocked'"
    obsolete = "1 = 1" if include_obsolete else f"{column} != 'obsolete'"
    return f"{blocked} AND {obsolete}"


def _profile_from_row(row) -> PublicProfile:
    return PublicProfile(
        user_id=int(row["user_id"]),
        slug=str(row["slug"]),
        display_name=str(row["display_name"]),
        bio=row["bio"],
        avatar_url=row["avatar_url"],
        location=row["location"],
        social_links={key: clean_optional_text(value) for key, value in _json_dict(row["social_links_json"]).items()},
        visibility=row["visibility"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _public_printer_from_row(row) -> PublicPrinter:
    return PublicPrinter(
        id=int(row["id"]),
        owner_user_id=int(row["owner_user_id"]),
        owner_slug=row["owner_slug"],
        owner_display_name=row["owner_display_name"],
        public_name=str(row["public_name"]),
        public_description=row["public_description"],
        public_mods=_json_list(row["public_mods_json"]),
        public_images=_json_list(row["public_images_json"]),
        catalog_variant_id=int(row["catalog_variant_id"]),
        manufacturer_name=str(row["manufacturer_name"]),
        model_name=str(row["model_name"]),
        variant_name=str(row["variant_name"]),
        variant_slug=str(row["variant_slug"]),
        updated_at=str(row["updated_at"]),
    )


def _community_from_row(row) -> Community:
    return Community(
        id=int(row["id"]),
        slug=str(row["slug"]),
        name=str(row["name"]),
        scope=row["scope"],
        status=row["status"],
        manufacturer_id=row["manufacturer_id"],
        model_id=row["model_id"],
        variant_id=row["variant_id"],
        member_count=int(row["member_count"] or 0),
        printer_count=int(row["printer_count"] or 0),
    )


def _relationship_from_row(row) -> RelationshipRecord:
    return RelationshipRecord(
        target_user_id=int(row["target_user_id"]),
        target_slug=row["target_slug"],
        target_display_name=row["target_display_name"],
        relation_type=row["relation_type"],
        status=row["status"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )
