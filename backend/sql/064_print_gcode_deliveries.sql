CREATE TABLE IF NOT EXISTS print_gcode_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER,
    printer_id INTEGER NOT NULL,
    slicing_job_id INTEGER NOT NULL,
    preflight_id INTEGER NOT NULL,
    remote_agent_job_id INTEGER,
    rollback_agent_job_id INTEGER,
    mode TEXT NOT NULL CHECK (mode IN ('save_only', 'save_and_print')),
    status TEXT NOT NULL CHECK (status IN ('pending_remote', 'saved', 'printing', 'blocked', 'failed', 'canceled', 'rollback_pending', 'rolled_back', 'rollback_failed')),
    remote_filename TEXT NOT NULL,
    gcode_checksum_sha256 TEXT NOT NULL,
    gcode_size_bytes INTEGER NOT NULL DEFAULT 0,
    confirmation_phrase TEXT NOT NULL DEFAULT '',
    confirmation_matched INTEGER NOT NULL DEFAULT 0,
    preflight_snapshot_json TEXT NOT NULL DEFAULT '{}',
    remote_result_json TEXT NOT NULL DEFAULT '{}',
    rollback_result_json TEXT NOT NULL DEFAULT '{}',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    audit_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    canceled_at TEXT,
    rolled_back_at TEXT,
    FOREIGN KEY (owner_user_id) REFERENCES auth_users(id) ON DELETE SET NULL,
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY (slicing_job_id) REFERENCES slicing_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (preflight_id) REFERENCES print_preflight_checks(id) ON DELETE CASCADE,
    FOREIGN KEY (remote_agent_job_id) REFERENCES agent_jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (rollback_agent_job_id) REFERENCES agent_jobs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_print_gcode_deliveries_owner_created
    ON print_gcode_deliveries(owner_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_print_gcode_deliveries_printer_created
    ON print_gcode_deliveries(printer_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_print_gcode_deliveries_preflight
    ON print_gcode_deliveries(preflight_id);
