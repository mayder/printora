import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "update_printora.sh"


def test_unix_update_script_plan_detects_macos_without_systemd(tmp_path: Path) -> None:
    remote, project = _create_git_project(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (project / "scripts" / "run_app.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (project / "scripts" / "run_app.sh").chmod(0o755)

    result = _run_plan(
        tmp_path=tmp_path,
        project=project,
        data_dir=data_dir,
        remote=remote,
        os_name="macos",
        systemd="false",
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "planned"
    assert payload["environment"] == "unix"
    assert payload["platform"] == "macos"
    assert payload["systemd_available"] is False
    assert payload["restart_mode"] == "runner"
    assert payload["will_modify_files"] is False


def test_unix_update_script_plan_detects_linux_systemd_service(tmp_path: Path) -> None:
    remote, project = _create_git_project(tmp_path)
    data_dir = tmp_path / "data"
    bin_dir = tmp_path / "bin"
    data_dir.mkdir()
    bin_dir.mkdir()
    _write_mock(bin_dir / "systemctl", "#!/usr/bin/env bash\nexit 0\n")

    result = _run_plan(
        tmp_path=tmp_path,
        project=project,
        data_dir=data_dir,
        remote=remote,
        os_name="linux",
        systemd="true",
        prepend_path=bin_dir,
    )

    payload = json.loads(result.stdout)
    assert payload["platform"] == "linux"
    assert payload["systemd_available"] is True
    assert payload["restart_mode"] == "systemd_user"


def test_unix_update_script_marks_run_before_systemd_restart() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "finish_systemd_self_restart_run" in script
    assert 'mark_step_skipped "validate_health"' in script
    assert 'if restart_mode_is_systemd; then' in script
    assert 'finish_systemd_self_restart_run "$db_backup" "$previous_path"' in script
    assert "restart_deferred" in script


def _run_plan(
    *,
    tmp_path: Path,
    project: Path,
    data_dir: Path,
    remote: Path,
    os_name: str,
    systemd: str,
    prepend_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    path_prefix = f"{prepend_path}:" if prepend_path is not None else ""
    env.update(
        {
            "PATH": f"{path_prefix}{env['PATH']}",
            "HOME": str(tmp_path),
            "ROOT_DIR": str(project),
            "PRINTORA_DATA_DIR": str(data_dir),
            "PRINTORA_UPDATE_REMOTE_URL": str(remote),
            "PRINTORA_UPDATE_OS_OVERRIDE": os_name,
            "PRINTORA_UPDATE_SYSTEMD_OVERRIDE": systemd,
        }
    )
    return subprocess.run(
        ["bash", str(SCRIPT), "--plan", "--tag", "v0.1.1"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def _create_git_project(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    project = tmp_path / "Printora"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "init", str(source)], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
    (source / "README.md").write_text("fixture\n", encoding="utf-8")
    (source / "scripts").mkdir()
    (source / "scripts" / "run_app.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
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
    return remote, project


def _write_mock(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
