CREATE TABLE IF NOT EXISTS print_job_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    printer_id INTEGER NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    slicing_job_id INTEGER REFERENCES slicing_jobs(id) ON DELETE SET NULL,
    delivery_id INTEGER REFERENCES print_gcode_deliveries(id) ON DELETE SET NULL,
    library_item_id INTEGER REFERENCES social_library_items(id) ON DELETE SET NULL,
    model_reference TEXT NOT NULL,
    model_version_reference TEXT NOT NULL DEFAULT '',
    profile_reference TEXT,
    quality_reference TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('sent', 'started', 'completed', 'failed', 'canceled')),
    visibility TEXT NOT NULL DEFAULT 'private' CHECK(visibility IN ('private', 'public')),
    telemetry_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    retention_days INTEGER NOT NULL DEFAULT 180,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(delivery_id)
);

CREATE INDEX IF NOT EXISTS idx_print_job_history_owner_created
ON print_job_history(owner_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_print_job_history_library_status
ON print_job_history(library_item_id, status, visibility);

CREATE INDEX IF NOT EXISTS idx_print_job_history_printer_created
ON print_job_history(printer_id, created_at DESC);

CREATE TABLE IF NOT EXISTS print_job_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    history_id INTEGER NOT NULL REFERENCES print_job_history(id) ON DELETE CASCADE,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('worked', 'failed', 'needs_adjustment')),
    visibility TEXT NOT NULL DEFAULT 'private' CHECK(visibility IN ('private', 'public')),
    note TEXT NOT NULL DEFAULT '',
    photo_url TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_print_job_feedback_history_created
ON print_job_feedback(history_id, created_at DESC);
