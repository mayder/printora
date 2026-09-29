from pathlib import Path
import subprocess


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_strict_secret_scan_ignores_generated_files_and_redacts_match(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for name in ("common.sh", "validate-no-secrets.sh"):
        (scripts_dir / name).write_text((ROOT_DIR / "scripts" / name).read_text())
    (tmp_path / ".gitignore").write_text("dist/\n")
    (tmp_path / "safe.txt").write_text("token = <configured-outside-git>\n")
    generated = tmp_path / "dist" / "bundle.js"
    generated.parent.mkdir()
    generated.write_text("token" + "=generated-placeholder\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", ".gitignore", "safe.txt", "scripts"], cwd=tmp_path, check=True)

    passed = subprocess.run(
        ["bash", "scripts/validate-no-secrets.sh"],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "CHECK_STRICT_SECRETS": "1"},
        capture_output=True,
        text=True,
    )
    assert passed.returncode == 0, passed.stderr

    leaked_value = "should-never-appear-in-scanner-output"
    sensitive_fixture = tmp_path / "tracked.env"
    sensitive_fixture.write_text("API" + f"_KEY={leaked_value}\n")
    subprocess.run(["git", "add", "tracked.env"], cwd=tmp_path, check=True)
    failed = subprocess.run(
        ["bash", "scripts/validate-no-secrets.sh"],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "CHECK_STRICT_SECRETS": "1"},
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "tracked.env" in failed.stderr
    assert leaked_value not in failed.stdout + failed.stderr
