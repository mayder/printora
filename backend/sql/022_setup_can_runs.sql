CREATE TABLE IF NOT EXISTS setup_can_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL CHECK (run_type IN ('preflight', 'plan', 'apply')),
    status TEXT NOT NULL CHECK (status IN ('ok', 'warning', 'error', 'blocked')),
    safe_mode TEXT NOT NULL,
    target_host TEXT NOT NULL,
    target_port INTEGER NOT NULL,
    target_user TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    bitrate INTEGER NOT NULL,
    summary_json TEXT NOT NULL,
    plan_json TEXT,
    command_log TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(target_port > 0 AND target_port <= 65535),
    CHECK(bitrate > 0)
);

CREATE INDEX IF NOT EXISTS idx_setup_can_runs_created_at
ON setup_can_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_setup_can_runs_run_type
ON setup_can_runs(run_type);
