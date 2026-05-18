CREATE TABLE IF NOT EXISTS firmware_build_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    board_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'dry_run_planned',
    klipper_path TEXT NOT NULL DEFAULT '~/klipper',
    output_dir TEXT NOT NULL,
    config_backup_path TEXT NOT NULL,
    binary_output_path TEXT NOT NULL,
    commands_json TEXT NOT NULL,
    checklist_json TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(board_id) REFERENCES firmware_boards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_firmware_build_runs_printer_created
ON firmware_build_runs(printer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_firmware_build_runs_board_created
ON firmware_build_runs(board_id, created_at);
