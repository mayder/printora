from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import agent_preflight_payload, firmware_inventory_payload
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *
from app.firmware_catalog import FirmwareCatalogSummary, build_firmware_hardware_inventory_unavailable, firmware_catalog_summary
from app.firmware.config_generator import generate_firmware_config_preview

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/firmware/board-presets")
async def list_firmware_board_presets() -> dict[str, list[BoardPreset]]:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    return {"presets": firmware_repository.list_presets()}




@router.get("/api/firmware/board-presets/{preset_id}/config-preview")
async def firmware_preset_config_preview(preset_id: str) -> FirmwareConfigPreview:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.generate_preset_config_preview(preset_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/firmware/catalog")
async def read_firmware_catalog_summary() -> FirmwareCatalogSummary:
    return firmware_catalog_summary()




@router.get("/api/printers/{printer_id}/firmware/boards")
async def list_firmware_boards(printer_id: int) -> dict[str, list[FirmwareBoardRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"boards": firmware_repository.list_boards(printer_id)}




@router.get("/api/printers/{printer_id}/firmware/hardware-inventory")
async def firmware_hardware_inventory(printer_id: int) -> FirmwareHardwareInventory:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    inventory_error: str | None = None
    object_names: list[str] = []
    object_payload: dict[str, object] = {}
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_firmware_inventory",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        object_names, object_payload = firmware_inventory_payload(job.result)
    except Exception as exc:
        inventory_error = _firmware_inventory_error_detail(exc)
    if inventory_error:
        return build_firmware_hardware_inventory_unavailable(printer_id=printer_id, reason=inventory_error)
    return build_firmware_hardware_inventory(
        printer_id=printer_id,
        registered_boards=firmware_repository.list_boards(printer_id),
        object_names=object_names,
        object_payload=object_payload,
    )


def _firmware_inventory_error_detail(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        detail = str(exc.detail)
        if exc.status_code == 409:
            return "Nenhum agente online respondeu por esta impressora."
        if exc.status_code == 504:
            return "O agente demorou para responder ao inventário de firmware."
        if exc.status_code == 502:
            return f"O agente retornou falha ao consultar o Moonraker. {detail}"
        return detail
    return str(exc)




@router.post("/api/printers/{printer_id}/firmware/boards")
async def create_firmware_board(printer_id: int, payload: FirmwareBoardCreate) -> FirmwareBoardRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return firmware_repository.create_board(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/printers/{printer_id}/firmware/build-runs")
async def list_firmware_build_runs(printer_id: int, limit: int = 20) -> dict[str, list[FirmwareBuildRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": firmware_repository.list_build_runs(printer_id, clean_limit)}




@router.post("/api/firmware/boards/{board_id}/build-runs/dry-run")
async def create_firmware_build_dry_run(
    board_id: int,
    payload: FirmwareBuildDryRunCreate,
) -> FirmwareBuildRunRecord:
    settings = get_settings()
    _require_scoped_firmware_board(settings, board_id)
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.create_build_dry_run(board_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/build-runs/preflight")
async def firmware_build_preflight(
    board_id: int,
    payload: FirmwareBuildDryRunCreate,
) -> FirmwareBuildPreflight:
    settings = get_settings()
    _require_scoped_firmware_board(settings, board_id)
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.build_build_preflight(
            board_id=board_id,
            payload=payload,
            mode=settings.firmware_build_mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/build-runs/execute-local")
async def execute_firmware_build_local(
    board_id: int,
    payload: FirmwareBuildExecuteCreate,
) -> FirmwareBuildRunRecord:
    import base64
    import json

    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    board = _require_scoped_firmware_board(settings, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="firmware board not found")
    preset = firmware_repository.get_preset(board.preset_id)
    if preset is None:
        raise HTTPException(status_code=400, detail="unknown board preset")
    if payload.confirmation != "EXECUTE_LOCAL_BUILD_NO_FLASH":
        return firmware_repository.create_agent_build_run(
            board_id,
            payload,
            status="blocked_invalid_build_confirmation",
            message="Build pelo agente bloqueado: confirmação textual inválida ou ausente.",
        )
    printer_repository = get_printer_repository(settings)
    printer = printer_repository.get_printer(board.printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    config_preview = generate_firmware_config_preview(preset)
    request_payload = base64.b64encode(
        json.dumps(
            {
                "klipper_path": payload.klipper_path,
                "output_root": payload.output_root,
                "board_name": board.name,
                "preset_id": preset.id,
                "build_output": preset.build_output,
                "config_file": board.config_file,
                "config_content": config_preview.content,
            },
            ensure_ascii=False,
        ).encode()
    ).decode()
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_host_script",
            payload={
                "kind": "firmware_build",
                "script": _agent_firmware_build_script(request_payload),
                "timeout_seconds": settings.firmware_build_timeout_seconds,
            },
            timeout_seconds=max(settings.firmware_build_timeout_seconds, 30.0),
        )
    except Exception as exc:
        return firmware_repository.create_agent_build_run(board_id, payload, status="build_failed", message=str(exc))
    result = job.result if isinstance(job.result, dict) else {}
    stdout = str(result.get("stdout") or "")
    try:
        build_result = json.loads(stdout.strip().splitlines()[-1])
    except Exception as exc:
        build_result = {"status": "build_failed", "message": stdout[-500:] or str(result.get("error") or exc)}
    return firmware_repository.create_agent_build_run(
        board_id,
        payload,
        status=str(build_result.get("status") or "build_failed"),
        message=str(build_result.get("message") or ""),
    )


def _agent_firmware_build_script(payload_b64: str) -> str:
    return f"""set -euo pipefail
python3 - <<'PY'
import base64, datetime, hashlib, json, pathlib, shutil, subprocess
data = json.loads(base64.b64decode({payload_b64!r}).decode())
klipper = pathlib.Path(data["klipper_path"]).expanduser().resolve()
output_root = pathlib.Path(data["output_root"]).expanduser().resolve()
slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in data["board_name"]).strip("-") or "board"
out_dir = output_root / "AGENT" / slug
generated_dir = out_dir / "generated"
logs_dir = out_dir / "logs"
generated_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)
config_path = klipper / ".config"
backup_path = out_dir / ".config.before-build"
generated_config = generated_dir / pathlib.Path(data["config_file"]).name
binary_output = out_dir / pathlib.Path(data["build_output"]).name
log_path = logs_dir / "build.log"
if not klipper.is_dir():
    print(json.dumps({{"status":"build_failed","message":f"Klipper path inexistente: {{klipper}}"}}))
    raise SystemExit(0)
generated_config.write_text(data["config_content"], encoding="utf-8")
if config_path.exists():
    shutil.copy2(config_path, backup_path)
try:
    shutil.copy2(generated_config, config_path)
    with log_path.open("w", encoding="utf-8") as log:
        subprocess.run(["make", "clean"], cwd=klipper, stdout=log, stderr=subprocess.STDOUT, timeout=120, check=False)
        result = subprocess.run(["make"], cwd=klipper, stdout=log, stderr=subprocess.STDOUT, timeout=900, check=False)
    build_output = klipper / data["build_output"]
    if result.returncode != 0 or not build_output.exists():
        print(json.dumps({{"status":"build_failed","message":f"Build falhou no agente. Log: {{log_path}}"}}))
    else:
        shutil.copy2(build_output, binary_output)
        digest = hashlib.sha256(binary_output.read_bytes()).hexdigest()
        print(json.dumps({{"status":"build_success","message":f"Build pelo agente concluído sem flash. Binário: {{binary_output}} sha256={{digest}}"}}))
finally:
    if backup_path.exists():
        shutil.copy2(backup_path, config_path)
PY
"""




@router.get("/api/printers/{printer_id}/firmware/flash-runs")
async def list_firmware_flash_runs(printer_id: int, limit: int = 20) -> dict[str, list[FirmwareFlashRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    firmware_repository = get_firmware_board_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": firmware_repository.list_flash_runs(printer_id, clean_limit)}




@router.post("/api/firmware/boards/{board_id}/flash-runs/dry-run")
async def create_firmware_flash_dry_run(
    board_id: int,
    payload: FirmwareFlashDryRunCreate,
) -> FirmwareFlashRunRecord:
    settings = get_settings()
    _require_scoped_firmware_board(settings, board_id)
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.create_flash_dry_run(board_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/flash-runs/preflight")
async def firmware_flash_preflight(
    board_id: int,
    payload: FirmwareFlashDryRunCreate,
) -> FirmwareFlashPreflight:
    settings = get_settings()
    _require_scoped_firmware_board(settings, board_id)
    firmware_repository = get_firmware_board_repository(settings)
    board = firmware_repository.get_board(board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="firmware board not found")
    printer_repository = get_printer_repository(settings)
    printer = printer_repository.get_printer(board.printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    job = await AgentCommandExecutor(settings.database_path).run(
        printer,
        job_type="remote_gcode_preflight",
        payload={"action_id": f"firmware_flash:{board.id}", "criticality": "firmware"},
        timeout_seconds=max(settings.request_timeout_seconds, 10.0),
    )
    preflight = agent_preflight_payload(job.result)
    try:
        return firmware_repository.build_flash_preflight(board_id, payload, preflight)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/firmware/boards/{board_id}/flash-runs/execute")
async def execute_firmware_flash_blocked(
    board_id: int,
    payload: FirmwareFlashExecuteCreate,
) -> FirmwareFlashRunRecord:
    settings = get_settings()
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.execute_flash_blocked(board_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/firmware/boards/{board_id}/recovery-plan")
async def firmware_recovery_plan(board_id: int) -> FirmwareRecoveryPlan:
    settings = get_settings()
    _require_scoped_firmware_board(settings, board_id)
    firmware_repository = get_firmware_board_repository(settings)
    try:
        return firmware_repository.build_recovery_plan(board_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _require_scoped_firmware_board(settings, board_id: int) -> FirmwareBoardRecord:
    firmware_repository = get_firmware_board_repository(settings)
    board = firmware_repository.get_board(board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="firmware board not found")
    printer_repository = get_printer_repository(settings)
    if printer_repository.get_printer(board.printer_id) is None:
        raise HTTPException(status_code=404, detail="firmware board not found")
    return board
