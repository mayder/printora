#!/usr/bin/env python3
from __future__ import annotations

import json
import time

from app.config import get_settings
from app.database import connect_database
from app.search_discovery import SearchDiscoveryRepository


def main() -> None:
    settings = get_settings()
    started = time.monotonic()
    indexed = SearchDiscoveryRepository(settings.database_path).rebuild_index()
    with connect_database(settings.database_path) as connection:
        rows = connection.execute(
            "SELECT entity_type, COUNT(*) AS total FROM search_documents WHERE is_active = true GROUP BY entity_type ORDER BY entity_type"
        ).fetchall()
        inactive = connection.execute("SELECT COUNT(*) AS total FROM search_documents WHERE is_active = false").fetchone()
    print(
        json.dumps(
            {
                "status": "passed",
                "indexed": indexed,
                "inactive_retained": int(inactive["total"] or 0),
                "by_type": {str(row["entity_type"]): int(row["total"]) for row in rows},
                "duration_seconds": round(time.monotonic() - started, 3),
                "source_deleted": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
