CREATE TABLE IF NOT EXISTS social_library_favorites (
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, item_id)
);

CREATE TABLE IF NOT EXISTS social_library_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    community_id INTEGER REFERENCES social_communities(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    visibility TEXT NOT NULL CHECK(visibility IN ('private', 'community', 'public')),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_library_collection_items (
    collection_id INTEGER NOT NULL REFERENCES social_library_collections(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    version_id INTEGER REFERENCES social_library_versions(id) ON DELETE SET NULL,
    added_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, item_id, version_id)
);

CREATE TABLE IF NOT EXISTS social_print_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    printer_id INTEGER REFERENCES printers(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_print_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    print_list_id INTEGER NOT NULL REFERENCES social_print_lists(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    version_id INTEGER NOT NULL REFERENCES social_library_versions(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'want_to_print' CHECK(status IN ('want_to_print', 'printed', 'problem')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(print_list_id, item_id, version_id)
);

CREATE INDEX IF NOT EXISTS idx_social_library_favorites_item
ON social_library_favorites(item_id, created_at);

CREATE INDEX IF NOT EXISTS idx_social_library_collections_owner
ON social_library_collections(owner_user_id, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_social_library_collections_community
ON social_library_collections(community_id, visibility, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_social_print_lists_owner
ON social_print_lists(owner_user_id, status, updated_at);
