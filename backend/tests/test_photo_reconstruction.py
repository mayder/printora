import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import Settings, get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.operations.reconstruction.contracts import ReconstructionCreate
from app.modules.operations.reconstruction.adapters import (
    CommandReconstructionAdapter,
    DisabledReconstructionAdapter,
    FixtureReconstructionAdapter,
    ReconstructionCancelledError,
    ReconstructionAdapterInput,
    ReconstructionPhotoInput,
    ReconstructionUnavailableError,
    build_reconstruction_adapter,
)
from app.modules.operations.reconstruction.processor import execute_reconstruction_job
from app.modules.operations.reconstruction.repository import ReconstructionRepository
from app.modules.platform.durable_execution import DurableExecutionRepository


def _ready_capture(database_path: Path, email: str = "reconstruction@example.com") -> tuple[int, int, int]:
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email=email, password="correct-horse"))
    with connect_database(database_path) as connection:
        project_id = int(connection.execute(
            "INSERT INTO print_projects (owner_user_id, slug, title, visibility, lifecycle_status, publication_status, commercial_class) VALUES (?, ?, 'Objeto', 'private', 'active', 'draft', 'free')",
            (user.id, f"reconstruction-{user.id}"),
        ).lastrowid)
        capture_id = int(connection.execute(
            "INSERT INTO photo_capture_sessions (project_id, owner_user_id, status, target_photo_count, consent_confirmed_at, scale_method, scale_confirmed_at, completed_at) VALUES (?, ?, 'ready', 12, CURRENT_TIMESTAMP, 'none', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (project_id, user.id),
        ).lastrowid)
        for index in range(1, 13):
            band = ("low", "middle", "high")[(index - 1) % 3]
            connection.execute(
                """
                INSERT INTO photo_capture_photos (
                    session_id, owner_user_id, capture_index, height_band, file_name,
                    storage_key, sha256, size_bytes, width, height, quality_status, quality_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 100, 1600, 1200, 'accepted', '{}')
                """,
                (capture_id, user.id, index, band, f"photo-{index}.png", f"photo-{index}.png", f"{index:064x}"),
            )
    return user.id, project_id, capture_id


def test_reconstruction_is_idempotent_owner_scoped_and_queued(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    other_id, _, _ = _ready_capture(database_path, "other-reconstruction@example.com")
    settings = Settings(data_dir=tmp_path, reconstruction_mode="fixture")
    repository = ReconstructionRepository(database_path, settings)

    created = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "create-1")
    repeated = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "create-1")

    assert created.id == repeated.id
    assert created.status == "queued"
    assert created.progress_percent is None
    with pytest.raises(PermissionError):
        repository.get(other_id, created.id)


def test_fixture_worker_persists_raw_mesh_and_provenance_without_claiming_real_coverage(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    settings = Settings(data_dir=tmp_path, reconstruction_mode="fixture")
    repository = ReconstructionRepository(database_path, settings)
    created = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "worker-1")
    durable = DurableExecutionRepository(database_path).claim_job("bulk", "worker-test")

    assert durable is not None
    result = execute_reconstruction_job(durable, settings)
    completed = repository.get(owner_id, created.id)

    assert result["status"] == "succeeded"
    assert completed.status == "succeeded"
    assert completed.stage == "ready"
    assert completed.artifacts[0].file_format == "obj"
    assert completed.artifacts[0].observed_ratio is None
    assert completed.artifacts[0].inferred_ratio is None
    assert completed.artifacts[0].provenance["classification"] == "synthetic_fixture"
    assert len(completed.artifacts[0].provenance["source_checksums"]) == 12
    assert completed.qualification is not None
    assert completed.qualification.reconstruction_artifact_id == completed.artifacts[0].id
    assert completed.qualification.status == "not_qualified"
    assert completed.qualification.report["mandatory_checks_complete"] is False


def test_engine_health_write_failure_does_not_retry_completed_reconstruction(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    settings = Settings(data_dir=tmp_path, reconstruction_mode="fixture")
    repository = ReconstructionRepository(database_path, settings)
    created = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "health-1")
    durable = DurableExecutionRepository(database_path).claim_job("bulk", "worker-test")
    monkeypatch.setattr(
        ReconstructionRepository,
        "record_engine_success",
        lambda self, engine_key: (_ for _ in ()).throw(RuntimeError("health unavailable")),
    )

    assert durable is not None
    result = execute_reconstruction_job(durable, settings)

    assert result["status"] == "succeeded"
    assert repository.get(owner_id, created.id).status == "succeeded"


def test_disabled_engine_fails_actionably_without_retry_loop(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    settings = Settings(data_dir=tmp_path, reconstruction_mode="disabled")
    repository = ReconstructionRepository(database_path, settings)
    created = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "disabled-1")
    durable = DurableExecutionRepository(database_path).claim_job("bulk", "worker-test")

    assert durable is not None
    result = execute_reconstruction_job(durable, settings)
    failed = repository.get(owner_id, created.id)

    assert result == {"reconstruction_job_id": created.id, "status": "failed", "error_code": "engine_unavailable"}
    assert failed.status == "failed"
    assert failed.can_retry is True
    assert "não está habilitada" in (failed.error_message or "")


def test_provider_failure_requires_human_retry_to_protect_billing(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    state_dir = tmp_path / "provider-state"
    state_dir.mkdir()
    executable = tmp_path / "provider-gateway"
    executable.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    executable.chmod(0o700)
    settings = Settings(
        data_dir=tmp_path,
        reconstruction_mode="provider_command",
        reconstruction_provider_command=executable,
        reconstruction_tripo_api_key="test-provider-key",
        reconstruction_tripo_state_dir=state_dir,
    )
    repository = ReconstructionRepository(database_path, settings)
    created = repository.create(
        owner_id,
        ReconstructionCreate(capture_session_id=capture_id, engine_policy="provider"),
        "provider-failure-1",
    )
    durable = DurableExecutionRepository(database_path).claim_job("bulk", "worker-test")

    assert durable is not None
    with pytest.raises(RuntimeError, match="processing failed"):
        execute_reconstruction_job(durable, settings)

    failed = repository.get(owner_id, created.id)
    assert failed.status == "failed"
    assert failed.error_code == "processing_failed"


def test_stale_attempt_cannot_replace_canonical_reconstruction(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    settings = Settings(data_dir=tmp_path, reconstruction_mode="fixture")
    repository = ReconstructionRepository(database_path, settings)
    created = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "fencing-1")
    first_id, first_request = repository.begin_attempt(created.id, "fixture-photogrammetry", "1")
    second_id, second_request = repository.begin_attempt(created.id, "fixture-photogrammetry", "1")
    adapter = FixtureReconstructionAdapter()

    with pytest.raises(ValueError, match="tentativa não é mais ativa"):
        repository.succeed(created.id, first_id, adapter.reconstruct(first_request, repository.storage.storage))
    completed = repository.succeed(created.id, second_id, adapter.reconstruct(second_request, repository.storage.storage))

    assert completed.status == "succeeded"
    assert len(completed.artifacts) == 1


def test_cancellation_is_terminal_for_current_durable_run(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, _, capture_id = _ready_capture(database_path)
    settings = Settings(data_dir=tmp_path, reconstruction_mode="fixture")
    repository = ReconstructionRepository(database_path, settings)
    created = repository.create(owner_id, ReconstructionCreate(capture_session_id=capture_id), "cancel-1")

    cancelled = repository.cancel(owner_id, created.id)

    assert cancelled.status == "cancelled"
    assert cancelled.can_retry is True
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT dj.status FROM durable_jobs dj JOIN photo_reconstruction_jobs rj ON rj.durable_job_id = dj.id WHERE rj.id = ?",
            (created.id,),
        ).fetchone()
        assert row["status"] == "canceled"


def test_engine_circuit_opens_after_repeated_failures_and_recovers(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = ReconstructionRepository(database_path, Settings(data_dir=tmp_path))

    for _ in range(3):
        repository.record_engine_failure("provider-gateway")

    with pytest.raises(ReconstructionUnavailableError, match="temporariamente pausado"):
        repository.ensure_engine_available("provider-gateway")
    repository.record_engine_success("provider-gateway")
    repository.ensure_engine_available("provider-gateway")


def test_command_adapter_uses_fixed_contract_and_validates_output(tmp_path: Path) -> None:
    executable = tmp_path / "adapter.sh"
    executable.write_text(
        """#!/bin/sh
set -eu
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-dir) output_dir="$2"; shift 2 ;;
    --result) result_file="$2"; shift 2 ;;
    *) shift ;;
  esac
done
printf 'v 0 0 0\\nv 1 0 0\\nv 0 1 0\\nf 1 2 3\\n' > "$output_dir/raw.obj"
printf '{"mesh_file":"raw.obj","mesh_format":"obj","model_version":"fixture-wrapper-v1","unit":"unknown","provenance":{"classification":"observed"}}' > "$result_file"
""",
        encoding="utf-8",
    )
    executable.chmod(0o700)

    class MemoryStorage:
        def open_promoted(self, key: str):
            from io import BytesIO
            from app.object_storage import ObjectReader

            body = b"photo"
            return ObjectReader(body=BytesIO(body), size_bytes=len(body), content_type="image/png")

    request = ReconstructionAdapterInput(
        job_id=1,
        correlation_id="contract-test",
        scale_method="none",
        scale_value_mm=None,
        scale_uncertainty_mm=None,
        photos=(ReconstructionPhotoInput(
            capture_index=1,
            height_band="middle",
            storage_key="photo.png",
            sha256=hashlib.sha256(b"photo").hexdigest(),
            width=1600,
            height=1200,
        ),),
    )

    result = CommandReconstructionAdapter(
        engine_key="local-photogrammetry",
        executable=executable,
        timeout_seconds=30,
    ).reconstruct(request, MemoryStorage())

    assert result.mesh_format == "obj"
    assert result.model_version == "fixture-wrapper-v1"
    assert result.provenance["classification"] == "observed"


def test_command_adapter_terminates_process_when_cancelled(tmp_path: Path) -> None:
    executable = tmp_path / "slow-adapter.sh"
    executable.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
    executable.chmod(0o700)

    class MemoryStorage:
        def open_promoted(self, key: str):
            from io import BytesIO
            from app.object_storage import ObjectReader

            body = b"photo"
            return ObjectReader(body=BytesIO(body), size_bytes=len(body), content_type="image/png")

    request = ReconstructionAdapterInput(
        job_id=1,
        correlation_id="cancel-test",
        scale_method="none",
        scale_value_mm=None,
        scale_uncertainty_mm=None,
        photos=(ReconstructionPhotoInput(
            capture_index=1,
            height_band="middle",
            storage_key="photo.png",
            sha256=hashlib.sha256(b"photo").hexdigest(),
            width=1600,
            height=1200,
        ),),
    )
    checks = iter((False, True))

    with pytest.raises(ReconstructionCancelledError):
        CommandReconstructionAdapter(
            engine_key="local-photogrammetry",
            executable=executable,
            timeout_seconds=30,
        ).reconstruct(request, MemoryStorage(), lambda: next(checks, True))


def test_provider_adapter_requires_checkpoint_and_secret(tmp_path: Path) -> None:
    executable = tmp_path / "provider"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    incomplete = Settings(
        data_dir=tmp_path,
        reconstruction_mode="provider_command",
        reconstruction_provider_command=executable,
    )
    assert isinstance(build_reconstruction_adapter(incomplete, "provider"), DisabledReconstructionAdapter)

    configured = Settings(
        data_dir=tmp_path,
        reconstruction_mode="provider_command",
        reconstruction_provider_command=executable,
        reconstruction_tripo_api_key="test-provider-key",
        reconstruction_tripo_state_dir=tmp_path / "provider-state",
    )
    adapter = build_reconstruction_adapter(configured, "provider")

    assert isinstance(adapter, CommandReconstructionAdapter)
    assert adapter.automatic_retry_safe is False
    assert adapter.environment["PRINTORA_TRIPO_API_KEY"] == "test-provider-key"
    assert adapter.environment["PRINTORA_TRIPO_STATE_DIR"] == str((tmp_path / "provider-state").resolve())


def test_reconstruction_routes_isolate_owner_and_stream_private_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RECONSTRUCTION_MODE", "fixture")
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner_token = client.post(
                "/api/auth/register",
                json={"email": "route-reconstruction@example.com", "password": "correct-horse"},
            ).json()["access_token"]
            other_token = client.post(
                "/api/auth/register",
                json={"email": "route-reconstruction-other@example.com", "password": "correct-horse"},
            ).json()["access_token"]
            with connect_database(tmp_path / "printora.db") as connection:
                owner_id = int(connection.execute(
                    "SELECT id FROM auth_users WHERE email = 'route-reconstruction@example.com'",
                ).fetchone()["id"])
                project_id = int(connection.execute(
                    "INSERT INTO print_projects (owner_user_id, slug, title, visibility, lifecycle_status, publication_status, commercial_class) VALUES (?, 'route-reconstruction', 'Objeto', 'private', 'active', 'draft', 'free')",
                    (owner_id,),
                ).lastrowid)
                capture_id = int(connection.execute(
                    "INSERT INTO photo_capture_sessions (project_id, owner_user_id, status, target_photo_count, consent_confirmed_at, scale_method, scale_confirmed_at, completed_at) VALUES (?, ?, 'ready', 12, CURRENT_TIMESTAMP, 'none', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (project_id, owner_id),
                ).lastrowid)
                for index in range(1, 13):
                    connection.execute(
                        "INSERT INTO photo_capture_photos (session_id, owner_user_id, capture_index, height_band, file_name, storage_key, sha256, size_bytes, width, height, quality_status, quality_json) VALUES (?, ?, ?, ?, ?, ?, ?, 100, 1600, 1200, 'accepted', '{}')",
                        (capture_id, owner_id, index, ("low", "middle", "high")[(index - 1) % 3], f"photo-{index}.png", f"photo-{index}.png", f"{index:064x}"),
                    )
            created = client.post(
                "/api/photo-reconstructions",
                headers={"Authorization": f"Bearer {owner_token}", "Idempotency-Key": "route-create"},
                json={"capture_session_id": capture_id, "engine_policy": "auto"},
            )
            assert created.status_code == 200
            job_id = created.json()["id"]
            durable = DurableExecutionRepository(tmp_path / "printora.db").claim_job("bulk", "route-worker")
            assert durable is not None
            execute_reconstruction_job(durable, get_settings())
            completed = client.get(
                f"/api/photo-reconstructions/{job_id}",
                headers={"Authorization": f"Bearer {owner_token}"},
            ).json()
            artifact_id = completed["artifacts"][0]["id"]

            hidden = client.get(
                f"/api/photo-reconstructions/{job_id}",
                headers={"Authorization": f"Bearer {other_token}"},
            )
            downloaded = client.get(
                f"/api/photo-reconstructions/{job_id}/artifacts/{artifact_id}",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

            assert hidden.status_code == 404
            assert downloaded.status_code == 200
            assert downloaded.headers["cache-control"] == "private, no-store"
            assert b"synthetic fixture" in downloaded.content
    finally:
        get_settings.cache_clear()
