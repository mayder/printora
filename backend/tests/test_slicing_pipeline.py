from pathlib import Path

from app.auth import AuthRepository, UserRegisterRequest
from app.config import Settings
from app.database import connect_database, initialize_database
from app.print_profiles import MaterialProfilePayload, PrintProfilesRepository, SlicingProfilePayload
from app.print_projects import PrintProjectCreateRequest, PrintProjectExternalLinkRequest, PrintProjectUpdateRequest, PrintProjectsRepository
from app.printers import PrinterCreate, PrinterRepository
from app.slicing_pipeline import ModelDimensions, ProjectSlicingJobCreate, SlicingJobCreate, SlicingPipelineRepository
from app.slicing_profile_bundles import NativeProfileBundle, ProfileBundleImport, SlicingProfileBundlesRepository
from app.social_catalog import SocialCatalogRepository

VALID_STL = b"solid printora\nfacet normal 0 0 0\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid\n"


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


def test_slicing_job_can_be_scheduled_and_canceled_in_durable_queue(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path))
    job = repository.create_job(
        user.id,
        SlicingJobCreate(
            printer_id=printer_id,
            material_profile_id=profile_id,
            model_reference="library://queued.stl",
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
        ),
    )

    scheduled = repository.schedule_job(job.id, user.id)
    repeated = repository.schedule_job(job.id, user.id)
    canceled = repository.cancel_job(job.id, user.id)

    assert scheduled.status == "planned"
    assert repeated.status == "planned"
    assert canceled.status == "canceled"
    with connect_database(database_path) as connection:
        rows = connection.execute(
            "SELECT status FROM durable_jobs WHERE owner_type = 'slicing_job' AND owner_id = ? ORDER BY id",
            (str(job.id),),
        ).fetchall()
    assert [row["status"] for row in rows] == ["canceled"]


def test_project_slicing_job_uses_immutable_project_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    projects = PrintProjectsRepository(database_path)
    project = projects.create_project(user.id, PrintProjectCreateRequest(title="Projeto para fatiar", visibility="private"))
    detail = projects.upload_file(user.id, project.id, "principal.stl", "primary", VALID_STL)
    file_id = detail.files[0].id
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path))

    job = repository.create_project_job(
        user.id,
        ProjectSlicingJobCreate(
            project_id=project.id,
            selected_file_ids=[file_id],
            printer_id=printer_id,
            material_profile_id=profile_id,
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
            profile_reference="ABS 0.4",
        ),
    )
    projects.update_project(user.id, project.id, PrintProjectUpdateRequest(title="Projeto alterado"))
    listed = repository.list_project_jobs(user.id, project.id)

    assert job.print_project_id == project.id
    assert job.print_project_version_id is not None
    assert job.selected_project_files[0]["file_name"] == "principal.stl"
    assert job.project_snapshot["title"] == "Projeto para fatiar"
    assert job.input["selected_files"][0]["sha256"]
    assert listed[0].id == job.id


def test_project_journey_preserves_quantities_preview_approval_and_reprint(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    projects = PrintProjectsRepository(database_path)
    project = projects.create_project(user.id, PrintProjectCreateRequest(title="Peças repetidas", visibility="private"))
    detail = projects.upload_file(user.id, project.id, "presilha.stl", "primary", VALID_STL)
    engine = tmp_path / "orcaslicer-journey"
    engine.write_text(
        """#!/usr/bin/env bash
if [[ "$1" == "--version" ]]; then echo "OrcaSlicer fake"; exit 0; fi
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
    original = repository.create_project_job(
        user.id,
        ProjectSlicingJobCreate(
            project_id=project.id,
            selected_file_ids=[detail.files[0].id],
            file_quantities={detail.files[0].id: 4},
            printer_id=printer_id,
            material_profile_id=profile_id,
        ),
    )
    completed = repository.run_job(original.id, user.id)
    approved = repository.approve_gcode(completed.id, user.id)
    reprint = repository.create_reprint_job(completed.id, user.id)

    assert approved.gcode_approved_at is not None
    assert approved.gcode_approved_checksum == completed.artifacts[0].checksum_sha256
    assert approved.selected_project_files[0]["quantity"] == 4
    assert reprint.status == "planned"
    assert reprint.reprint_of_job_id == completed.id
    assert reprint.print_project_version_id == completed.print_project_version_id
    assert reprint.selected_project_files == completed.selected_project_files
    assert reprint.slicing_profile_sha256 == completed.slicing_profile_sha256


def test_slicing_job_pins_immutable_executable_profile_revision(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    bundles = SlicingProfileBundlesRepository(database_path)
    first = bundles.import_bundle(
        user.id,
        ProfileBundleImport(
            title="Voron qualidade",
            engine_version="2.3.1",
            native_bundle=NativeProfileBundle(
                machine={"name": "Voron 2.4", "nozzle_diameter": ["0.6"]},
                process={"name": "0.20 Quality", "outer_wall_speed": "180"},
                filament={"name": "PLA", "nozzle_temperature": ["215"]},
            ),
        ),
    )
    revision_id = first.current_revision_id or 0
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path))

    job = repository.create_job(
        user.id,
        SlicingJobCreate(
            printer_id=printer_id,
            material_profile_id=profile_id,
            slicing_profile_revision_id=revision_id,
            model_reference="library://profile-pinned.stl",
            model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
            quality_reference="0.20 qualidade",
        ),
    )
    bundles.import_bundle(
        user.id,
        ProfileBundleImport(
            title="Voron qualidade",
            engine_version="2.3.2",
            bundle_id=first.id,
            parent_revision_id=revision_id,
            native_bundle=NativeProfileBundle(
                machine={"name": "Voron 2.4", "nozzle_diameter": ["0.6"]},
                process={"name": "0.20 Quality", "outer_wall_speed": "220"},
                filament={"name": "PLA", "nozzle_temperature": ["215"]},
            ),
        ),
    )
    stored = repository.get_job(job.id, user.id)

    assert stored is not None
    assert stored.slicing_profile_revision_id == revision_id
    assert stored.slicing_profile_sha256 == first.current_sha256
    assert stored.slicing_profile_engine_version == "2.3.1"
    assert stored.input["slicing_profile_revision"]["canonical"]["presets"]["process"]["outer_wall_speed"] == "180"


def test_project_slicing_blocks_external_reference_without_local_file(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user, printer_id, profile_id = _seed_printer_and_profile(database_path)
    projects = PrintProjectsRepository(database_path)
    project = projects.create_project(user.id, PrintProjectCreateRequest(title="Projeto link externo"))
    detail = projects.add_external_link(
        user.id,
        project.id,
        PrintProjectExternalLinkRequest(url="https://example.com/model", label="Modelo externo"),
    )
    repository = SlicingPipelineRepository(database_path, Settings(data_dir=tmp_path))

    try:
        repository.create_project_job(
            user.id,
            ProjectSlicingJobCreate(
                project_id=project.id,
                selected_file_ids=[detail.files[0].id],
                printer_id=printer_id,
                material_profile_id=profile_id,
                model_dimensions=ModelDimensions(x_mm=20, y_mm=20, z_mm=20),
                quality_reference="0.20 qualidade",
            ),
        )
    except ValueError as exc:
        assert "não podem ser fatiados" in str(exc)
    else:
        raise AssertionError("link externo sem arquivo local deveria bloquear fatiamento")


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
