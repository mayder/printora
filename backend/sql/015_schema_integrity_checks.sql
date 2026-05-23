CREATE TABLE IF NOT EXISTS schema_integrity_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    schema_revision INTEGER NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_schema_integrity_checks_checked
ON schema_integrity_checks(checked_at);
