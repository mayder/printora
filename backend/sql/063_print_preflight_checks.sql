CREATE TABLE IF NOT EXISTS print_preflight_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    printer_id INTEGER NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    slicing_job_id INTEGER NOT NULL REFERENCES slicing_jobs(id) ON DELETE CASCADE,
    remote_agent_job_id INTEGER REFERENCES agent_jobs(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK(status IN ('approved', 'blocked', 'pending_remote', 'failed')),
    local_metadata_json TEXT NOT NULL DEFAULT '{}',
    remote_preflight_json TEXT NOT NULL DEFAULT '{}',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    checklist_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_print_preflight_checks_slicing_job
ON print_preflight_checks(slicing_job_id, created_at);

CREATE INDEX IF NOT EXISTS idx_print_preflight_checks_printer
ON print_preflight_checks(printer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_print_preflight_checks_remote_job
ON print_preflight_checks(remote_agent_job_id);
