CREATE TABLE IF NOT EXISTS mesh_qualifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconstruction_artifact_id INTEGER NOT NULL UNIQUE,
    source_sha256 TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    status TEXT NOT NULL,
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(reconstruction_artifact_id) REFERENCES photo_reconstruction_artifacts(id)
);

CREATE INDEX IF NOT EXISTS idx_mesh_qualifications_status
ON mesh_qualifications(status, created_at DESC, id DESC);
