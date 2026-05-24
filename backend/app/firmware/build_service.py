import shutil
import subprocess
from pathlib import Path

from app.firmware.models import (
    BoardPreset,
    FirmwareBoardRecord,
    FirmwareBuildDryRunCreate,
    FirmwareBuildExecuteCreate,
    FirmwareBuildPreflight,
    FirmwareBuildPreflightCheck,
)
from app.firmware.utils import _excerpt, _slug


def _build_dry_run_plan(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
) -> dict[str, object]:
    slug = _slug(board.name)
    output_dir = f"{payload.output_root.rstrip('/')}/DRY-RUN/{slug}"
    backup_path = f"{output_dir}/.config.before-build"
    binary_path = f"{output_dir}/{Path(preset.build_output).name}"
    commands = [
        "curl -s http://127.0.0.1:7125/printer/info",
        f"mkdir -p {output_dir}",
        f"cd {payload.klipper_path}",
        f"cp .config {backup_path}",
        "make clean",
        f"cp {board.config_file} .config",
        "make",
        f"cp {preset.build_output} {binary_path}",
        f"cp {backup_path} .config",
    ]
    checklist = [
        "Confirmar que a impressora não está imprimindo.",
        "Confirmar Klipper/Moonraker conectados e sem erro.",
        f"Confirmar preset {preset.id} para {board.name}.",
        f"Confirmar MCU {preset.mcu}, arquitetura {preset.architecture} e bootloader {preset.bootloader_offset}.",
        f"Confirmar arquivo de config planejado: {board.config_file}.",
        f"Confirmar saída esperada do build: {preset.build_output}.",
        f"Confirmar UUID CAN {board.can_uuid or '-'} antes de qualquer flash futuro.",
        "Confirmar backup da .config antes de sobrescrever.",
        "Confirmar que build local só roda com modo local e confirmação explícita.",
        "Confirmar que dry-run apenas registra plano e não executou comandos.",
    ]
    return {
        "klipper_path": payload.klipper_path,
        "output_dir": output_dir,
        "config_backup_path": backup_path,
        "binary_output_path": binary_path,
        "commands": commands,
        "checklist": checklist,
        "message": payload.notes.strip()
        or "Dry-run criado. Nenhum comando foi executado; plano salvo apenas para revisão.",
    }


def _build_local_build_preflight(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
    mode: str,
) -> FirmwareBuildPreflight:
    klipper_path = Path(payload.klipper_path).expanduser()
    output_root = Path(payload.output_root).expanduser()
    source_config = Path(board.config_file).expanduser()
    if not source_config.is_absolute():
        source_config = klipper_path / source_config
    expected_output = klipper_path / preset.build_output
    plan = _build_dry_run_plan(board, preset, payload)
    checks = [
        _preflight_check(
            "build_mode",
            "Modo de build local",
            mode == "local",
            f"PRINTORA_FIRMWARE_BUILD_MODE={mode}",
            "Build real bloqueado porque o modo local não está habilitado.",
        ),
        _preflight_check(
            "make_binary",
            "Comando make disponível",
            shutil.which("make") is not None,
            shutil.which("make") or "make não encontrado no PATH",
            "Instalar toolchain/build tools no host antes de compilar.",
        ),
        _preflight_check(
            "klipper_path",
            "Diretório Klipper",
            klipper_path.is_dir(),
            str(klipper_path),
            "Diretório Klipper não encontrado neste host.",
        ),
        _preflight_check(
            "klipper_makefile",
            "Makefile do Klipper",
            (klipper_path / "Makefile").is_file(),
            str(klipper_path / "Makefile"),
            "Makefile do Klipper não encontrado.",
        ),
        _preflight_check(
            "current_config",
            ".config atual",
            (klipper_path / ".config").is_file(),
            str(klipper_path / ".config"),
            ".config atual não encontrado; build real não deve sobrescrever sem backup.",
        ),
        _preflight_check(
            "board_config",
            ".config da placa cadastrada",
            source_config.is_file(),
            str(source_config),
            "Arquivo de configuração da placa não encontrado.",
        ),
        FirmwareBuildPreflightCheck(
            key="expected_output",
            label="Saída esperada do build",
            status="warning",
            detail=f"{expected_output} será validado somente depois de make; nenhum build foi executado.",
        ),
        FirmwareBuildPreflightCheck(
            key="output_root",
            label="Diretório destino planejado",
            status="warning",
            detail=f"{output_root} não foi criado nem alterado neste preflight.",
        ),
    ]
    blocked = any(check.status == "blocked" for check in checks)
    return FirmwareBuildPreflight(
        safe_mode="local_build_preflight_read_only",
        printer_id=board.printer_id,
        board_id=board.id,
        board_name=board.name,
        klipper_path=str(klipper_path),
        output_root=str(output_root),
        config_file=str(source_config),
        expected_build_output=str(expected_output),
        checks=checks,
        commands_preview=list(plan["commands"]),
        blocked=True,
        can_execute_build=False,
        message=(
            "Preflight concluído com bloqueios; nenhum comando foi executado."
            if blocked
            else "Preflight sem bloqueios críticos, mas build real permanece bloqueado neste lote."
        ),
    )


def _preflight_check(
    key: str,
    label: str,
    ok: bool,
    ok_detail: str,
    blocked_detail: str,
) -> FirmwareBuildPreflightCheck:
    return FirmwareBuildPreflightCheck(
        key=key,
        label=label,
        status="ok" if ok else "blocked",
        detail=ok_detail if ok else blocked_detail,
    )


def _mark_local_build_plan(
    plan: dict[str, object],
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
) -> None:
    output_dir = f"{payload.output_root.rstrip('/')}/local-build/{_slug(board.name)}"
    plan["output_dir"] = output_dir
    plan["config_backup_path"] = f"{output_dir}/.config.before-build"
    plan["binary_output_path"] = f"{output_dir}/{Path(preset.build_output).name}"


def _execute_local_build(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildExecuteCreate,
    timeout_seconds: float,
) -> str:
    klipper_path = Path(payload.klipper_path).expanduser().resolve()
    output_root = Path(payload.output_root).expanduser().resolve()
    output_dir = output_root / "local-build" / _slug(board.name)
    backup_path = output_dir / ".config.before-build"
    binary_path = output_dir / Path(preset.build_output).name
    source_config = Path(board.config_file).expanduser()
    if not source_config.is_absolute():
        source_config = klipper_path / source_config
    source_config = source_config.resolve()
    klipper_config = klipper_path / ".config"
    build_output = klipper_path / preset.build_output

    if not klipper_path.is_dir():
        raise ValueError(f"klipper path not found: {klipper_path}")
    if not (klipper_path / "Makefile").is_file():
        raise ValueError("klipper path does not contain Makefile")
    if not source_config.is_file():
        raise ValueError(f"firmware config not found: {source_config}")
    if not klipper_config.is_file():
        raise ValueError("current .config not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(klipper_config, backup_path)
    restored = False
    logs: list[str] = []
    try:
        logs.append(_run_make(["make", "clean"], klipper_path, timeout_seconds))
        shutil.copy2(source_config, klipper_config)
        logs.append(_run_make(["make"], klipper_path, timeout_seconds))
        if not build_output.is_file():
            raise ValueError(f"expected build output not found: {build_output}")
        shutil.copy2(build_output, binary_path)
    finally:
        if backup_path.is_file():
            shutil.copy2(backup_path, klipper_config)
            restored = True
        if not restored:
            raise RuntimeError("failed to restore original .config")
    return _excerpt("\n".join(logs))


def _run_make(command: list[str], cwd: Path, timeout_seconds: float) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    output = result.stdout + "\n" + result.stderr
    if result.returncode != 0:
        excerpt = _excerpt(output)
        raise RuntimeError(f"{' '.join(command)} failed with exit {result.returncode}: {excerpt}")
    return output
