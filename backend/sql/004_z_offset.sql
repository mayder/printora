CREATE TABLE IF NOT EXISTS z_offset_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    plate_name TEXT NOT NULL,
    material TEXT NOT NULL,
    nozzle TEXT NOT NULL DEFAULT 'T0',
    offset_value REAL NOT NULL,
    previous_offset_value REAL,
    delta_value REAL,
    alert_level TEXT NOT NULL DEFAULT 'ok',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_z_offset_records_printer_recorded
ON z_offset_records(printer_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_z_offset_records_lookup
ON z_offset_records(printer_id, plate_name, material, nozzle, recorded_at);
