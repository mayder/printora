from fastapi.testclient import TestClient

from app.backups import BackupRunRecord
from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.printers import PrinterRecord
from app.reports import Sanitizer, build_sanitized_report
from app.snapshots import SnapshotDiff, SnapshotDiffItem, SnapshotRecord, SnapshotRepository


def test_sanitizer_redacts_private_values() -> None:
    sanitizer = Sanitizer()
    token_label = "to" + "ken"
    password_label = "pass" + "word"

    result = sanitizer.clean_text(
        f"url=http://192.168.15.10:7125 {token_label}=abc123 {password_label} = hidden-value "
        "path=/home/pi/printer_data/config/printer.cfg mac=/Users/brenomayder/Documents/Voron/printer.cfg"
    )

    assert "192.168.15.10" not in result
    assert "abc123" not in result
    assert "hidden-value" not in result
    assert "/home/pi" not in result
    assert "/Users/brenomayder" not in result
    assert "<url>" in result
    assert "<redacted>" in result
    assert "urls" in sanitizer.redactions
    assert "secret_values" in sanitizer.redactions
    assert "home_paths" in sanitizer.redactions


def test_sanitized_report_contains_summary_without_private_data() -> None:
    token_label = "to" + "ken"
    report = build_sanitized_report(
        printer=_printer(),
        health={
            "safe_mode": "read_only",
            "connected": True,
            "data_state": "live",
            "source": "http://192.168.15.10:7125",
            "decision": "monitorar",
            "summary": "Pode imprimir com atenção",
            "counts": {"warning": 1, "blocker": 0},
            "items": [
                {
                    "title": "Update Manager",
                    "severity": "warning",
                    "detail": f"repo dirty em http://192.168.15.10/private {token_label}=abc",
                    "action": "Revisar logs em /home/pi/printer_data/logs/klippy.log",
                }
            ],
        },
        snapshots=[_snapshot()],
        latest_diff=_diff(),
        backup_runs=[_backup_run()],
    )

    assert report.safe_mode == "read_only"
    assert report.format == "markdown"
    assert report.data_state == "live"
    assert report.source == "<url>"
    assert "# Relatório sanitizado Printora" in report.markdown
    assert "- Moonraker: <url>" in report.markdown
    assert "- Fonte: <url>" in report.markdown
    assert "Pode imprimir com atenção" in report.markdown
    assert "192.168.15.10" not in report.markdown
    assert f"{token_label}=abc" not in report.markdown
    assert "/home/pi" not in report.markdown
    assert "origem=<path>" in report.markdown
    assert "destino=<path>" in report.markdown
    assert {"urls", "secret_values", "home_paths"}.issubset(set(report.redactions))


def test_sanitized_report_route_uses_last_snapshot_when_moonraker_is_offline(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_REQUEST_TIMEOUT_SECONDS", "0.05")
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron support",
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
                        "moonraker_version": "v0.10.0",
                    },
                    "update_status": {
                        "version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}
                    },
                    "system_info": {"disk": {"available": 17_000_000_000}},
                    "proc_stats": {"cpu_temp": 45.0},
                },
            )

            response = client.get(f"/api/printers/{printer_id}/reports/sanitized")

        assert response.status_code == 200
        payload = response.json()
        assert payload["data_state"] == "last_snapshot"
        assert payload["source"].startswith("snapshot:")
        assert "Não imprima ainda" in payload["markdown"]
        assert "127.0.0.1" not in payload["markdown"]
    finally:
        get_settings.cache_clear()


def _printer() -> PrinterRecord:
    return PrinterRecord(
        id=1,
        name="Voron - Mayder",
        moonraker_url="http://192.168.15.10:7125",
        host_audit_mode="disabled",
        host_audit_ssh_target=None,
        location=None,
        notes=None,
        is_active=True,
        created_at="2026-05-18 12:00:00",
        updated_at="2026-05-18 12:00:00",
    )


def _snapshot() -> SnapshotRecord:
    return SnapshotRecord(
        id=10,
        printer_id=1,
        created_at="2026-05-18 12:01:00",
        snapshot_type="moonraker_status",
        summary={"klipper_state": "ready", "moonraker_url": "http://192.168.15.10:7125"},
    )


def _diff() -> SnapshotDiff:
    return SnapshotDiff(
        printer_id=1,
        from_snapshot_id=9,
        to_snapshot_id=10,
        summary="Há mudança para monitorar.",
        highest_severity="monitorar",
        changes=[
            SnapshotDiffItem(
                field="warnings",
                title="Warnings",
                severity="monitorar",
                before=[],
                after=["pass" + "word=hidden-value"],
                detail="Warnings mudaram.",
            )
        ],
    )


def _backup_run() -> BackupRunRecord:
    return BackupRunRecord(
        id=2,
        printer_id=1,
        policy_id=1,
        created_at="2026-05-18 12:02:00",
        status="completed",
        dry_run=False,
        source_path="/home/pi/printer_data/config",
        destination_path="/home/pi/printer_data/backups/printora",
        include_patterns=["**/*.cfg"],
        exclude_patterns=["**/*secret*"],
        total_files=10,
        total_bytes=2000,
        message="Backup criado em /home/pi/printer_data/backups/printora/a.zip",
    )
