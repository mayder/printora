from app.updates import (
    UpdateAlertSilenceRepository,
    UpdateAlertSilence,
    apply_update_alert_silences,
    build_update_status,
    risky_update_components,
    update_component_version_key,
    update_route_for_target,
)
from app.database import connect_database, initialize_database
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient


def test_build_update_status_detects_available_updates() -> None:
    result = build_update_status(
        {
            "version_info": {
                "klipper": {
                    "configured_type": "git_repo",
                    "version": "v0.13.0-438",
                    "remote_version": "v0.13.0-658",
                    "commits_behind_count": 220,
                    "is_dirty": False,
                    "is_valid": True,
                },
                "mainsail-config": {
                    "configured_type": "git_repo",
                    "version": "v1.2.1-1",
                    "remote_version": "v1.2.1-1",
                    "commits_behind_count": 0,
                    "is_dirty": False,
                    "is_valid": True,
                },
            }
        }
    )

    assert result.summary == "1 componente(s) com update disponível"
    assert result.counts["update_available"] == 1
    assert result.components[0].name == "klipper"
    assert result.components[0].status == "update_available"
    assert result.components[0].can_update is True
    assert result.components[0].risk_level == "high"
    assert result.components[0].requires_confirmation is True
    assert result.components[1].status == "up_to_date"
    assert result.components[1].can_update is False


def test_build_update_status_warns_on_dirty_or_invalid_component() -> None:
    result = build_update_status(
        {
            "version_info": {
                "custom": {
                    "configured_type": "git_repo",
                    "version": "v1",
                    "remote_version": "v1",
                    "is_dirty": True,
                    "warnings": ["repo dirty"],
                }
            }
        }
    )

    assert result.summary == "Há componentes com alerta"
    assert result.counts["warning"] == 1
    assert result.components[0].status == "warning"
    assert result.components[0].can_update is True


def test_update_route_for_target_uses_safe_moonraker_routes() -> None:
    assert update_route_for_target("all") == ("/machine/update/full", "all")
    assert update_route_for_target("system") == ("/machine/update/system", "system")
    assert update_route_for_target("klipper") == ("/machine/update/klipper", "klipper")
    assert update_route_for_target("mainsail") == ("/machine/update/client", "mainsail")


def test_build_update_status_exposes_rollback_when_moonraker_reports_previous_version() -> None:
    result = build_update_status(
        {
            "version_info": {
                "klipper": {
                    "configured_type": "git_repo",
                    "version": "v0.13.0-686",
                    "remote_version": "v0.13.0-686",
                    "rollback_version": "v0.13.0-662",
                    "commits_behind_count": 0,
                    "is_dirty": False,
                    "is_valid": True,
                }
            }
        }
    )

    assert result.components[0].status == "up_to_date"
    assert result.components[0].rollback_version == "v0.13.0-662"
    assert result.components[0].can_rollback is True


def test_risky_update_components_finds_high_risk_target_and_all_updates() -> None:
    result = build_update_status(
        {
            "version_info": {
                "klipper": {
                    "configured_type": "git_repo",
                    "version": "v0.13.0-662",
                    "remote_version": "v0.13.0-686",
                    "commits_behind_count": 24,
                    "is_dirty": False,
                    "is_valid": True,
                },
                "klipper-toolchanger-easy": {
                    "configured_type": "git_repo",
                    "version": "v0.0.0-250",
                    "remote_version": "v0.0.0-252",
                    "commits_behind_count": 2,
                    "is_dirty": False,
                    "is_valid": True,
                },
                "mainsail": {
                    "configured_type": "web",
                    "version": "v2.17.0",
                    "remote_version": "v2.17.1",
                    "commits_behind_count": 1,
                    "is_dirty": False,
                    "is_valid": True,
                },
            }
        }
    )

    assert [item.name for item in risky_update_components(result, "all")] == ["klipper", "klipper-toolchanger-easy"]
    assert [item.name for item in risky_update_components(result, "klipper")] == ["klipper"]
    assert risky_update_components(result, "mainsail") == []


def test_build_update_status_marks_silenced_component_without_counting_alert() -> None:
    raw_status = {
        "version_info": {
            "mainsail": {
                "configured_type": "web",
                "version": "v2.17.0",
                "remote_version": "v2.17.1",
                "commits_behind_count": 1,
                "is_dirty": False,
                "is_valid": True,
            }
        }
    }
    version_key = update_component_version_key("mainsail", raw_status["version_info"]["mainsail"])
    apply_update_alert_silences(
        raw_status,
        [
            UpdateAlertSilence(
                id=7,
                printer_id=1,
                component_name="mainsail",
                version_key=version_key,
                current_version="v2.17.0",
                remote_version="v2.17.1",
                full_version=None,
                reason=None,
                created_at="2026-05-26 00:00:00",
                updated_at="2026-05-26 00:00:00",
            )
        ],
    )

    result = build_update_status(raw_status)

    assert result.summary == "Updates silenciados"
    assert result.counts["update_available"] == 0
    assert result.counts["silenced"] == 1
    assert result.components[0].can_update is True
    assert result.components[0].alert_silenced is True
    assert result.components[0].alert_silence_id == 7


def test_update_silence_expires_when_remote_version_changes() -> None:
    old_payload = {"version": "v2.17.0", "remote_version": "v2.17.1", "commits_behind_count": 1}
    new_payload = {"version": "v2.17.0", "remote_version": "v2.17.2", "commits_behind_count": 2}

    assert update_component_version_key("mainsail", old_payload) != update_component_version_key("mainsail", new_payload)


def test_update_alert_silence_repository_persists_by_version_key(tmp_path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO printers (name, moonraker_url) VALUES (?, ?)",
            ("Voron", "http://voron.local:7125"),
        )
        printer_id = int(cursor.lastrowid)
    repository = UpdateAlertSilenceRepository(database_path)
    component = {
        "version": "v0.13.0-662",
        "remote_version": "v0.13.0-686",
        "commits_behind_count": 24,
    }

    silence = repository.silence_component(printer_id, "klipper", component, "aguardar próxima versão")

    assert silence.component_name == "klipper"
    assert silence.reason == "aguardar próxima versão"
    assert repository.get_matching(printer_id, "klipper", update_component_version_key("klipper", component)) is not None
    assert repository.delete_matching(printer_id, "klipper", silence.version_key) == 1
    assert repository.list_for_printer(printer_id) == []


def test_update_silence_routes_are_registered_and_unknown_api_post_returns_404(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        route_methods = {
            getattr(route, "path", ""): getattr(route, "methods", set())
            for route in app.routes
        }
        assert "POST" in route_methods["/api/printers/{printer_id}/updates/silences"]
        assert "POST" in route_methods["/api/printers/{printer_id}/updates/silences/clear"]

        with TestClient(app) as client:
            response = client.post("/api/route-that-does-not-exist", json={})

        assert response.status_code == 404
        assert response.json()["detail"] == "api route not found"
    finally:
        get_settings.cache_clear()


def test_update_silence_route_persists_displayed_version_without_moonraker_lookup(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        settings = get_settings()
        initialize_database(settings.database_path)
        with connect_database(settings.database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO printers (name, moonraker_url) VALUES (?, ?)",
                ("Voron", "http://unresolvable-printer.local:7125"),
            )
            printer_id = int(cursor.lastrowid)

        payload = {
            "target": "klipper",
            "current_version": "v0.13.0-662",
            "remote_version": "v0.13.0-686",
            "commits_behind_count": 24,
            "package_count": 0,
            "warnings": [],
            "anomalies": [],
            "reason": "aguardar próxima versão",
        }
        with TestClient(app) as client:
            response = client.post(f"/api/printers/{printer_id}/updates/silences", json=payload)

        assert response.status_code == 200
        assert response.json()["silenced"] is True
        repository = UpdateAlertSilenceRepository(settings.database_path)
        silences = repository.list_for_printer(printer_id)
        assert len(silences) == 1
        assert silences[0].component_name == "klipper"
        assert silences[0].current_version == "v0.13.0-662"
        assert silences[0].remote_version == "v0.13.0-686"
    finally:
        get_settings.cache_clear()
