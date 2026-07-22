from pathlib import Path
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import subprocess
import threading


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_systemd_service_points_to_installed_backend() -> None:
    service = (ROOT_DIR / "packaging/systemd/printora.service").read_text()

    assert "WorkingDirectory=/home/pi/Printora" in service
    assert "EnvironmentFile=-/home/pi/Printora/.env" in service
    assert "ExecStart=/home/pi/Printora/scripts/run_app.sh --foreground --no-open" in service


def test_linux_installers_configure_limited_sudoers_restart() -> None:
    raspberry_installer = (ROOT_DIR / "scripts" / "install_raspberry.sh").read_text()
    autostart_installer = (ROOT_DIR / "scripts" / "install_printora_autostart.sh").read_text()
    doctor = (ROOT_DIR / "scripts" / "doctor_install.sh").read_text()

    for text in (raspberry_installer, autostart_installer):
        assert "/etc/sudoers.d/printora-restart" in text
        assert "NOPASSWD" in text
        assert "restart printora.service" in text
        assert "status printora.service" in text
        assert "visudo -cf" in text

    assert "sudoers printora-restart ausente" in doctor


def test_moonraker_update_manager_snippet_is_non_empty() -> None:
    snippet = (ROOT_DIR / "packaging/moonraker/update_manager_printora.conf").read_text()

    assert "[update_manager printora]" in snippet
    assert "type: git_repo" in snippet
    assert "managed_services: printora" in snippet


def test_mainsail_navigation_links_to_local_service() -> None:
    navigation = (ROOT_DIR / "packaging/mainsail/navi.json").read_text()

    assert "Printora" in navigation
    assert "http://voron.local:8069" in navigation


def test_multiplatform_bootstrap_artifacts_exist() -> None:
    assert (ROOT_DIR / "scripts/mpl_platform.sh").is_file()
    assert (ROOT_DIR / "scripts/bootstrap_dev.sh").is_file()
    assert (ROOT_DIR / "scripts/bootstrap_windows.ps1").is_file()
    assert (ROOT_DIR / "scripts/run_app.sh").is_file()
    assert (ROOT_DIR / "scripts/run_app_windows.ps1").is_file()
    assert (ROOT_DIR / "Abrir Printora.command").is_file()
    assert (ROOT_DIR / "Abrir Printora.bat").is_file()
    assert (ROOT_DIR / "docs/INSTALL_MULTIPLATFORM.md").is_file()


def test_update_scripts_validate_running_version_after_restart() -> None:
    unix_script = (ROOT_DIR / "scripts/update_printora.sh").read_text()
    android_script = (ROOT_DIR / "scripts/android_update_printora.sh").read_text()
    windows_script = (ROOT_DIR / "scripts/update_printora_windows.ps1").read_text()

    assert "openapi.json" in unix_script
    assert "validate_running_version" in unix_script
    assert "processo antigo ainda responde" in unix_script
    assert "openapi.json" in android_script
    assert "validate_running_version" in android_script
    assert "openapi.json" in windows_script
    assert "Test-RunningVersion" in windows_script


def test_docker_compose_uses_safe_defaults() -> None:
    compose = (ROOT_DIR / "docker-compose.yml").read_text()

    assert "8069:8069" in compose
    assert "PRINTORA_HOST_AUDIT_MODE: \"disabled\"" in compose
    assert "PRINTORA_FIRMWARE_BUILD_MODE: \"disabled\"" in compose
    assert "printora-data:/data" in compose


def test_integration_validator_runs_offline() -> None:
    result = subprocess.run(
        ["bash", "scripts/validate_integration.sh"],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "validada em modo offline" in result.stdout


def test_cloud_blue_green_packaging_is_independent_and_fail_closed() -> None:
    service = (ROOT_DIR / "packaging/systemd/printora-cloud@.service").read_text()
    nginx = (ROOT_DIR / "packaging/nginx/print3dmaker.xyz.conf").read_text()
    deploy = (ROOT_DIR / "scripts/cloud/deploy-blue-green.sh").read_text()
    workflow = (ROOT_DIR / ".github/workflows/deploy-cloud.yml").read_text()

    assert "/slots/%i/venv/bin/python" in service
    assert "EnvironmentFile=/var/www/print3dmaker.xyz/shared/slots/%i.env" in service
    assert "LimitNOFILE=65536" in service
    assert "proxy_pass http://printora_cloud" in nginx
    assert "location = /metrics" in nginx
    assert "wait_until_ready" in deploy
    assert "switch_nginx_to_slot" in deploy
    assert "data_restored" not in deploy
    assert "shared/venv" not in workflow
    assert "RUN_PYTHON_TESTS: \"1\"" in workflow
    assert "RUN_FRONTEND_CHECKS: \"1\"" in workflow
    assert "printora-cloud-preflight" in workflow


def test_cloud_rollback_never_restores_database_snapshot() -> None:
    rollback = (ROOT_DIR / "scripts/cloud/rollback-blue-green.sh").read_text()

    assert "switch_nginx_to_slot" in rollback
    assert "data_restored=false" in rollback
    assert "sqlite" not in rollback.lower()
    assert "shutil" not in rollback.lower()
    assert "cp " not in rollback.lower()


def test_cloud_backup_has_external_restore_test_without_automatic_deletion() -> None:
    backup = (ROOT_DIR / "scripts/cloud/backup-sqlite.sh").read_text()
    bootstrap = (ROOT_DIR / "scripts/cloud/bootstrap-blue-green.sh").read_text()
    restore = (ROOT_DIR / "scripts/cloud/restore-backup-test.sh").read_text()
    timer = (ROOT_DIR / "packaging/systemd/printora-cloud-backup.timer").read_text()

    assert "restic backup" in backup
    assert "PRAGMA integrity_check" in backup
    assert "restic restore latest" in restore
    assert "aplicação não foi iniciada" in restore
    assert "forget" not in backup
    assert "prune" not in backup
    assert "Persistent=true" in timer
    assert "systemctl enable --now printora-cloud-backup.timer" in bootstrap


def test_postgresql_backup_is_encrypted_and_restored_in_isolated_cluster() -> None:
    backup = (ROOT_DIR / "scripts/cloud/backup-postgresql.sh").read_text()
    restore = (ROOT_DIR / "scripts/cloud/restore-postgresql-backup-test.sh").read_text()

    assert "pg_dump" in backup
    assert "pg_basebackup" in backup
    assert "--wal-method=stream" in backup
    assert "--serializable-deferrable" in backup
    assert "printora-cloud-postgresql" in backup
    assert "restic backup" in backup
    assert "backup-postgresql.sh" in (ROOT_DIR / "scripts/cloud/bootstrap-blue-green.sh").read_text()
    assert "forget" not in backup
    assert "prune" not in backup
    assert "base.tar.zst" in restore
    assert "recovery.signal" in restore
    assert "restore_command" in restore
    assert "checksum do dump divergente" in restore
    assert "aplicação não foi iniciada" in restore


def test_postgresql_bootstrap_uses_dedicated_checksummed_cluster() -> None:
    bootstrap = (ROOT_DIR / "scripts/cloud/bootstrap-postgresql.sh").read_text()
    config = (ROOT_DIR / "packaging/postgresql/printora.conf").read_text()
    sql = (ROOT_DIR / "backend/sql/postgresql/admin/000_cluster_bootstrap.sql").read_text()

    assert "--data-checksums" in bootstrap
    assert "5433" in bootstrap
    assert "archive_mode = on" in config
    assert "127.0.0.1" in config
    assert "CREATE ROLE printora_owner NOLOGIN" in sql
    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION" in sql
    assert "PostgreSQL dedicado" in bootstrap


def test_postgresql_cutover_locks_source_and_never_restores_snapshot() -> None:
    canary = (ROOT_DIR / "scripts/cloud/prepare-postgresql-canary.sh").read_text()
    cutover = (ROOT_DIR / "scripts/cloud/cutover-postgresql.py").read_text()

    assert "traffic_switched=false" in canary
    assert "PRINTORA_RUNTIME_PROFILE=cloud" in canary
    assert 'source.execute("BEGIN IMMEDIATE")' in cutover
    assert "catch_up_under_lock" in cutover
    assert "printora_transition_replication_state" in cutover
    assert "systemctl\", \"reload\", \"nginx" in cutover
    assert "data_restored=false" in cutover
    assert "snapshot" not in cutover.lower()


def test_cloud_load_smoke_reports_zero_errors() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            [
                "python3",
                "scripts/cloud/load-smoke.py",
                f"http://127.0.0.1:{server.server_port}/health",
                "--requests",
                "20",
                "--concurrency",
                "4",
            ],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        server.shutdown()
        server.server_close()
    report = json.loads(result.stdout)
    assert report["requests"] == 20
    assert report["error_count"] == 0
