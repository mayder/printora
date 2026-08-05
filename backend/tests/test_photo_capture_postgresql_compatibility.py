from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_photo_capture_postgresql_timestamps_follow_shared_adapter_contract() -> None:
    sql = (
        ROOT_DIR
        / "backend/sql/postgresql/031_photo_capture_timestamp_compatibility.sql"
    ).read_text()

    assert "'photo_capture_sessions'" in sql
    assert "'photo_capture_photos'" in sql
    assert "data_type IN ('timestamp with time zone', 'timestamp without time zone')" in sql
    assert "ALTER COLUMN %I TYPE TEXT USING %I::text" in sql


def test_photo_capture_repository_uses_cross_database_boolean_parameters() -> None:
    source = (
        ROOT_DIR / "backend/app/modules/community/photo_capture.py"
    ).read_text()

    assert "is_current = ? ORDER BY capture_index" in source
    assert "(session_id, True)" in source
    assert "SET is_current = ?, replaced_at = CURRENT_TIMESTAMP" in source
    assert "(False, session_id, capture_index, True)" in source
