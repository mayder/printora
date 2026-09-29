from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import Settings, get_settings
from app.database import initialize_database
from app.main import app
from app.print_preflight import parse_gcode_metadata
from app.printers import PrinterCreate, PrinterRepository
from app.slicing_pipeline import ModelDimensions, SlicingJobCreate, SlicingPipelineRepository


def test_gcode_metadata_parser_extracts_motion_and_temperatures() -> None:
    fixture = Path(__file__).parent / "fixtures" / "gcode" / "preflight_abs_cube.gcode"
    metadata = parse_gcode_metadata(fixture.read_text())

    assert metadata.command_count == 5
    assert metadata.max_x_mm == 80
    assert metadata.max_y_mm == 75
    assert metadata.max_z_mm == 2.0
    assert metadata.max_nozzle_temperature_c == 245
    assert metadata.max_bed_temperature_c == 110
    assert metadata.filament_type == "ABS"
    assert metadata.nozzle_diameter_mm == 0.4
    assert metadata.estimated_time_seconds == 1110


def test_print_preflight_blocks_without_online_agent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "preflight-no-agent@example.com")
            job = _completed_slicing_job(tmp_path, token)

            response = client.post(f"/api/slicing/jobs/{job['id']}/preflight", headers=_auth(token))

            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "blocked"
            assert "Preflight remoto exige agente ativo" in " ".join(payload["blockers"])
            assert payload["local_metadata"]["command_count"] > 0
    finally:
        get_settings.cache_clear()


def test_print_preflight_approves_after_remote_agent_result(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "preflight-agent@example.com")
            job = _completed_slicing_job(tmp_path, token)
            credential = _pair_agent(client, token, job["printer_id"], "agent-preflight-001")

            created = client.post(f"/api/slicing/jobs/{job['id']}/preflight", headers=_auth(token))
            assert created.status_code == 200
            preflight = created.json()
            assert preflight["status"] == "pending_remote"
            assert preflight["remote_agent_job_id"]

            _finish_job(
                client,
                credential,
                preflight["remote_agent_job_id"],
                {
                    "safe_mode": "remote_gcode_preflight",
                    "can_execute": True,
                    "printing": False,
                    "print_state": "standby",
                    "blockers": [],
                },
            )
            refreshed = client.post(f"/api/slicing/preflights/{preflight['id']}/refresh", headers=_auth(token))

            assert refreshed.status_code == 200
            payload = refreshed.json()
            assert payload["status"] == "approved"
            assert payload["approved_at"] is not None
    finally:
        get_settings.cache_clear()


def test_print_preflight_blocks_dangerous_gcode_temperature(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="danger-temp@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron temp", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
    )
    job = _completed_job_with_gcode(tmp_path, database_path, user.id, printer.id, "M104 S360\nG1 X10 Y10 Z1\n")
    repository = __import__("app.print_preflight", fromlist=["PrintPreflightRepository"]).PrintPreflightRepository(database_path, tmp_path)

    preflight = repository.create_preflight(printer, user.id, job.id)

    assert preflight.status == "blocked"
    assert any("nozzle" in blocker for blocker in preflight.blockers)


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _completed_slicing_job(tmp_path: Path, token: str) -> dict:
    database_path = tmp_path / "printora.db"
    with TestClient(app) as client:
        printer = client.post(
            "/api/printers",
            json={"name": "Voron preflight", "moonraker_url": "http://127.0.0.1:7125", "host_audit_mode": "disabled"},
            headers=_auth(token),
        ).json()
    user_id = AuthRepository(database_path).get_user_by_session(token).id
    return _completed_job_with_gcode(tmp_path, database_path, user_id, printer["id"], "; filament_type = ABS\nM104 S245\nM140 S110\nG1 X50 Y50 Z2\n").model_dump()


def _completed_job_with_gcode(tmp_path: Path, database_path: Path, user_id: int, printer_id: int, gcode: str):
    engine = tmp_path / "orcaslicer"
    engine.write_text(
        """#!/usr/bin/env bash
if [[ "$1" == "--version" ]]; then echo "OrcaSlicer fake"; exit 0; fi
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == "--output" ]]; then shift; cat "$PRINTORA_FAKE_GCODE" > "$1"; exit 0; fi
  shift
done
exit 2
""",
        encoding="utf-8",
    )
    engine.chmod(0o755)
    fake_gcode = tmp_path / "fake.gcode"
    fake_gcode.write_text(gcode, encoding="utf-8")
    import os

    os.environ["PRINTORA_FAKE_GCODE"] = str(fake_gcode)
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path, slicer_engine_path=engine))
    job = repository.create_job(
        user_id,
        SlicingJobCreate(
            printer_id=printer_id,
            model_reference="library://preflight.stl",
            model_version_reference="v1",
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
        ),
    )
    return repository.run_job(job.id, user_id)


def _pair_agent(client: TestClient, token: str, printer_id: int, stable_id: str) -> str:
    pairing = client.post(f"/api/printers/{printer_id}/pairing/tokens", json={"ttl_minutes": 15}, headers=_auth(token)).json()
    exchanged = client.post(
        "/api/agent/pairing/exchange",
        json={"pairing_token": pairing["token"], "stable_id": stable_id, "agent_version": "0.1.36"},
    )
    assert exchanged.status_code == 200
    credential = exchanged.json()["credential"]
    heartbeat = client.post("/api/agent/heartbeat", json={"agent_version": "0.1.36", "platform": "test"}, headers=_auth(credential))
    assert heartbeat.status_code == 200
    return credential


def _finish_job(client: TestClient, credential: str, job_id: int, result: dict) -> None:
    job = client.get("/api/agent/jobs/next", headers=_auth(credential)).json()["jobs"][0]
    assert job["id"] == job_id
    assert client.post(f"/api/agent/jobs/{job_id}/ack", headers=_auth(credential)).status_code == 200
    response = client.post(
        f"/api/agent/jobs/{job_id}/result",
        json={"correlation_id": job["correlation_id"], "result": result},
        headers=_auth(credential),
    )
    assert response.status_code == 200


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
