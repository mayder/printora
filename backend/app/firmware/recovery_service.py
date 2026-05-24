from app.firmware.models import FirmwareBoardRecord, FirmwareRecoveryPlan


def build_firmware_recovery_plan(board: FirmwareBoardRecord) -> FirmwareRecoveryPlan:
    return FirmwareRecoveryPlan(
        safe_mode="manual_recovery_plan_only",
        printer_id=board.printer_id,
        board_id=board.id,
        board_name=board.name,
        flash_method=board.flash_method,
        can_uuid=board.can_uuid,
        can_interface=board.can_interface,
        prerequisites=[
            "Confirmar impressora parada e energia estável.",
            "Ter backup da .config e binário anterior antes de qualquer flash.",
            "Confirmar método de bootloader da placa e acesso físico se necessário.",
            "Registrar UUID/serial atual antes de alterar firmware.",
        ],
        recovery_steps=_firmware_recovery_steps(board),
        validation_steps=[
            "Validar UUID/serial após recuperação.",
            "Reiniciar Klipper somente depois de confirmar que a MCU voltou a responder.",
            "Conferir printer/info e logs antes de liberar impressão.",
        ],
        rollback_notes=[
            "Este plano não executou flash, restart, SSH nem comandos locais.",
            "Se o flash falhar, usar o binário anterior e o método de bootloader documentado para a placa.",
        ],
        blocked=True,
    )


def _firmware_recovery_steps(board: FirmwareBoardRecord) -> list[str]:
    if board.flash_method == "katapult_can":
        return [
            f"Confirmar interface CAN: {board.can_interface}.",
            f"Confirmar UUID atual/esperado: {board.can_uuid or '-'}.",
            "Colocar a placa em Katapult pelo procedimento físico/documentado.",
            "Reaplicar o binário anterior com o comando Katapult validado manualmente.",
        ]
    if board.flash_method == "katapult_usb_can":
        return [
            "Confirmar que a bridge USB-CAN continua aparecendo no host.",
            f"Confirmar interface CAN: {board.can_interface}.",
            "Colocar a placa em Katapult pelo procedimento físico/documentado.",
            "Reaplicar o binário anterior com o comando da bridge validado manualmente.",
        ]
    if board.flash_method == "dfu_usb":
        return [
            "Colocar a placa em DFU/bootloader pelo jumper ou botão documentado.",
            "Confirmar presença no host com ferramenta de listagem USB apropriada.",
            "Reaplicar o binário anterior com o comando DFU validado manualmente.",
        ]
    return [
        "Seguir o procedimento manual da placa.",
        "Usar binário anterior e .config preservados.",
        "Registrar comando, resultado e evidência antes de reiniciar Klipper.",
    ]
