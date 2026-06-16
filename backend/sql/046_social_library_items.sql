CREATE TABLE IF NOT EXISTS social_library_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    community_id INTEGER REFERENCES social_communities(id) ON DELETE SET NULL,
    catalog_variant_id INTEGER REFERENCES catalog_printer_variants(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    visibility TEXT NOT NULL CHECK(visibility IN ('private', 'friends', 'community', 'public')),
    component TEXT,
    version_label TEXT NOT NULL DEFAULT 'v1',
    material_suggestion TEXT,
    supports_required INTEGER NOT NULL DEFAULT 0,
    orientation_notes TEXT,
    license TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_library_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    file_kind TEXT NOT NULL CHECK(file_kind IN ('stl', '3mf', 'bundle')),
    file_name TEXT NOT NULL,
    original_url TEXT,
    size_bytes INTEGER,
    sha256 TEXT,
    validation_status TEXT NOT NULL DEFAULT 'metadata_only',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_library_downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    anonymous_label TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_library_items_owner ON social_library_items(owner_user_id, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_social_library_items_community ON social_library_items(community_id, visibility, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_social_library_items_variant ON social_library_items(catalog_variant_id, status);
CREATE INDEX IF NOT EXISTS idx_social_library_downloads_item ON social_library_downloads(item_id, created_at);
