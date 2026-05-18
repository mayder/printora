from pathlib import Path

from app.backups import BackupPolicyCreate, BackupRepository
from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository


def test_create_backup_policy_and_dry_run(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    backup_repository = BackupRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )

    policy = backup_repository.create_policy(
        printer.id,
        BackupPolicyCreate(
            name="Configs",
            source_path="/home/pi/printer_data/config",
            destination_path="/home/pi/printer_data/backups/mayderprintlab",
        ),
    )
    run = backup_repository.create_dry_run(policy.id)

    assert policy.dry_run_only is True
    assert "secret" in " ".join(policy.exclude_patterns)
    assert run is not None
    assert run.status == "dry_run_planned"
    assert run.dry_run is True
    assert run.total_files == 0
    assert run.total_bytes == 0
    assert "Nenhum arquivo foi lido" in run.message


def test_backup_history_is_scoped_by_printer(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    backup_repository = BackupRepository(database_path)
    first = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    second = printer_repository.create_printer(
        PrinterCreate(name="Other", moonraker_url="http://other.local:7125")
    )

    first_policy = backup_repository.create_policy(first.id, BackupPolicyCreate(name="First"))
    second_policy = backup_repository.create_policy(second.id, BackupPolicyCreate(name="Second"))
    backup_repository.create_dry_run(first_policy.id)
    backup_repository.create_dry_run(second_policy.id)

    assert len(backup_repository.list_policies(first.id)) == 1
    assert len(backup_repository.list_runs(first.id)) == 1
    assert backup_repository.list_runs(first.id)[0].policy_id == first_policy.id


def test_execute_local_backup_creates_archive(tmp_path: Path) -> None:
    source = tmp_path / "config"
    source.mkdir()
    (source / "printer.cfg").write_text("[printer]\n", encoding="utf-8")
    (source / "moonraker.log").write_text("ignore\n", encoding="utf-8")
    (source / "api_token.txt").write_text("ignore\n", encoding="utf-8")
    destination = tmp_path / "backups"
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    backup_repository = BackupRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    policy = backup_repository.create_policy(
        printer.id,
        BackupPolicyCreate(
            name="Executable",
            source_path=str(source),
            destination_path=str(destination),
            dry_run_only=False,
        ),
    )

    run = backup_repository.execute_local_backup(policy.id)

    assert run is not None
    assert run.status == "completed"
    assert run.dry_run is False
    assert run.total_files == 1
    assert run.total_bytes == len("[printer]\n")
    assert len(list(destination.glob("*.zip"))) == 1


def test_execute_local_backup_is_blocked_for_dry_run_policy(tmp_path: Path) -> None:
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    backup_repository = BackupRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    policy = backup_repository.create_policy(printer.id, BackupPolicyCreate(name="Blocked"))

    run = backup_repository.execute_local_backup(policy.id)

    assert run is not None
    assert run.status == "blocked"
    assert run.dry_run is True
    assert "dry_run_only" in run.message


def test_execute_local_backup_rejects_destination_inside_source(tmp_path: Path) -> None:
    source = tmp_path / "config"
    source.mkdir()
    database_path = tmp_path / "mayderprintlab.db"
    initialize_database(database_path)
    printer_repository = PrinterRepository(database_path)
    backup_repository = BackupRepository(database_path)
    printer = printer_repository.create_printer(
        PrinterCreate(name="Voron", moonraker_url="http://voron.local:7125")
    )
    policy = backup_repository.create_policy(
        printer.id,
        BackupPolicyCreate(
            name="Invalid",
            source_path=str(source),
            destination_path=str(source / "backups"),
            dry_run_only=False,
        ),
    )

    run = backup_repository.execute_local_backup(policy.id)

    assert run is not None
    assert run.status == "failed"
    assert "Destino não pode" in run.message
