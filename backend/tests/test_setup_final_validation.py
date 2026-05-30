import asyncio
from pathlib import Path

from app.database import initialize_database
from app.setup_final_validation import (
    SetupFinalValidationRepository,
    SetupFinalValidationRequest,
    run_setup_final_validation,
)
from app.setup_wizard import SetupSshTarget


VALIDATION_OK_OUTPUT = """SECTION tools
curl=present:/usr/bin/curl
python3=present:/usr/bin/python3
systemctl=present:/usr/bin/systemctl
ip=present:/usr/sbin/ip

SECTION services
klipper=active
moonraker=active
crowsnest=active
mainsail=inactive
nginx=active
can0=active

SECTION server_info
{"klippy_state":"ready","moonraker_version":"v0.9.0","warnings":[]}

SECTION printer_info
{"state":"ready","state_message":"Printer is ready"}

SECTION print_stats
{"status":{"print_stats":{"state":"standby"}}}

SECTION temperatures
{"status":{"extruder":{"temperature":24.1,"target":0.0},"heater_bed":{"temperature":25.0,"target":0.0}}}

SECTION update_status
{"version_info":{"klipper":{"version":"v0.12.0"},"moonraker":{"version":"v0.9.0"}}}

SECTION can
4: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UNKNOWN mode DEFAULT group default qlen 10

SECTION uuid_query
Found canbus_uuid=0123456789ab, Application: Klipper
Found canbus_uuid=abcdef123456, Application: Klipper

SECTION config_summary
config_root_exists=yes
cfg=/home/pi/printer_data/config/printer.cfg
/home/pi/printer_data/config/printer.cfg:[include mainsail.cfg]
/home/pi/printer_data/config/printer.cfg:[mcu]
/home/pi/printer_data/config/printer.cfg:canbus_uuid: 0123456789ab
/home/pi/printer_data/config/toolhead.cfg:[mcu toolhead]
/home/pi/printer_data/config/toolhead.cfg:canbus_uuid: abcdef123456

SECTION recent_errors
missing_log=/home/pi/printer_data/logs/old.log
"""


def _request(**kwargs) -> SetupFinalValidationRequest:
    data = {
        "target": SetupSshTarget(host="btt-pi.local", username="pi"),
        "interface_name": "can0",
        "expected_uuids": ["0123456789ab", "abcdef123456"],
    }
    data.update(kwargs)
    return SetupFinalValidationRequest(**data)


def test_final_validation_approves_ready_base_and_sanitizes_report(monkeypatch) -> None:
    async def fake_remote(*args, **kwargs):
        return {"stdout": VALIDATION_OK_OUTPUT, "stderr": "", "exit_code": 0, "error": None}

    monkeypatch.setattr("app.setup_final_validation._run_remote_script", fake_remote)

    response = asyncio.run(run_setup_final_validation(_request()))

    assert response.status == "approved_for_calibration"
    assert "aprovados para iniciar calibração" in response.summary
    assert all(check.status == "ok" for check in response.checks if check.key not in {"updates"})
    assert "home/pi" not in response.report_markdown
    assert "canbus_uuid" not in response.report_markdown
    assert "0123456789ab" in response.report_markdown


def test_final_validation_blocks_missing_uuid(monkeypatch) -> None:
    async def fake_remote(*args, **kwargs):
        output = VALIDATION_OK_OUTPUT.replace("abcdef123456", "999999999999")
        return {"stdout": output, "stderr": "", "exit_code": 0, "error": None}

    monkeypatch.setattr("app.setup_final_validation._run_remote_script", fake_remote)

    response = asyncio.run(run_setup_final_validation(_request()))

    assert response.status == "blocked"
    assert any(check.key == "uuids" and check.status == "blocked" for check in response.checks)


def test_final_validation_requires_manual_uuid_when_not_informed(monkeypatch) -> None:
    async def fake_remote(*args, **kwargs):
        return {"stdout": VALIDATION_OK_OUTPUT, "stderr": "", "exit_code": 0, "error": None}

    monkeypatch.setattr("app.setup_final_validation._run_remote_script", fake_remote)

    response = asyncio.run(run_setup_final_validation(_request(expected_uuids=[])))

    assert response.status == "needs_manual_intervention"
    assert any(check.key == "uuids" and check.status == "manual" for check in response.checks)


def test_final_validation_history_does_not_store_key_path(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SetupFinalValidationRepository(database_path)
    request = _request(
        target=SetupSshTarget(
            host="btt-pi.local",
            username="pi",
            auth_method="key_path",
            key_path="/Users/local/.ssh/id_ed25519",
        )
    )
    response = _response_for_history(request)

    history_id = repository.create_run(request, response)
    records = repository.list_runs()

    assert history_id > 0
    assert records[0].interface_name == "can0"
    assert "/Users/local/.ssh/id_ed25519" not in records[0].model_dump_json()


def _response_for_history(request: SetupFinalValidationRequest):
    from app.setup_final_validation import SetupFinalValidationResponse

    return SetupFinalValidationResponse(
        safe_mode="final_validation_read_only",
        connected=True,
        status="approved_for_calibration",
        target="pi@btt-pi.local:22",
        interface_name=request.interface_name,
        expected_uuids=request.expected_uuids,
        summary="Base eletrônica e software aprovados para iniciar calibração.",
        checks=[],
        sections={},
        report_markdown="# Aceite técnico\n",
    )
