from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.accessibility.catalog import SUPPORTED_STATES, build_catalog
from app.modules.accessibility.contracts import AccessibilityPreferenceValues
from app.modules.accessibility.repository import (
    AccessibilityPreferencesConflict,
    AccessibilityPreferencesRepository,
)


def test_catalog_has_complete_traceability_and_evidence() -> None:
    catalog = build_catalog()

    assert catalog.contract_version == "1.0.0"
    assert catalog.compatible_with == ("1.x",)
    assert [item.capability_id for item in catalog.capabilities] == [
        f"CAP-09-{number:02d}" for number in range(1, 9)
    ]
    assert [com_id for item in catalog.capabilities for com_id in item.com_ids] == [
        f"COM-{number:04d}" for number in range(449, 505)
    ]
    assert [item.screen_id for item in catalog.capabilities] == [
        f"SCR-{number:04d}" for number in range(65, 73)
    ]
    assert all(item.supported_states == SUPPORTED_STATES for item in catalog.capabilities)
    assert all(item.evidence for item in catalog.capabilities)


def test_repository_is_idempotent_and_detects_conflict(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user_id = _create_user(database_path, "accessibility-repository@example.test")
    repository = AccessibilityPreferencesRepository(database_path)
    values = AccessibilityPreferenceValues(theme="high-contrast", text_scale_percent=125)

    created = repository.save(user_id, values, expected_revision=0)
    repeated = repository.save(user_id, values, expected_revision=created.revision)
    updated = repository.save(
        user_id,
        AccessibilityPreferenceValues(theme="dark", text_scale_percent=150),
        expected_revision=created.revision,
    )

    assert created.revision == 1
    assert repeated == created
    assert updated.revision == 2
    with pytest.raises(AccessibilityPreferencesConflict):
        repository.save(user_id, values, expected_revision=1)


def test_schema_is_idempotent_and_rejects_invalid_values(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    initialize_database(database_path)
    user_id = _create_user(database_path, "accessibility-schema@example.test")

    with connect_database(database_path) as connection:
        with pytest.raises(Exception):
            connection.execute(
                """
                INSERT INTO accessibility_preferences(user_id, text_scale_percent)
                VALUES (?, 99)
                """,
                (user_id,),
            )


def test_api_requires_authentication_and_idempotency_key(
    tmp_path: Path,
    monkeypatch,
) -> None:
    with _client(tmp_path, monkeypatch) as client:
        assert client.get("/api/accessibility/v1/capabilities").status_code == 401
        assert client.get("/api/accessibility/v1/preferences").status_code == 401
        token = _register(client, "accessibility-auth@example.test")
        response = client.put(
            "/api/accessibility/v1/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"expected_revision": 0},
        )

    assert response.status_code == 422


def test_api_syncs_preferences_and_replays_same_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    with _client(tmp_path, monkeypatch) as client:
        token = _register(client, "accessibility-sync@example.test")
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "accessibility-sync-request-1",
        }
        payload = {
            "expected_revision": 0,
            "theme": "high-contrast",
            "text_scale_percent": 150,
            "reduce_motion": True,
            "simple_language": True,
        }
        created = client.put(
            "/api/accessibility/v1/preferences",
            headers=headers,
            json=payload,
        )
        replayed = client.put(
            "/api/accessibility/v1/preferences",
            headers=headers,
            json=payload,
        )
        loaded = client.get(
            "/api/accessibility/v1/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert created.status_code == 200
    assert created.headers["Idempotency-Status"] == "stored"
    assert created.json()["revision"] == 1
    assert replayed.headers["Idempotency-Status"] == "replayed"
    assert replayed.json() == created.json()
    assert loaded.json()["theme"] == "high-contrast"
    assert loaded.json()["text_scale_percent"] == 150


def test_api_isolates_users_and_rejects_stale_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    with _client(tmp_path, monkeypatch) as client:
        first_token = _register(client, "accessibility-first@example.test")
        second_token = _register(client, "accessibility-second@example.test")
        first_headers = {
            "Authorization": f"Bearer {first_token}",
            "Idempotency-Key": "accessibility-first-save",
        }
        assert client.put(
            "/api/accessibility/v1/preferences",
            headers=first_headers,
            json={"expected_revision": 0, "theme": "dark"},
        ).status_code == 200
        conflict = client.put(
            "/api/accessibility/v1/preferences",
            headers={
                "Authorization": f"Bearer {first_token}",
                "Idempotency-Key": "accessibility-stale-save",
            },
            json={"expected_revision": 0, "theme": "light"},
        )
        second = client.get(
            "/api/accessibility/v1/preferences",
            headers={"Authorization": f"Bearer {second_token}"},
        )

    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "preferências foram alteradas"
    assert second.json()["revision"] == 0
    assert second.json()["theme"] == "system"


def test_api_rejects_unknown_and_out_of_range_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    with _client(tmp_path, monkeypatch) as client:
        token = _register(client, "accessibility-validation@example.test")
        response = client.put(
            "/api/accessibility/v1/preferences",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "accessibility-invalid-save",
            },
            json={
                "expected_revision": 0,
                "text_scale_percent": 250,
                "user_id": 999,
            },
        )

    assert response.status_code == 422


@contextmanager
def _client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "correct-horse"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_user(database_path: Path, email: str) -> int:
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO auth_users(email, password_hash)
            VALUES (?, 'synthetic-hash')
            """,
            (email,),
        )
        return int(cursor.lastrowid)
