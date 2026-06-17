CREATE TABLE IF NOT EXISTS external_content_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    license_policy TEXT NOT NULL DEFAULT '',
    attribution_required INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paused', 'blocked')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_user_id, base_url)
);

CREATE TABLE IF NOT EXISTS external_library_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    source_id INTEGER REFERENCES external_content_sources(id) ON DELETE SET NULL,
    library_item_id INTEGER REFERENCES social_library_items(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    external_url TEXT NOT NULL,
    author_name TEXT NOT NULL DEFAULT '',
    license TEXT NOT NULL DEFAULT '',
    attribution_text TEXT NOT NULL DEFAULT '',
    checksum_sha256 TEXT,
    import_mode TEXT NOT NULL CHECK(import_mode IN ('bookmark', 'metadata_only')),
    duplicate_library_file_id INTEGER REFERENCES social_library_files(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_user_id, external_url)
);

CREATE INDEX IF NOT EXISTS idx_external_library_references_owner_created
ON external_library_references(owner_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_external_library_references_checksum
ON external_library_references(checksum_sha256);
