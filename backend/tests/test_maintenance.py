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
    database_path = tmp_path / "printora.db"
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
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Other", moonraker_url="http://other.local:7125"))
    repository = MaintenanceRepository(database_path)

    repository.create_event(first.id, MaintenanceEventCreate(title="Limpeza da mesa"))
    repository.create_event(second.id, MaintenanceEventCreate(title="Lubrificação"))

    assert [event.title for event in repository.list_events(first.id)] == ["Limpeza da mesa"]


def test_create_and_complete_preventive_task(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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


def test_delete_latest_task_event_removes_history_and_recalculates_last_done(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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

    first_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    second_date = datetime.now(timezone.utc).isoformat()
    first = repository.complete_task(task.id, MaintenanceTaskComplete(performed_at=first_date))
    second = repository.complete_task(task.id, MaintenanceTaskComplete(performed_at=second_date))

    assert first is not None
    assert second is not None
    deleted = repository.delete_latest_task_event(task.id)
    updated = repository.get_task(task.id)
    events = repository.list_events(printer.id)

    assert deleted is not None
    assert deleted.id == second.id
    assert updated is not None
    assert updated.last_done_at == first_date
    assert [event.id for event in events] == [first.id]


def test_delete_event_removes_history_and_clears_task_when_no_previous_event(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)
    task = repository.create_task(
        printer.id,
        MaintenanceTaskCreate(
            name="Limpar mesa",
            component="bed",
            interval_days=7,
        ),
    )
    event = repository.complete_task(task.id, MaintenanceTaskComplete())

    assert event is not None
    deleted = repository.delete_event(event.id)
    updated = repository.get_task(task.id)

    assert deleted is not None
    assert repository.list_events(printer.id) == []
    assert updated is not None
    assert updated.last_done_at is None
    assert updated.due_status == "due"


def test_maintenance_summary_counts_due_and_recommendations(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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
    database_path = tmp_path / "printora.db"
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


def test_print_hours_task_is_due_when_delta_reaches_interval(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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
            interval_kind="print_hours",
            interval_value=80,
            last_done_at=datetime.now(timezone.utc).isoformat(),
            last_done_print_hours=100,
        ),
    )
    repository.update_current_print_hours(printer.id, 181, read_at=datetime.now(timezone.utc).isoformat(), source="live")

    updated = repository.get_task(task.id)

    assert updated is not None
    assert updated.due_status == "due"
    assert updated.print_hours_delta == 81
    assert updated.print_hours_until_due == 0


def test_print_hours_task_without_baseline_is_not_validated(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)
    task = repository.create_task(
        printer.id,
        MaintenanceTaskCreate(
            name="Trocar bico",
            component="hotend",
            interval_kind="print_hours",
            interval_value=120,
            last_done_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    repository.update_current_print_hours(printer.id, 120, read_at=datetime.now(timezone.utc).isoformat(), source="live")

    updated = repository.get_task(task.id)

    assert updated is not None
    assert updated.due_status == "not_validated"


def test_print_hours_task_needs_review_when_current_is_lower_than_baseline(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)
    task = repository.create_task(
        printer.id,
        MaintenanceTaskCreate(
            name="Inspecionar correias",
            component="motion",
            interval_kind="print_hours",
            interval_value=80,
            last_done_at=datetime.now(timezone.utc).isoformat(),
            last_done_print_hours=200,
        ),
    )
    repository.update_current_print_hours(printer.id, 10, read_at=datetime.now(timezone.utc).isoformat(), source="live")

    updated = repository.get_task(task.id)

    assert updated is not None
    assert updated.due_status == "needs_review"


def test_complete_print_hours_task_saves_baseline_when_reading_is_available(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        async def fake_read_print_hours(_moonraker_url: str) -> float:
            return 42.5

        monkeypatch.setattr("app.main._read_printer_print_hours", fake_read_print_hours)
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://127.0.0.1:7125",
                    "host_audit_mode": "disabled",
                },
            )
            printer_id = created.json()["id"]
            task = client.post(
                f"/api/printers/{printer_id}/maintenance/tasks",
                json={
                    "name": "Lubrificar trilhos",
                    "component": "motion",
                    "interval_kind": "print_hours",
                    "interval_value": 80,
                },
            ).json()
            response = client.post(
                f"/api/maintenance/tasks/{task['id']}/complete",
                json={"next_interval_kind": "print_hours", "next_interval_value": 80},
            )
            tasks = client.get(f"/api/printers/{printer_id}/maintenance/tasks").json()["tasks"]

        assert response.status_code == 200
        assert tasks[0]["last_done_print_hours"] == 42.5
        assert tasks[0]["due_status"] == "ok"
    finally:
        get_settings.cache_clear()


def test_complete_print_hours_task_offline_is_blocked(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        async def fake_read_print_hours(_moonraker_url: str) -> None:
            return None

        monkeypatch.setattr("app.main._read_printer_print_hours", fake_read_print_hours)
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Offline",
                    "moonraker_url": "http://127.0.0.1:1",
                    "host_audit_mode": "disabled",
                },
            )
            printer_id = created.json()["id"]
            task = client.post(
                f"/api/printers/{printer_id}/maintenance/tasks",
                json={
                    "name": "Trocar bico",
                    "component": "hotend",
                    "interval_kind": "print_hours",
                    "interval_value": 120,
                },
            ).json()
            response = client.post(
                f"/api/maintenance/tasks/{task['id']}/complete",
                json={"next_interval_kind": "print_hours", "next_interval_value": 120},
            )
            tasks = client.get(f"/api/printers/{printer_id}/maintenance/tasks").json()["tasks"]

        assert response.status_code == 400
        assert tasks[0]["last_done_print_hours"] is None
        assert tasks[0]["due_status"] == "not_validated"
    finally:
        get_settings.cache_clear()


def test_print_hours_status_endpoint_reports_available_total(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        async def fake_read_print_hours(_moonraker_url: str) -> float:
            return 12.25

        monkeypatch.setattr("app.main._read_printer_print_hours", fake_read_print_hours)
        with TestClient(app) as client:
            created = client.post(
                "/api/printers",
                json={
                    "name": "Voron",
                    "moonraker_url": "http://127.0.0.1:7125",
                    "host_audit_mode": "disabled",
                },
            )
            printer_id = created.json()["id"]
            response = client.get(f"/api/printers/{printer_id}/maintenance/print-hours")

        assert response.status_code == 200
        payload = response.json()
        assert payload["available"] is True
        assert payload["total_print_hours"] == 12.25
    finally:
        get_settings.cache_clear()


def test_create_default_tasks_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)

    first = repository.create_default_tasks(printer.id)
    second = repository.create_default_tasks(printer.id)

    assert len(first) == 33
    assert second == []
    assert {task.component for task in first} == {
        "acessórios",
        "calibração",
        "elétrica",
        "estrutura",
        "extrusor",
        "filamento",
        "hotend",
        "mesa",
        "movimento",
        "refrigeração",
        "software",
    }


def test_default_tasks_expose_print_hours_recommendation_without_changing_fallback_days(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)

    tasks = repository.create_default_tasks(printer.id)
    mesh = next(task for task in tasks if task.name == "Refazer malha da mesa")
    cable = next(task for task in tasks if task.name == "Inspecionar conectores CAN/USB")

    assert mesh.interval_kind == "days"
    assert mesh.interval_value == 30
    assert mesh.recommended_interval_kind == "print_hours"
    assert mesh.recommended_interval_value == 200
    assert cable.recommended_interval_kind is None
    assert cable.recommended_interval_value is None


def test_recommended_print_hours_becomes_effective_only_with_live_reading(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = MaintenanceRepository(database_path)
    repository.create_default_tasks(printer.id)

    repository.update_current_print_hours(printer.id, 2140.8, read_at=datetime.now(timezone.utc).isoformat(), source="live")
    live_task = next(task for task in repository.list_tasks(printer.id) if task.name == "Inspecionar desgaste das correias")
    live_summary = repository.summary(printer.id)

    assert live_task.interval_kind == "print_hours"
    assert live_task.interval_value == 250
    assert live_task.due_status == "due"
    assert live_task.due_detail == "Primeira execução pendente."
    assert live_summary.counts["due"] == 33

    repository.update_current_print_hours(printer.id, None, read_at=datetime.now(timezone.utc).isoformat(), source="cached")
    cached_task = next(task for task in repository.list_tasks(printer.id) if task.name == "Inspecionar desgaste das correias")

    assert cached_task.interval_kind == "days"
    assert cached_task.interval_value == 60


def test_maintenance_summary_endpoint_is_local_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
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

            defaults = client.post(f"/api/printers/{printer_id}/maintenance/tasks/defaults")
            summary = client.get(f"/api/printers/{printer_id}/maintenance/summary")

        assert defaults.status_code == 200
        assert len(defaults.json()["tasks"]) == 33
        assert summary.status_code == 200
        assert summary.json()["safe_mode"] == "local_only"
        assert summary.json()["counts"]["due"] == 33
    finally:
        get_settings.cache_clear()


def test_complete_missing_task_returns_none(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = MaintenanceRepository(database_path)

    assert repository.complete_task(999, MaintenanceTaskComplete()) is None
