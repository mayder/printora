from pathlib import Path

from app.firmware.models import (
    BoardPreset,
    FirmwareBoardRecord,
    FirmwareBuildRunRecord,
    FirmwareFlashDryRunCreate,
    FirmwareFlashPreflight,
    FirmwareFlashPreflightCheck,
)
from app.firmware.utils import _optional_str, _slug


def _flash_dry_run_plan(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareFlashDryRunCreate,
    build_run: FirmwareBuildRunRecord | None,
) -> dict[str, object]:
    binary_path = _flash_binary_path(board, preset, payload, build_run)
    commands = _flash_commands(board, binary_path)
    checklist = [
        "Confirmar que a impressora não está imprimindo.",
        "Confirmar hotend, mesa e câmara em condição segura.",
        "Confirmar energia estável antes de qualquer flash futuro.",
        "Confirmar que o binário foi gerado com a mesma versão do Klipper em uso.",
        "Confirmar backup da configuração de firmware e binário anterior.",
        f"Confirmar UUID CAN esperado: {board.can_uuid or '-'}; abortar se não bater.",
        f"Confirmar interface CAN esperada: {board.can_interface}.",
        f"Confirmar método de flash esperado: {board.flash_method}.",
        "Confirmar plano de recuperação caso a MCU não volte.",
        "Confirmar rollback manual antes de qualquer flash real.",
        "Confirmar que este registro é dry-run: nenhum comando foi executado.",
    ]
    return {
        "flash_method": board.flash_method,
        "can_uuid": board.can_uuid,
        "can_interface": board.can_interface,
        "binary_path": binary_path,
        "commands": commands,
        "checklist": checklist,
        "message": payload.notes.strip()
        or "Dry-run de flash criado. Nenhum comando foi executado; usar apenas para revisão.",
    }


def _build_flash_preflight(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareFlashDryRunCreate,
    build_run: FirmwareBuildRunRecord | None,
    preflight: dict[str, object],
) -> FirmwareFlashPreflight:
    binary_path = _flash_binary_path(board, preset, payload, build_run)
    connected = bool(preflight.get("connected"))
    printing = bool(preflight.get("printing"))
    print_state = str(preflight.get("print_state") or "")
    klipper_state = _optional_str(preflight.get("klipper_state"))
    klippy_state = _optional_str(preflight.get("klippy_state"))
    checks = [
        FirmwareFlashPreflightCheck(
            key="moonraker_connected",
            label="Moonraker/Klipper acessível",
            status="ok" if connected else "blocked",
            detail="Moonraker respondeu ao preflight read-only." if connected else str(preflight.get("error") or "Moonraker indisponível."),
        ),
        FirmwareFlashPreflightCheck(
            key="not_printing",
            label="Impressão parada",
            status="blocked" if printing else "ok",
            detail=f"print_stats.state={print_state or '-'}",
        ),
        FirmwareFlashPreflightCheck(
            key="klipper_ready",
            label="Klipper ready",
            status="ok" if klipper_state == "ready" else "blocked",
            detail=f"printer/info.state={klipper_state or '-'}",
        ),
        FirmwareFlashPreflightCheck(
            key="klippy_ready",
            label="Klippy ready",
            status="ok" if klippy_state == "ready" else "blocked",
            detail=f"server/info.klippy_state={klippy_state or '-'}",
        ),
        FirmwareFlashPreflightCheck(
            key="binary_selected",
            label="Binário selecionado",
            status="ok" if binary_path.strip() else "blocked",
            detail=binary_path or "Nenhum binário informado ou planejado.",
        ),
        FirmwareFlashPreflightCheck(
            key="flash_method",
            label="Método de flash cadastrado",
            status="ok",
            detail=board.flash_method,
        ),
        FirmwareFlashPreflightCheck(
            key="can_identity",
            label="Identidade CAN/USB",
            status="ok" if board.connection_type == "usb" or bool(board.can_uuid) else "blocked",
            detail=f"uuid={board.can_uuid or '-'} interface={board.can_interface}",
        ),
        FirmwareFlashPreflightCheck(
            key="execution_policy",
            label="Política de execução",
            status="blocked",
            detail="Flash real permanece bloqueado neste lote.",
        ),
    ]
    blocked = any(check.status == "blocked" for check in checks)
    return FirmwareFlashPreflight(
        safe_mode="flash_preflight_read_only",
        printer_id=board.printer_id,
        board_id=board.id,
        board_name=board.name,
        flash_method=board.flash_method,
        can_uuid=board.can_uuid,
        can_interface=board.can_interface,
        binary_path=binary_path,
        connected=connected,
        printing=printing,
        print_state=print_state,
        klipper_state=klipper_state,
        klippy_state=klippy_state,
        checks=checks,
        commands_preview=_flash_commands(board, binary_path),
        rollback_plan=[
            "Nenhum flash, restart, SSH ou comando local foi executado neste preflight.",
            "Flash real futuro deve preservar binário anterior e .config antes da execução.",
            "Flash real futuro deve validar UUID/serial antes e depois, reiniciar Klipper separadamente e confirmar printer/info ready.",
        ],
        blocked=True,
        can_execute_flash=False,
        message=(
            "Preflight de flash concluiu com bloqueios; nenhuma ação foi executada."
            if blocked
            else "Preflight sem bloqueios operacionais, mas flash real permanece bloqueado neste lote."
        ),
    )


def _flash_binary_path(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareFlashDryRunCreate,
    build_run: FirmwareBuildRunRecord | None,
) -> str:
    if payload.binary_path and payload.binary_path.strip():
        return payload.binary_path.strip()
    if build_run is not None:
        return build_run.binary_output_path
    return f"~/printer_data/firmware_builds/DRY-RUN/{_slug(board.name)}/{Path(preset.build_output).name}"


def _flash_commands(board: FirmwareBoardRecord, binary_path: str) -> list[str]:
    if board.flash_method in {"katapult_can", "katapult_usb_can"}:
        return [
            "curl -s http://127.0.0.1:7125/printer/info",
            f"python3 ~/katapult/scripts/flashtool.py -i {board.can_interface} -u {board.can_uuid} -f {binary_path}",
            "sudo systemctl restart klipper",
            "curl -s http://127.0.0.1:7125/printer/info",
        ]
    if board.flash_method == "dfu_usb":
        return [
            "curl -s http://127.0.0.1:7125/printer/info",
            f"# DFU USB exige identificar o dispositivo correto antes do flash de {binary_path}.",
            "# Exemplo futuro: make flash FLASH_DEVICE=<device> depois de validação manual.",
            "sudo systemctl restart klipper",
            "curl -s http://127.0.0.1:7125/printer/info",
        ]
    return [
        "curl -s http://127.0.0.1:7125/printer/info",
        f"# Método manual: revisar documentação da placa antes de usar {binary_path}.",
        "sudo systemctl restart klipper",
        "curl -s http://127.0.0.1:7125/printer/info",
    ]
