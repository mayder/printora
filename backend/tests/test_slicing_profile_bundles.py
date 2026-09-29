import json
from pathlib import Path

import pytest

from app.auth import AuthRepository, UserRegisterRequest
from app.database import initialize_database
from app.slicing_profile_bundles import NativeProfileBundle, ProfileBundleImport, SlicingProfileBundlesRepository


def test_native_bundle_round_trip_revision_and_diff(tmp_path: Path) -> None:
    repository, user_id = _seed(tmp_path)
    first = repository.import_bundle(user_id, _payload(speed="180"))

    assert first.current_sha256
    assert first.revisions[0].native_bundle["process"]["unknown_future_key"] == ["preserved"]
    exported = repository.export_revision(user_id, first.current_revision_id or 0)
    assert exported["sha256"] == first.current_sha256
    assert exported["native_bundle"] == first.revisions[0].native_bundle

    repeated = repository.import_bundle(user_id, _payload(speed="180"))
    assert repeated.id == first.id
    assert len(repeated.revisions) == 1

    second = repository.import_bundle(
        user_id,
        _payload(speed="220", bundle_id=first.id, parent_revision_id=first.current_revision_id),
    )
    assert len(second.revisions) == 2
    assert second.revisions[1].sha256 == first.current_sha256
    difference = repository.diff(user_id, second.revisions[1].id, second.revisions[0].id)
    assert difference.changed["presets.process.outer_wall_speed"] == {"before": "180", "after": "220"}


def test_bundle_rejects_sensitive_content_and_isolates_owner(tmp_path: Path) -> None:
    repository, user_id = _seed(tmp_path)
    bundle = repository.import_bundle(user_id, _payload(speed="180"))
    other = AuthRepository(repository.database_path).create_user(UserRegisterRequest(email="other@example.test", password="correct-horse-44"))

    assert repository.detail(other.id, bundle.id) is None
    with pytest.raises(PermissionError):
        repository.export_revision(other.id, bundle.current_revision_id or 0)
    with pytest.raises(ValueError, match="sensível"):
        repository.import_bundle(user_id, _payload(speed="180", extra={"ssh_host": "10.0.0.2"}))


def test_bundle_accepts_ordinary_orcaslicer_words_without_false_sensitive_match(tmp_path: Path) -> None:
    repository, user_id = _seed(tmp_path)

    bundle = repository.import_bundle(
        user_id,
        _payload(speed="180", extra={"toolpath_settings": "Ghost compensation"}),
    )

    assert bundle.revisions[0].native_bundle["process"]["toolpath_settings"] == "Ghost compensation"


def test_controlled_orcaslicer_fixture_round_trips_semantically(tmp_path: Path) -> None:
    repository, user_id = _seed(tmp_path)
    fixture_path = Path(__file__).parent / "fixtures" / "orcaslicer_native_bundle.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    bundle = repository.import_bundle(
        user_id,
        ProfileBundleImport(
            title="Fixture OrcaSlicer controlada",
            engine_version="2.3.1.10",
            native_bundle=NativeProfileBundle.model_validate(fixture),
        ),
    )
    exported = repository.export_revision(user_id, bundle.current_revision_id or 0)

    assert exported["native_bundle"] == fixture


def _seed(tmp_path: Path):
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="owner@example.test", password="correct-horse-44"))
    return SlicingProfileBundlesRepository(database_path), user.id


def _payload(speed: str, bundle_id: int | None = None, parent_revision_id: int | None = None,
             extra: dict | None = None) -> ProfileBundleImport:
    process = {"name": "0.20 Quality", "layer_height": "0.2", "outer_wall_speed": speed,
               "inherits": "Voron base", "unknown_future_key": ["preserved"]}
    process.update(extra or {})
    return ProfileBundleImport(
        title="Voron PLA qualidade",
        engine_version="2.3.1",
        schema_version="1.2",
        compatibility={"printer": "Voron 2.4", "nozzle": "0.6"},
        native_bundle=NativeProfileBundle(
            machine={"name": "Voron 2.4", "nozzle_diameter": ["0.6"]},
            process=process,
            filament={"name": "PLA", "nozzle_temperature": ["215"]},
        ),
        bundle_id=bundle_id,
        parent_revision_id=parent_revision_id,
    )
