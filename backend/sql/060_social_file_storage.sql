CREATE TABLE IF NOT EXISTS social_file_storage_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_type TEXT NOT NULL CHECK(scope_type IN ('global', 'user', 'organization')),
    scope_id INTEGER,
    quota_bytes INTEGER NOT NULL CHECK(quota_bytes > 0),
    retention_days INTEGER NOT NULL CHECK(retention_days >= 0),
    cost_per_gb_month_cents INTEGER NOT NULL DEFAULT 0 CHECK(cost_per_gb_month_cents >= 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    updated_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scope_type, scope_id)
);

CREATE TABLE IF NOT EXISTS social_file_retention_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    requested_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    mode TEXT NOT NULL DEFAULT 'dry_run' CHECK(mode IN ('dry_run')),
    candidate_count INTEGER NOT NULL DEFAULT 0 CHECK(candidate_count >= 0),
    blocked_count INTEGER NOT NULL DEFAULT 0 CHECK(blocked_count >= 0),
    reclaimable_bytes INTEGER NOT NULL DEFAULT 0 CHECK(reclaimable_bytes >= 0),
    result_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO social_file_storage_policies (
    scope_type, scope_id, quota_bytes, retention_days, cost_per_gb_month_cents
)
VALUES ('global', NULL, 1073741824, 180, 8);

CREATE INDEX IF NOT EXISTS idx_social_file_storage_policies_scope
ON social_file_storage_policies(scope_type, scope_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_social_file_storage_policies_unique_scope
ON social_file_storage_policies(scope_type, COALESCE(scope_id, 0));

CREATE INDEX IF NOT EXISTS idx_social_file_retention_reviews_owner
ON social_file_retention_reviews(owner_user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_social_library_files_quarantine
ON social_library_files(quarantine_key);
