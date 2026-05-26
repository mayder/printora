CREATE TABLE IF NOT EXISTS update_alert_silences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    version_key TEXT NOT NULL,
    current_version TEXT,
    remote_version TEXT,
    full_version TEXT,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    UNIQUE(printer_id, component_name, version_key)
);

CREATE INDEX IF NOT EXISTS idx_update_alert_silences_printer
ON update_alert_silences(printer_id, component_name);
