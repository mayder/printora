from pathlib import Path

from app.database import connect_database, initialize_database
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


def test_printer_ssh_access_is_stored_without_exposing_credential(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = PrinterRepository(database_path)

    created = repository.create_printer(
        PrinterCreate(
            name="Voron 0.2",
            moonraker_url="http://voron-02-pro.local:7125",
            ssh_host="voron-02-pro.local",
            ssh_port=2222,
            ssh_username="linaro",
            ssh_credential="linaro",
        )
    )

    assert created.host_audit_mode == "ssh"
    assert created.host_audit_ssh_target == "linaro@voron-02-pro.local"
    assert created.ssh_host == "voron-02-pro.local"
    assert created.ssh_port == 2222
    assert created.ssh_username == "linaro"
    assert created.ssh_credential_configured is True
    assert "ssh_credential" not in created.model_dump()

    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT credential_blob FROM printer_ssh_access WHERE printer_id = ?",
            (created.id,),
        ).fetchone()

    assert row is not None
    assert row["credential_blob"].startswith("v1:")
    assert row["credential_blob"] != "linaro"


def test_printer_ssh_access_can_be_updated_and_cleared(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    repository = PrinterRepository(database_path)
    created = repository.create_printer(
        PrinterCreate(
            name="Voron",
            moonraker_url="http://voron.local:7125",
            ssh_host="voron.local",
            ssh_username="pi",
            ssh_credential="pi",
        )
    )

    updated = repository.update_printer(
        created.id,
        PrinterUpdate(
            ssh_host="192.168.15.10",
            ssh_username="pi",
            clear_ssh_credential=True,
        ),
    )

    assert updated is not None
    assert updated.host_audit_mode == "ssh"
    assert updated.host_audit_ssh_target == "pi@192.168.15.10"
    assert updated.ssh_host == "192.168.15.10"
    assert updated.ssh_username == "pi"
    assert updated.ssh_credential_configured is False


def test_database_schema_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"

    initialize_database(database_path)
    initialize_database(database_path)
    repository = PrinterRepository(database_path)

    assert repository.list_printers() == []
