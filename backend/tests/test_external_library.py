from pathlib import Path

from app.auth import AuthRepository, UserRegisterRequest
from app.database import connect_database, initialize_database
from app.external_library import ExternalLibraryRepository, ExternalReferenceCreate, ExternalSourceCreate
from app.social_catalog import LibraryFileMetadata, LibraryItemCreate, PublicProfileUpdate, SocialCatalogRepository


def test_external_bookmark_requires_attribution_and_does_not_copy_file(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="external@example.com", password="correct-horse"))
    repository = ExternalLibraryRepository(database_path)
    source = repository.create_source(user.id, ExternalSourceCreate(name="Printables", base_url="https://printables.com", attribution_required=True))

    try:
        repository.create_reference(
            user.id,
            ExternalReferenceCreate(source_id=source.id, title="Modelo externo", external_url="https://printables.com/model/123", import_mode="bookmark"),
        )
    except ValueError as exc:
        assert "atribuição" in str(exc)
    else:
        raise AssertionError("referência externa sem atribuição deveria falhar")

    reference = repository.create_reference(
        user.id,
        ExternalReferenceCreate(
            source_id=source.id,
            title="Modelo externo",
            external_url="https://printables.com/model/123",
            author_name="Maker",
            attribution_text="Fonte: Printables",
            import_mode="bookmark",
        ),
    )

    assert reference.hosted_in_printora is False
    assert reference.source_name == "Printables"
    assert reference.attribution_text == "Fonte: Printables"


def test_external_reference_detects_duplicate_by_checksum(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="duplicate@example.com", password="correct-horse"))
    social = SocialCatalogRepository(database_path)
    social.update_profile(user.id, PublicProfileUpdate(slug="duplicate-maker", display_name="Duplicate Maker", visibility="public"))
    item = social.create_library_item(
        user.id,
        LibraryItemCreate(
            title="Peça local",
            visibility="private",
            license="cc-by",
            files=[LibraryFileMetadata(file_kind="stl", file_name="local.stl", sha256="a" * 64)],
        ),
    )
    with connect_database(database_path) as connection:
        file_id = connection.execute("SELECT id FROM social_library_files WHERE item_id = ?", (item.id,)).fetchone()["id"]

    repository = ExternalLibraryRepository(database_path)
    reference = repository.create_reference(
        user.id,
        ExternalReferenceCreate(
            title="Peça externa",
            external_url="https://example.com/local.stl",
            attribution_text="Fonte externa",
            checksum_sha256="a" * 64,
            import_mode="bookmark",
        ),
    )

    assert reference.duplicate_library_file_id == file_id
