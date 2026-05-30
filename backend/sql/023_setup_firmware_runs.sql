CREATE TABLE IF NOT EXISTS setup_firmware_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL CHECK (run_type IN ('plan', 'build')),
    status TEXT NOT NULL CHECK (status IN ('ok', 'warning', 'error', 'blocked')),
    safe_mode TEXT NOT NULL,
    target_host TEXT NOT NULL,
    target_port INTEGER NOT NULL,
    target_user TEXT NOT NULL,
    board_name TEXT NOT NULL,
    board_role TEXT NOT NULL,
    preset_id TEXT NOT NULL,
    can_interface TEXT NOT NULL,
    config_path TEXT,
    artifact_dir TEXT,
    binary_path TEXT,
    config_sha256 TEXT,
    binary_sha256 TEXT,
    uuid_query_json TEXT,
    summary_json TEXT NOT NULL,
    plan_json TEXT,
    command_log TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(target_port > 0 AND target_port <= 65535)
);

CREATE INDEX IF NOT EXISTS idx_setup_firmware_runs_created_at
ON setup_firmware_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_setup_firmware_runs_preset
ON setup_firmware_runs(preset_id);
