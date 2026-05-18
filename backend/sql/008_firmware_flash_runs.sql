CREATE TABLE IF NOT EXISTS firmware_flash_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    board_id INTEGER NOT NULL,
    build_run_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'flash_dry_run_planned',
    flash_method TEXT NOT NULL,
    can_uuid TEXT,
    can_interface TEXT NOT NULL DEFAULT 'can0',
    binary_path TEXT NOT NULL,
    commands_json TEXT NOT NULL,
    checklist_json TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(board_id) REFERENCES firmware_boards(id) ON DELETE CASCADE,
    FOREIGN KEY(build_run_id) REFERENCES firmware_build_runs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_firmware_flash_runs_printer_created
ON firmware_flash_runs(printer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_firmware_flash_runs_board_created
ON firmware_flash_runs(board_id, created_at);
