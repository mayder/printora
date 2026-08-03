from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import Settings, get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.community.storage_usage import total_personal_storage_used
from app.modules.operations.mesh_qualification.contracts import MeshRepairCreate
from app.modules.operations.mesh_qualification.processor import execute_mesh_repair
from app.modules.operations.mesh_qualification.repository import MeshRevisionRepository
from app.modules.operations.mesh_qualification.review_contracts import MeshReviewCreate
from app.modules.operations.mesh_qualification.review_repository import MeshReviewRepository
from app.modules.operations.reconstruction.contracts import ReconstructionCreate
from app.modules.operations.reconstruction.processor import execute_reconstruction_job
from app.modules.operations.reconstruction.repository import ReconstructionRepository
from app.modules.platform.durable_execution import DurableExecutionRepository


def _ready_reconstruction(database_path: Path, settings: Settings, email: str = "repair@example.com"):
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email=email, password="correct-horse"))
    with connect_database(database_path) as connection:
        project_id = int(connection.execute(
            "INSERT INTO print_projects (owner_user_id, slug, title, visibility, lifecycle_status, publication_status, commercial_class) VALUES (?, ?, 'Objeto', 'private', 'active', 'draft', 'free')",
            (user.id, f"repair-{user.id}"),
        ).lastrowid)
        capture_id = int(connection.execute(
            "INSERT INTO photo_capture_sessions (project_id, owner_user_id, status, target_photo_count, consent_confirmed_at, scale_method, scale_confirmed_at, completed_at) VALUES (?, ?, 'ready', 12, CURRENT_TIMESTAMP, 'none', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (project_id, user.id),
        ).lastrowid)
        for index in range(1, 13):
            connection.execute(
                "INSERT INTO photo_capture_photos (session_id, owner_user_id, capture_index, height_band, file_name, storage_key, sha256, size_bytes, width, height, quality_status, quality_json) VALUES (?, ?, ?, ?, ?, ?, ?, 100, 1600, 1200, 'accepted', '{}')",
                (capture_id, user.id, index, ("low", "middle", "high")[(index - 1) % 3], f"photo-{index}.png", f"photo-{index}.png", f"{index:064x}"),
            )
    reconstruction = ReconstructionRepository(database_path, settings).create(
        user.id, ReconstructionCreate(capture_session_id=capture_id), f"reconstruction-{user.id}",
    )
    durable_repository = DurableExecutionRepository(database_path)
    job = durable_repository.claim_job("bulk", "reconstruction-worker")
    assert job is not None
    result = execute_reconstruction_job(job, settings)
    durable_repository.complete_job(job.id, job.lease_token or "", result)
    return user, ReconstructionRepository(database_path, settings).get(user.id, reconstruction.id)


def _execute_next_repair(database_path: Path, settings: Settings):
    durable_repository = DurableExecutionRepository(database_path)
    job = durable_repository.claim_job("bulk", "repair-worker")
    assert job is not None
    result = execute_mesh_repair(job, settings)
    durable_repository.complete_job(job.id, job.lease_token or "", result)
    return result


def test_mesh_revisions_are_idempotent_chained_qualified_and_owner_scoped(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    settings = Settings(data_dir=tmp_path, reconstruction_mode="fixture")
    owner, reconstruction = _ready_reconstruction(database_path, settings)
    other = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="other-repair@example.com", password="correct-horse")
    )
    repository = MeshRevisionRepository(database_path, settings)
    payload = MeshRepairCreate(operation="clean", parameters={"output_format": "obj"})

    created = repository.create(owner.id, reconstruction.id, payload, "repair-1")
    repeated = repository.create(owner.id, reconstruction.id, payload, "repair-1")
    assert created.id == repeated.id
    assert created.status == "queued"
    with pytest.raises(ValueError):
        repository.create(
            owner.id, reconstruction.id,
            MeshRepairCreate(operation="orient_normals", parameters={"output_format": "obj"}),
            "repair-1",
        )

    assert _execute_next_repair(database_path, settings)["status"] == "succeeded"
    repaired = repository.get(owner.id, reconstruction.id, created.id)
    assert repaired.status == "succeeded"
    assert repaired.manifest["source_sha256"] == reconstruction.artifacts[0].sha256
    assert repaired.manifest["output_sha256"] == repaired.sha256
    assert repaired.qualification["triangle_count"] > 0

    scaled = repository.create(
        owner.id, reconstruction.id,
        MeshRepairCreate(operation="scale", source_revision_id=repaired.id, parameters={
            "scale_factor": 10, "known_axis": "x", "known_dimension_mm": 20, "output_format": "obj",
        }),
        "repair-2",
    )
    _execute_next_repair(database_path, settings)
    scaled = repository.get(owner.id, reconstruction.id, scaled.id)
    assert scaled.unit == "mm"
    assert scaled.qualification["dimensions"]["x"] == 20.0

    converted = repository.create(
        owner.id, reconstruction.id,
        MeshRepairCreate(operation="convert", source_revision_id=scaled.id, parameters={"output_format": "stl"}),
        "repair-3",
    )
    _execute_next_repair(database_path, settings)
    converted = repository.get(owner.id, reconstruction.id, converted.id)
    reader, file_format = repository.open(owner.id, reconstruction.id, converted.id)
    try:
        assert file_format == "stl"
        assert reader.body.read(5) == b"Print"
    finally:
        reader.body.close()

    reviews = MeshReviewRepository(database_path)
    with pytest.raises(ValueError, match="Uso mecânico"):
        reviews.create(owner.id, reconstruction.id, converted.id, MeshReviewCreate(
            decision="approve", intended_use="mechanical", known_axis="x", known_dimension_mm=20,
            shape_reviewed=True, limitations_accepted=True,
        ), "mechanical-review")
    with connect_database(database_path) as connection:
        usage_before_approval = total_personal_storage_used(connection, owner.id)
    approved = reviews.create(owner.id, reconstruction.id, converted.id, MeshReviewCreate(
        decision="approve", intended_use="decorative", known_axis="x", known_dimension_mm=20,
        shape_reviewed=True, limitations_accepted=True,
    ), "approve-review")
    repeated_approval = reviews.create(owner.id, reconstruction.id, converted.id, MeshReviewCreate(
        decision="approve", intended_use="decorative", known_axis="x", known_dimension_mm=20,
        shape_reviewed=True, limitations_accepted=True,
    ), "approve-review")
    assert approved.id == repeated_approval.id
    assert approved.project_file_id is not None
    assert approved.review_manifest["scope"] == "slicing_only"
    with connect_database(database_path) as connection:
        project_file = connection.execute(
            "SELECT * FROM print_project_files WHERE id = ?", (approved.project_file_id,),
        ).fetchone()
        project = connection.execute(
            "SELECT * FROM print_projects WHERE id = ?", (reconstruction.project_id,),
        ).fetchone()
        assert project_file["sha256"] == converted.sha256
        assert project_file["can_slice"] == 1
        assert project["current_version_id"] is not None
        assert total_personal_storage_used(connection, owner.id) == usage_before_approval

    cancelled = repository.create(
        owner.id, reconstruction.id,
        MeshRepairCreate(operation="convert", source_revision_id=converted.id, parameters={"output_format": "obj"}),
        "repair-4",
    )
    assert repository.cancel(owner.id, reconstruction.id, cancelled.id).status == "cancelled"
    assert len(repository.list(owner.id, reconstruction.id)) == 4
    with pytest.raises(PermissionError):
        repository.get(other.id, reconstruction.id, repaired.id)
    with connect_database(database_path) as connection:
        assert total_personal_storage_used(connection, owner.id) > sum(
            artifact.size_bytes for artifact in reconstruction.artifacts
        )


def test_mesh_revision_routes_create_poll_cancel_and_download(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RECONSTRUCTION_MODE", "fixture")
    get_settings.cache_clear()
    try:
        database_path = tmp_path / "printora.db"
        initialize_database(database_path)
        settings = get_settings()
        owner, reconstruction = _ready_reconstruction(database_path, settings, "route-repair@example.com")
        with TestClient(app) as client:
            token = client.post(
                "/api/auth/login",
                json={"email": owner.email, "password": "correct-horse"},
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "route-repair-1"}
            created = client.post(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions",
                headers=headers,
                json={"operation": "clean", "parameters": {"output_format": "obj"}},
            )
            assert created.status_code == 200
            revision_id = created.json()["id"]
            _execute_next_repair(database_path, settings)

            listed = client.get(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions",
                headers={"Authorization": f"Bearer {token}"},
            )
            downloaded = client.get(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions/{revision_id}/download",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert listed.json()[0]["status"] == "succeeded"
            assert downloaded.status_code == 200
            assert downloaded.headers["cache-control"] == "private, no-store"
            assert downloaded.content.startswith(b"v -1 -1 0")

            scaled = client.post(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "route-scale"},
                json={"operation": "scale", "source_revision_id": revision_id, "parameters": {
                    "scale_factor": 10, "known_axis": "x", "known_dimension_mm": 20, "output_format": "obj",
                }},
            ).json()
            _execute_next_repair(database_path, settings)
            converted = client.post(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "route-convert"},
                json={"operation": "convert", "source_revision_id": scaled["id"], "parameters": {"output_format": "stl"}},
            ).json()
            _execute_next_repair(database_path, settings)
            approved = client.post(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions/{converted['id']}/reviews",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "route-approval"},
                json={
                    "decision": "approve", "intended_use": "decorative", "known_axis": "x",
                    "known_dimension_mm": 20, "shape_reviewed": True, "limitations_accepted": True,
                },
            )
            assert approved.status_code == 200
            assert approved.json()["decision"] == "approved_for_slicing"
            assert approved.json()["project_file_id"] is not None

            queued = client.post(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "route-repair-2"},
                json={"operation": "convert", "source_revision_id": revision_id, "parameters": {"output_format": "stl"}},
            ).json()
            cancelled = client.post(
                f"/api/photo-reconstructions/{reconstruction.id}/mesh-revisions/{queued['id']}/cancel",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert cancelled.json()["status"] == "cancelled"
    finally:
        get_settings.cache_clear()
