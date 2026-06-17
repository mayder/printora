CREATE TABLE IF NOT EXISTS slicing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    printer_id INTEGER REFERENCES printers(id) ON DELETE SET NULL,
    material_profile_id INTEGER REFERENCES social_material_profiles(id) ON DELETE SET NULL,
    engine TEXT NOT NULL CHECK(engine IN ('orcaslicer', 'prusaslicer')),
    model_reference TEXT NOT NULL,
    model_version_reference TEXT NOT NULL DEFAULT '',
    model_dimensions_json TEXT NOT NULL DEFAULT '{}',
    quality_reference TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned', 'running', 'completed', 'failed', 'canceled')),
    compatibility_json TEXT NOT NULL DEFAULT '{}',
    input_json TEXT NOT NULL DEFAULT '{}',
    output_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    canceled_at TEXT
);

CREATE TABLE IF NOT EXISTS slicing_job_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES slicing_jobs(id) ON DELETE CASCADE,
    artifact_kind TEXT NOT NULL CHECK(artifact_kind IN ('gcode', 'log', 'metadata', 'preview')),
    storage_key TEXT NOT NULL,
    checksum_sha256 TEXT,
    size_bytes INTEGER NOT NULL DEFAULT 0 CHECK(size_bytes >= 0),
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_owner_created
ON slicing_jobs(owner_user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_printer_created
ON slicing_jobs(printer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_status
ON slicing_jobs(status, created_at);

CREATE INDEX IF NOT EXISTS idx_slicing_job_artifacts_job
ON slicing_job_artifacts(job_id, artifact_kind);
