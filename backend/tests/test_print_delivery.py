from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.auth import AuthRepository
from app.config import Settings, get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.printers import PrinterCreate, PrinterRepository
from app.slicing_pipeline import ModelDimensions, SlicingJobCreate, SlicingPipelineRepository


def test_print_delivery_saves_gcode_after_approved_preflight(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "delivery-save@example.com")
            job = _completed_job(tmp_path, token)
            preflight_id = _approved_preflight(tmp_path / "printora.db", job)
            _patch_agent_executor(monkeypatch, tmp_path / "printora.db", {"status": "uploaded", "remote_filename": "printora/cube_job_1.gcode", "started": False})

            response = client.post(
                "/api/slicing/deliveries",
                headers=_auth(token),
                json={"preflight_id": preflight_id, "mode": "save_only"},
            )

            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "saved"
            assert payload["remote_agent_job_id"]
            assert payload["remote_filename"].endswith(".gcode")
            assert "gcode_content" not in payload["remote_result"]
    finally:
        get_settings.cache_clear()


def test_print_delivery_requires_confirmation_or_step_up_to_start_print(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "delivery-confirm@example.com")
            job = _completed_job(tmp_path, token)
            preflight_id = _approved_preflight(tmp_path / "printora.db", job)
            _patch_agent_executor(monkeypatch, tmp_path / "printora.db", {"status": "started", "started": True})

            blocked = client.post(
                "/api/slicing/deliveries",
                headers=_auth(token),
                json={"preflight_id": preflight_id, "mode": "save_and_print", "confirmation_phrase": "errado"},
            ).json()
            assert blocked["status"] == "blocked"
            assert "confirmação" in " ".join(blocked["blockers"]).lower()

            confirmed = client.post(
                "/api/slicing/deliveries",
                headers=_auth(token),
                json={"preflight_id": preflight_id, "mode": "save_and_print", "confirmation_phrase": f"IMPRIMIR {job['printer_id']}-{preflight_id}"},
            )
            assert confirmed.status_code == 200
            assert confirmed.json()["status"] == "printing"
    finally:
        get_settings.cache_clear()


def test_print_delivery_blocks_expired_preflight(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "delivery-expired@example.com")
            job = _completed_job(tmp_path, token)
            preflight_id = _approved_preflight(tmp_path / "printora.db", job, approved_at="2020-01-01 00:00:00")

            response = client.post(
                "/api/slicing/deliveries",
                headers=_auth(token),
                json={"preflight_id": preflight_id, "mode": "save_only"},
            )

            assert response.status_code == 200
            assert response.json()["status"] == "blocked"
            assert "expirou" in " ".join(response.json()["blockers"])
    finally:
        get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _completed_job(tmp_path: Path, token: str) -> dict:
    database_path = tmp_path / "printora.db"
    user = AuthRepository(database_path).get_user_by_session(token)
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron delivery", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
    )
    engine = tmp_path / "orcaslicer"
    engine.write_text(
        """#!/usr/bin/env bash
if [[ "$1" == "--version" ]]; then echo "OrcaSlicer fake"; exit 0; fi
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == "--output" ]]; then shift; printf '; filament_type = ABS\\nM104 S245\\nM140 S110\\nG1 X50 Y50 Z2\\n' > "$1"; exit 0; fi
  shift
done
exit 2
""",
        encoding="utf-8",
    )
    engine.chmod(0o755)
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path, slicer_engine_path=engine))
    job = repository.create_job(
        user.id,
        SlicingJobCreate(
            printer_id=printer.id,
            model_reference="library://cube.stl",
            model_version_reference="v1",
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
        ),
    )
    return repository.run_job(job.id, user.id).model_dump()


def _approved_preflight(database_path: Path, job: dict, approved_at: str = "2030-01-01 00:00:00") -> int:
    artifact = next(item for item in job["artifacts"] if item["artifact_kind"] == "gcode")
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO print_preflight_checks (
                owner_user_id, printer_id, slicing_job_id, status, local_metadata_json,
                remote_preflight_json, blockers_json, warnings_json, checklist_json, approved_at
            )
            VALUES (?, ?, ?, 'approved', ?, ?, '[]', '[]', ?, ?)
            """,
            (
                job["owner_user_id"],
                job["printer_id"],
                job["id"],
                f'{{"checksum_sha256":"{artifact["checksum_sha256"]}","command_count":4}}',
                '{"can_execute":true,"printing":false}',
                '["Conferir impressora selecionada."]',
                approved_at,
            ),
        )
        return int(cursor.lastrowid)


def _patch_agent_executor(monkeypatch, database_path: Path, result: dict) -> None:
    class FakeExecutor:
        def __init__(self, _database_path):
            pass

        async def run(self, printer, *, job_type, payload=None, timeout_seconds=12.0, require_online=True):
            with connect_database(database_path) as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO agent_jobs (printer_id, correlation_id, job_type, payload_json, status, result_json)
                    VALUES (?, ?, ?, ?, 'succeeded', ?)
                    """,
                    (printer.id, f"{job_type}_test", job_type, "{}", "{}"),
                )
                job_id = int(cursor.lastrowid)
            return SimpleNamespace(id=job_id, result=result)

    monkeypatch.setattr("app.routes.slicing.AgentCommandExecutor", FakeExecutor)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
