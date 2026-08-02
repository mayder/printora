CREATE TABLE IF NOT EXISTS photo_reconstruction_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capture_session_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    owner_user_id INTEGER NOT NULL,
    durable_job_id INTEGER,
    active_attempt_id INTEGER,
    run_generation INTEGER NOT NULL DEFAULT 1,
    engine_policy TEXT NOT NULL DEFAULT 'auto',
    engine_key TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    stage TEXT NOT NULL DEFAULT 'waiting',
    progress_percent INTEGER,
    idempotency_key TEXT NOT NULL,
    correlation_id TEXT NOT NULL UNIQUE,
    error_code TEXT,
    error_message TEXT,
    estimated_cost_cents INTEGER,
    actual_cost_cents INTEGER,
    cancel_requested_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(capture_session_id) REFERENCES photo_capture_sessions(id),
    FOREIGN KEY(project_id) REFERENCES print_projects(id),
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id),
    FOREIGN KEY(durable_job_id) REFERENCES durable_jobs(id),
    UNIQUE(owner_user_id, idempotency_key),
    UNIQUE(capture_session_id)
);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_owner
ON photo_reconstruction_jobs(owner_user_id, updated_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_status
ON photo_reconstruction_jobs(status, stage, updated_at);

CREATE TABLE IF NOT EXISTS photo_reconstruction_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconstruction_job_id INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL,
    engine_key TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    stage TEXT NOT NULL DEFAULT 'preparing',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    error_code TEXT,
    error_message TEXT,
    estimated_cost_cents INTEGER,
    actual_cost_cents INTEGER,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY(reconstruction_job_id) REFERENCES photo_reconstruction_jobs(id),
    UNIQUE(reconstruction_job_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_attempts_job
ON photo_reconstruction_attempts(reconstruction_job_id, attempt_number DESC);

CREATE TABLE IF NOT EXISTS photo_reconstruction_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconstruction_job_id INTEGER NOT NULL,
    attempt_id INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,
    file_format TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    unit TEXT NOT NULL DEFAULT 'unknown',
    observed_ratio REAL,
    inferred_ratio REAL,
    provenance_json TEXT NOT NULL DEFAULT '{}',
    is_canonical INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(reconstruction_job_id) REFERENCES photo_reconstruction_jobs(id),
    FOREIGN KEY(attempt_id) REFERENCES photo_reconstruction_attempts(id),
    UNIQUE(reconstruction_job_id, artifact_type, sha256)
);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_artifacts_job
ON photo_reconstruction_artifacts(reconstruction_job_id, is_canonical, artifact_type, id);

CREATE TABLE IF NOT EXISTS photo_reconstruction_engine_health (
    engine_key TEXT PRIMARY KEY,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    circuit_open_until TEXT,
    last_success_at TEXT,
    last_failure_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
