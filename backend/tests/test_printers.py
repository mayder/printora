from pathlib import Path

from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository, PrinterUpdate


def test_create_and_list_multiple_printers(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = PrinterRepository(database_path)

    first = repository.create_printer(
        PrinterCreate(
            name="Voron - Mayder",
            moonraker_url="http://voron.local:7125",
            host_audit_mode="ssh",
            host_audit_ssh_target="pi@voron.local",
        )
    )
    second = repository.create_printer(
        PrinterCreate(
            name="Mock local",
            moonraker_url="http://127.0.0.1:7125",
            host_audit_mode="disabled",
        )
    )

    printers = repository.list_printers()

    assert first.id != second.id
    assert [printer.name for printer in printers] == ["Mock local", "Voron - Mayder"]
    assert printers[1].moonraker_url == "http://voron.local:7125"


def test_update_printer_keeps_existing_values(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = PrinterRepository(database_path)
    created = repository.create_printer(
        PrinterCreate(
            name="Voron",
            moonraker_url="http://voron.local:7125",
            host_audit_mode="disabled",
        )
    )

    updated = repository.update_printer(created.id, PrinterUpdate(location="Bancada"))

    assert updated is not None
    assert updated.name == "Voron"
    assert updated.location == "Bancada"
    assert updated.host_audit_mode == "disabled"


def test_database_schema_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"

    initialize_database(database_path)
    initialize_database(database_path)
    repository = PrinterRepository(database_path)

    assert repository.list_printers() == []
