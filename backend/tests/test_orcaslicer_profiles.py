from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/orcaslicer/install-voron-02-profiles.py"
PROCESS_DIR = REPO_ROOT / "packaging/orcaslicer/profiles/process"


def _load_installer():
    spec = importlib.util.spec_from_file_location("orcaslicer_installer", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_v02_profiles_are_exact_safe_derivations_of_v24_profiles() -> None:
    installer = _load_installer()
    sources = installer.load_v24_profiles(PROCESS_DIR)
    targets = installer.validate_v02_profiles(sources, PROCESS_DIR)

    assert len(sources) == len(targets) == 14
    for target_path in targets:
        profile = installer.read_json(target_path)
        assert profile["name"].startswith(installer.V02_PREFIX)
        assert profile["compatible_printers"] == [
            installer.V02_SYSTEM_MACHINE,
            installer.V02_MACHINE,
        ]
        for key in installer.WIDTH_KEYS:
            if key in profile:
                assert float(profile[key]) >= 0.4


def test_default_command_only_validates_without_touching_orca(tmp_path: Path) -> None:
    missing_orca = tmp_path / "OrcaSlicer"

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--orca-dir", str(missing_orca)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "mode=validation" in result.stdout
    assert "Nenhum arquivo local foi alterado" in result.stdout
    assert not missing_orca.exists()


def test_apply_backs_up_and_installs_profiles_in_controlled_directory(
    tmp_path: Path,
) -> None:
    installer = _load_installer()
    orca_dir = tmp_path / "OrcaSlicer"
    _write_json(
        orca_dir / "OrcaSlicer.conf",
        {
            "models": [],
            "orca_presets": [
                {
                    "machine": installer.V02_SYSTEM_MACHINE,
                    "process": "0.20mm Standard @Voron",
                    "filament": "Generic PLA @System",
                }
            ],
        },
    )
    _write_json(orca_dir / "user/default/process/Anterior.json", {"name": "Anterior"})
    _write_json(orca_dir / "user/default/machine/Anterior.json", {"name": "Anterior"})

    profiles = installer.validate_v02_profiles(
        installer.load_v24_profiles(PROCESS_DIR), PROCESS_DIR
    )
    installer.validate_local_state(orca_dir)
    installer.validate_print_host("http://voron-02-pro.local")
    backup = installer.backup_local_state(orca_dir)
    installer.install_machine(orca_dir, "http://voron-02-pro.local")
    installer.install_process_profiles(orca_dir, profiles)
    installer.enable_v02_model(orca_dir)

    assert (backup / "process/Anterior.json").is_file()
    assert (backup / "machine/Anterior.json").is_file()
    assert (backup / "OrcaSlicer.conf").is_file()
    installed = sorted((orca_dir / "user/default/process").glob("V02 0.4 - *.json"))
    assert len(installed) == 14
    machine = installer.read_json(
        orca_dir / f"user/default/machine/{installer.V02_MACHINE}.json"
    )
    assert machine["print_host"] == "http://voron-02-pro.local"
    config = installer.read_json(orca_dir / "OrcaSlicer.conf")
    assert any(model["model"] == "Voron 0.1" for model in config["models"])
    assert any(
        preset["machine"] == installer.V02_MACHINE
        and preset["process"] == "V02 0.4 - 0.24 Qualidade Padrao"
        for preset in config["orca_presets"]
    )


@pytest.mark.parametrize(
    "host",
    ["voron-02-pro.local", "ftp://voron-02-pro.local", "http://user:secret@host"],
)
def test_print_host_rejects_invalid_or_embedded_credentials(host: str) -> None:
    installer = _load_installer()
    with pytest.raises(RuntimeError):
        installer.validate_print_host(host)
