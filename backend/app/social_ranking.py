from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.database import connect_database, initialize_database
from app.search_discovery import SearchDiscoveryRepository, SearchEntityType, SearchResult


class RecommendationItem(BaseModel):
    result: SearchResult
    score: int
    reasons: list[str] = Field(default_factory=list)
    contributor_reputation: int = 0


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
    indexed_count: int
    scoring: dict[str, int]


class ReputationRecord(BaseModel):
    user_id: int
    slug: str | None = None
    display_name: str | None = None
    contribution_count: int
    reputation_score: int
    breakdown: dict[str, int]


class ReputationResponse(BaseModel):
    records: list[ReputationRecord]


class SocialRankingRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.search_repository = SearchDiscoveryRepository(database_path)

    def ensure_schema(self) -> None:
        initialize_database(self.database_path)

    def recommendations(
        self,
        *,
        query: str = "",
        community: str | None = None,
        material: str | None = None,
        component: str | None = None,
        entity_type: SearchEntityType | None = None,
        page_size: int = 12,
        viewer_user_id: int | None = None,
    ) -> RecommendationResponse:
        self.ensure_signals_current()
        search = self.search_repository.search(
            query=query,
            community=community,
            material=material,
            component=component,
            entity_type=entity_type,
            order="popular",
            page=1,
            page_size=min(max(page_size * 3, page_size), 50),
            viewer_user_id=viewer_user_id,
        )
        with connect_database(self.database_path) as connection:
            scored = [
                RecommendationItem(
                    result=item,
                    score=self._content_score(connection, item),
                    reasons=self._reasons(connection, item),
                    contributor_reputation=self._owner_reputation(connection, item.owner_slug),
                )
                for item in search.results
            ]
        scored.sort(key=lambda item: (-item.score, item.result.updated_at, item.result.title))
        return RecommendationResponse(
            items=scored[:page_size],
            indexed_count=search.indexed_count,
            scoring={"download": 2, "favorite": 4, "solution": 8, "reaction": 2, "report": -12},
        )

    def leaderboard(self, *, limit: int = 20) -> ReputationResponse:
        self.ensure_signals_current()
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT rs.user_id, sp.slug, sp.display_name, rs.contribution_count,
                       rs.reputation_score, rs.breakdown_json
                FROM social_user_reputation_snapshots rs
                LEFT JOIN social_profiles sp ON sp.user_id = rs.user_id
                WHERE rs.reputation_score > 0
                ORDER BY rs.reputation_score DESC, rs.contribution_count DESC, rs.user_id
                LIMIT ?
                """,
                (min(max(limit, 1), 50),),
            ).fetchall()
        return ReputationResponse(records=[_reputation_from_row(row) for row in rows])

    def profile_reputation(self, slug: str) -> ReputationRecord:
        self.ensure_signals_current()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT rs.user_id, sp.slug, sp.display_name, rs.contribution_count,
                       rs.reputation_score, rs.breakdown_json
                FROM social_profiles sp
                LEFT JOIN social_user_reputation_snapshots rs ON rs.user_id = sp.user_id
                WHERE sp.slug = ? AND sp.visibility IN ('public', 'unlisted')
                """,
                (slug,),
            ).fetchone()
        if row is None:
            raise ValueError("perfil não encontrado")
        if row["reputation_score"] is None:
            return ReputationRecord(user_id=row["user_id"], slug=row["slug"], display_name=row["display_name"], contribution_count=0, reputation_score=0, breakdown={})
        return _reputation_from_row(row)

    def rebuild_signals(self) -> None:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._rebuild_signals(connection)

    def ensure_signals_current(self) -> None:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            source_signature = self._source_signature(connection)
            signal_count = self._signal_count(connection)
            if self._signals_are_current(connection, source_signature):
                return
            has_state = self._has_materialization_state(connection, "social_quality_signals")
            if has_state:
                return
            if signal_count > 0:
                self._record_materialization(connection, source_signature)
                return
            if signal_count == 0:
                self._rebuild_signals(connection, source_signature)

    def _rebuild_signals(self, connection, source_signature: str | None = None) -> None:
        connection.execute("DELETE FROM social_quality_signals")
        self._library_download_signals(connection)
        self._library_favorite_signals(connection)
        self._solution_signals(connection)
        self._reaction_signals(connection)
        self._refresh_reputation(connection)
        self._record_materialization(connection, source_signature or self._source_signature(connection))

    def _signals_are_current(self, connection, source_signature: str) -> bool:
        row = connection.execute(
            """
            SELECT source_signature
            FROM social_materialization_state
            WHERE name = 'social_quality_signals'
            """
        ).fetchone()
        return row is not None and row["source_signature"] == source_signature

    def _has_materialization_state(self, connection, name: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM social_materialization_state WHERE name = ?",
            (name,),
        ).fetchone()
        return row is not None

    def _signal_count(self, connection) -> int:
        row = connection.execute("SELECT COUNT(*) AS total FROM social_quality_signals").fetchone()
        return int(row["total"] or 0)

    def _record_materialization(self, connection, source_signature: str) -> None:
        connection.execute(
            """
            INSERT INTO social_materialization_state (name, source_signature, refreshed_at)
            VALUES ('social_quality_signals', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                source_signature = excluded.source_signature,
                refreshed_at = CURRENT_TIMESTAMP
            """,
            (source_signature,),
        )

    def _source_signature(self, connection) -> str:
        rows = connection.execute(
            """
            SELECT source_name, COUNT(*) AS total, MAX(updated_at) AS newest
            FROM (
                SELECT 'download' AS source_name, d.created_at AS updated_at
                FROM social_library_downloads d
                JOIN social_library_items li ON li.id = d.item_id
                WHERE li.visibility IN ('community', 'public')
                  AND li.status = 'active'
                  AND (d.user_id IS NULL OR d.user_id != li.owner_user_id)
                UNION ALL
                SELECT 'favorite' AS source_name, fav.created_at AS updated_at
                FROM social_library_favorites fav
                JOIN social_library_items li ON li.id = fav.item_id
                WHERE li.visibility IN ('community', 'public')
                  AND li.status = 'active'
                  AND fav.user_id != li.owner_user_id
                UNION ALL
                SELECT 'solution' AS source_name, fi.updated_at
                FROM social_feed_items fi
                JOIN social_discussion_comments c ON c.id = fi.solution_comment_id
                WHERE fi.visibility = 'public'
                  AND fi.deleted_at IS NULL
                  AND c.deleted_at IS NULL
                UNION ALL
                SELECT 'reaction' AS source_name, r.created_at AS updated_at
                FROM social_discussion_reactions r
                JOIN social_feed_items fi ON fi.id = r.target_id AND r.target_type = 'post'
                WHERE fi.visibility = 'public'
                  AND fi.deleted_at IS NULL
                  AND r.user_id != fi.author_user_id
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

    def _content_score(self, connection, item: SearchResult) -> int:
        signal_score = connection.execute(
            """
            SELECT COALESCE(SUM(weight), 0) AS score
            FROM social_quality_signals
            WHERE entity_type = ? AND entity_id = ?
            """,
            (item.entity_type, item.entity_id),
        ).fetchone()["score"]
        return int(item.popularity_score or 0) + int(signal_score or 0) + self._owner_reputation(connection, item.owner_slug)

    def _owner_reputation(self, connection, owner_slug: str | None) -> int:
        if not owner_slug:
            return 0
        row = connection.execute(
            """
            SELECT rs.reputation_score
            FROM social_profiles sp
            JOIN social_user_reputation_snapshots rs ON rs.user_id = sp.user_id
            WHERE sp.slug = ?
            """,
            (owner_slug,),
        ).fetchone()
        return min(int(row["reputation_score"] or 0), 25) if row else 0

    def _reasons(self, connection, item: SearchResult) -> list[str]:
        rows = connection.execute(
            """
            SELECT signal_type, COUNT(*) AS count, COALESCE(SUM(weight), 0) AS weight
            FROM social_quality_signals
            WHERE entity_type = ? AND entity_id = ?
            GROUP BY signal_type
            ORDER BY weight DESC, count DESC
            """,
            (item.entity_type, item.entity_id),
        ).fetchall()
        reasons: list[str] = []
        for row in rows:
            signal_type = row["signal_type"]
            count = int(row["count"] or 0)
            weight = int(row["weight"] or 0)
            if signal_type == "download":
                reasons.append(f"{count} download(s) público(s)")
            elif signal_type == "favorite":
                reasons.append(f"{count} favorito(s) de outros usuários")
            elif signal_type == "solution":
                reasons.append("tem solução técnica marcada")
            elif signal_type == "reaction":
                reasons.append(f"{count} reação(ões) úteis")
            elif signal_type == "report" and weight < 0:
                reasons.append("exposição reduzida por denúncia")
        if item.community_name:
            reasons.append(f"relacionado à comunidade {item.community_name}")
        if item.material_type:
            reasons.append(f"compatível com material {item.material_type}")
        return reasons[:4] or ["conteúdo público compatível com os filtros"]

    def _library_download_signals(self, connection) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO social_quality_signals (
                entity_type, entity_id, signal_type, actor_user_id, target_user_id,
                source_table, source_id, weight, reason, created_at
            )
            SELECT 'library_item', li.id, 'download', d.user_id, li.owner_user_id,
                   'social_library_downloads', CAST(d.id AS TEXT),
                   CASE WHEN d.user_id IS NULL THEN 1 ELSE 2 END,
                   'download público por usuário diferente do autor', d.created_at
            FROM social_library_downloads d
            JOIN social_library_items li ON li.id = d.item_id
            WHERE li.visibility IN ('community', 'public')
              AND li.status = 'active'
              AND (d.user_id IS NULL OR d.user_id != li.owner_user_id)
            """
        )

    def _library_favorite_signals(self, connection) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO social_quality_signals (
                entity_type, entity_id, signal_type, actor_user_id, target_user_id,
                source_table, source_id, weight, reason, created_at
            )
            SELECT 'library_item', li.id, 'favorite', fav.user_id, li.owner_user_id,
                   'social_library_favorites', CAST(fav.user_id AS TEXT) || ':' || CAST(fav.item_id AS TEXT),
                   4, 'favorito de outro usuário', fav.created_at
            FROM social_library_favorites fav
            JOIN social_library_items li ON li.id = fav.item_id
            WHERE li.visibility IN ('community', 'public')
              AND li.status = 'active'
              AND fav.user_id != li.owner_user_id
            """
        )

    def _solution_signals(self, connection) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO social_quality_signals (
                entity_type, entity_id, signal_type, actor_user_id, target_user_id,
                source_table, source_id, weight, reason, created_at
            )
            SELECT 'post', fi.id, 'solution', c.author_user_id, c.author_user_id,
                   'social_feed_items', CAST(fi.id AS TEXT) || ':solution',
                   8, 'comentário marcado como solução', fi.updated_at
            FROM social_feed_items fi
            JOIN social_discussion_comments c ON c.id = fi.solution_comment_id
            WHERE fi.visibility = 'public'
              AND fi.deleted_at IS NULL
              AND c.deleted_at IS NULL
            """
        )

    def _reaction_signals(self, connection) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO social_quality_signals (
                entity_type, entity_id, signal_type, actor_user_id, target_user_id,
                source_table, source_id, weight, reason, created_at
            )
            SELECT 'post', fi.id, 'reaction', r.user_id, fi.author_user_id,
                   'social_discussion_reactions', CAST(r.id AS TEXT),
                   CASE r.reaction_type WHEN 'useful' THEN 3 WHEN 'thanks' THEN 2 ELSE 1 END,
                   'reação pública por usuário diferente do autor', r.created_at
            FROM social_discussion_reactions r
            JOIN social_feed_items fi ON fi.id = r.target_id AND r.target_type = 'post'
            WHERE fi.visibility = 'public'
              AND fi.deleted_at IS NULL
              AND r.user_id != fi.author_user_id
            """
        )

    def _refresh_reputation(self, connection) -> None:
        connection.execute("DELETE FROM social_user_reputation_snapshots")
        rows = connection.execute(
            """
            SELECT target_user_id, signal_type, COUNT(*) AS count, COALESCE(SUM(weight), 0) AS score
            FROM social_quality_signals
            WHERE target_user_id IS NOT NULL
            GROUP BY target_user_id, signal_type
            """
        ).fetchall()
        grouped: dict[int, dict[str, int]] = {}
        counts: dict[int, int] = {}
        for row in rows:
            user_id = int(row["target_user_id"])
            grouped.setdefault(user_id, {})[row["signal_type"]] = int(row["score"] or 0)
            counts[user_id] = counts.get(user_id, 0) + int(row["count"] or 0)
        for user_id, breakdown in grouped.items():
            score = max(0, sum(breakdown.values()))
            connection.execute(
                """
                INSERT INTO social_user_reputation_snapshots (
                    user_id, contribution_count, reputation_score, breakdown_json, updated_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, counts[user_id], score, json.dumps(breakdown, ensure_ascii=False)),
            )


def _reputation_from_row(row) -> ReputationRecord:
    return ReputationRecord(
        user_id=row["user_id"],
        slug=row["slug"],
        display_name=row["display_name"],
        contribution_count=int(row["contribution_count"] or 0),
        reputation_score=int(row["reputation_score"] or 0),
        breakdown=json.loads(row["breakdown_json"] or "{}"),
    )
