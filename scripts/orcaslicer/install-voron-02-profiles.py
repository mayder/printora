#!/usr/bin/env python3
"""Version and install Voron 0.2 profiles derived from the Voron 2.4 set."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse


V24_PREFIX = "V24 0.6 - "
V02_PREFIX = "V02 0.4 - "
V02_MACHINE = "Voron 0.2 120 0.4 nozzle - 290126"
V02_SYSTEM_MACHINE = "Voron 0.1 0.4 nozzle"
WIDTH_KEYS = {
    "line_width",
    "initial_layer_line_width",
    "outer_wall_line_width",
    "inner_wall_line_width",
    "top_surface_line_width",
    "sparse_infill_line_width",
    "internal_solid_infill_line_width",
    "support_line_width",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--orca-dir",
        type=Path,
        default=Path.home() / "Library/Application Support/OrcaSlicer",
    )
    parser.add_argument("--v02-host", default="http://voron-02-pro.local")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Cria o backup e instala os perfis. Sem esta opção, apenas valida.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent="\t") + "\n",
        encoding="utf-8",
    )


def write_info(path: Path, base_id: str) -> None:
    path.write_text(
        "\n".join(
            [
                "sync_info = create",
                "user_id = ",
                "setting_id = ",
                f"base_id = {base_id}",
                f"updated_time = {int(time.time())}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def load_v24_profiles(repo_process: Path) -> list[Path]:
    sources = sorted(repo_process.glob(f"{V24_PREFIX}*.json"))
    if len(sources) != 14:
        raise RuntimeError(
            f"Esperados 14 perfis V24 versionados em {repo_process}; "
            f"encontrados {len(sources)}"
        )
    return sources


def base_process_for(layer_height: float) -> str:
    if layer_height <= 0.20:
        return "0.20mm Standard @Voron"
    if layer_height <= 0.24:
        return "0.24mm Draft @Voron"
    return "0.28mm Extra Draft @Voron"


def scale_width(value: str) -> str:
    scaled = max(0.4, float(value) * 2 / 3)
    return f"{scaled:.2f}".rstrip("0").rstrip(".")


def derive_v02_profile(source: dict) -> dict:
    source_name = source["name"]
    if not source_name.startswith(V24_PREFIX):
        raise RuntimeError(f"Nome V24 inesperado: {source_name}")

    target = dict(source)
    target_name = V02_PREFIX + source_name.removeprefix(V24_PREFIX)
    layer_height = float(target.get("layer_height", "0.18"))

    target["name"] = target_name
    target["print_settings_id"] = target_name
    target["inherits"] = base_process_for(layer_height)
    target["layer_height"] = f"{layer_height:.2f}"
    target["compatible_printers"] = [V02_SYSTEM_MACHINE, V02_MACHINE]

    for key in WIDTH_KEYS:
        if key in target:
            target[key] = scale_width(target[key])

    return target


def validate_v02_profiles(v24_sources: list[Path], repo_process: Path) -> list[Path]:
    expected_names: set[str] = set()
    targets: list[Path] = []
    for source_path in v24_sources:
        expected = derive_v02_profile(read_json(source_path))
        target_path = repo_process / f"{expected['name']}.json"
        expected_names.add(target_path.name)
        if not target_path.exists():
            raise RuntimeError(f"Perfil V02 ausente: {target_path.name}")
        if read_json(target_path) != expected:
            raise RuntimeError(
                f"Perfil V02 divergiu da fonte V24: {target_path.name}"
            )
        targets.append(target_path)

    unexpected = sorted(
        path.name
        for path in repo_process.glob(f"{V02_PREFIX}*.json")
        if path.name not in expected_names
    )
    if unexpected:
        raise RuntimeError(f"Perfis V02 inesperados: {', '.join(unexpected)}")
    return targets


def validate_local_state(orca_dir: Path) -> None:
    if not orca_dir.is_dir():
        raise RuntimeError(f"Diretório do OrcaSlicer não encontrado: {orca_dir}")
    config = orca_dir / "OrcaSlicer.conf"
    if not config.is_file():
        raise RuntimeError(f"Configuração do OrcaSlicer não encontrada: {config}")
    read_json(config)


def validate_print_host(print_host: str) -> None:
    parsed = urlparse(print_host)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RuntimeError("O endereço da Voron 0.2 deve usar HTTP ou HTTPS")
    if parsed.username or parsed.password:
        raise RuntimeError("O endereço da impressora não pode conter credenciais")


def backup_local_state(orca_dir: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = orca_dir / f"user_profile_backup_before_v02_restore_{stamp}"
    user_default = orca_dir / "user/default"
    backup.mkdir(parents=True, exist_ok=False)
    for subdir in ("machine", "process", "filament"):
        source = user_default / subdir
        if source.exists():
            shutil.copytree(source, backup / subdir)
    config = orca_dir / "OrcaSlicer.conf"
    if config.exists():
        shutil.copy2(config, backup / config.name)
    return backup


def install_machine(orca_dir: Path, print_host: str) -> None:
    backup_machine = (
        orca_dir
        / "user_profile_backup_before_v24_06_profiles_20260608-220702"
        / "machine"
        / "Voron 0.1 0.4 nozzle - Cópia.json"
    )
    machine = read_json(backup_machine) if backup_machine.exists() else {}
    machine.update(
        {
            "default_print_profile": f"{V02_PREFIX}0.24 Qualidade Padrao",
            "from": "User",
            "inherits": V02_SYSTEM_MACHINE,
            "is_custom_defined": "0",
            "name": V02_MACHINE,
            "print_host": print_host,
            "printer_settings_id": V02_MACHINE,
            "thumbnails": "48x48/PNG, 300x300/PNG",
            "version": machine.get("version", "2.4.0.3"),
        }
    )
    local_machine = orca_dir / "user/default/machine"
    write_json(local_machine / f"{V02_MACHINE}.json", machine)
    write_info(local_machine / f"{V02_MACHINE}.info", "GM001")


def install_process_profiles(orca_dir: Path, profiles: list[Path]) -> None:
    local_process = orca_dir / "user/default/process"
    local_process.mkdir(parents=True, exist_ok=True)
    for profile in profiles:
        destination = local_process / profile.name
        shutil.copy2(profile, destination)
        write_info(destination.with_suffix(".info"), "GP004")


def enable_v02_model(orca_dir: Path) -> None:
    config_path = orca_dir / "OrcaSlicer.conf"
    config = read_json(config_path)
    models = config.setdefault("models", [])
    wanted = {
        "model": "Voron 0.1",
        "nozzle_diameter": "0.4",
        "vendor": "Voron",
    }
    if not any(
        model.get("model") == wanted["model"]
        and model.get("nozzle_diameter") == wanted["nozzle_diameter"]
        and model.get("vendor") == wanted["vendor"]
        for model in models
    ):
        models.insert(0, wanted)
    process_name = f"{V02_PREFIX}0.24 Qualidade Padrao"
    presets = config.setdefault("orca_presets", [])
    matching = [preset for preset in presets if preset.get("machine") == V02_MACHINE]
    if not matching:
        base = next(
            (
                preset
                for preset in presets
                if preset.get("machine") == V02_SYSTEM_MACHINE
            ),
            {
                "curr_bed_type": "3",
                "filament": "Generic PLA @System",
                "filament_colors": "#26A69A",
            },
        )
        matching = [dict(base)]
        matching[0]["machine"] = V02_MACHINE
        presets.append(matching[0])
    matching[0]["process"] = process_name
    write_json(config_path, config)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    repo_process = repo_root / "packaging/orcaslicer/profiles/process"

    v24_sources = load_v24_profiles(repo_process)
    v02_profiles = validate_v02_profiles(v24_sources, repo_process)
    print(f"v24_profiles={len(v24_sources)}")
    print(f"v02_profiles={len(v02_profiles)}")
    if not args.apply:
        print("mode=validation")
        print("Nenhum arquivo local foi alterado. Use --apply para instalar.")
        return

    validate_print_host(args.v02_host)
    validate_local_state(args.orca_dir)
    backup = backup_local_state(args.orca_dir)
    install_machine(args.orca_dir, args.v02_host)
    install_process_profiles(args.orca_dir, v02_profiles)
    enable_v02_model(args.orca_dir)

    print(f"backup={backup}")
    print(f"machine={V02_MACHINE}")


if __name__ == "__main__":
    main()
