from pathlib import Path

from app.database import initialize_database
from app.setup_can import (
    CAN_SETUP_CONFIRMATION,
    SetupCanApplyRequest,
    SetupCanRequest,
    SetupCanRunRepository,
    build_can_findings,
    build_setup_can_plan,
    parse_can_preflight_sections,
    split_sections,
)
from app.setup_wizard import SetupSshTarget


CAN_PREFLIGHT_OK = """SECTION tools
ip=present:/usr/sbin/ip
lsusb=present:/usr/bin/lsusb
systemctl=present:/usr/bin/systemctl
sudo=present:/usr/bin/sudo
modprobe=present:/usr/sbin/modprobe
lsmod=present:/usr/sbin/lsmod
curl=present:/usr/bin/curl
python3=present:/usr/bin/python3

SECTION sudo
sudo_nopasswd=yes

SECTION modules
can_raw 16384 1
can 24576 1 can_raw
gs_usb 20480 0

SECTION usb
Bus 001 Device 004: ID 1d50:606f OpenMoko, Inc. Geschwister Schneider CAN adapter / BTT U2C

SECTION links
can0             UNKNOWN        00:00:00:00:00:00 <NOARP,UP,LOWER_UP>

SECTION can
can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UNKNOWN mode DEFAULT group default qlen 10
    link/can  promiscuity 0 minmtu 0 maxmtu 0
    can state ERROR-ACTIVE restart-ms 0
          bitrate 1000000 sample-point 0.875
    RX: bytes  packets  errors  dropped missed  mcast
    128        16       0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    64         8        0       0       0       0

SECTION config_files
missing /etc/systemd/system/can0.service

SECTION services
klipper.service loaded active running
moonraker.service loaded active running

SECTION print_state
{"result":{"status":{"print_stats":{"state":"standby"}}}}

SECTION uuid_query
Found canbus_uuid=1234abcd, Application: Klipper
"""


CAN_PREFLIGHT_MISSING = """SECTION tools
ip=present:/usr/sbin/ip
lsusb=missing
systemctl=present:/usr/bin/systemctl
sudo=present:/usr/bin/sudo
modprobe=missing
lsmod=missing
curl=present:/usr/bin/curl
python3=present:/usr/bin/python3

SECTION sudo
sudo_nopasswd=no

SECTION modules
lsmod_unavailable

SECTION usb
lsusb_unavailable

SECTION links
lo UNKNOWN

SECTION can
Device "can0" does not exist.

SECTION services
klipper.service loaded active running

SECTION print_state
{"result":{"status":{"print_stats":{"state":"printing"}}}}

SECTION uuid_query
canbus_query_unavailable
"""


def test_parse_can_preflight_sections_reads_u2c_can_and_uuid() -> None:
    parsed = parse_can_preflight_sections(split_sections(CAN_PREFLIGHT_OK))

    assert parsed["u2c_detected"] is True
    assert parsed["can_modules_loaded"] is True
    assert parsed["can_state"] == "ERROR-ACTIVE"
    assert parsed["bitrate"] == 1000000
    assert parsed["uuid_count"] == 1
    assert parsed["printing"] is False


def test_can_findings_differentiate_missing_u2c_interface_and_printing() -> None:
    sections = split_sections(CAN_PREFLIGHT_MISSING)
    findings = build_can_findings(0, sections, "", "can0", 1000000)
    by_key = {finding.key: finding for finding in findings}

    assert by_key["u2c_usb"].status == "warning"
    assert by_key["can_modules"].status == "warning"
    assert by_key["can_interface"].status == "warning"
    assert by_key["print_state"].status == "blocked"


def test_can_plan_blocks_when_printing_and_uses_plan_commands() -> None:
    sections = split_sections(CAN_PREFLIGHT_MISSING)
    findings = build_can_findings(0, sections, "", "can0", 1000000)
    preflight = _can_preflight(sections, findings)

    plan = build_setup_can_plan(preflight)

    assert plan.status == "blocked"
    assert any("Impressão em andamento" in reason for reason in plan.blocked_reasons)
    assert all(command.command.startswith("PLAN ") for step in plan.steps for command in step.commands)


def test_can_history_persists_without_key_path(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SetupCanRunRepository(database_path)
    request = SetupCanRequest(
        target=SetupSshTarget(
            host="btt-pi.local",
            username="pi",
            auth_method="key_path",
            key_path="/Users/local/.ssh/id_ed25519",
        ),
        interface_name="can0",
        bitrate=1000000,
    )
    sections = split_sections(CAN_PREFLIGHT_OK)
    findings = build_can_findings(0, sections, "", "can0", 1000000)
    preflight = _can_preflight(sections, findings)

    history_id = repository.create_preflight(request, preflight)
    records = repository.list_runs()

    assert history_id > 0
    assert records[0].interface_name == "can0"
    assert "/Users/local/.ssh/id_ed25519" not in records[0].model_dump_json()


def test_can_apply_request_uses_explicit_confirmation() -> None:
    request = SetupCanApplyRequest(
        target=SetupSshTarget(host="btt-pi.local", username="pi"),
        confirmation=CAN_SETUP_CONFIRMATION,
    )

    assert request.confirmation == "CONFIGURAR CAN0"


def _can_preflight(sections, findings):
    from app.setup_can import SetupCanPreflightResponse, _overall_status, _summary, parse_can_preflight_sections

    return SetupCanPreflightResponse(
        safe_mode="can_read_only_preflight",
        connected=True,
        status=_overall_status(findings),
        target="pi@btt-pi.local:22",
        interface_name="can0",
        bitrate=1000000,
        summary=_summary(findings, True),
        findings=findings,
        sections=sections,
        parsed=parse_can_preflight_sections(sections),
    )
