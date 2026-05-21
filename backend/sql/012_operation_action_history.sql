CREATE TABLE IF NOT EXISTS operation_action_previews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action_id TEXT NOT NULL,
    action_label TEXT NOT NULL,
    safe_mode TEXT NOT NULL,
    executable INTEGER NOT NULL DEFAULT 0,
    would_send_gcode INTEGER NOT NULL DEFAULT 0,
    command_preview_json TEXT NOT NULL,
    blockers_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_operation_action_previews_printer_created
ON operation_action_previews(printer_id, created_at);
