CREATE TABLE IF NOT EXISTS backup_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    destination_path TEXT NOT NULL,
    include_patterns_json TEXT NOT NULL,
    exclude_patterns_json TEXT NOT NULL,
    dry_run_only INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    UNIQUE(printer_id, name)
);

CREATE TABLE IF NOT EXISTS backup_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    policy_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    dry_run INTEGER NOT NULL DEFAULT 1,
    source_path TEXT NOT NULL,
    destination_path TEXT NOT NULL,
    include_patterns_json TEXT NOT NULL,
    exclude_patterns_json TEXT NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    total_bytes INTEGER NOT NULL DEFAULT 0,
    message TEXT NOT NULL,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(policy_id) REFERENCES backup_policies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_backup_policies_printer_active
ON backup_policies(printer_id, is_active);

CREATE INDEX IF NOT EXISTS idx_backup_runs_printer_created
ON backup_runs(printer_id, created_at);
