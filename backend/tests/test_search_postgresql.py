from pathlib import Path

from app.search_discovery import SearchDiscoveryRepository
from app.worker import _handlers


def test_postgresql_search_uses_fts_and_reapplies_permissions() -> None:
    repository = SearchDiscoveryRepository(Path("unused.db"))

    where, params = repository._where(
        query="voron gantry",
        postgresql=True,
        viewer_user_id=42,
    )

    assert "search_vector @@ websearch_to_tsquery" in where
    assert "social_community_members" in where
    assert "social_relationships" in where
    assert "social_library_items" in where
    assert "commercial_status = 'approved'" in where
    assert params == (42, 42, 42, "voron gantry")


def test_search_rebuild_has_durable_worker_handler() -> None:
    assert "search.rebuild" in _handlers()
