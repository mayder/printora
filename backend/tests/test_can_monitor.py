from pathlib import Path

from fastapi.testclient import TestClient

from app.can_monitor import CanBusParseRequest, CanBusRecordCreate, CanMonitorRepository, parse_ip_link_can_output
from app.config import get_settings
from app.database import initialize_database
from app.main import app
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


def test_can_record_flags_problem_when_bus_state_is_stopped(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)

    record = repository.create_record(printer.id, CanBusRecordCreate(bus_state="STOPPED"))

    assert record.alert_level == "problema"
    assert record.diagnosis == "Estado CAN não está ativo: STOPPED."


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


def test_can_summary_reports_latest_interface_state(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)
    repository.create_record(printer.id, CanBusRecordCreate(interface_name="can0", tx_retries=2))
    repository.create_record(printer.id, CanBusRecordCreate(interface_name="can0", tx_retries=5))

    summary = repository.summary(printer.id)

    assert summary.safe_mode == "manual_read_only"
    assert summary.data_state == "manual_records"
    assert summary.source == "local_can_bus_records"
    assert summary.overall_alert == "monitorar"
    assert summary.interfaces[0].interface_name == "can0"
    assert summary.interfaces[0].delta_tx_retries == 3
    assert summary.recommended_actions


def test_can_summary_reports_no_data_explicitly(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)

    summary = repository.summary(printer.id)

    assert summary.safe_mode == "manual_read_only"
    assert summary.data_state == "no_data"
    assert summary.source == "local_can_bus_records"
    assert summary.interfaces == []
    assert summary.counts == {"ok": 0, "monitorar": 0, "problema": 0}


def test_can_records_can_be_compared_as_offline_session(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = CanMonitorRepository(database_path)
    before = repository.create_record(printer.id, CanBusRecordCreate(interface_name="can0", rx_error=0, tx_error=0, tx_retries=2))
    after = repository.create_record(printer.id, CanBusRecordCreate(interface_name="can0", rx_error=1, tx_error=0, tx_retries=5))

    comparison = repository.compare_records(printer.id, before.id, after.id)

    assert comparison.safe_mode == "manual_read_only_comparison"
    assert comparison.delta_rx_error == 1
    assert comparison.delta_tx_retries == 3
    assert comparison.alert_level == "problema"
    assert comparison.recommended_actions


def test_parse_ip_link_can_output_extracts_counters() -> None:
    output = """5: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1024
    link/can
    can state ERROR-ACTIVE restart-ms 0
          bitrate 1000000 sample-point 0.750
    RX: bytes  packets  errors  dropped missed  mcast
        1000   20       2       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
        900    18       1       0       0       0
    retries=7
"""

    parsed = parse_ip_link_can_output(CanBusParseRequest(interface_name="can1", output=output))

    assert parsed.interface_name == "can0"
    assert parsed.rx_error == 2
    assert parsed.tx_error == 1
    assert parsed.tx_retries == 7
    assert parsed.bus_state == "ERROR-ACTIVE"
    assert parsed.bitrate == 1000000


def test_can_endpoints_are_local_only_with_offline_printer(tmp_path, monkeypatch) -> None:
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

            first = client.post(
                f"/api/printers/{printer_id}/can/records",
                json={"interface_name": "can0", "rx_error": 0, "tx_error": 0, "tx_retries": 1},
            )
            assert first.status_code == 200
            record = client.post(
                f"/api/printers/{printer_id}/can/records",
                json={"interface_name": "can0", "rx_error": 0, "tx_error": 0, "tx_retries": 4},
            )
            summary = client.get(f"/api/printers/{printer_id}/can/summary")

        assert record.status_code == 200
        assert summary.status_code == 200
        assert summary.json()["safe_mode"] == "manual_read_only"
        assert summary.json()["counts"]["monitorar"] == 1
    finally:
        get_settings.cache_clear()
