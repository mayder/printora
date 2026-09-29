CREATE TABLE IF NOT EXISTS cloud_object_download_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_sha256 TEXT NOT NULL UNIQUE,
    object_id INTEGER NOT NULL,
    issued_to_user_id INTEGER NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(object_id) REFERENCES cloud_objects(id) ON DELETE RESTRICT,
    CHECK(length(token_sha256) = 64),
    CHECK(status IN ('active', 'used', 'revoked', 'expired'))
);

CREATE INDEX IF NOT EXISTS idx_cloud_object_download_tokens_expiry
ON cloud_object_download_tokens(status, expires_at);
