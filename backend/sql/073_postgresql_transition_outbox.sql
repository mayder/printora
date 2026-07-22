CREATE TABLE IF NOT EXISTS postgresql_transition_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('insert', 'update', 'delete')),
    primary_key_json TEXT NOT NULL,
    row_json TEXT,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_postgresql_transition_outbox_table_id
    ON postgresql_transition_outbox (table_name, id);

