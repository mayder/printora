CREATE TABLE IF NOT EXISTS app_update_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_version TEXT NOT NULL,
    target_tag TEXT NOT NULL,
    source_url TEXT,
    environment TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned', 'running', 'succeeded', 'failed', 'rolled_back')),
    started_at TEXT,
    finished_at TEXT,
    backup_db_path TEXT,
    backup_project_path TEXT,
    previous_project_path TEXT,
    current_project_path TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_update_runs_created_at
ON app_update_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_app_update_runs_status
ON app_update_runs(status);

CREATE TABLE IF NOT EXISTS app_update_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    step_key TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'skipped')),
    log_excerpt TEXT,
    started_at TEXT,
    finished_at TEXT,
    FOREIGN KEY (run_id) REFERENCES app_update_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_app_update_steps_run_id
ON app_update_steps(run_id);

CREATE INDEX IF NOT EXISTS idx_app_update_steps_status
ON app_update_steps(status);
