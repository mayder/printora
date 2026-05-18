from app.health import build_printer_health, build_unreachable_health
from app.snapshots import SnapshotDiff, SnapshotRecord


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
        proc_stats={"cpu_temp": 45.0},
        snapshots=[_snapshot(1)],
    )

    assert result["decision"] == "ok_para_imprimir"
    assert result["summary"] == "OK para imprimir"
    assert result["counts"]["blocker"] == 0


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
    assert result["items"][0]["key"] == "klipper_ready"


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
    assert result["decision"] == "nao_imprimir"
    assert result["counts"]["blocker"] == 1


def _snapshot(snapshot_id: int) -> SnapshotRecord:
    return SnapshotRecord(
        id=snapshot_id,
        printer_id=1,
        created_at="2026-05-18 12:00:00",
        snapshot_type="moonraker_status",
        summary={"klipper_state": "ready"},
    )
