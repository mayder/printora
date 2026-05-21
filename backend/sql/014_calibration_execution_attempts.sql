CREATE TABLE IF NOT EXISTS calibration_execution_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    test_key TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    confirmation_matched INTEGER NOT NULL DEFAULT 0,
    operator_present INTEGER NOT NULL DEFAULT 0,
    gcode_reviewed INTEGER NOT NULL DEFAULT 0,
    connected INTEGER NOT NULL DEFAULT 0,
    printing INTEGER NOT NULL DEFAULT 0,
    print_state TEXT NOT NULL DEFAULT '',
    klipper_state TEXT,
    klippy_state TEXT,
    commands_json TEXT NOT NULL,
    sent_commands_json TEXT NOT NULL,
    result_json TEXT NOT NULL,
    block_reasons_json TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY (test_key) REFERENCES calibration_tests(test_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_calibration_execution_attempts_printer_created
ON calibration_execution_attempts(printer_id, created_at DESC);
