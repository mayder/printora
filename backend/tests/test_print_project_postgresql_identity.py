from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
IDENTITY_TABLES = (
    "print_projects",
    "print_project_files",
    "print_project_versions",
    "print_project_community_shares",
    "print_project_saves",
    "print_project_publication_reviews",
)


def test_print_project_postgresql_identity_covers_every_writable_core_table() -> None:
    sql = (
        ROOT_DIR / "backend/sql/postgresql/030_print_project_identity.sql"
    ).read_text()

    for table_name in IDENTITY_TABLES:
        assert f"'{table_name}'" in sql

    assert "IN SHARE ROW EXCLUSIVE MODE" in sql
    assert "CREATE SEQUENCE IF NOT EXISTS" in sql
    assert "OWNED BY public.%I.id" in sql
    assert "ALTER COLUMN id SET DEFAULT nextval" in sql
    assert "COALESCE(MAX(id), 0)" in sql
    assert "COUNT(*) > 0" in sql


def test_cloud_deploy_applies_incremental_postgresql_identity_before_runtime() -> None:
    deploy = (ROOT_DIR / "scripts/cloud/deploy-blue-green.sh").read_text()
    schema_runner = (
        ROOT_DIR / "scripts/cloud/apply-postgresql-schema.sh"
    ).read_text()

    assert '"$SCRIPT_DIR/apply-postgresql-schema.sh" "$release_dir"' in deploy
    assert 'backend/sql/postgresql/[0-9]*.sql' in schema_runner
    assert "postgresql-runtime-permissions.sql" in schema_runner
