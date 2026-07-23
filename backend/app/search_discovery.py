from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.database import connect_database, initialize_database
from app.modules.platform.database_target import uses_postgresql


SearchEntityType = Literal["community", "post", "library_item", "technical_config", "material_profile", "catalog_variant"]
SearchOrder = Literal["recent", "popular", "relevance"]


class SearchResult(BaseModel):
    entity_type: SearchEntityType
    entity_id: int
    title: str
    summary: str
    tags: list[str]
    community_slug: str | None = None
    community_name: str | None = None
    manufacturer_name: str | None = None
    model_name: str | None = None
    variant_name: str | None = None
    owner_slug: str | None = None
    owner_display_name: str | None = None
    material_type: str | None = None
    component: str | None = None
    license: str | None = None
    file_kind: str | None = None
    popularity_score: int
    updated_at: str
    url: str


class SearchFacetOption(BaseModel):
    value: str
    label: str
    count: int


class SearchFacets(BaseModel):
    entity_types: list[SearchFacetOption] = Field(default_factory=list)
    tags: list[SearchFacetOption] = Field(default_factory=list)
    communities: list[SearchFacetOption] = Field(default_factory=list)
    materials: list[SearchFacetOption] = Field(default_factory=list)
    components: list[SearchFacetOption] = Field(default_factory=list)
    licenses: list[SearchFacetOption] = Field(default_factory=list)
    file_kinds: list[SearchFacetOption] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    page: int
    page_size: int
    has_more: bool
    results: list[SearchResult]
    facets: SearchFacets
    indexed_count: int


class TagRecord(BaseModel):
    slug: str
    label: str
    status: str
    source: str


class SearchDiscoveryRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def ensure_schema(self) -> None:
        initialize_database(self.database_path)

    def rebuild_index(self) -> int:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            return self._rebuild_index(connection)

    def ensure_index_current(self) -> int:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            if uses_postgresql():
                return self._indexed_count(connection)
            source_signature = self._source_signature(connection)
            current_count = self._indexed_count(connection)
            if self._index_is_current(connection, source_signature):
                return current_count
            if current_count > 0 and not self._has_materialization_state(connection, "social_search_index"):
                self._record_materialization(connection, source_signature)
                return current_count
            if current_count == 0:
                return self._rebuild_index(connection, source_signature)
            return current_count

    def search(
        self,
        *,
        query: str = "",
        entity_type: SearchEntityType | None = None,
        tag: str | None = None,
        community: str | None = None,
        printer: str | None = None,
        component: str | None = None,
        material: str | None = None,
        license: str | None = None,
        file_kind: str | None = None,
        order: SearchOrder = "relevance",
        page: int = 1,
        page_size: int = 20,
        viewer_user_id: int | None = None,
    ) -> SearchResponse:
        indexed_count = self.ensure_index_current()
        page = max(page, 1)
        page_size = min(max(page_size, 1), 50)
        offset = (page - 1) * page_size
        postgresql = uses_postgresql()
        where, params = self._where(
            query=query,
            entity_type=entity_type,
            tag=tag,
            community=community,
            printer=printer,
            component=component,
            material=material,
            license=license,
            file_kind=file_kind,
            postgresql=postgresql,
            viewer_user_id=viewer_user_id,
        )
        if postgresql and order == "relevance" and query.strip():
            order_sql = "ts_rank_cd(idx.search_vector, websearch_to_tsquery('simple', ?)) DESC, idx.popularity_score DESC, idx.source_updated_at DESC"
            order_params: list[object] = [query.strip()]
        else:
            order_sql = {
                "popular": "idx.popularity_score DESC, idx.source_updated_at DESC",
                "recent": "idx.source_updated_at DESC, idx.popularity_score DESC",
                "relevance": "CASE WHEN lower(idx.title) LIKE ? THEN 0 ELSE 1 END, idx.popularity_score DESC, idx.source_updated_at DESC",
            }[order]
            order_params = [f"%{query.lower()}%"] if order == "relevance" else []
        search_table = "search_documents" if postgresql else "social_search_index"
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT idx.*, sc.slug AS community_slug, sc.name AS community_name,
                       cm.name AS manufacturer_name, cpm.name AS model_name, cpv.name AS variant_name,
                       sp.slug AS owner_slug, sp.display_name AS owner_display_name
                FROM {search_table} idx
                LEFT JOIN social_communities sc ON sc.id = idx.community_id
                LEFT JOIN catalog_printer_variants cpv ON cpv.id = idx.catalog_variant_id
                LEFT JOIN catalog_printer_models cpm ON cpm.id = cpv.model_id
                LEFT JOIN catalog_manufacturers cm ON cm.id = cpm.manufacturer_id
                LEFT JOIN social_profiles sp ON sp.user_id = idx.owner_user_id
                WHERE {where}
                ORDER BY {order_sql}
                LIMIT ? OFFSET ?
                """,
                (*params, *order_params, page_size + 1, offset),
            ).fetchall()
            facets = self._facets(connection, where, params, search_table)
        results = [_row_to_result(row) for row in rows[:page_size]]
        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            has_more=len(rows) > page_size,
            results=results,
            facets=facets,
            indexed_count=indexed_count,
        )

    def list_tags(self) -> list[TagRecord]:
        self.ensure_index_current()
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT slug, label, status, source FROM social_content_tags WHERE status != 'blocked' ORDER BY label"
            ).fetchall()
        return [TagRecord(slug=row["slug"], label=row["label"], status=row["status"], source=row["source"]) for row in rows]

    def curate_tag(self, slug: str, status: str, actor_user_id: int) -> TagRecord:
        if status not in {"active", "curated", "blocked"}:
            raise ValueError("estado de tag inválido")
        clean_slug = _slug(slug)
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT id, label FROM social_content_tags WHERE slug = ?", (clean_slug,)).fetchone()
            if row is None:
                raise ValueError("tag não encontrada")
            connection.execute(
                "UPDATE social_content_tags SET status = ?, source = 'curation', updated_at = CURRENT_TIMESTAMP WHERE slug = ?",
                (status, clean_slug),
            )
            connection.execute(
                """
                INSERT INTO catalog_audit_events (entity_type, entity_id, action, actor_user_id, payload_json)
                VALUES ('social_tag', ?, 'curate', ?, ?)
                """,
                (row["id"], actor_user_id, json.dumps({"slug": clean_slug, "status": status})),
            )
        return self.list_tags_by_slug(clean_slug)

    def list_tags_by_slug(self, slug: str) -> TagRecord:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT slug, label, status, source FROM social_content_tags WHERE slug = ?",
                (_slug(slug),),
            ).fetchone()
        if row is None:
            raise ValueError("tag não encontrada")
        return TagRecord(slug=row["slug"], label=row["label"], status=row["status"], source=row["source"])

    def _collect_rows(self, connection) -> list[tuple[object, ...]]:
        rows: list[tuple[object, ...]] = []
        rows.extend(_community_rows(connection))
        rows.extend(_post_rows(connection))
        rows.extend(_library_rows(connection))
        rows.extend(_technical_rows(connection))
        rows.extend(_material_rows(connection))
        rows.extend(_catalog_rows(connection))
        return rows

    def _rebuild_index(self, connection, source_signature: str | None = None) -> int:
        postgresql = uses_postgresql()
        search_table = "search_documents" if postgresql else "social_search_index"
        if not postgresql:
            connection.execute(f"DELETE FROM {search_table}")
            connection.execute("DELETE FROM social_content_tag_links")
        else:
            connection.execute("UPDATE search_documents SET is_active = false WHERE is_active = true")
        rows = self._collect_rows(connection)
        conflict_sql = (
            """
            ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                title = excluded.title, body = excluded.body, tags_json = excluded.tags_json,
                community_id = excluded.community_id, catalog_variant_id = excluded.catalog_variant_id,
                owner_user_id = excluded.owner_user_id, visibility = excluded.visibility,
                popularity_score = excluded.popularity_score, source_updated_at = excluded.source_updated_at,
                indexed_at = CURRENT_TIMESTAMP, is_active = true
            """
            if postgresql
            else ""
        )
        connection.executemany(
            f"""
            INSERT INTO {search_table} (
                entity_type, entity_id, title, body, tags_json, community_id,
                catalog_variant_id, owner_user_id, visibility, popularity_score, source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            {conflict_sql}
            """,
            rows,
        )
        self._sync_tags(connection, search_table)
        self._record_materialization(
            connection,
            source_signature or self._source_signature(connection),
            "search_documents" if uses_postgresql() else "social_search_index",
        )
        return len(rows)

    def _index_is_current(self, connection, source_signature: str) -> bool:
        row = connection.execute(
            """
            SELECT source_signature
            FROM social_materialization_state
            WHERE name = 'social_search_index'
            """
        ).fetchone()
        return row is not None and row["source_signature"] == source_signature

    def _has_materialization_state(self, connection, name: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM social_materialization_state WHERE name = ?",
            (name,),
        ).fetchone()
        return row is not None

    def _indexed_count(self, connection) -> int:
        table = "search_documents" if uses_postgresql() else "social_search_index"
        row = connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
        return int(row["total"] or 0)

    def _record_materialization(self, connection, source_signature: str, name: str = "social_search_index") -> None:
        connection.execute(
            """
            INSERT INTO social_materialization_state (name, source_signature, refreshed_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                source_signature = excluded.source_signature,
                refreshed_at = CURRENT_TIMESTAMP
            """,
            (name, source_signature),
        )

    def _source_signature(self, connection) -> str:
        rows = connection.execute(
            """
            SELECT source_name, COUNT(*) AS total, MAX(updated_at) AS newest
            FROM (
                SELECT 'community' AS source_name, updated_at
                FROM social_communities
                WHERE status IN ('active', 'uncurated')
                UNION ALL
                SELECT 'post' AS source_name, updated_at
                FROM social_feed_items
                WHERE visibility = 'public' AND deleted_at IS NULL
                UNION ALL
                SELECT 'library_item' AS source_name, updated_at
                FROM social_library_items
                WHERE status = 'active' AND visibility IN ('community', 'public')
                UNION ALL
                SELECT 'technical_config' AS source_name, updated_at
                FROM social_technical_printer_configs
                WHERE status = 'active' AND visibility IN ('community', 'public')
                UNION ALL
                SELECT 'material_profile' AS source_name, mp.updated_at
                FROM social_material_profiles mp
                JOIN social_slicing_profiles sl ON sl.material_profile_id = mp.id
                WHERE mp.status = 'active' AND mp.visibility IN ('community', 'public')
                UNION ALL
                SELECT 'catalog_variant' AS source_name, updated_at
                FROM catalog_printer_variants
                WHERE trust_state NOT IN ('blocked')
            )
            GROUP BY source_name
            ORDER BY source_name
            """
        ).fetchall()
        return json.dumps(
            [(row["source_name"], int(row["total"] or 0), row["newest"] or "") for row in rows],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _sync_tags(self, connection, search_table: str = "social_search_index") -> None:
        index_rows = connection.execute(f"SELECT entity_type, entity_id, tags_json FROM {search_table}").fetchall()
        for row in index_rows:
            for tag in json.loads(row["tags_json"] or "[]"):
                slug = _slug(tag)
                if not slug:
                    continue
                connection.execute(
                    """
                    INSERT INTO social_content_tags (slug, label, source)
                    VALUES (?, ?, 'index')
                    ON CONFLICT(slug) DO UPDATE SET label = excluded.label, updated_at = CURRENT_TIMESTAMP
                    """,
                    (slug, _label(tag)),
                )
                tag_row = connection.execute("SELECT id FROM social_content_tags WHERE slug = ?", (slug,)).fetchone()
                connection.execute(
                    """
                    INSERT OR IGNORE INTO social_content_tag_links (tag_id, entity_type, entity_id)
                    VALUES (?, ?, ?)
                    """,
                    (tag_row["id"], row["entity_type"], row["entity_id"]),
                )

    def _where(self, **filters) -> tuple[str, tuple[object, ...]]:
        postgresql = bool(filters.get("postgresql"))
        viewer_user_id = filters.get("viewer_user_id")
        if postgresql:
            clauses = ["idx.is_active = true", _postgresql_visibility_clause(viewer_user_id), _postgresql_canonical_clause()]
        else:
            clauses = ["idx.visibility IN ('public', 'community')"]
        params: list[object] = []
        if postgresql and viewer_user_id is not None:
            params.append(viewer_user_id)
        if postgresql and viewer_user_id is not None:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM social_relationships blocked WHERE blocked.relation_type = 'block' AND blocked.status = 'active' AND ((blocked.actor_user_id = ? AND blocked.target_user_id = idx.owner_user_id) OR (blocked.target_user_id = ? AND blocked.actor_user_id = idx.owner_user_id)))"
            )
            params.extend([viewer_user_id, viewer_user_id])
        query = filters.get("query", "").strip().lower()
        if query:
            if postgresql:
                clauses.append("idx.search_vector @@ websearch_to_tsquery('simple', ?)")
                params.append(query)
            else:
                like = f"%{query}%"
                clauses.append("(lower(idx.title) LIKE ? OR lower(idx.body) LIKE ? OR lower(idx.tags_json) LIKE ?)")
                params.extend([like, like, like])
        if filters.get("entity_type"):
            clauses.append("idx.entity_type = ?")
            params.append(filters["entity_type"])
        if filters.get("tag"):
            clauses.append("lower(idx.tags_json) LIKE ?")
            params.append(f"%{_slug(filters['tag'])}%")
        if filters.get("community"):
            clauses.append("sc.slug = ?")
            params.append(filters["community"])
        if filters.get("printer"):
            clauses.append("(lower(cm.name) LIKE ? OR lower(cpm.name) LIKE ? OR lower(cpv.name) LIKE ?)")
            like = f"%{filters['printer'].lower()}%"
            params.extend([like, like, like])
        prefixes = {"component": "component", "material": "material", "license": "license", "file_kind": "file"}
        for key, json_key in prefixes.items():
            value = filters.get(key)
            if value:
                clauses.append("lower(idx.tags_json) LIKE ?")
                params.append(f"%{_slug(f'{json_key}:{value}')}%")
        return " AND ".join(clauses), tuple(params)

    def _facets(self, connection, where: str, params: tuple[object, ...], search_table: str = "social_search_index") -> SearchFacets:
        rows = connection.execute(f"SELECT entity_type, tags_json, community_id FROM {search_table} idx LEFT JOIN social_communities sc ON sc.id = idx.community_id WHERE {where}", params).fetchall()
        entity_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}
        for row in rows:
            entity_counts[row["entity_type"]] = entity_counts.get(row["entity_type"], 0) + 1
            for tag in json.loads(row["tags_json"] or "[]"):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return SearchFacets(
            entity_types=_options(entity_counts),
            tags=_options(tag_counts, limit=30),
            materials=_options({tag: count for tag, count in tag_counts.items() if tag.startswith("material-")}, 20),
            components=_options({tag: count for tag, count in tag_counts.items() if tag.startswith("component-")}, 20),
            licenses=_options({tag: count for tag, count in tag_counts.items() if tag.startswith("license-")}, 20),
            file_kinds=_options({tag: count for tag, count in tag_counts.items() if tag.startswith("file-")}, 20),
        )


def _postgresql_visibility_clause(viewer_user_id: int | None) -> str:
    if viewer_user_id is None:
        return "idx.visibility = 'public'"
    return """
    (
        idx.visibility = 'public'
        OR (
            idx.visibility = 'community'
            AND idx.community_id IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM social_community_members membership
                WHERE membership.community_id = idx.community_id
                  AND membership.user_id = ?
                  AND membership.active = 1
            )
        )
    )
    """


def _postgresql_canonical_clause() -> str:
    return """
    (
        (idx.entity_type = 'community' AND EXISTS (
            SELECT 1 FROM social_communities source
            WHERE source.id = idx.entity_id AND source.status IN ('active', 'uncurated')
        ))
        OR (idx.entity_type = 'post' AND EXISTS (
            SELECT 1 FROM social_feed_items source
            WHERE source.id = idx.entity_id AND source.visibility = 'public' AND source.deleted_at IS NULL
        ))
        OR (idx.entity_type = 'library_item' AND EXISTS (
            SELECT 1 FROM social_library_items source
            WHERE source.id = idx.entity_id AND source.status = 'active'
              AND source.visibility = idx.visibility
              AND (source.content_class IN ('community', 'curated') OR source.commercial_status = 'approved')
        ))
        OR (idx.entity_type = 'technical_config' AND EXISTS (
            SELECT 1 FROM social_technical_printer_configs source
            WHERE source.id = idx.entity_id AND source.status = 'active' AND source.visibility = idx.visibility
        ))
        OR (idx.entity_type = 'material_profile' AND EXISTS (
            SELECT 1 FROM social_material_profiles source
            WHERE source.id = idx.entity_id AND source.status = 'active' AND source.visibility = idx.visibility
        ))
        OR (idx.entity_type = 'catalog_variant' AND EXISTS (
            SELECT 1 FROM catalog_printer_variants source
            WHERE source.id = idx.entity_id AND source.trust_state <> 'blocked'
        ))
    )
    """


def _community_rows(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        """
        SELECT sc.id, sc.name, sc.scope, sc.status, sc.updated_at, sc.variant_id,
               cm.name AS manufacturer_name, cpm.name AS model_name, cpv.name AS variant_name,
               sc.id AS community_id
        FROM social_communities sc
        LEFT JOIN catalog_manufacturers cm ON cm.id = sc.manufacturer_id
        LEFT JOIN catalog_printer_models cpm ON cpm.id = sc.model_id
        LEFT JOIN catalog_printer_variants cpv ON cpv.id = sc.variant_id
        WHERE sc.status IN ('active', 'uncurated')
        """
    ).fetchall()
    return [
        _index_row(
            "community",
            row["id"],
            row["name"],
            " ".join(str(row[key] or "") for key in ("scope", "status", "manufacturer_name", "model_name", "variant_name")),
            [f"printer:{row['manufacturer_name']}", f"model:{row['model_name']}", f"variant:{row['variant_name']}"],
            row["community_id"],
            row["variant_id"],
            None,
            "public",
            20,
            row["updated_at"],
        )
        for row in rows
    ]


def _post_rows(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        """
        SELECT fi.id, fi.community_id, fi.author_user_id, fi.title, fi.body, fi.content_type,
               fi.component, fi.material, fi.firmware_family, fi.problem_tag, fi.pinned,
               fi.updated_at,
               (SELECT COUNT(*) FROM social_discussion_comments c WHERE c.feed_item_id = fi.id AND c.deleted_at IS NULL) AS comment_count,
               (SELECT COUNT(*) FROM social_discussion_reactions r WHERE r.target_type = 'post' AND r.target_id = fi.id) AS reaction_count
        FROM social_feed_items fi
        WHERE fi.visibility = 'public' AND fi.deleted_at IS NULL
        """
    ).fetchall()
    return [
        _index_row(
            "post",
            row["id"],
            row["title"],
            row["body"],
            [row["content_type"], f"component:{row['component']}", f"material:{row['material']}", f"firmware:{row['firmware_family']}", f"problem:{row['problem_tag']}"],
            row["community_id"],
            None,
            row["author_user_id"],
            "public",
            int(row["pinned"] or 0) * 100 + int(row["comment_count"] or 0) * 3 + int(row["reaction_count"] or 0),
            row["updated_at"],
        )
        for row in rows
    ]


def _library_rows(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        """
        SELECT li.id, li.owner_user_id, li.community_id, li.catalog_variant_id, li.title, li.description,
               li.visibility, li.component, li.material_suggestion, li.license, li.updated_at,
               (SELECT COUNT(*) FROM social_library_downloads d WHERE d.item_id = li.id) AS download_count,
               (SELECT COUNT(*) FROM social_library_favorites fav WHERE fav.item_id = li.id) AS favorite_count,
               (SELECT group_concat(file_kind) FROM social_library_files lf WHERE lf.item_id = li.id) AS file_kinds
        FROM social_library_items li
        WHERE li.status = 'active' AND li.visibility IN ('community', 'public')
        """
    ).fetchall()
    return [
        _index_row(
            "library_item",
            row["id"],
            row["title"],
            row["description"],
            [f"component:{row['component']}", f"material:{row['material_suggestion']}", f"license:{row['license']}", *[f"file:{item}" for item in str(row["file_kinds"] or "").split(",") if item]],
            row["community_id"],
            row["catalog_variant_id"],
            row["owner_user_id"],
            row["visibility"],
            int(row["download_count"] or 0) + int(row["favorite_count"] or 0) * 5,
            row["updated_at"],
        )
        for row in rows
    ]


def _technical_rows(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        """
        SELECT id, owner_user_id, community_id, catalog_variant_id, title, notes, visibility,
               mods_json, components_json, calibrations_json, updated_at
        FROM social_technical_printer_configs
        WHERE status = 'active' AND visibility IN ('community', 'public')
        """
    ).fetchall()
    return [
        _index_row(
            "technical_config",
            row["id"],
            row["title"],
            row["notes"],
            [*json.loads(row["mods_json"] or "[]"), *[f"component:{key}" for key in json.loads(row["components_json"] or "{}").keys()], *[f"calibration:{key}" for key in json.loads(row["calibrations_json"] or "{}").keys()]],
            row["community_id"],
            row["catalog_variant_id"],
            row["owner_user_id"],
            row["visibility"],
            5,
            row["updated_at"],
        )
        for row in rows
    ]


def _material_rows(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        """
        SELECT mp.id, mp.owner_user_id, mp.community_id, mp.catalog_variant_id, mp.title, mp.notes,
               mp.visibility, mp.material_brand, mp.material_type, mp.nozzle_diameter_mm,
               mp.version_label, mp.compatibility_json, mp.updated_at, sl.goal
        FROM social_material_profiles mp
        JOIN social_slicing_profiles sl ON sl.material_profile_id = mp.id
        WHERE mp.status = 'active' AND mp.visibility IN ('community', 'public')
        """
    ).fetchall()
    return [
        _index_row(
            "material_profile",
            row["id"],
            row["title"],
            row["notes"],
            [f"material:{row['material_type']}", f"brand:{row['material_brand']}", f"nozzle:{row['nozzle_diameter_mm']}", f"goal:{row['goal']}", row["version_label"], *[f"compat:{key}" for key in json.loads(row["compatibility_json"] or "{}").keys()]],
            row["community_id"],
            row["catalog_variant_id"],
            row["owner_user_id"],
            row["visibility"],
            5,
            row["updated_at"],
        )
        for row in rows
    ]


def _catalog_rows(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        """
        SELECT cpv.id, cpv.name AS variant_name, cpv.components_json, cpv.firmware_family, cpv.trust_state,
               cpv.updated_at, cpm.name AS model_name, cm.name AS manufacturer_name
        FROM catalog_printer_variants cpv
        JOIN catalog_printer_models cpm ON cpm.id = cpv.model_id
        JOIN catalog_manufacturers cm ON cm.id = cpm.manufacturer_id
        WHERE cpv.trust_state NOT IN ('blocked')
        """
    ).fetchall()
    return [
        _index_row(
            "catalog_variant",
            row["id"],
            row["variant_name"],
            " ".join(str(row[key] or "") for key in ("manufacturer_name", "model_name", "firmware_family", "trust_state")),
            [f"printer:{row['manufacturer_name']}", f"model:{row['model_name']}", f"firmware:{row['firmware_family']}", *[f"component:{key}" for key in json.loads(row["components_json"] or "{}").keys()]],
            None,
            row["id"],
            None,
            "public",
            10,
            row["updated_at"],
        )
        for row in rows
    ]


def _index_row(entity_type: str, entity_id: int, title: str, body: str, tags: list[object], community_id, variant_id, owner_user_id, visibility, popularity, updated_at):
    clean_tags = sorted({_slug(str(tag)) for tag in tags if tag and str(tag).strip() and str(tag).lower() != "none"})
    return (
        entity_type,
        entity_id,
        title or "",
        body or "",
        json.dumps(clean_tags, ensure_ascii=False),
        community_id,
        variant_id,
        owner_user_id,
        visibility,
        popularity,
        updated_at,
    )


def _row_to_result(row) -> SearchResult:
    tags = json.loads(row["tags_json"] or "[]")
    summary = re.sub(r"\s+", " ", row["body"] or "").strip()[:220]
    return SearchResult(
        entity_type=row["entity_type"],
        entity_id=row["entity_id"],
        title=row["title"],
        summary=summary,
        tags=tags,
        community_slug=row["community_slug"],
        community_name=row["community_name"],
        manufacturer_name=row["manufacturer_name"],
        model_name=row["model_name"],
        variant_name=row["variant_name"],
        owner_slug=row["owner_slug"],
        owner_display_name=row["owner_display_name"],
        material_type=_first_tag_value(tags, "material-"),
        component=_first_tag_value(tags, "component-"),
        license=_first_tag_value(tags, "license-"),
        file_kind=_first_tag_value(tags, "file-"),
        popularity_score=row["popularity_score"],
        updated_at=row["source_updated_at"],
        url=_result_url(row),
    )


def _result_url(row) -> str:
    if row["entity_type"] == "community" and row["community_slug"]:
        return f"/c/{row['community_slug']}"
    if row["community_slug"]:
        return f"/c/{row['community_slug']}"
    if row["owner_slug"]:
        return f"/u/{row['owner_slug']}"
    return "/?section=social"


def _options(counts: dict[str, int], limit: int = 20) -> list[SearchFacetOption]:
    return [
        SearchFacetOption(value=value, label=_label(value), count=count)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
        if value
    ]


def _first_tag_value(tags: list[str], prefix: str) -> str | None:
    for tag in tags:
        if tag.startswith(prefix):
            value = tag.removeprefix(prefix)
            if value.lower() in {"none", "null", "na", "n-a"}:
                continue
            return _label(value)
    return None


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-")[:80]


def _label(value: str) -> str:
    return value.replace("-", " ").replace(":", ": ").strip().title()
