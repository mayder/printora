CREATE TABLE IF NOT EXISTS maintenance_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    performed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    component TEXT,
    title TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    component TEXT NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 30,
    last_done_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    UNIQUE(printer_id, name)
);

CREATE INDEX IF NOT EXISTS idx_maintenance_events_printer_performed
ON maintenance_events(printer_id, performed_at);

CREATE INDEX IF NOT EXISTS idx_maintenance_tasks_printer_active
ON maintenance_tasks(printer_id, is_active);
