import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "android_update_printora.sh"


def test_android_update_script_plan_uses_mocks_and_does_not_modify_project(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    project = tmp_path / "Printora"
    data_dir = tmp_path / "data"
    bin_dir = tmp_path / "bin"
    data_dir.mkdir()
    bin_dir.mkdir()

    subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "init", str(source)], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
    (source / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-m", "fixture"], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "-C", str(source), "tag", "v0.1.1"], check=True)
    subprocess.run(["git", "-C", str(source), "remote", "add", "origin", str(remote)], check=True)
    branch = subprocess.run(
        ["git", "-C", str(source), "branch", "--show-current"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    subprocess.run(["git", "-C", str(source), "push", "origin", branch, "--tags"], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "clone", str(remote), str(project)], check=True, stdout=subprocess.PIPE)

    tmux_mock = bin_dir / "tmux"
    tmux_mock.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    tmux_mock.chmod(0o755)
    python_mock = bin_dir / "python"
    python_mock.write_text("#!/usr/bin/env bash\nexec python3 \"$@\"\n", encoding="utf-8")
    python_mock.chmod(0o755)
    before = sorted(path.relative_to(project) for path in project.rglob("*"))

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "HOME": str(tmp_path),
            "ROOT_DIR": str(project),
            "PRINTORA_DATA_DIR": str(data_dir),
            "PRINTORA_UPDATE_REMOTE_URL": str(remote),
        }
    )
    result = subprocess.run(
        ["bash", str(SCRIPT), "--plan", "--tag", "v0.1.1"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    payload = json.loads(result.stdout)
    after = sorted(path.relative_to(project) for path in project.rglob("*"))
    assert payload["status"] == "planned"
    assert payload["environment"] == "android_termux"
    assert payload["target_tag"] == "v0.1.1"
    assert payload["will_modify_files"] is False
    assert [step["key"] for step in payload["steps"]][0] == "validate_environment"
    assert before == after
