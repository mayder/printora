from __future__ import annotations

from pathlib import Path
import struct

import pytest

from app.auth import AuthRepository, UserRegisterRequest
from app.database import initialize_database
from app.social_catalog import LibraryFileMetadata, LibraryItemCreate, PublicProfileUpdate, SocialCatalogRepository
from app.social_object_downloads import SocialObjectDownloadRepository


def test_promoted_download_token_is_short_lived_single_use_and_owner_scoped(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    stranger = auth.create_user(UserRegisterRequest(email="stranger@example.com", password="correct-horse"))
    catalog = SocialCatalogRepository(database_path)
    catalog.update_profile(owner.id, PublicProfileUpdate(slug="owner", display_name="Owner", visibility="public"))
    item = catalog.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Private model",
            visibility="private",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="metadata.stl")],
        ),
    )
    body = _binary_stl([(0, 0, 0), (20, 0, 0), (0, 30, 0), (0, 0, 80)])
    uploaded = catalog.upload_library_file(item.id, owner.id, False, "model.stl", body)
    file_id = next(file.id for file in uploaded.files if file.file_name == "model.stl")
    catalog.analyze_library_file(file_id, owner.id, False)
    downloads = SocialObjectDownloadRepository(database_path)

    with pytest.raises(PermissionError, match="não autorizado"):
        downloads.issue_social_file_token(file_id, stranger.id, False)

    token = downloads.issue_social_file_token(file_id, owner.id, False)
    assert token.download_url == "/api/storage/download"
    assert token.authorization_token not in token.download_url
    reader, file_name = downloads.consume(token.authorization_token)
    try:
        assert reader.body.read() == body
        assert file_name == "model.stl"
    finally:
        reader.body.close()

    with pytest.raises(PermissionError, match="já utilizado"):
        downloads.consume(token.authorization_token)


def _binary_stl(points: list[tuple[float, float, float]]) -> bytes:
    triangles = []
    for point in points:
        triangles.append(struct.pack("<12fH", 0, 0, 1, *point, *point, *point, 0))
    return b"Printora".ljust(80, b"\0") + struct.pack("<I", len(triangles)) + b"".join(triangles)
