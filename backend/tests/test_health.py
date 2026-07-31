from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.health import build_printer_health, build_unreachable_health
from app.main import app
from app.snapshots import SnapshotDiff, SnapshotRecord, SnapshotRepository


def test_health_allows_ready_printer() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "moonraker_version": "v0.10.0",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={"disk": {"available": 17_000_000_000}},
        proc_stats={"cpu_temp": 45.0, "memory": {"total": 4_000_000_000, "available": 2_000_000_000}},
        snapshots=[_snapshot(1)],
        api_latency_ms=120,
    )

    assert result["decision"] == "ok_para_imprimir"
    assert result["summary"] == "OK para imprimir"
    assert result["counts"]["blocker"] == 0
    assert result["data_state"] == "live"
    assert result["metrics"]["api_latency_ms"] == 120
    assert result["metrics"]["memory_available_bytes"] == 2_000_000_000


def test_health_normalizes_real_moonraker_memory_kb_and_sd_info() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "moonraker_version": "v0.10.0",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={"system_info": {"sd_info": {"total_bytes": 31_914_983_424}}},
        proc_stats={"system_memory": {"total": 3_705_536, "available": 3_381_776, "used": 323_760}},
        snapshots=[_snapshot(1)],
        api_latency_ms=120,
    )

    assert result["metrics"]["memory_total_bytes"] == 3_705_536 * 1024
    assert result["metrics"]["memory_available_bytes"] == 3_381_776 * 1024
    assert result["metrics"]["disk_total_bytes"] == 31_914_983_424
    assert any(item["key"] == "disk_space" for item in result["items"])


def test_health_reports_disk_info_when_moonraker_has_unknown_sd_capacity() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "moonraker_version": "v0.10.0",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={"system_info": {"sd_info": {"total_bytes": 0}}},
        proc_stats={"system_memory": {"total": 1_996_660, "available": 1_681_220, "used": 315_440}},
        snapshots=[_snapshot(1)],
    )

    assert result["metrics"]["disk_total_bytes"] is None
    disk_item = next(item for item in result["items"] if item["key"] == "disk_space")
    assert disk_item["severity"] == "info"
    assert "não reportou" in disk_item["detail"]


def test_health_blocks_when_klipper_is_not_ready() -> None:
    result = build_printer_health(
        printer_info={"state": "error", "state_message": "config error"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[],
    )

    assert result["decision"] == "nao_imprimir"
    assert result["summary"] == "Não imprima ainda"
    assert any(item["key"] == "klipper_ready" and item["severity"] == "blocker" for item in result["items"])


def test_health_warns_on_deprecated_mcu_runtime_code() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[],
        runtime_alerts=[
            "Klipper warning MCU 'mcu' has deprecated code (it is missing feature 'i2c_transfer'). "
            "Recompiling and flashing is recommended."
        ],
        runtime_alerts_state="loaded",
    )

    runtime_alert = next(item for item in result["items"] if item["key"].startswith("klipper_runtime_"))
    assert result["decision"] == "monitorar"
    assert runtime_alert["severity"] == "warning"
    assert runtime_alert["title"] == "Firmware da MCU desatualizado"
    assert "i2c_transfer" in runtime_alert["detail"]
    assert "impressora parada" in runtime_alert["action"]


def test_health_blocks_on_critical_klipper_runtime_error() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[],
        runtime_alerts=["!! Lost communication with MCU 'head'"],
        runtime_alerts_state="loaded",
    )

    runtime_alert = next(item for item in result["items"] if item["key"].startswith("klipper_runtime_"))
    assert result["decision"] == "nao_imprimir"
    assert runtime_alert["severity"] == "blocker"
    assert runtime_alert["title"] == "Comunicação com MCU interrompida"


def test_health_reports_clean_runtime_alert_collection() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[],
        runtime_alerts=[],
        runtime_alerts_state="loaded",
    )

    runtime_item = next(item for item in result["items"] if item["key"] == "klipper_runtime_alerts")
    assert runtime_item["severity"] == "ok"
    assert runtime_item["ok"] is True


def test_health_warns_on_dirty_repo() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": True, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[],
    )

    assert result["decision"] == "monitorar"
    assert result["summary"] == "Pode imprimir com atenção"
    assert any(item["key"] == "update_manager" and item["severity"] == "warning" for item in result["items"])


def test_health_ignores_silenced_update_manager_version() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
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
        system_info={},
        proc_stats={},
        snapshots=[],
    )

    assert result["decision"] == "ok_para_imprimir"
    assert any(item["key"] == "update_manager" and item["severity"] == "ok" for item in result["items"])


def test_health_warns_but_does_not_block_on_slow_printora_network() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[_snapshot(1)],
        api_latency_ms=11_700,
    )

    latency = next(item for item in result["items"] if item["key"] == "api_latency")
    assert result["decision"] == "monitorar"
    assert latency["severity"] == "warning"
    assert "não a impressão" in latency["action"]


def test_health_blocks_on_latest_blocking_diff() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={},
        proc_stats={},
        snapshots=[_snapshot(2), _snapshot(1)],
        latest_diff=SnapshotDiff(
            printer_id=1,
            from_snapshot_id=1,
            to_snapshot_id=2,
            summary="Há mudança crítica. Revisar antes de imprimir.",
            highest_severity="bloqueio",
            changes=[],
        ),
    )

    assert result["decision"] == "nao_imprimir"
    assert any(item["key"] == "latest_snapshot_diff" and item["severity"] == "blocker" for item in result["items"])


def test_unreachable_health_blocks_printing() -> None:
    result = build_unreachable_health("http://voron.local:7125", "connection failed")

    assert result["connected"] is False
    assert result["data_state"] == "offline"
    assert result["decision"] == "nao_imprimir"
    assert result["counts"]["blocker"] == 1


def test_health_blocks_when_using_last_snapshot() -> None:
    result = build_printer_health(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
        system_info={"disk": {"available": 17_000_000_000}},
        proc_stats={"cpu_temp": 45.0},
        snapshots=[_snapshot(1)],
        data_state="last_snapshot",
        source="snapshot:1",
        error="connection failed",
    )

    assert result["connected"] is False
    assert result["decision"] == "nao_imprimir"
    assert result["items"][0]["key"] == "data_state"
    assert result["items"][0]["severity"] == "blocker"


def test_printer_health_uses_last_snapshot_when_moonraker_is_offline(tmp_path, monkeypatch) -> None:
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
                    "printer_info": {"state": "ready", "state_message": "Printer is ready"},
                    "server_info": {
                        "klippy_connected": True,
                        "klippy_state": "ready",
                        "failed_components": [],
                        "warnings": [],
                    },
                    "update_status": {
                        "version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}
                    },
                    "system_info": {"disk": {"available": 17_000_000_000}},
                    "proc_stats": {"cpu_temp": 45.0},
                },
            )

            response = client.get(f"/api/printers/{printer_id}/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["connected"] is False
        assert payload["data_state"] == "last_snapshot"
        assert payload["decision"] == "nao_imprimir"
        assert payload["source"].startswith("snapshot:")
    finally:
        get_settings.cache_clear()


def _snapshot(snapshot_id: int) -> SnapshotRecord:
    return SnapshotRecord(
        id=snapshot_id,
        printer_id=1,
        created_at="2026-05-18 12:00:00",
        snapshot_type="moonraker_status",
        summary={"klipper_state": "ready"},
    )
