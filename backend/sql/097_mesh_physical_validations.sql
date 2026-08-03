CREATE TABLE IF NOT EXISTS mesh_physical_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL REFERENCES mesh_revision_reviews(id),
    history_id INTEGER NOT NULL REFERENCES print_job_history(id),
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id),
    outcome TEXT NOT NULL CHECK(outcome IN ('passed', 'needs_adjustment', 'failed')),
    instrument_label TEXT NOT NULL,
    expected_x_mm REAL,
    expected_y_mm REAL,
    expected_z_mm REAL,
    measured_x_mm REAL,
    measured_y_mm REAL,
    measured_z_mm REAL,
    error_x_percent REAL,
    error_y_percent REAL,
    error_z_percent REAL,
    max_error_percent REAL NOT NULL,
    printer_snapshot_json TEXT NOT NULL DEFAULT '{}',
    material_snapshot_json TEXT NOT NULL DEFAULT '{}',
    profile_snapshot_json TEXT NOT NULL DEFAULT '{}',
    revision_sha256 TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(history_id),
    UNIQUE(owner_user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_mesh_physical_validations_review
ON mesh_physical_validations(review_id, created_at DESC, id DESC);
