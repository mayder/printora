CREATE TABLE IF NOT EXISTS printers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    moonraker_url TEXT NOT NULL,
    host_audit_mode TEXT NOT NULL DEFAULT 'disabled',
    host_audit_ssh_target TEXT,
    location TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS app_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS printer_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snapshot_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_printers_active ON printers(is_active);
CREATE INDEX IF NOT EXISTS idx_app_events_printer_created ON app_events(printer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_printer_snapshots_printer_created ON printer_snapshots(printer_id, created_at);
