CREATE TABLE IF NOT EXISTS setup_flash_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL CHECK (run_type IN ('preflight', 'plan', 'flash')),
    status TEXT NOT NULL CHECK (status IN ('ok', 'warning', 'error', 'blocked', 'requires_recovery')),
    safe_mode TEXT NOT NULL,
    target_host TEXT NOT NULL,
    target_port INTEGER NOT NULL,
    target_user TEXT NOT NULL,
    board_name TEXT NOT NULL,
    board_role TEXT NOT NULL,
    flash_method TEXT NOT NULL,
    can_interface TEXT,
    expected_uuid TEXT,
    artifact_path TEXT NOT NULL,
    artifact_sha256 TEXT,
    previous_binary_path TEXT,
    confirmation_phrase TEXT,
    duration_ms INTEGER,
    summary_json TEXT NOT NULL,
    preflight_json TEXT,
    plan_json TEXT,
    command_log TEXT,
    rollback_json TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(target_port > 0 AND target_port <= 65535)
);

CREATE INDEX IF NOT EXISTS idx_setup_flash_runs_created_at
ON setup_flash_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_setup_flash_runs_board
ON setup_flash_runs(board_name, flash_method);
