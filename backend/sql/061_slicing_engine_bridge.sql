CREATE TABLE IF NOT EXISTS slicing_engine_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine TEXT NOT NULL,
    configured_path TEXT,
    detected_path TEXT,
    version_text TEXT,
    status TEXT NOT NULL CHECK(status IN ('ready', 'blocked')),
    warnings_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS slicing_dry_run_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine TEXT NOT NULL,
    model_reference TEXT NOT NULL,
    printer_reference TEXT NOT NULL,
    material_reference TEXT NOT NULL,
    quality_reference TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ready', 'blocked')),
    command_preview_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    sanitized_log TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_slicing_engine_checks_created
ON slicing_engine_checks(created_at);

CREATE INDEX IF NOT EXISTS idx_slicing_dry_run_logs_created
ON slicing_dry_run_logs(created_at);
