CREATE TABLE IF NOT EXISTS operation_action_execution_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    preview_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action_id TEXT NOT NULL,
    status TEXT NOT NULL,
    confirmation_matched INTEGER NOT NULL DEFAULT 0,
    executable INTEGER NOT NULL DEFAULT 0,
    would_send_gcode INTEGER NOT NULL DEFAULT 0,
    block_reason TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(preview_id) REFERENCES operation_action_previews(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_operation_action_execution_attempts_printer_created
ON operation_action_execution_attempts(printer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_operation_action_execution_attempts_preview
ON operation_action_execution_attempts(preview_id);
