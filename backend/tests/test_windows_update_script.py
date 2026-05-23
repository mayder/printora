import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "update_printora_windows.ps1"


def test_windows_update_script_documents_required_modes_and_process_policy() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "--Plan" in text
    assert "--Apply" in text
    assert "--Rollback" in text
    assert "ExecutionPolicy" in text
    assert "Bypass" in text
    assert "printora.db.before-update-" in text
    assert "previous-update-" in text
    assert "Invoke-WebRequest" in text
    assert "npm --prefix" in text
    assert "-m pip install -e backend --no-deps" in text


def test_windows_update_script_parses_when_powershell_is_available() -> None:
    executable = shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe")
    if executable is None:
        return

    result = subprocess.run(
        [
            executable,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"$null = [scriptblock]::Create((Get-Content -Raw '{SCRIPT}'))",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
