from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import initialize_database
from app.database import connect_database
from app.main import app


def test_agent_jobs_are_isolated_by_printer_and_idempotent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-channel@example.com")
            other_token = _register(client, "other-channel@example.com")
            printer = _create_printer(client, owner_token, "Voron Owner")
            other_printer = _create_printer(client, other_token, "Voron Other")
            credential = _pair_agent(client, owner_token, printer["id"], "agent-channel-owner")
            other_credential = _pair_agent(client, other_token, other_printer["id"], "agent-channel-other")

            created_job = client.post(
                f"/api/printers/{printer['id']}/agent/jobs",
                json={"job_type": "ping", "payload": {"safe": True}, "correlation_id": "job-owner-001"},
                headers=_auth(owner_token),
            )
            assert created_job.status_code == 200
            job = created_job.json()

            other_jobs = client.get("/api/agent/jobs/next", headers=_auth(other_credential))
            assert other_jobs.status_code == 200
            assert other_jobs.json()["jobs"] == []

            jobs = client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"]
            assert [item["correlation_id"] for item in jobs] == ["job-owner-001"]

            ack = client.post(f"/api/agent/jobs/{job['id']}/ack", headers=_auth(credential))
            assert ack.status_code == 200
            assert ack.json()["status"] == "in_progress"

            result_payload = {"correlation_id": "job-owner-001", "result": {"pong": True}}
            first_result = client.post(f"/api/agent/jobs/{job['id']}/result", json=result_payload, headers=_auth(credential))
            second_result = client.post(f"/api/agent/jobs/{job['id']}/result", json=result_payload, headers=_auth(credential))
            assert first_result.status_code == 200
            assert second_result.status_code == 200
            assert first_result.json()["status"] == "succeeded"
            assert second_result.json()["status"] == "succeeded"
            assert client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"] == []
    finally:
        get_settings.cache_clear()


def test_agent_job_result_accepts_visual_payload_above_command_limit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-channel-visual@example.com")
            printer = _create_printer(client, owner_token, "Voron Visual")
            credential = _pair_agent(client, owner_token, printer["id"], "agent-channel-visual")
            job = client.post(
                f"/api/printers/{printer['id']}/agent/jobs",
                json={"job_type": "remote_operation_status", "payload": {}, "correlation_id": "job-visual-001"},
                headers=_auth(owner_token),
            ).json()

            assert client.post(f"/api/agent/jobs/{job['id']}/ack", headers=_auth(credential)).status_code == 200
            visual_result = {
                "safe_mode": "read_only",
                "kind": "operation_status",
                "file_metadata": {
                    "result": {
                        "printora_visuals": {
                            "layer_preview": {
                                "source": "agent_gcode",
                                "scene": {"kind": "gcode_layer_scene", "printed": "x" * (96 * 1024)},
                            }
                        }
                    }
                },
            }
            response = client.post(
                f"/api/agent/jobs/{job['id']}/result",
                json={"correlation_id": "job-visual-001", "result": visual_result},
                headers=_auth(credential),
            )

            assert response.status_code == 200
            assert response.json()["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_in_progress_job_is_resumed_after_agent_reconnect(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-resume@example.com")
            printer = _create_printer(client, owner_token, "Voron Resume")
            credential = _pair_agent(client, owner_token, printer["id"], "agent-channel-resume")
            job = client.post(
                f"/api/printers/{printer['id']}/agent/jobs",
                json={"job_type": "ping", "payload": {}, "correlation_id": "job-resume-001"},
                headers=_auth(owner_token),
            ).json()
            assert client.post(f"/api/agent/jobs/{job['id']}/ack", headers=_auth(credential)).status_code == 200

            resumed = client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"]
            assert [item["id"] for item in resumed] == [job["id"]]
            assert resumed[0]["status"] == "in_progress"
            result = client.post(
                f"/api/agent/jobs/{job['id']}/result",
                json={"correlation_id": "job-resume-001", "result": {"pong": True}},
                headers=_auth(credential),
            )
            assert result.json()["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_agent_websocket_contract_version_and_job_flow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-ws@example.com")
            printer = _create_printer(client, owner_token, "Voron WS")
            credential = _pair_agent(client, owner_token, printer["id"], "agent-channel-ws")
            job = client.post(
                f"/api/printers/{printer['id']}/agent/jobs",
                json={"job_type": "ping", "payload": {}, "correlation_id": "job-ws-001"},
                headers=_auth(owner_token),
            ).json()

            with client.websocket_connect("/api/agent/ws", headers=_auth(credential)) as websocket:
                hello = websocket.receive_json()
                assert hello["message_type"] == "hello"
                websocket.send_json(
                    {
                        "protocol_version": 1,
                        "message_type": "hello",
                        "correlation_id": "hello-agent",
                        "payload": {"agent_version": "0.1.0", "platform": "linux", "capabilities": {"jobs": True}},
                    }
                )
                assert websocket.receive_json()["message_type"] == "ack"
                job_message = websocket.receive_json()
                assert job_message["message_type"] == "job"
                assert job_message["payload"]["correlation_id"] == "job-ws-001"
                websocket.send_json(
                    {
                        "protocol_version": 1,
                        "message_type": "ack",
                        "correlation_id": "ack-job",
                        "payload": {"job_id": job["id"]},
                    }
                )
                assert websocket.receive_json()["message_type"] == "ack"
                websocket.send_json(
                    {
                        "protocol_version": 1,
                        "message_type": "result",
                        "correlation_id": "result-job",
                        "payload": {"job_id": job["id"], "correlation_id": "job-ws-001", "result": {"pong": True}},
                    }
                )
                result_ack = websocket.receive_json()
                assert result_ack["payload"]["status"] == "succeeded"

            assert client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"] == []
        with connect_database(tmp_path / "printora.db") as connection:
            session = connection.execute(
                "SELECT disconnected_at, last_acknowledged_job_id FROM realtime_sessions ORDER BY connected_at DESC LIMIT 1"
            ).fetchone()
        assert session["disconnected_at"] is not None
        assert session["last_acknowledged_job_id"] == job["id"]
    finally:
        get_settings.cache_clear()


def test_agent_websocket_rejects_incompatible_protocol(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = _register(client, "owner-ws-bad@example.com")
            printer = _create_printer(client, owner_token, "Voron WS Bad")
            credential = _pair_agent(client, owner_token, printer["id"], "agent-channel-ws-bad")
            with client.websocket_connect("/api/agent/ws", headers=_auth(credential)) as websocket:
                assert websocket.receive_json()["message_type"] == "hello"
                websocket.send_json(
                    {"protocol_version": 999, "message_type": "hello", "correlation_id": "bad-version", "payload": {}}
                )
                response = websocket.receive_json()
                assert response["message_type"] == "error"
                assert response["payload"]["reason"] == "protocol_version_incompatible"
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_printer(client: TestClient, token: str, name: str) -> dict:
    response = client.post(
        "/api/printers",
        json={"name": name, "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    return response.json()


def _pair_agent(client: TestClient, token: str, printer_id: int, stable_id: str) -> str:
    pairing = client.post(
        f"/api/printers/{printer_id}/pairing/tokens",
        json={"ttl_minutes": 15},
        headers=_auth(token),
    ).json()
    exchanged = client.post(
        "/api/agent/pairing/exchange",
        json={"pairing_token": pairing["token"], "stable_id": stable_id, "agent_version": "0.1.0"},
    )
    assert exchanged.status_code == 200
    return exchanged.json()["credential"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
