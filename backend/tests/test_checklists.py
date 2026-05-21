from fastapi.testclient import TestClient

from app.checklists import build_post_update_checklist, build_unavailable_post_update_checklist
from app.config import get_settings
from app.main import app


def test_post_update_checklist_allows_ready_printer() -> None:
    result = build_post_update_checklist(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
    )

    assert result["can_print"] is True
    assert result["summary"] == "Seguro imprimir após smoke manual"
    assert result["data_state"] == "live"
    assert any(item["severity"] == "manual" for item in result["items"])


def test_post_update_checklist_blocks_when_klipper_is_not_ready() -> None:
    result = build_post_update_checklist(
        printer_info={"state": "error", "state_message": "config error"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {}},
    )

    assert result["can_print"] is False
    assert result["summary"] == "Não imprima ainda"


def test_post_update_checklist_does_not_allow_last_snapshot_as_safe() -> None:
    result = build_post_update_checklist(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"moonraker": {"is_dirty": False, "commits_behind_count": 0}}},
        data_state="last_snapshot",
        source="snapshot:42",
    )

    assert result["can_print"] is False
    assert result["summary"] == "Não imprima ainda: usando último snapshot"
    assert result["source"] == "snapshot:42"


def test_post_update_checklist_reports_update_manager_warnings() -> None:
    result = build_post_update_checklist(
        printer_info={"state": "ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": True, "commits_behind_count": 2}}},
    )

    update_manager = next(item for item in result["items"] if item["key"] == "update_manager")
    assert result["can_print"] is True
    assert update_manager["ok"] is False
    assert update_manager["severity"] == "warning"
    assert update_manager["status"] == "warning"


def test_unavailable_post_update_checklist_blocks_printing() -> None:
    result = build_unavailable_post_update_checklist(
        data_state="offline",
        source="http://printer.local:7125",
        error="connection refused",
    )

    assert result["can_print"] is False
    assert result["summary"] == "Não imprima ainda: Moonraker offline"
    assert result["items"][0]["key"] == "moonraker_read"
    assert result["items"][0]["severity"] == "blocker"


def test_printer_post_update_checklist_returns_offline_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_REQUEST_TIMEOUT_SECONDS", "0.05")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Offline printer",
                    "moonraker_url": "http://127.0.0.1:1",
                    "host_audit_mode": "disabled",
                },
            )
            assert created.status_code == 200

            response = client.get(f"/api/printers/{created.json()['id']}/checklist/post-update")

        assert response.status_code == 200
        payload = response.json()
        assert payload["can_print"] is False
        assert payload["data_state"] == "offline"
        assert payload["items"][0]["severity"] == "blocker"
    finally:
        get_settings.cache_clear()
