from pathlib import Path
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.maintenance import (
    MaintenanceEventCreate,
    MaintenanceRepository,
    MaintenanceTaskComplete,
    MaintenanceTaskCreate,
)
from app.printers import PrinterCreate, PrinterRepository


def test_create_and_list_maintenance_events(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)

    event = repository.create_event(
        printer.id,
        MaintenanceEventCreate(
            event_type="maintenance",
            component="correias",
            title="Verificação de tensão",
            notes="Ajuste manual após inspeção.",
        ),
    )

    events = repository.list_events(printer.id)
    assert event.id == events[0].id
    assert events[0].component == "correias"
    assert events[0].title == "Verificação de tensão"


def test_maintenance_history_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Other", moonraker_url="http://other.local:7125"))
    repository = MaintenanceRepository(database_path)

    repository.create_event(first.id, MaintenanceEventCreate(title="Limpeza da mesa"))
    repository.create_event(second.id, MaintenanceEventCreate(title="Lubrificação"))

    assert [event.title for event in repository.list_events(first.id)] == ["Limpeza da mesa"]


def test_create_and_complete_preventive_task(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)
    task = repository.create_task(
        printer.id,
        MaintenanceTaskCreate(
            name="Lubrificar trilhos",
            component="motion",
            interval_days=30,
        ),
    )

    assert task.due_status == "due"
    event = repository.complete_task(task.id, MaintenanceTaskComplete(notes="Aplicado lubrificante leve."))
    updated = repository.get_task(task.id)

    assert event is not None
    assert event.title == "Lubrificar trilhos"
    assert updated is not None
    assert updated.last_done_at is not None
    assert updated.due_status == "ok"


def test_maintenance_summary_counts_due_and_recommendations(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)
    repository.create_task(
        printer.id,
        MaintenanceTaskCreate(
            name="Limpar mesa",
            component="bed",
            interval_days=7,
            last_done_at=(datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
        ),
    )

    summary = repository.summary(printer.id)

    assert summary.safe_mode == "local_only"
    assert summary.counts["due"] == 1
    assert summary.due_components == ["bed"]
    assert summary.next_due_task is not None
    assert all(task["name"] != "Limpar mesa" for task in summary.recommended_tasks)


def test_maintenance_task_can_be_due_soon(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)

    task = repository.create_task(
        printer.id,
        MaintenanceTaskCreate(
            name="Inspecionar fans",
            component="fans",
            interval_days=10,
            last_done_at=(datetime.now(timezone.utc) - timedelta(days=9)).isoformat(),
        ),
    )

    assert task.due_status == "soon"
    assert task.days_until_due == 1


def test_create_default_tasks_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)

    first = repository.create_default_tasks(printer.id)
    second = repository.create_default_tasks(printer.id)

    assert len(first) == 7
    assert second == []
    assert {task.component for task in first} == {"bed", "belts", "can", "fans", "frame", "hotend", "motion"}


def test_maintenance_summary_endpoint_is_local_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MAYDER_PRINT_LAB_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "mayderprintlab.db")
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

            defaults = client.post(f"/api/printers/{printer_id}/maintenance/tasks/defaults")
            summary = client.get(f"/api/printers/{printer_id}/maintenance/summary")

        assert defaults.status_code == 200
        assert len(defaults.json()["tasks"]) == 7
        assert summary.status_code == 200
        assert summary.json()["safe_mode"] == "local_only"
        assert summary.json()["counts"]["due"] == 7
    finally:
        get_settings.cache_clear()


def test_complete_missing_task_returns_none(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = MaintenanceRepository(database_path)

    assert repository.complete_task(999, MaintenanceTaskComplete()) is None
