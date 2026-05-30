CREATE TABLE IF NOT EXISTS setup_final_validation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL CHECK (status IN ('approved_for_calibration', 'approved_with_notes', 'blocked', 'needs_manual_intervention')),
    safe_mode TEXT NOT NULL,
    target_host TEXT NOT NULL,
    target_port INTEGER NOT NULL,
    target_user TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    expected_uuids_json TEXT NOT NULL,
    summary TEXT NOT NULL,
    checks_json TEXT NOT NULL,
    sections_json TEXT NOT NULL,
    report_markdown TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(target_port > 0 AND target_port <= 65535)
);

CREATE INDEX IF NOT EXISTS idx_setup_final_validation_runs_created_at
ON setup_final_validation_runs(created_at);
