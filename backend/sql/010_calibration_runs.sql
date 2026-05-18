CREATE TABLE IF NOT EXISTS calibration_test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    test_key TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    result_status TEXT NOT NULL,
    material TEXT NOT NULL DEFAULT '',
    plate_name TEXT NOT NULL DEFAULT '',
    nozzle TEXT NOT NULL DEFAULT '',
    observed_value TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    gcode_reviewed INTEGER NOT NULL DEFAULT 0,
    photo_reference TEXT,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(test_key) REFERENCES calibration_tests(test_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_calibration_test_runs_printer_created
ON calibration_test_runs(printer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_calibration_test_runs_test_created
ON calibration_test_runs(test_key, created_at);
