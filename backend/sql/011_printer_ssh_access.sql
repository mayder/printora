CREATE TABLE IF NOT EXISTS printer_ssh_access (
    printer_id INTEGER PRIMARY KEY,
    ssh_host TEXT,
    ssh_port INTEGER NOT NULL DEFAULT 22,
    ssh_username TEXT,
    credential_blob TEXT,
    credential_configured INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    CHECK(ssh_port > 0 AND ssh_port <= 65535)
);
