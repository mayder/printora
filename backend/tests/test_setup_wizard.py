from pathlib import Path

import pytest
from pydantic import ValidationError

from app.database import initialize_database
from app.setup_wizard import (
    SetupSshRunRepository,
    SetupSshTarget,
    build_setup_checks,
    build_setup_plan,
    split_sections,
)


SAMPLE_PREFLIGHT = """SECTION host
user=pi
uid=1000
groups=pi sudo
kernel=Linux btt-pi 6.1
arch=aarch64
home=/home/pi

SECTION os
PRETTY_NAME="Debian GNU/Linux 12"

SECTION tools
bash=present:/usr/bin/bash
git=present:/usr/bin/git
python3=present:/usr/bin/python3
make=missing
gcc=missing
curl=present:/usr/bin/curl
systemctl=present:/usr/bin/systemctl
ss=present:/usr/bin/ss
ip=present:/usr/sbin/ip
lsusb=present:/usr/bin/lsusb

SECTION services

SECTION paths
missing /home/pi/klipper
missing /home/pi/moonraker
missing /home/pi/mainsail
missing /home/pi/fluidd
missing /home/pi/printer_data
missing /home/pi/printer_data/config
missing /home/pi/Printora

SECTION can
Device "can0" does not exist.
"""


def test_split_sections_reads_setup_blocks() -> None:
    sections = split_sections(SAMPLE_PREFLIGHT)

    assert sections["host"].startswith("user=pi")
    assert "PRETTY_NAME" in sections["os"]
    assert "make=missing" in sections["tools"]


def test_setup_checks_classify_missing_dependencies_without_mutation() -> None:
    sections = split_sections(SAMPLE_PREFLIGHT)
    checks = build_setup_checks(0, sections)
    by_key = {check.key: check for check in checks}

    assert by_key["ssh"].status == "ok"
    assert by_key["base_tools"].status == "ok"
    assert by_key["build_tools"].status == "warning"
    assert by_key["klipper"].status == "warning"
    assert by_key["can0"].status == "warning"


def test_setup_plan_includes_boot_media_boundary_and_dry_run_commands() -> None:
    sections = split_sections(SAMPLE_PREFLIGHT)
    checks = build_setup_checks(0, sections)
    preflight = _preflight_response(sections, checks)

    plan = build_setup_plan(preflight)
    steps_by_key = {step.key: step for step in plan.steps}

    assert plan.safe_mode == "ssh_dry_run_plan"
    assert steps_by_key["prepare_os_media"].status == "manual"
    assert "Placa virgem não aceita SSH" in steps_by_key["prepare_os_media"].detail
    assert steps_by_key["install_klipper"].status == "missing"
    assert all(command.command.startswith("PLAN ") for step in plan.steps for command in step.commands)
    assert not any("flash" in command.command.lower() for step in plan.steps for command in step.commands if step.key != "firmware_next")


def test_ssh_target_rejects_shell_injection_parts() -> None:
    with pytest.raises(ValidationError):
        SetupSshTarget(host="printer.local;rm -rf /", username="pi")


def test_setup_history_does_not_store_key_path(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SetupSshRunRepository(database_path)
    target = SetupSshTarget(host="btt-pi.local", username="pi", auth_method="key_path", key_path="/home/user/.ssh/id_ed25519")
    sections = split_sections(SAMPLE_PREFLIGHT)
    checks = build_setup_checks(0, sections)
    preflight = _preflight_response(sections, checks)

    history_id = repository.create_preflight(target, preflight)
    records = repository.list_runs()

    assert history_id > 0
    assert records[0].target_host == "btt-pi.local"
    assert records[0].auth_method == "key_path"
    assert "/home/user/.ssh/id_ed25519" not in records[0].model_dump_json()


def _preflight_response(sections, checks):
    from app.setup_wizard import SetupSshPreflightResponse

    return SetupSshPreflightResponse(
        safe_mode="ssh_read_only_preflight",
        connected=True,
        status="warning",
        target="pi@btt-pi.local:22",
        summary="Host acessível com pendências.",
        checks=checks,
        sections=sections,
        redacted_target={
            "host": "btt-pi.local",
            "port": 22,
            "username": "pi",
            "auth_method": "agent",
            "key_path_configured": False,
        },
    )
