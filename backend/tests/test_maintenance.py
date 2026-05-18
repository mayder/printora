from pathlib import Path

from app.database import initialize_database
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


def test_complete_missing_task_returns_none(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = MaintenanceRepository(database_path)

    assert repository.complete_task(999, MaintenanceTaskComplete()) is None
