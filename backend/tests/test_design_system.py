from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.modules.design_system.catalog import SEMANTIC_TOKENS, SUPPORTED_STATES, build_catalog


def test_catalog_has_complete_non_overlapping_traceability() -> None:
    catalog = build_catalog()

    assert catalog.contract_version == "1.0.0"
    assert catalog.compatible_with == ("1.x",)
    assert len(catalog.capabilities) == 8
    assert [item.capability_id for item in catalog.capabilities] == [
        f"CAP-18-{number:02d}" for number in range(1, 9)
    ]
    assert [com_id for item in catalog.capabilities for com_id in item.com_ids] == [
        f"COM-{number:04d}" for number in range(953, 1009)
    ]
    assert [item.screen_id for item in catalog.capabilities] == [
        f"SCR-{number:04d}" for number in range(137, 145)
    ]
    assert all(item.supported_states == SUPPORTED_STATES for item in catalog.capabilities)


def test_catalog_is_read_only_and_tokens_are_semantic() -> None:
    catalog = build_catalog()

    assert catalog.permissions.can_view is True
    assert catalog.permissions.can_customize_local is True
    assert catalog.permissions.can_publish_global is False
    assert catalog.capabilities[0].tokens == SEMANTIC_TOKENS
    assert all(token.name.startswith("--ds-") for token in SEMANTIC_TOKENS)
    assert all(item.tokens == () for item in catalog.capabilities[1:])


def test_catalog_api_is_authenticated_and_versioned(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    initialize_database(tmp_path / "printora.db")
    try:
        with TestClient(app) as client:
            assert client.get("/api/design-system/v1/capabilities").status_code == 401
            registration = client.post(
                "/api/auth/register",
                json={"email": "design-reader@example.test", "password": "correct-horse"},
            )
            token = registration.json()["access_token"]
            response = client.get(
                "/api/design-system/v1/capabilities",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["contract_version"] == "1.0.0"
        assert len(response.content) < 64 * 1024
        assert response.json()["permissions"]["can_publish_global"] is False
    finally:
        get_settings.cache_clear()
