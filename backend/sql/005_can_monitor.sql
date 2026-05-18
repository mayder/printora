CREATE TABLE IF NOT EXISTS can_bus_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    interface_name TEXT NOT NULL DEFAULT 'can0',
    rx_error INTEGER NOT NULL DEFAULT 0,
    tx_error INTEGER NOT NULL DEFAULT 0,
    tx_retries INTEGER NOT NULL DEFAULT 0,
    bus_state TEXT,
    bitrate INTEGER,
    previous_rx_error INTEGER,
    previous_tx_error INTEGER,
    previous_tx_retries INTEGER,
    delta_rx_error INTEGER,
    delta_tx_error INTEGER,
    delta_tx_retries INTEGER,
    alert_level TEXT NOT NULL DEFAULT 'ok',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_can_bus_records_printer_recorded
ON can_bus_records(printer_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_can_bus_records_lookup
ON can_bus_records(printer_id, interface_name, recorded_at);
