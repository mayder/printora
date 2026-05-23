import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "npm_frontend_install.sh"


def test_frontend_npm_install_cleans_node_modules_and_retries(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    bin_dir = tmp_path / "bin"
    state = tmp_path / "npm-attempt"
    frontend.mkdir()
    bin_dir.mkdir()
    (frontend / "package.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
    (frontend / "node_modules" / "caniuse-lite").mkdir(parents=True)
    npm = bin_dir / "npm"
    npm.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "cache" ]]; then exit 0; fi
if [[ ! -f "{state}" ]]; then
  touch "{state}"
  echo "npm ERR! code ENOTEMPTY" >&2
  exit 217
fi
mkdir -p "$2/node_modules/react"
""",
        encoding="utf-8",
    )
    npm.chmod(0o755)

    result = subprocess.run(
        ["bash", str(SCRIPT), str(frontend), str(npm)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )

    assert "limpando somente" in result.stderr
    assert not (frontend / "node_modules" / "caniuse-lite").exists()
    assert (frontend / "node_modules" / "react").is_dir()
