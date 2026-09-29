CREATE TABLE IF NOT EXISTS social_materialization_state (
    name TEXT PRIMARY KEY,
    source_signature TEXT NOT NULL,
    refreshed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

