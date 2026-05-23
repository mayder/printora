CREATE TABLE IF NOT EXISTS schema_versions (
    script_name TEXT PRIMARY KEY,
    checksum_sha256 TEXT NOT NULL,
    execution_order INTEGER NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schema_versions_execution_order
ON schema_versions(execution_order);

CREATE TABLE IF NOT EXISTS app_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    app_name TEXT NOT NULL DEFAULT 'Printora',
    version TEXT NOT NULL,
    schema_revision INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
