from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.print_projects import (
    PrintProjectCreateRequest,
    PrintProjectExternalLinkRequest,
    PrintProjectPublicationRequest,
    PrintProjectPublicationReviewRequest,
    PrintProjectSaveRequest,
    PrintProjectShareRequest,
    PrintProjectUpdateRequest,
    PrintProjectsRepository,
)


VALID_STL = b"solid printora\nfacet normal 0 0 0\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid\n"


def test_print_project_contract_sets_project_as_root_entity(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)

    contract = PrintProjectsRepository(database_path).contract()

    assert contract.root_entity == "Projeto de impressão"
    assert "Compartilhamento em comunidade" in contract.relations
    assert "slicing_job" in contract.immutable_snapshot_required_for
    assert "Comunidade compartilha" in contract.community_ownership_rule
    assert "Link externo" in contract.external_link_rule


def test_public_project_explore_keeps_external_bookmark_unslicable(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="projects@example.com", password="correct-horse")
    )
    with connect_database(database_path) as connection:
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, description, visibility, lifecycle_status,
                publication_status, commercial_class, license, tags_json
            )
            VALUES (?, 'bookmark-voron-door', 'Porta Voron externa', 'Referencia externa', 'public',
                'active', 'approved', 'free', 'cc-by', '["voron", "porta"]')
            """,
            (user.id,),
        ).lastrowid
        file_id = connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, external_url, validation_status, can_slice
            )
            VALUES (?, 'link', 'external_reference', 'Printables', 'https://printables.com/model/123',
                'metadata_only', 0)
            """,
            (project_id,),
        ).lastrowid
        connection.execute("UPDATE print_projects SET primary_file_id = ? WHERE id = ?", (file_id, project_id))

    projects = PrintProjectsRepository(database_path).explore("voron")

    assert len(projects) == 1
    assert projects[0].external_reference_only is True
    assert projects[0].hosted_in_printora is False
    assert projects[0].can_slice is False
    assert projects[0].primary_file is not None
    assert projects[0].primary_file.file_role == "external_reference"


def test_public_project_explore_allows_partial_valid_files(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="partial@example.com", password="correct-horse")
    )
    with connect_database(database_path) as connection:
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, description, visibility, lifecycle_status,
                publication_status, commercial_class, license
            )
            VALUES (?, 'multi-file-project', 'Projeto multi arquivo', 'Uma peça válida e uma rejeitada',
                'public', 'active', 'approved', 'free', 'cc-by')
            """,
            (user.id,),
        ).lastrowid
        valid_file_id = connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, validation_status, can_slice
            )
            VALUES (?, 'stl', 'primary', 'valid.stl', 'validated', 1)
            """,
            (project_id,),
        ).lastrowid
        connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, validation_status, can_slice
            )
            VALUES (?, 'stl', 'optional_part', 'broken.stl', 'rejected', 0)
            """,
            (project_id,),
        )
        connection.execute("UPDATE print_projects SET primary_file_id = ? WHERE id = ?", (valid_file_id, project_id))

    projects = PrintProjectsRepository(database_path).explore("multi")

    assert len(projects) == 1
    assert projects[0].file_count == 2
    assert projects[0].printable_file_count == 2
    assert projects[0].can_slice is True
    assert projects[0].primary_file is not None
    assert projects[0].primary_file.validation_status == "validated"


def test_project_detail_uses_immutable_snapshot_and_does_not_change_after_project_update(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="snapshot@example.com", password="correct-horse")
    )
    with connect_database(database_path) as connection:
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, description, visibility, lifecycle_status,
                publication_status, commercial_class, license
            )
            VALUES (?, 'snapshot-project', 'Projeto snapshot', 'Original',
                'public', 'active', 'approved', 'free', 'cc-by')
            """,
            (user.id,),
        ).lastrowid
        file_id = connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, validation_status, can_slice
            )
            VALUES (?, 'stl', 'primary', 'part-v1.stl', 'validated', 1)
            """,
            (project_id,),
        ).lastrowid
        version_id = connection.execute(
            """
            INSERT INTO print_project_versions (
                project_id, version_label, project_snapshot_json, files_snapshot_json, created_by_user_id
            )
            VALUES (?, 'v1', '{"title":"Projeto snapshot"}', '[{"file_name":"part-v1.stl"}]', ?)
            """,
            (project_id, user.id),
        ).lastrowid
        connection.execute(
            "UPDATE print_projects SET primary_file_id = ?, current_version_id = ?, title = 'Projeto alterado' WHERE id = ?",
            (file_id, version_id, project_id),
        )

    detail = PrintProjectsRepository(database_path).detail("snapshot-project", user.id)

    assert detail is not None
    assert detail.title == "Projeto alterado"
    assert detail.immutable_snapshot_ready is True
    assert detail.versions[0].project_snapshot["title"] == "Projeto snapshot"
    assert detail.versions[0].files_snapshot[0]["file_name"] == "part-v1.stl"
    anonymous = PrintProjectsRepository(database_path).detail("snapshot-project")
    assert anonymous is not None
    assert anonymous.versions == []
    assert anonymous.publication_reviews == []


def test_save_project_creates_reference_without_copying_files(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="owner@example.com", password="correct-horse")
    )
    viewer = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="viewer@example.com", password="correct-horse")
    )
    with connect_database(database_path) as connection:
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license
            )
            VALUES (?, 'save-reference-project', 'Salvar referência', 'public',
                'active', 'approved', 'free', 'cc-by')
            """,
            (owner.id,),
        ).lastrowid
        connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, validation_status, can_slice
            )
            VALUES (?, 'stl', 'primary', 'single.stl', 'validated', 1)
            """,
            (project_id,),
        )

    detail = PrintProjectsRepository(database_path).save_project(
        viewer.id,
        project_id,
        PrintProjectSaveRequest(save_kind="reference"),
    )

    with connect_database(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM print_project_files WHERE project_id = ?", (project_id,)).fetchone()[0] == 1
        save = connection.execute("SELECT save_kind, status FROM print_project_saves WHERE owner_user_id = ?", (viewer.id,)).fetchone()
    assert detail.saved_by_viewer is True
    assert save["save_kind"] == "reference"
    assert save["status"] == "active"


def test_community_share_is_many_to_many_and_does_not_change_project_ownership_or_visibility(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="share-owner@example.com", password="correct-horse")
    )
    with connect_database(database_path) as connection:
        project_id = connection.execute(
            """
            INSERT INTO print_projects (
                owner_user_id, slug, title, visibility, lifecycle_status,
                publication_status, commercial_class, license
            )
            VALUES (?, 'shared-project', 'Projeto compartilhado', 'public',
                'active', 'approved', 'free', 'cc-by')
            """,
            (owner.id,),
        ).lastrowid
        connection.execute(
            """
            INSERT INTO print_project_files (
                project_id, file_kind, file_role, file_name, validation_status, can_slice
            )
            VALUES (?, 'stl', 'primary', 'shared.stl', 'validated', 1)
            """,
            (project_id,),
        )
        community_slug = "voron-share"
        connection.execute(
            """
            INSERT INTO social_communities (slug, name, scope, status)
            VALUES (?, 'Voron Share', 'manufacturer', 'active')
            """,
            (community_slug,),
        )

    repository = PrintProjectsRepository(database_path)
    detail = repository.share_with_community(
        owner.id,
        project_id,
        PrintProjectShareRequest(community_slug=community_slug),
    )
    community_projects = repository.community_projects(community_slug)

    with connect_database(database_path) as connection:
        project = connection.execute(
            "SELECT owner_user_id, visibility, commercial_class FROM print_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
    assert detail.community_shares
    assert len(community_projects) == 1
    assert community_projects[0].id == project_id
    assert project["owner_user_id"] == owner.id
    assert project["visibility"] == "public"
    assert project["commercial_class"] == "free"


def test_create_personal_project_without_community_and_upload_multiple_files(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="personal@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)

    created = repository.create_project(
        user.id,
        PrintProjectCreateRequest(
            title="Suporte de mesa",
            description="Projeto pessoal multi arquivo",
            visibility="private",
            license="cc-by",
            tags=["mesa", "organizador"],
            material="PLA",
            component="suporte",
        ),
    )
    uploaded = repository.upload_file(user.id, created.id, "suporte-principal.stl", "primary", VALID_STL)
    uploaded = repository.upload_file(user.id, created.id, "clipe-opcional.stl", "optional_part", VALID_STL)
    my_projects = repository.my_projects(user.id)
    storage = repository.storage_report(user.id)

    assert uploaded.visibility == "private"
    assert uploaded.community_shares == []
    assert uploaded.file_count == 2
    assert uploaded.primary_file is not None
    assert uploaded.primary_file.file_name == "suporte-principal.stl"
    assert uploaded.primary_file.slice_status in {"pending", "eligible"}
    assert storage.file_count == 2
    assert storage.used_bytes == len(VALID_STL) * 2
    assert my_projects[0].id == created.id


def test_upload_rejection_blocks_only_the_affected_project_file(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="rejected-file@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(user.id, PrintProjectCreateRequest(title="Projeto parcial"))

    detail = repository.upload_file(user.id, project.id, "valido.stl", "primary", VALID_STL)
    detail = repository.upload_file(user.id, project.id, "quebrado.stl", "optional_part", b"bad")

    rejected = next(file for file in detail.files if file.file_name == "quebrado.stl")
    assert detail.can_slice is True
    assert detail.file_count == 2
    assert rejected.can_slice is False
    assert rejected.validation_status == "rejected"
    assert rejected.slice_status == "failure"


def test_external_link_is_personal_bookmark_and_cannot_slice_without_local_file(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="external-link@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(user.id, PrintProjectCreateRequest(title="Bookmark externo", source_url="https://example.com/model"))

    detail = repository.add_external_link(
        user.id,
        project.id,
        PrintProjectExternalLinkRequest(url="https://example.com/model", label="Modelo externo"),
    )

    assert detail.external_reference_only is True
    assert detail.can_slice is False
    assert detail.files[0].file_role == "external_reference"
    assert detail.files[0].slice_status == "external_no_local"


def test_update_project_metadata_creates_new_snapshot_without_changing_previous_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="edit-project@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(user.id, PrintProjectCreateRequest(title="Projeto editável"))

    detail = repository.update_project(
        user.id,
        project.id,
        PrintProjectUpdateRequest(title="Projeto editado", tags=["editado"], material="PETG"),
    )

    assert detail.title == "Projeto editado"
    assert len(detail.versions) == 2
    assert detail.versions[-1].project_snapshot["title"] == "Projeto editável"
    assert detail.versions[0].project_snapshot["title"] == "Projeto editado"


def test_archive_project_hides_it_without_deleting_files(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="archive-project@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(user.id, PrintProjectCreateRequest(title="Projeto arquivável"))
    repository.upload_file(user.id, project.id, "peca.stl", "primary", VALID_STL)

    repository.archive_project(user.id, project.id)

    with connect_database(database_path) as connection:
        file_count = connection.execute("SELECT COUNT(*) FROM print_project_files WHERE project_id = ?", (project.id,)).fetchone()[0]
        lifecycle = connection.execute("SELECT lifecycle_status FROM print_projects WHERE id = ?", (project.id,)).fetchone()["lifecycle_status"]
    assert file_count == 1
    assert lifecycle == "archived"
    assert repository.detail(project.slug, user.id) is None


def test_private_project_detail_route_uses_authenticated_viewer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            token_response = client.post(
                "/api/auth/register",
                json={"email": "private-detail@example.com", "password": "correct-horse"},
            )
            assert token_response.status_code == 200
            token = token_response.json()["access_token"]
            created = client.post(
                "/api/print-projects",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "Projeto privado via rota", "visibility": "private"},
            )
            assert created.status_code == 200
            slug = created.json()["slug"]

            public_response = client.get(f"/api/print-projects/{slug}")
            authenticated_response = client.get(f"/api/print-projects/{slug}", headers={"Authorization": f"Bearer {token}"})

            assert public_response.status_code == 404
            assert authenticated_response.status_code == 200
            assert authenticated_response.json()["title"] == "Projeto privado via rota"
    finally:
        get_settings.cache_clear()


def test_publication_keeps_draft_out_of_public_explore_until_approved(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="publish-free@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(user.id, PrintProjectCreateRequest(title="Projeto publico livre"))
    repository.upload_file(user.id, project.id, "peca.stl", "primary", VALID_STL)

    draft = repository.update_publication(
        user.id,
        project.id,
        PrintProjectPublicationRequest(visibility="public", commercial_class="free", submit_for_review=False),
    )
    assert draft.publication_status == "draft"
    assert repository.explore("publico") == []

    approved = repository.update_publication(
        user.id,
        project.id,
        PrintProjectPublicationRequest(visibility="public", commercial_class="free", submit_for_review=True),
    )

    public_projects = repository.explore("publico")
    assert approved.publication_status == "approved"
    assert len(public_projects) == 1
    assert public_projects[0].commercial_class == "free"


def test_premium_project_requires_review_before_public_exposure(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="premium-owner@example.com", password="correct-horse")
    )
    reviewer = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="breno@mayder.com.br", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(owner.id, PrintProjectCreateRequest(title="Projeto premium"))
    repository.upload_file(owner.id, project.id, "premium.stl", "primary", VALID_STL)

    in_review = repository.update_publication(
        owner.id,
        project.id,
        PrintProjectPublicationRequest(
            visibility="public",
            commercial_class="premium",
            price_cents=1990,
            commercial_terms="Pagamento real fora do escopo atual.",
            submit_for_review=True,
        ),
    )
    assert in_review.publication_status == "in_review"
    assert in_review.price_cents == 1990
    assert repository.explore("premium") == []

    approved = repository.review_publication(
        reviewer.id,
        project.id,
        PrintProjectPublicationReviewRequest(status="approved", note="Revisado para vitrine premium."),
    )

    public_projects = repository.explore("premium")
    assert approved.publication_status == "approved"
    assert approved.publication_reviews[0].status == "approved"
    assert public_projects[0].commercial_class == "premium"


def test_sponsored_project_requires_disclosure_and_community_share_does_not_publish(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    owner = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="sponsored-owner@example.com", password="correct-horse")
    )
    repository = PrintProjectsRepository(database_path)
    project = repository.create_project(owner.id, PrintProjectCreateRequest(title="Projeto patrocinado"))
    with connect_database(database_path) as connection:
        connection.execute(
            """
            INSERT INTO social_communities (slug, name, scope, status)
            VALUES ('vitrine-share', 'Vitrine Share', 'manufacturer', 'active')
            """
        )

    try:
        repository.update_publication(
            owner.id,
            project.id,
            PrintProjectPublicationRequest(visibility="public", commercial_class="sponsored", submit_for_review=True),
        )
    except ValueError as exc:
        assert "transparência" in str(exc)
    else:
        raise AssertionError("sponsored without disclosure should fail")

    shared = repository.share_with_community(owner.id, project.id, PrintProjectShareRequest(community_slug="vitrine-share"))
    assert shared.publication_status == "draft"
    assert shared.visibility == "private"
    assert repository.community_projects("vitrine-share") == []
