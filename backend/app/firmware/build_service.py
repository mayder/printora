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
from app.firmware.config_generator import generate_firmware_config_preview
from app.firmware.utils import _excerpt, _slug


def _build_dry_run_plan(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
) -> dict[str, object]:
    config_preview = generate_firmware_config_preview(preset)
    paths = _build_dry_run_paths(board, preset, payload)
    return {
        "klipper_path": payload.klipper_path,
        "output_dir": paths["output_dir"],
        "config_backup_path": paths["config_backup_path"],
        "binary_output_path": paths["binary_output_path"],
        "generated_config_path": paths["generated_config_path"],
        "work_dir": paths["work_dir"],
        "expected_build_output": paths["expected_build_output"],
        "log_path": paths["log_path"],
        "commands": _build_dry_run_commands(preset, paths, len(config_preview.lines)),
        "checklist": _build_dry_run_checklist(board, preset, paths),
        "message": payload.notes.strip()
        or "Dry-run criado. Nenhum comando foi executado; plano salvo apenas para revisão.",
    }


def _build_dry_run_paths(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
) -> dict[str, str]:
    output_dir = f"{payload.output_root.rstrip('/')}/DRY-RUN/{_slug(board.name)}"
    work_dir = payload.klipper_path.rstrip("/")
    return {
        "output_dir": output_dir,
        "config_backup_path": f"{output_dir}/.config.before-build",
        "generated_config_path": f"{output_dir}/generated/{Path(board.config_file).name}",
        "work_dir": work_dir,
        "expected_build_output": f"{work_dir}/{preset.build_output}",
        "binary_output_path": f"{output_dir}/{Path(preset.build_output).name}",
        "log_path": f"{output_dir}/logs/build.log",
    }


def _build_dry_run_commands(
    preset: BoardPreset,
    paths: dict[str, str],
    generated_config_lines: int,
) -> list[str]:
    return [
        "PLAN dry_run_only=true",
        f"PLAN preset_id={preset.id}",
        f"PLAN preset_build_config_status={preset.build_config_status}",
        f"PLAN generated_config_path={paths['generated_config_path']}",
        f"PLAN config_backup_path={paths['config_backup_path']}",
        f"PLAN work_dir={paths['work_dir']}",
        f"PLAN expected_build_output={paths['expected_build_output']}",
        f"PLAN binary_output_path={paths['binary_output_path']}",
        f"PLAN log_path={paths['log_path']}",
        f"PLAN generated_config_lines={generated_config_lines}",
        f"PLAN mkdir -p {paths['output_dir']}/generated {paths['output_dir']}/logs",
        f"PLAN write deterministic .config preview to {paths['generated_config_path']}",
        f"PLAN cd {paths['work_dir']}",
        f"PLAN cp .config {paths['config_backup_path']}",
        "PLAN make clean",
        f"PLAN cp {paths['generated_config_path']} .config",
        "PLAN make",
        f"PLAN cp {preset.build_output} {paths['binary_output_path']}",
        f"PLAN cp {paths['config_backup_path']} .config",
        f"PLAN capture build log at {paths['log_path']}",
    ]


def _build_dry_run_checklist(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    paths: dict[str, str],
) -> list[str]:
    return [
        "Confirmar que a impressora não está imprimindo.",
        "Confirmar Klipper/Moonraker conectados e sem erro.",
        f"Confirmar preset {preset.id} para {board.name}.",
        f"Confirmar status do preset: {preset.build_config_status}.",
        f"Confirmar MCU {preset.mcu}, arquitetura {preset.architecture} e bootloader {preset.bootloader_offset}.",
        f"Confirmar .config gerado planejado: {paths['generated_config_path']}.",
        f"Confirmar backup planejado da .config atual: {paths['config_backup_path']}.",
        f"Confirmar diretório de trabalho planejado: {paths['work_dir']}.",
        f"Confirmar saída esperada do build: {paths['expected_build_output']}.",
        f"Confirmar log planejado: {paths['log_path']}.",
        f"Confirmar binário planejado para artefato Printora: {paths['binary_output_path']}.",
        f"Confirmar UUID CAN {board.can_uuid or '-'} antes de qualquer flash futuro.",
        "Confirmar backup da .config antes de sobrescrever em build real futuro.",
        "Confirmar que build local só roda com modo local e confirmação explícita.",
        "Confirmar que dry-run apenas registra plano e não executou comandos.",
    ]


def _build_local_build_preflight(
    board: FirmwareBoardRecord,
    preset: BoardPreset,
    payload: FirmwareBuildDryRunCreate,
    mode: str,
) -> FirmwareBuildPreflight:
    klipper_path = Path(payload.klipper_path).expanduser()
    output_root = Path(payload.output_root).expanduser()
    expected_output = klipper_path / preset.build_output
    plan = _build_dry_run_plan(board, preset, payload)
    generated_config_path = str(plan["generated_config_path"])
    checks = [
        _preflight_check(
            "preset_build_config",
            "Preset completo para build config",
            preset.build_config_status == "complete",
            f"{preset.id}: {preset.build_config_status}",
            "Preset sem dados suficientes para gerar .config.",
        ),
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
        FirmwareBuildPreflightCheck(
            key="generated_config",
            label=".config gerado planejado",
            status="warning",
            detail=f"{generated_config_path} será criado somente em build futuro controlado; nenhum arquivo foi escrito.",
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
        config_file=generated_config_path,
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
    config_preview = generate_firmware_config_preview(preset)
    output_dir = f"{payload.output_root.rstrip('/')}/local-build/{_slug(board.name)}"
    paths = {
        "output_dir": output_dir,
        "config_backup_path": f"{output_dir}/.config.before-build",
        "generated_config_path": f"{output_dir}/generated/{Path(board.config_file).name}",
        "work_dir": payload.klipper_path.rstrip("/"),
        "expected_build_output": f"{payload.klipper_path.rstrip('/')}/{preset.build_output}",
        "binary_output_path": f"{output_dir}/{Path(preset.build_output).name}",
        "log_path": f"{output_dir}/logs/build.log",
    }
    plan["output_dir"] = output_dir
    plan["config_backup_path"] = paths["config_backup_path"]
    plan["binary_output_path"] = paths["binary_output_path"]
    plan["generated_config_path"] = paths["generated_config_path"]
    plan["work_dir"] = paths["work_dir"]
    plan["expected_build_output"] = paths["expected_build_output"]
    plan["log_path"] = paths["log_path"]
    plan["commands"] = _build_dry_run_commands(preset, paths, len(config_preview.lines))
    plan["checklist"] = _build_dry_run_checklist(board, preset, paths)


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
    generated_config_path = output_dir / "generated" / Path(board.config_file).name
    log_path = output_dir / "logs" / "build.log"
    klipper_config = klipper_path / ".config"
    build_output = klipper_path / preset.build_output
    config_preview = generate_firmware_config_preview(preset)

    if not klipper_path.is_dir():
        raise ValueError(f"klipper path not found: {klipper_path}")
    if not (klipper_path / "Makefile").is_file():
        raise ValueError("klipper path does not contain Makefile")
    if not klipper_config.is_file():
        raise ValueError("current .config not found")

    generated_config_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    generated_config_path.write_text(config_preview.content, encoding="utf-8")
    shutil.copy2(klipper_config, backup_path)
    restored = False
    logs: list[str] = []
    try:
        logs.append(_run_make(["make", "clean"], klipper_path, timeout_seconds))
        shutil.copy2(generated_config_path, klipper_config)
        logs.append(_run_make(["make"], klipper_path, timeout_seconds))
        if not build_output.is_file():
            raise ValueError(f"expected build output not found: {build_output}")
        shutil.copy2(build_output, binary_path)
    except Exception as exc:
        logs.append(f"ERROR: {exc}")
        raise
    finally:
        log_path.write_text("\n".join(logs), encoding="utf-8")
        if backup_path.is_file():
            shutil.copy2(backup_path, klipper_config)
            restored = True
        if not restored:
            raise RuntimeError("failed to restore original .config")
    return f"{log_path}: {_excerpt(chr(10).join(logs))}"


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
