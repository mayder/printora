from pathlib import Path

from app.database import initialize_database
from app.operation import build_operation_action_preview
from app.operation_history import OperationActionHistoryRepository
from app.printers import PrinterCreate, PrinterRepository


def test_operation_action_preview_history_persists_dry_run(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = OperationActionHistoryRepository(database_path)
    preview = build_operation_action_preview(
        action_id="move_z",
        parameters={"distance_mm": 2, "feedrate": 900},
        connected=False,
        print_state="",
    )

    record = repository.create_preview(printer.id, preview)
    records = repository.list_previews(printer.id)

    assert record.id == records[0].id
    assert records[0].action_id == "move_z"
    assert records[0].would_send_gcode is False
    assert records[0].executable is False
    assert records[0].command_preview == ["G91", "G0 Z2 F900", "G90"]
    assert records[0].payload["safe_mode"] == "dry_run_only"


def test_operation_action_preview_history_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron A", moonraker_url="http://a.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Voron B", moonraker_url="http://b.local:7125"))
    repository = OperationActionHistoryRepository(database_path)
    preview = build_operation_action_preview(action_id="home_xyz", parameters={}, connected=False, print_state="")

    repository.create_preview(first.id, preview)
    repository.create_preview(second.id, preview)

    assert len(repository.list_previews(first.id)) == 1
    assert repository.list_previews(first.id)[0].printer_id == first.id


def test_operation_execution_gate_persists_blocked_attempt(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = OperationActionHistoryRepository(database_path)
    preview = repository.create_preview(
        printer.id,
        build_operation_action_preview(action_id="home_xyz", parameters={}, connected=False, print_state=""),
    )

    attempt = repository.create_execution_attempt(
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase="CONFIRM_HOME_XYZ",
    )

    assert attempt.status == "blocked"
    assert attempt.confirmation_matched is True
    assert attempt.executable is False
    assert attempt.would_send_gcode is False
    assert attempt.block_reason == "Bloqueado: preview marcado como não executável."
    assert attempt.payload["rollback_plan"] == "Nenhum rollback necessário: a execução foi bloqueada antes de chamar Moonraker."


def test_operation_execution_gate_blocks_wrong_confirmation(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = OperationActionHistoryRepository(database_path)
    preview = repository.create_preview(
        printer.id,
        build_operation_action_preview(action_id="set_fan", parameters={"speed_percent": 20}, connected=False, print_state=""),
    )

    attempt = repository.create_execution_attempt(
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase="wrong",
    )

    assert attempt.confirmation_matched is False
    assert attempt.block_reason == "Bloqueado: frase de confirmação inválida."


def test_operation_execution_gate_records_offline_preflight(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = OperationActionHistoryRepository(database_path)
    preview = repository.create_preview(
        printer.id,
        build_operation_action_preview(action_id="move_z", parameters={"distance_mm": 2}, connected=False, print_state=""),
    )

    attempt = repository.create_execution_attempt(
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase="CONFIRM_MOVE_Z",
        preflight={"safe_mode": "read_only_preflight", "connected": False, "printing": False, "summary": "offline"},
    )

    assert attempt.block_reason == "Bloqueado: preflight sem leitura ao vivo do Moonraker."
    assert attempt.payload["preflight"]["connected"] is False
    assert attempt.payload["would_send_gcode"] is False


def test_operation_execution_gate_records_printing_preflight(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer = PrinterRepository(database_path).create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    repository = OperationActionHistoryRepository(database_path)
    preview = repository.create_preview(
        printer.id,
        build_operation_action_preview(action_id="home_xyz", parameters={}, connected=True, print_state="standby"),
    )

    attempt = repository.create_execution_attempt(
        printer_id=printer.id,
        preview=preview,
        confirmation_phrase="CONFIRM_HOME_XYZ",
        preflight={
            "safe_mode": "read_only_preflight",
            "connected": True,
            "printing": True,
            "print_state": "printing",
        },
    )

    assert attempt.block_reason == "Bloqueado: preflight detectou impressão em andamento."
    assert attempt.payload["preflight"]["print_state"] == "printing"


def test_operation_execution_attempts_are_listed_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    first = printer_repository.create_printer(PrinterCreate(name="Voron A", moonraker_url="http://a.local:7125"))
    second = printer_repository.create_printer(PrinterCreate(name="Voron B", moonraker_url="http://b.local:7125"))
    repository = OperationActionHistoryRepository(database_path)
    preview_a = repository.create_preview(
        first.id,
        build_operation_action_preview(action_id="home_xyz", parameters={}, connected=False, print_state=""),
    )
    preview_b = repository.create_preview(
        second.id,
        build_operation_action_preview(action_id="set_fan", parameters={"speed_percent": 20}, connected=False, print_state=""),
    )

    repository.create_execution_attempt(printer_id=first.id, preview=preview_a, confirmation_phrase="CONFIRM_HOME_XYZ")
    repository.create_execution_attempt(printer_id=second.id, preview=preview_b, confirmation_phrase="CONFIRM_SET_FAN")

    attempts = repository.list_execution_attempts(first.id)

    assert len(attempts) == 1
    assert attempts[0].printer_id == first.id
    assert attempts[0].action_id == "home_xyz"
