from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_systemd_service_points_to_installed_backend() -> None:
    service = (ROOT_DIR / "packaging/systemd/mayderprintlab.service").read_text()

    assert "WorkingDirectory=/home/pi/MayderPrintLab/backend" in service
    assert "EnvironmentFile=-/home/pi/MayderPrintLab/.env" in service
    assert "uvicorn app.main:app --host 0.0.0.0 --port 8085" in service


def test_moonraker_update_manager_snippet_is_non_empty() -> None:
    snippet = (ROOT_DIR / "packaging/moonraker/update_manager_mayderprintlab.conf").read_text()

    assert "[update_manager mayderprintlab]" in snippet
    assert "type: git_repo" in snippet
    assert "managed_services: mayderprintlab" in snippet


def test_mainsail_navigation_links_to_local_service() -> None:
    navigation = (ROOT_DIR / "packaging/mainsail/navi.json").read_text()

    assert "MayderPrintLab" in navigation
    assert "http://voron.local:8085" in navigation
