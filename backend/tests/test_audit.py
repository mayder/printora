from fastapi.testclient import TestClient

from app.audit import build_read_only_audit
from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.snapshots import SnapshotRepository


def test_read_only_audit_returns_info_when_no_issues() -> None:
    result = build_read_only_audit(
        printer_info={"state": "ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
    )

    assert result["safe_mode"] == "read_only"
    assert result["data_state"] == "live"
    assert result["source"] == "moonraker"
    assert result["counts"]["ignorar"] == 1
    assert result["summary"] == "Ambiente sem problemas críticos nos dados disponíveis."


def test_read_only_audit_blocks_when_klipper_is_not_ready() -> None:
    result = build_read_only_audit(
        printer_info={"state": "error", "state_message": "config error"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
    )

    assert result["counts"]["corrigir_agora"] == 1
    assert result["summary"] == "Há bloqueios. Não inicie nova impressão antes de corrigir."
    assert result["findings"][0]["id"] == "klipper_not_ready"


def test_read_only_audit_flags_dirty_repo() -> None:
    result = build_read_only_audit(
        printer_info={"state": "ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": True, "commits_behind_count": 0}}},
    )

    assert result["counts"]["monitorar"] == 1
    assert result["findings"][0]["id"] == "repo_klipper_needs_attention"


def test_read_only_audit_ignores_silenced_update_manager_version() -> None:
    result = build_read_only_audit(
        printer_info={"state": "ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={
            "version_info": {
                "klipper": {
                    "is_dirty": False,
                    "commits_behind_count": 2,
                    "printora_alert_silenced": True,
                }
            }
        },
    )

    assert result["counts"]["monitorar"] == 0
    assert result["summary"] == "Ambiente sem problemas críticos nos dados disponíveis."


def test_printer_read_only_audit_uses_last_snapshot_when_moonraker_is_offline(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_REQUEST_TIMEOUT_SECONDS", "0.05")
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
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
            printer_id = created.json()["id"]
            SnapshotRepository(tmp_path / "printora.db").create_snapshot(
                printer_id=printer_id,
                snapshot_type="moonraker_status",
                payload={
                    "printer_info": {"state": "ready", "software_version": "v0.13.0"},
                    "server_info": {"klippy_connected": True, "klippy_state": "ready"},
                    "update_status": {"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
                    "system_info": {},
                    "proc_stats": {},
                },
            )

            response = client.get(f"/api/printers/{printer_id}/audit/read-only")

        assert response.status_code == 200
        payload = response.json()
        assert payload["connected"] is False
        assert payload["data_state"] == "last_snapshot"
        assert payload["source"].startswith("snapshot:")
        assert payload["counts"]["ignorar"] == 1
    finally:
        get_settings.cache_clear()
