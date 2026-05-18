from pathlib import Path

from app.can_monitor import CanBusRecordCreate, CanMonitorRepository
from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository


def test_create_first_can_record_without_delta(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)

    record = repository.create_record(
        printer.id,
        CanBusRecordCreate(interface_name="can0", rx_error=0, tx_error=0, tx_retries=0),
    )

    assert record.alert_level == "ok"
    assert record.previous_rx_error is None
    assert record.delta_tx_retries is None


def test_can_record_warns_when_retries_increase(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)
    repository.create_record(printer.id, CanBusRecordCreate(tx_retries=2))

    record = repository.create_record(printer.id, CanBusRecordCreate(tx_retries=5))

    assert record.previous_tx_retries == 2
    assert record.delta_tx_retries == 3
    assert record.alert_level == "monitorar"


def test_can_record_flags_problem_when_error_counter_increases(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)
    repository.create_record(printer.id, CanBusRecordCreate(rx_error=0, tx_error=0))

    record = repository.create_record(printer.id, CanBusRecordCreate(rx_error=1, tx_error=0))

    assert record.delta_rx_error == 1
    assert record.alert_level == "problema"


def test_can_history_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Other", moonraker_url="http://other.local:7125"))
    repository = CanMonitorRepository(database_path)

    repository.create_record(first.id, CanBusRecordCreate(tx_retries=1))
    repository.create_record(second.id, CanBusRecordCreate(tx_retries=7))

    assert len(repository.list_records(first.id)) == 1
    assert repository.list_records(first.id)[0].tx_retries == 1
