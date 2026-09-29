CREATE TABLE IF NOT EXISTS mesh_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconstruction_job_id INTEGER NOT NULL,
    source_artifact_id INTEGER NOT NULL,
    parent_revision_id INTEGER,
    owner_user_id INTEGER NOT NULL,
    durable_job_id INTEGER,
    operation TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    request_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    output_format TEXT,
    storage_key TEXT,
    sha256 TEXT,
    size_bytes INTEGER,
    unit TEXT NOT NULL DEFAULT 'unknown',
    manifest_json TEXT NOT NULL DEFAULT '{}',
    qualification_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(reconstruction_job_id) REFERENCES photo_reconstruction_jobs(id),
    FOREIGN KEY(source_artifact_id) REFERENCES photo_reconstruction_artifacts(id),
    FOREIGN KEY(parent_revision_id) REFERENCES mesh_revisions(id),
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id),
    FOREIGN KEY(durable_job_id) REFERENCES durable_jobs(id),
    UNIQUE(owner_user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_mesh_revisions_job
ON mesh_revisions(reconstruction_job_id, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_mesh_revisions_status
ON mesh_revisions(status, updated_at, id);
