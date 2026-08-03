import struct
import zlib
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.community.photo_capture import PhotoCaptureRepository
from app.modules.community.photo_capture_contracts import PhotoCaptureCreate, PhotoCaptureScaleUpdate
from app.modules.community.photo_capture_exports import PhotoCaptureExportRepository
from app.modules.community.photo_image import sanitize_photo
from app.print_projects import PrintProjectsRepository


def _png(width: int = 32, height: int = 24, *, with_metadata: bool = False) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + (bytes([row % 255, 80, 160]) * width) for row in range(height))
    body = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    if with_metadata:
        body += chunk(b"tEXt", b"Location\x00private-place")
    return body + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _owner_and_project(database_path: Path, email: str) -> tuple[int, int]:
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email=email, password="correct-horse"))
    with connect_database(database_path) as connection:
        project_id = int(connection.execute(
            "INSERT INTO print_projects (owner_user_id, slug, title, visibility, lifecycle_status, publication_status, commercial_class) VALUES (?, ?, 'Objeto', 'private', 'active', 'draft', 'free')",
            (user.id, f"object-{user.id}"),
        ).lastrowid)
    return user.id, project_id


def test_png_capture_removes_metadata_and_reports_actionable_quality(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "capture@example.com")
    repository = PhotoCaptureRepository(database_path)
    session = repository.create(owner_id, PhotoCaptureCreate(project_id=project_id, consent_confirmed=True))

    updated = repository.upload(owner_id, session.id, "object.png", 1, "middle", _png(with_metadata=True), "upload-1")
    repeated = repository.upload(owner_id, session.id, "object.png", 1, "middle", _png(with_metadata=True), "upload-1")

    assert len(updated.photos) == 1
    assert len(repeated.photos) == 1
    assert updated.photos[0].quality_status == "needs_review"
    assert "pouca resolução" in updated.photos[0].issues[0]
    reader = repository.storage.storage.open_promoted(updated.photos[0].sha256 + ".png")
    try:
        assert b"private-place" not in reader.body.read()
    finally:
        reader.body.close()


def test_capture_is_owner_isolated_and_scale_keeps_uncertainty(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "owner@example.com")
    other_id, _ = _owner_and_project(database_path, "other@example.com")
    repository = PhotoCaptureRepository(database_path)
    session = repository.create(owner_id, PhotoCaptureCreate(project_id=project_id, target_photo_count=12, consent_confirmed=True))

    scaled = repository.update_scale(owner_id, session.id, PhotoCaptureScaleUpdate(method="known_measurement", value_mm=42, uncertainty_mm=0.5))

    assert scaled.scale_value_mm == 42
    assert scaled.scale_uncertainty_mm == 0.5
    with pytest.raises(PermissionError):
        repository.get(other_id, session.id)


def test_capture_only_completes_with_coverage_and_explicit_scale_choice(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "complete@example.com")
    repository = PhotoCaptureRepository(database_path)
    session = repository.create(owner_id, PhotoCaptureCreate(project_id=project_id, target_photo_count=12, consent_confirmed=True))
    with pytest.raises(ValueError, match="revise as fotos"):
        repository.complete(owner_id, session.id)
    repository.update_scale(owner_id, session.id, PhotoCaptureScaleUpdate(method="none"))
    with connect_database(database_path) as connection:
        for index in range(1, 13):
            band = ("low", "middle", "high")[(index - 1) % 3]
            connection.execute(
                """
                INSERT INTO photo_capture_photos (
                    session_id, owner_user_id, capture_index, height_band, file_name,
                    storage_key, sha256, size_bytes, width, height, quality_status, quality_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 100000, 1600, 1200, 'accepted', '{}')
                """,
                (session.id, owner_id, index, band, f"photo-{index}.jpg", f"photo-{index}.jpg", f"checksum-{index}"),
            )

    completed = repository.complete(owner_id, session.id)

    assert completed.status == "ready"
    assert completed.can_complete is True
    assert completed.scale_method == "none"
    assert completed.accepted_by_height_band == {"low": 4, "middle": 4, "high": 4}
    assert completed.required_by_height_band == {"low": 4, "middle": 4, "high": 4}


def test_capture_explains_missing_views_instead_of_accepting_unbalanced_total(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "unbalanced@example.com")
    repository = PhotoCaptureRepository(database_path)
    session = repository.create(
        owner_id,
        PhotoCaptureCreate(project_id=project_id, target_photo_count=12, consent_confirmed=True),
    )
    repository.update_scale(owner_id, session.id, PhotoCaptureScaleUpdate(method="none"))
    with connect_database(database_path) as connection:
        for index in range(1, 13):
            connection.execute(
                """
                INSERT INTO photo_capture_photos (
                    session_id, owner_user_id, capture_index, height_band, file_name,
                    storage_key, sha256, size_bytes, width, height, quality_status, quality_json
                ) VALUES (?, ?, ?, 'middle', ?, ?, ?, 100000, 1600, 1200, 'accepted', '{}')
                """,
                (session.id, owner_id, index, f"photo-{index}.jpg", f"photo-{index}.jpg", f"checksum-{index}"),
            )

    current = repository.get(owner_id, session.id)

    assert current.can_complete is False
    assert current.accepted_photo_count == 12
    assert current.covered_photo_count == 4
    assert current.next_actions == [
        "De cima: faça mais 4 foto(s) durante a volta.",
        "De baixo: faça mais 4 foto(s) durante a volta.",
    ]


def test_photo_signature_is_checked_instead_of_extension() -> None:
    with pytest.raises(ValueError, match="PNG válida"):
        sanitize_photo("fake.png", b"not an image")


def test_jpeg_is_normalized_without_embedded_metadata() -> None:
    source = BytesIO()
    exif = Image.Exif()
    exif[270] = "private-place"
    Image.new("RGB", (1200, 1200), (80, 140, 200)).save(source, format="JPEG", exif=exif)

    cleaned, content_type, width, height = sanitize_photo("object.jpg", source.getvalue())

    assert content_type == "image/jpeg"
    assert (width, height) == (1200, 1200)
    assert b"private-place" not in cleaned


def test_jpeg_dimensions_follow_normalized_orientation() -> None:
    source = BytesIO()
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (1200, 1600), (80, 140, 200)).save(source, format="JPEG", exif=exif)

    cleaned, _, width, height = sanitize_photo("object.jpg", source.getvalue())

    assert (width, height) == (1600, 1200)
    with Image.open(BytesIO(cleaned)) as normalized:
        assert normalized.size == (1600, 1200)


def test_photo_capture_routes_do_not_enumerate_another_owner(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "route-owner@example.com", "password": "correct-horse"}).json()["access_token"]
            other = client.post("/api/auth/register", json={"email": "route-other@example.com", "password": "correct-horse"}).json()["access_token"]
            project = client.post(
                "/api/print-projects",
                headers={"Authorization": f"Bearer {owner}"},
                json={"title": "Objeto privado", "visibility": "private"},
            ).json()
            created = client.post(
                "/api/photo-captures",
                headers={"Authorization": f"Bearer {owner}"},
                json={"project_id": project["id"], "target_photo_count": 12, "consent_confirmed": True},
            )
            assert created.status_code == 200
            session_id = created.json()["id"]

            hidden = client.get(f"/api/photo-captures/{session_id}", headers={"Authorization": f"Bearer {other}"})
            uploaded = client.post(
                f"/api/photo-captures/{session_id}/photos?file_name=object.png&capture_index=1&height_band=middle",
                headers={"Authorization": f"Bearer {owner}", "Content-Type": "application/octet-stream", "Idempotency-Key": "route-upload"},
                content=_png(),
            )

            assert hidden.status_code == 404
            assert uploaded.status_code == 200
            assert uploaded.json()["photos"][0]["capture_index"] == 1
    finally:
        get_settings.cache_clear()


def test_owner_export_contains_sanitized_photo_and_manifest(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "export@example.com")
    session = PhotoCaptureRepository(database_path).create(
        owner_id,
        PhotoCaptureCreate(project_id=project_id, target_photo_count=12, consent_confirmed=True),
    )
    PhotoCaptureRepository(database_path).upload(owner_id, session.id, "object.png", 1, "middle", _png(with_metadata=True), "export-upload")

    exported = PhotoCaptureExportRepository(database_path).build(owner_id, session.id)
    try:
        with ZipFile(exported.path) as archive:
            assert "manifest.json" in archive.namelist()
            assert "photos/001-middle.png" in archive.namelist()
            assert b"private-place" not in archive.read("photos/001-middle.png")
    finally:
        exported.path.unlink(missing_ok=True)


def test_capture_uses_shared_quota_and_appears_in_personal_storage(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "quota@example.com")
    repository = PhotoCaptureRepository(database_path)
    session = repository.create(
        owner_id,
        PhotoCaptureCreate(project_id=project_id, target_photo_count=12, consent_confirmed=True),
    )

    uploaded = repository.upload(owner_id, session.id, "object.png", 1, "middle", _png(), "quota-upload")
    report = PrintProjectsRepository(database_path).storage_report(owner_id)

    assert report.used_bytes == uploaded.photos[0].size_bytes
    assert report.file_count == 1
    with connect_database(database_path) as connection:
        connection.execute(
            "UPDATE social_file_storage_policies SET quota_bytes = ? WHERE scope_type = 'global'",
            (report.used_bytes,),
        )
    with pytest.raises(ValueError, match="cota"):
        repository.upload(owner_id, session.id, "next.png", 2, "high", _png(width=40), "quota-overflow")


def test_expiration_is_logical_and_keeps_photo_history(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner_id, project_id = _owner_and_project(database_path, "retention@example.com")
    repository = PhotoCaptureRepository(database_path)
    session = repository.create(owner_id, PhotoCaptureCreate(project_id=project_id, target_photo_count=12, consent_confirmed=True))
    repository.upload(owner_id, session.id, "first.png", 1, "middle", _png(), "first")
    repository.upload(owner_id, session.id, "replacement.png", 1, "middle", _png(40, 32), "replacement")
    with connect_database(database_path) as connection:
        connection.execute("UPDATE photo_capture_sessions SET expires_at = '2000-01-01 00:00:00' WHERE id = ?", (session.id,))

    expired = repository.list_for_owner(owner_id)[0]

    assert expired.status == "expired"
    assert len(expired.photos) == 1
    with connect_database(database_path) as connection:
        rows = connection.execute("SELECT is_current, replaced_at FROM photo_capture_photos WHERE session_id = ? ORDER BY id", (session.id,)).fetchall()
    assert len(rows) == 2
    assert [int(row["is_current"]) for row in rows] == [0, 1]
    assert rows[0]["replaced_at"] is not None
