from pathlib import Path

from app.auth import AuthRepository, UserRegisterRequest
from app.config import Settings
from app.database import connect_database, initialize_database
from app.print_profiles import MaterialProfilePayload, PrintProfilesRepository, SlicingProfilePayload
from app.printers import PrinterCreate, PrinterRepository
from app.slicing_pipeline import ModelDimensions, SlicingJobCreate, SlicingPipelineRepository
from app.social_catalog import SocialCatalogRepository


def test_slicing_job_fails_when_engine_is_unavailable(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path, slicer_engine_path=tmp_path / "missing"))

    job = repository.create_job(
        user.id,
        SlicingJobCreate(
            printer_id=printer_id,
            material_profile_id=profile_id,
            model_reference="library://benchy.stl",
            model_version_reference="v1",
            model_dimensions=ModelDimensions(x_mm=30, y_mm=30, z_mm=40),
            quality_reference="0.20 qualidade",
        ),
    )
    result = repository.run_job(job.id, user.id)

    assert result.status == "failed"
    assert result.error_message
    assert result.artifacts[0].artifact_kind == "log"
    assert result.compatibility["status"] == "compatible"


def test_slicing_job_completes_with_controlled_engine(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    engine = tmp_path / "orcaslicer"
    engine.write_text(
        """#!/usr/bin/env bash
if [[ "$1" == "--version" ]]; then echo "OrcaSlicer fake 2.0"; exit 0; fi
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == "--output" ]]; then shift; printf '; fake gcode\\nG28\\n' > "$1"; exit 0; fi
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
            printer_id=printer_id,
            material_profile_id=profile_id,
            model_reference="library://cube.stl",
            model_version_reference="v2",
            model_dimensions=ModelDimensions(x_mm=40, y_mm=40, z_mm=40),
            quality_reference="0.20 qualidade",
        ),
    )
    result = repository.run_job(job.id, user.id)

    assert result.status == "completed"
    assert {artifact.artifact_kind for artifact in result.artifacts} == {"gcode", "log", "metadata"}
    assert result.output["gcode_storage_key"].endswith("output.gcode")
    assert result.artifacts[0].checksum_sha256
    assert str(tmp_path) not in result.model_dump_json()


def test_slicing_job_blocks_oversized_model_and_cancels_planned_job(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path))

    try:
        repository.create_job(
            user.id,
            SlicingJobCreate(
                printer_id=printer_id,
                material_profile_id=profile_id,
                model_reference="library://huge.stl",
                model_dimensions=ModelDimensions(x_mm=999, y_mm=40, z_mm=40),
                quality_reference="0.20 qualidade",
            ),
        )
    except ValueError as exc:
        assert "volume útil" in str(exc)
    else:
        raise AssertionError("modelo maior que volume útil deveria bloquear")

    job = repository.create_job(
        user.id,
        SlicingJobCreate(
            printer_id=printer_id,
            material_profile_id=profile_id,
            model_reference="library://small.stl",
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
        ),
    )
    canceled = repository.cancel_job(job.id, user.id)

    assert canceled.status == "canceled"
    assert canceled.canceled_at is not None


def _seed_printer_and_profile(database_path: Path):
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="slicer@example.com", password="correct-horse"))
    social = SocialCatalogRepository(database_path)
    variant = next(
        variant
        for manufacturer in social.list_catalog().manufacturers
        for model in manufacturer.models
        for variant in model.variants
        if variant.slug == "voron-2-4-r2-350"
    )
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron slicer", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
    )
    with connect_database(database_path) as connection:
        connection.execute("UPDATE printers SET catalog_variant_id = ? WHERE id = ?", (variant.id, printer.id))
    profile = PrintProfilesRepository(database_path).create_profile(
        user.id,
        MaterialProfilePayload(
            printer_id=printer.id,
            catalog_variant_id=variant.id,
            title="ABS 0.4",
            visibility="private",
            material_type="ABS",
            nozzle_diameter_mm=0.4,
            slicing=SlicingProfilePayload(layer_height_mm=0.2, speed_mm_s=180, infill_percent=25),
        ),
    )
    return user, printer.id, profile.id
