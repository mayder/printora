from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.auth import AuthRepository
from app.database import connect_database, initialize_database
from app.main import app
from app.print_projects import PrintProjectCreateRequest, PrintProjectsRepository
from app.printers import PrinterCreate, PrinterRepository
from app.slicing_pipeline import ModelDimensions, ProjectSlicingJobCreate, SlicingJobCreate, SlicingPipelineRepository
from app.config import Settings, get_settings

VALID_STL = b"solid printora\nfacet normal 0 0 0\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid\n"


def test_print_history_records_feedback_without_public_printer_leak(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "history@example.com")
            job = _completed_job(tmp_path, token)
            preflight_id = _approved_preflight(tmp_path / "printora.db", job)
            _patch_agent_executor(monkeypatch, tmp_path / "printora.db", {"status": "started", "started": True, "filament_used_g": 12.5})

            delivery = client.post(
                "/api/slicing/deliveries",
                headers=_auth(token),
                json={"preflight_id": preflight_id, "mode": "save_and_print", "confirmation_phrase": f"IMPRIMIR {job['printer_id']}-{preflight_id}"},
            ).json()
            assert delivery["status"] == "printing"

            history = client.get("/api/slicing/history", headers=_auth(token)).json()
            assert history[0]["printer_id"] == job["printer_id"]
            assert history[0]["telemetry"]["filament_used_g"] == 12.5

            updated = client.post(
                f"/api/slicing/history/{history[0]['id']}/feedback",
                headers=_auth(token),
                json={"outcome": "worked", "visibility": "public", "note": "Primeira camada ok", "photo_url": "https://example.com/print.jpg"},
            ).json()
            assert updated["feedback"][0]["visibility"] == "public"

            viewer_token = _register(client, "history-viewer@example.com")
            public = client.get("/api/slicing/history?include_public=true", headers=_auth(viewer_token)).json()
            assert public[0]["printer_id"] is None
            assert public[0]["feedback"][0]["note"] == "Primeira camada ok"
            assert "remote_filename" not in public[0]["result"]
    finally:
        get_settings.cache_clear()


def test_project_delivery_history_keeps_project_snapshot_and_public_privacy(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token = _register(client, "project-history@example.com")
            job = _completed_project_job(tmp_path, token)
            preflight_id = _approved_preflight(tmp_path / "printora.db", job)
            _patch_agent_executor(monkeypatch, tmp_path / "printora.db", {"status": "uploaded", "started": False, "remote_filename": "printora/project.gcode"})

            delivery = client.post(
                "/api/slicing/deliveries",
                headers=_auth(token),
                json={"preflight_id": preflight_id, "mode": "save_only"},
            ).json()
            assert delivery["status"] == "saved"

            history = client.get("/api/slicing/history", headers=_auth(token)).json()
            assert history[0]["slicing_job_id"] == job["id"]
            assert history[0]["model_reference"].startswith("project://")
            assert history[0]["model_version_reference"] == f"project-version:{job['print_project_version_id']}"

            updated = client.post(
                f"/api/slicing/history/{history[0]['id']}/feedback",
                headers=_auth(token),
                json={"outcome": "worked", "visibility": "public", "note": "Projeto funcionou"},
            ).json()
            assert updated["visibility"] == "public"

            viewer_token = _register(client, "project-history-viewer@example.com")
            public = client.get("/api/slicing/history?include_public=true", headers=_auth(viewer_token)).json()
            assert public[0]["printer_id"] is None
            assert public[0]["slicing_job_id"] == job["id"]
            assert "remote_filename" not in public[0]["result"]
            assert "Moonraker" not in str(public[0])
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
        PrinterCreate(name="Voron history", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
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


def _completed_project_job(tmp_path: Path, token: str) -> dict:
    database_path = tmp_path / "printora.db"
    user = AuthRepository(database_path).get_user_by_session(token)
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron project history", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
    )
    projects = PrintProjectsRepository(database_path)
    project = projects.create_project(user.id, PrintProjectCreateRequest(title="Projeto histórico", visibility="private"))
    detail = projects.upload_file(user.id, project.id, "principal.stl", "primary", VALID_STL)
    engine = tmp_path / "orcaslicer-project"
    engine.write_text(
        """#!/usr/bin/env bash
if [[ "$1" == "--version" ]]; then echo "OrcaSlicer fake"; exit 0; fi
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == "--output" ]]; then shift; printf '; filament_type = PLA\\nM104 S205\\nG1 X20 Y20 Z1\\n' > "$1"; exit 0; fi
  shift
done
exit 2
""",
        encoding="utf-8",
    )
    engine.chmod(0o755)
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path, slicer_engine_path=engine))
    job = repository.create_project_job(
        user.id,
        ProjectSlicingJobCreate(
            project_id=project.id,
            selected_file_ids=[detail.files[0].id],
            printer_id=printer.id,
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
        ),
    )
    return repository.run_job(job.id, user.id).model_dump()


def _approved_preflight(database_path: Path, job: dict) -> int:
    artifact = next(item for item in job["artifacts"] if item["artifact_kind"] == "gcode")
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO print_preflight_checks (
                owner_user_id, printer_id, slicing_job_id, status, local_metadata_json,
                remote_preflight_json, blockers_json, warnings_json, checklist_json, approved_at
            )
            VALUES (?, ?, ?, 'approved', ?, ?, '[]', '[]', ?, '2030-01-01 00:00:00')
            """,
            (
                job["owner_user_id"],
                job["printer_id"],
                job["id"],
                f'{{"checksum_sha256":"{artifact["checksum_sha256"]}","command_count":4}}',
                '{"can_execute":true,"printing":false}',
                '["Conferir impressora selecionada."]',
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
            return SimpleNamespace(id=int(cursor.lastrowid), result=result)

    monkeypatch.setattr("app.routes.slicing.AgentCommandExecutor", FakeExecutor)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
