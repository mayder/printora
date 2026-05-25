from pathlib import Path
import subprocess


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_systemd_service_points_to_installed_backend() -> None:
    service = (ROOT_DIR / "packaging/systemd/printora.service").read_text()

    assert "WorkingDirectory=/home/pi/Printora" in service
    assert "EnvironmentFile=-/home/pi/Printora/.env" in service
    assert "ExecStart=/home/pi/Printora/scripts/run_app.sh --foreground --no-open" in service


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
