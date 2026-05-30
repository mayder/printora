import asyncio
from pathlib import Path

from app.database import initialize_database
from app.setup_flash import (
    FLASH_MODE_ENV,
    SetupFlashPreflightResponse,
    SetupFlashExecuteRequest,
    SetupFlashRequest,
    SetupFlashRunRepository,
    build_setup_flash_plan,
    confirmation_phrase,
    execute_setup_flash,
    run_setup_flash_preflight,
)
from app.setup_wizard import SetupSshTarget


PRELIGHT_OK_OUTPUT = """SECTION tools
test=present:/usr/bin/test
sha256sum=present:/usr/bin/sha256sum
stat=present:/usr/bin/stat
timeout=present:/usr/bin/timeout
curl=present:/usr/bin/curl
python3=present:/usr/bin/python3

SECTION artifact
artifact_exists=yes
artifact_size=12345
artifact_sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

SECTION print_state
standby

SECTION flash_tool
flash_can=present:/home/pi/klipper/scripts/flash_can.py
klippy_python=present:/home/pi/klippy-env/bin/python

SECTION uuid_query
Found canbus_uuid=0123456789ab, Application: Katapult

SECTION printer_info
{"result":{"state":"ready"}}
"""


def _request(**kwargs) -> SetupFlashRequest:
    data = {
        "target": SetupSshTarget(host="btt-pi.local", username="pi"),
        "board_name": "EBB36 v1.2",
        "board_role": "toolhead",
        "flash_method": "can_katapult",
        "artifact_path": "~/.local/share/printora/firmware-setup/ebb36/klipper.bin",
        "expected_uuid": "0123456789ab",
        "checklist_confirmed": True,
    }
    data.update(kwargs)
    return SetupFlashRequest(**data)


def test_flash_preflight_blocks_without_checklist(monkeypatch) -> None:
    async def fake_remote(*args, **kwargs):
        return {"stdout": PRELIGHT_OK_OUTPUT, "stderr": "", "exit_code": 0, "error": None}

    monkeypatch.setattr("app.setup_flash._run_remote_script", fake_remote)

    preflight = asyncio.run(run_setup_flash_preflight(_request(checklist_confirmed=False)))

    assert preflight.status == "blocked"
    assert any(finding.key == "checklist" and finding.status == "blocked" for finding in preflight.findings)
    assert preflight.artifact_sha256 == "a" * 64


def test_flash_plan_requires_visible_uuid_and_uses_plan_commands(monkeypatch) -> None:
    async def fake_remote(*args, **kwargs):
        output = PRELIGHT_OK_OUTPUT.replace("0123456789ab", "999999999999")
        return {"stdout": output, "stderr": "", "exit_code": 0, "error": None}

    monkeypatch.setattr("app.setup_flash._run_remote_script", fake_remote)

    plan = asyncio.run(build_setup_flash_plan(_request()))

    assert plan.status == "blocked"
    assert any("UUID esperado" in reason or "UUID" in reason for reason in plan.blocked_reasons)
    assert all(command.command.startswith("PLAN ") for step in plan.steps for command in step.commands)


def test_flash_execute_is_blocked_without_env(monkeypatch) -> None:
    monkeypatch.delenv(FLASH_MODE_ENV, raising=False)
    request = SetupFlashExecuteRequest(**_request().model_dump(), confirmation=confirmation_phrase(_request()))

    response = asyncio.run(execute_setup_flash(request))

    assert response.status == "blocked"
    assert f"{FLASH_MODE_ENV}=remote não está habilitado." in response.blocked_reasons
    assert response.command_log == ""


def test_flash_execute_can_katapult_when_gate_is_enabled(monkeypatch) -> None:
    calls: list[str] = []

    async def fake_remote(_target, script, **kwargs):
        calls.append(script)
        if "flash_can.py\" -i" in script:
            return {
                "stdout": "SECTION artifact\nartifact_sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n\nSECTION flash\nflash_exit_code=0\n",
                "stderr": "",
                "exit_code": 0,
                "error": None,
            }
        return {"stdout": PRELIGHT_OK_OUTPUT, "stderr": "", "exit_code": 0, "error": None}

    monkeypatch.setenv(FLASH_MODE_ENV, "remote")
    monkeypatch.setattr("app.setup_flash._run_remote_script", fake_remote)
    base = _request()
    request = SetupFlashExecuteRequest(**base.model_dump(), confirmation=confirmation_phrase(base))

    response = asyncio.run(execute_setup_flash(request))

    assert response.status == "ok"
    assert response.artifact_sha256 == "a" * 64
    assert any("flash_can.py" in call for call in calls)
    assert not any("systemctl restart" in call for call in calls)
    assert not any("printer.cfg" in call for call in calls)


def test_flash_history_does_not_store_key_path(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SetupFlashRunRepository(database_path)
    request = _request(
        target=SetupSshTarget(
            host="btt-pi.local",
            username="pi",
            auth_method="key_path",
            key_path="/Users/local/.ssh/id_ed25519",
        )
    )
    preflight = SetupFlashPreflightResponse(
        safe_mode="flash_preflight_read_only",
        connected=True,
        status="ok",
        target="pi@btt-pi.local:22",
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        artifact_sha256="a" * 64,
        expected_uuid=request.expected_uuid,
        summary="Preflight de flash aprovado.",
        findings=[],
        sections={},
        parsed={},
        rollback=[],
    )

    history_id = repository.create_preflight(request, preflight)
    records = repository.list_runs()

    assert history_id > 0
    assert records[0].board_name == "EBB36 v1.2"
    assert "/Users/local/.ssh/id_ed25519" not in records[0].model_dump_json()
