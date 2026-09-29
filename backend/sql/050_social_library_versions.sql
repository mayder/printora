CREATE TABLE IF NOT EXISTS social_library_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    changelog TEXT NOT NULL DEFAULT '',
    files_snapshot_json TEXT NOT NULL DEFAULT '[]',
    metadata_snapshot_json TEXT NOT NULL DEFAULT '{}',
    created_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    is_current INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE social_library_downloads ADD COLUMN version_id INTEGER REFERENCES social_library_versions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_social_library_versions_item_current
ON social_library_versions(item_id, is_current, created_at);

CREATE INDEX IF NOT EXISTS idx_social_library_downloads_version
ON social_library_downloads(version_id, created_at);
