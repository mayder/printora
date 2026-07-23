from pathlib import Path
import json
import os
import subprocess

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import connect_database
from app.database import initialize_database
from app.main import app


def test_agent_install_plan_generates_single_use_token_and_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-install@example.com")
            other_token = _register(client, "other-install@example.com")
            printer = _create_printer(client, owner_token)

            blocked = client.post(f"/api/printers/{printer['id']}/agent/install-plan", headers=_auth(other_token))
            assert blocked.status_code == 404

            plan_response = client.post(f"/api/printers/{printer['id']}/agent/install-plan", headers=_auth(owner_token))
            assert plan_response.status_code == 200
            plan = plan_response.json()
            assert plan["install_command"].startswith("curl -fsSL")
            assert "/api/agent/install/linux.sh" in plan["install_command"]
            assert "PRINTORA_PAIRING_TOKEN='ptr_pair_" in plan["install_command"]
            assert "PRINTORA_AGENT_VERSION='0.1.34'" in plan["install_command"]
            assert "PRINTORA_AGENT_BIN_URL='http://testserver/api/agent/update/releases/0.1.34/linux-arm64'" in plan["install_command"]
            assert "PRINTORA_AGENT_SHA256='c430f3b1" in plan["install_command"]
            assert "PRINTORA_AGENT_SIGNATURE=" in plan["install_command"]
            assert "PRINTORA_MOONRAKER_URL='http://127.0.0.1:7125'" in plan["install_command"]
            assert plan["token_prefix"] in plan["install_command"]

            token = _extract_token(plan["install_command"])
            exchanged = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token, "stable_id": "agent-install-001", "agent_version": "0.1.34"},
            )
            assert exchanged.status_code == 200
            reused = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token, "stable_id": "agent-install-002", "agent_version": "0.1.34"},
            )
            assert reused.status_code == 400
    finally:
        get_settings.cache_clear()


def test_agent_install_status_requires_heartbeat_and_expected_version(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-install-status@example.com")
            printer = _create_printer(client, owner_token)
            initial = client.get(f"/api/printers/{printer['id']}/agent/install-status", headers=_auth(owner_token))
            assert initial.status_code == 200
            assert initial.json()["ready"] is False
            assert "nenhum agente" in initial.json()["diagnostic"]

            plan = client.post(f"/api/printers/{printer['id']}/agent/install-plan", headers=_auth(owner_token)).json()
            token = _extract_token(plan["install_command"])
            credential = client.post(
                "/api/agent/pairing/exchange",
                json={"pairing_token": token, "stable_id": "agent-install-status", "agent_version": "0.1.34"},
            ).json()["credential"]
            paired = client.get(f"/api/printers/{printer['id']}/agent/install-status", headers=_auth(owner_token)).json()
            assert paired["ready"] is False
            assert "aguardando heartbeat" in paired["diagnostic"]

            heartbeat = client.post(
                "/api/agent/heartbeat",
                json={"agent_version": "0.1.34", "platform": "linux/arm64", "capabilities": {"installer": True}},
                headers=_auth(credential),
            )
            assert heartbeat.status_code == 200
            ready = client.get(f"/api/printers/{printer['id']}/agent/install-status", headers=_auth(owner_token)).json()
            assert ready["ready"] is True
            assert ready["latest_version"] == "0.1.34"

            with connect_database(tmp_path / "printora.db") as connection:
                connection.execute(
                    "UPDATE printer_agents SET last_seen_at = datetime('now', '-10 minutes') WHERE id = ?",
                    (ready["latest_agent_id"],),
                )
            offline = client.get(f"/api/printers/{printer['id']}/agent/install-status", headers=_auth(owner_token)).json()
            assert offline["ready"] is False
            assert "offline" in offline["diagnostic"]
            assert "revogue/remova" in offline["diagnostic"]
    finally:
        get_settings.cache_clear()


def test_agent_installer_preflight_is_safe_and_redacts_token() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "install_agent_linux.sh"
    env = {
        **os.environ,
        "PRINTORA_AGENT_INSTALL_TEST_MODE": "1",
        "PRINTORA_API_BASE": "https://printora.example.test",
        "PRINTORA_PAIRING_TOKEN": "ptr_pair_secret_should_not_leak",
        "PRINTORA_MOONRAKER_URL": "http://127.0.0.1:1",
    }
    result = subprocess.run(["bash", str(script), "--preflight"], env=env, text=True, capture_output=True, check=False)
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "preflight concluído" in combined
    assert "ptr_pair_secret_should_not_leak" not in combined
    assert "token: configurado" in combined


def test_agent_installer_pairing_error_json_is_actionable_and_redacted(tmp_path: Path) -> None:
    result = _run_exchange_with_fake_curl(
        tmp_path,
        status="409",
        body='{"detail":"Este host já está pareado como printora-FrankXY-d595193a29ec. Revogue/remova o agente antigo antes de reinstalar."}',
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "falha ao parear agente (HTTP 409)" in combined
    assert "Revogue/remova o agente antigo" in combined
    assert "JSONDecodeError" not in combined
    assert "ptr_pair_secret_should_not_leak" not in combined


def test_agent_installer_pairing_error_text_body_does_not_parse_as_json(tmp_path: Path) -> None:
    result = _run_exchange_with_fake_curl(
        tmp_path,
        status="400",
        body="<html><body>Bad request</body></html>",
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "falha ao parear agente (HTTP 400)" in combined
    assert "Gere um novo comando ou remova o agente antigo" in combined
    assert "JSONDecodeError" not in combined
    assert "Bad request" not in combined
    assert "ptr_pair_secret_should_not_leak" not in combined


def test_agent_installer_notifies_api_after_service_install() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "install_agent_linux.sh"
    content = script.read_text()
    assert "notify_install_success" in content
    assert "$API_BASE/api/agent/heartbeat" in content
    assert "install_success" in content


def test_agent_installer_verifies_release_checksum_and_signature(tmp_path: Path) -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    script = backend_dir / "scripts" / "install_agent_linux.sh"
    release_dir = backend_dir / "app" / "data" / "agent_releases"
    artifact = release_dir / "printora-agent-linux-arm64-0.1.34"
    metadata = json.loads(
        (release_dir / "printora-agent-linux-arm64-0.1.34.metadata.json").read_text()
    )
    env = {
        **os.environ,
        "PRINTORA_AGENT_INSTALL_SOURCE_ONLY": "1",
        "PRINTORA_AGENT_SHA256": metadata["sha256"],
        "PRINTORA_AGENT_SIGNATURE": metadata["signature"],
    }
    valid = subprocess.run(
        ["bash", "-c", f"source {script!s}; verify_release {artifact!s}"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert valid.returncode == 0, valid.stderr

    tampered = tmp_path / "tampered-agent"
    tampered.write_bytes(artifact.read_bytes() + b"tampered")
    invalid = subprocess.run(
        ["bash", "-c", f"source {script!s}; verify_release {tampered!s}"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert invalid.returncode != 0
    assert "checksum do agente não confere" in invalid.stderr

    invalid_signature_env = {
        **env,
        "PRINTORA_AGENT_SIGNATURE": metadata["signature"][:-4] + "AAAA",
    }
    invalid_signature = subprocess.run(
        ["bash", "-c", f"source {script!s}; verify_release {artifact!s}"],
        env=invalid_signature_env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert invalid_signature.returncode != 0
    assert "assinatura do agente não confere" in invalid_signature.stderr


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": "Voron Install", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _extract_token(command: str) -> str:
    marker = "PRINTORA_PAIRING_TOKEN='"
    start = command.index(marker) + len(marker)
    end = command.index("'", start)
    return command[start:end]


def _run_exchange_with_fake_curl(tmp_path: Path, *, status: str, body: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "install_agent_linux.sh"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
out=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) out="$2"; shift 2 ;;
    -w) shift 2 ;;
    *) shift ;;
  esac
done
printf '%s' {body!r} > "$out"
printf '%s' {status!r}
"""
    )
    fake_curl.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PRINTORA_AGENT_INSTALL_SOURCE_ONLY": "1",
        "PRINTORA_API_BASE": "https://printora.example.test",
        "PRINTORA_PAIRING_TOKEN": "ptr_pair_secret_should_not_leak",
        "PRINTORA_AGENT_VERSION": "0.1.17",
    }
    return subprocess.run(
        ["bash", "-c", f"source {script}; exchange_token"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
