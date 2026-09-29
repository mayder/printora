#!/usr/bin/env python3
from __future__ import annotations

import json

from app.config import get_settings
from app.database import connect_database
from app.search_discovery import SearchDiscoveryRepository


TERMS = ("voron", "pla", "klipper")


def main() -> None:
    settings = get_settings()
    repository = SearchDiscoveryRepository(settings.database_path)
    comparisons: dict[str, dict[str, int]] = {}
    for term in TERMS:
        response = repository.search(query=term, page_size=50, viewer_user_id=None)
        top_ids = {(result.entity_type, result.entity_id) for result in response.results}
        with connect_database(settings.database_path) as connection:
            legacy = connection.execute(
                """
                SELECT entity_type, entity_id
                FROM social_search_index
                WHERE visibility IN ('public', 'community')
                  AND (lower(title) LIKE ? OR lower(body) LIKE ? OR lower(tags_json) LIKE ?)
                """,
                (f"%{term}%", f"%{term}%", f"%{term}%"),
            ).fetchall()
            fts = connection.execute(
                """
                SELECT entity_type, entity_id
                FROM search_documents
                WHERE is_active = true AND visibility = 'public'
                  AND search_vector @@ websearch_to_tsquery('simple', ?)
                """,
                (term,),
            ).fetchall()
        legacy_ids = {(str(row["entity_type"]), int(row["entity_id"])) for row in legacy}
        fts_ids = {(str(row["entity_type"]), int(row["entity_id"])) for row in fts}
        comparisons[term] = {
            "fts_total": len(fts_ids),
            "fts_top_count": len(top_ids),
            "legacy_like_count": len(legacy_ids),
            "overlap_count": len(fts_ids & legacy_ids),
        }

    with connect_database(settings.database_path) as connection:
        gin = connection.execute(
            "SELECT COUNT(*) AS total FROM pg_indexes WHERE tablename = 'search_documents' AND lower(indexdef) LIKE ?",
            ("%using gin%",),
        ).fetchone()
        inactive_visible = connection.execute(
            "SELECT COUNT(*) AS total FROM search_documents WHERE is_active = false AND is_active = true"
        ).fetchone()
        non_public_without_membership = connection.execute(
            "SELECT COUNT(*) AS total FROM search_documents WHERE is_active = true AND visibility <> 'public'"
        ).fetchone()
    if int(gin["total"]) != 1 or int(inactive_visible["total"]) != 0:
        raise RuntimeError("índice GIN ou filtro de geração inválido")
    print(
        json.dumps(
            {
                "status": "passed",
                "gin_index_count": int(gin["total"]),
                "inactive_visible": int(inactive_visible["total"]),
                "non_public_documents_require_membership": int(non_public_without_membership["total"]),
                "comparisons": comparisons,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
