from pathlib import Path
import zipfile

from app.backups import (
    BackupArchiveCompareRequest,
    BackupPolicyCreate,
    BackupRepository,
    BackupRestoreExecuteRequest,
    BackupRestorePlanRequest,
    build_backup_restore_gate,
    build_backup_restore_plan,
    compare_backup_archives,
)
from app.database import initialize_database
from app.printers import PrinterCreate, PrinterRepository


def test_create_backup_policy_and_dry_run(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
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
            destination_path="/home/pi/printer_data/backups/printora",
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
    database_path = tmp_path / "printora.db"
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
    database_path = tmp_path / "printora.db"
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
    database_path = tmp_path / "printora.db"
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
    database_path = tmp_path / "printora.db"
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


def test_compare_backup_archives_is_read_only(tmp_path: Path) -> None:
    base = tmp_path / "base.zip"
    target = tmp_path / "target.zip"
    with zipfile.ZipFile(base, "w") as archive:
        archive.writestr("printer.cfg", "[printer]\n")
        archive.writestr("old.cfg", "old\n")
        archive.writestr("same.cfg", "same\n")
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("printer.cfg", "[printer]\nchanged\n")
        archive.writestr("same.cfg", "same\n")
        archive.writestr("new.cfg", "new\n")

    diff = compare_backup_archives(
        BackupArchiveCompareRequest(base_archive_path=str(base), target_archive_path=str(target))
    )

    assert diff.safe_mode == "local_zip_read_only"
    assert diff.added == ["new.cfg"]
    assert diff.removed == ["old.cfg"]
    assert diff.changed == ["printer.cfg"]
    assert diff.unchanged_count == 1


def test_restore_plan_is_blocked_and_does_not_extract_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "backup.zip"
    restore_root = tmp_path / "restore"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("printer.cfg", "[printer]\n")

    plan = build_backup_restore_plan(
        BackupRestorePlanRequest(
            archive_path=str(archive_path),
            restore_root=str(restore_root),
            files=["printer.cfg", "missing.cfg"],
        )
    )

    assert plan.safe_mode == "restore_dry_run_only"
    assert plan.blocked is True
    assert plan.selected_files == ["printer.cfg"]
    assert plan.missing_files == ["missing.cfg"]
    assert "unzip -p" in plan.planned_commands[-1]
    assert not restore_root.exists()


def test_restore_gate_accepts_confirmation_but_stays_blocked(tmp_path: Path) -> None:
    archive_path = tmp_path / "backup.zip"
    restore_root = tmp_path / "restore"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("printer.cfg", "[printer]\n")

    gate = build_backup_restore_gate(
        BackupRestoreExecuteRequest(
            archive_path=str(archive_path),
            restore_root=str(restore_root),
            files=["printer.cfg"],
            confirmation="BLOCK_REAL_RESTORE",
        )
    )

    assert gate.safe_mode == "restore_execution_gate_blocked"
    assert gate.accepted_confirmation is True
    assert gate.blocked is True
    assert gate.plan.blocked is True
    assert gate.plan.selected_files == ["printer.cfg"]
    assert any("Nenhum arquivo foi extraído" in item for item in gate.rollback_plan)
    assert not restore_root.exists()


def test_restore_gate_rejects_wrong_confirmation_without_extracting(tmp_path: Path) -> None:
    archive_path = tmp_path / "backup.zip"
    restore_root = tmp_path / "restore"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("printer.cfg", "[printer]\n")

    gate = build_backup_restore_gate(
        BackupRestoreExecuteRequest(
            archive_path=str(archive_path),
            restore_root=str(restore_root),
            files=["printer.cfg"],
            confirmation="wrong",
        )
    )

    assert gate.accepted_confirmation is False
    assert gate.blocked is True
    assert "Confirmação inválida" in gate.message
    assert not restore_root.exists()
