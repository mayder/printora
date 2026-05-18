CREATE TABLE IF NOT EXISTS firmware_boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    preset_id TEXT NOT NULL,
    can_uuid TEXT,
    can_interface TEXT NOT NULL DEFAULT 'can0',
    connection_type TEXT NOT NULL,
    mcu TEXT NOT NULL,
    flash_method TEXT NOT NULL,
    config_file TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    UNIQUE(printer_id, name)
);

CREATE INDEX IF NOT EXISTS idx_firmware_boards_printer
ON firmware_boards(printer_id, is_active, name);

CREATE INDEX IF NOT EXISTS idx_firmware_boards_preset
ON firmware_boards(preset_id);
