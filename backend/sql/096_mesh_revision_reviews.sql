CREATE TABLE IF NOT EXISTS mesh_revision_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    revision_id INTEGER NOT NULL,
    reconstruction_job_id INTEGER NOT NULL,
    owner_user_id INTEGER NOT NULL,
    decision TEXT NOT NULL,
    intended_use TEXT NOT NULL,
    known_axis TEXT,
    known_dimension_mm REAL,
    model_dimension_mm REAL,
    deviation_percent REAL,
    revision_sha256 TEXT NOT NULL,
    review_manifest_json TEXT NOT NULL DEFAULT '{}',
    qualification_json TEXT NOT NULL DEFAULT '{}',
    project_file_id INTEGER,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(revision_id) REFERENCES mesh_revisions(id),
    FOREIGN KEY(reconstruction_job_id) REFERENCES photo_reconstruction_jobs(id),
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id),
    FOREIGN KEY(project_file_id) REFERENCES print_project_files(id),
    UNIQUE(owner_user_id, idempotency_key),
    CHECK(decision IN ('approved_for_slicing', 'rejected')),
    CHECK(intended_use IN ('decorative', 'prototype', 'mechanical')),
    CHECK(known_axis IS NULL OR known_axis IN ('x', 'y', 'z'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mesh_revision_one_approval
ON mesh_revision_reviews(revision_id)
WHERE decision = 'approved_for_slicing';

CREATE INDEX IF NOT EXISTS idx_mesh_revision_reviews_job
ON mesh_revision_reviews(reconstruction_job_id, created_at DESC, id DESC);
