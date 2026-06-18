from pathlib import Path

from app.auth import AuthRepository, UserRegisterRequest
from app.database import connect_database, initialize_database
from app.print_projects import PrintProjectSaveRequest, PrintProjectShareRequest, PrintProjectsRepository


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

    detail = PrintProjectsRepository(database_path).detail("snapshot-project")

    assert detail is not None
    assert detail.title == "Projeto alterado"
    assert detail.immutable_snapshot_ready is True
    assert detail.versions[0].project_snapshot["title"] == "Projeto snapshot"
    assert detail.versions[0].files_snapshot[0]["file_name"] == "part-v1.stl"


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
