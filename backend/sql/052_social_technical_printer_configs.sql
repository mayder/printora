CREATE TABLE IF NOT EXISTS social_technical_printer_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    printer_id INTEGER REFERENCES printers(id) ON DELETE SET NULL,
    catalog_variant_id INTEGER REFERENCES catalog_printer_variants(id) ON DELETE SET NULL,
    community_id INTEGER REFERENCES social_communities(id) ON DELETE SET NULL,
    linked_library_item_id INTEGER REFERENCES social_library_items(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    visibility TEXT NOT NULL CHECK(visibility IN ('private', 'community', 'public')),
    mods_json TEXT NOT NULL DEFAULT '[]',
    components_json TEXT NOT NULL DEFAULT '{}',
    calibrations_json TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_technical_configs_owner
ON social_technical_printer_configs(owner_user_id, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_social_technical_configs_community
ON social_technical_printer_configs(community_id, visibility, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_social_technical_configs_variant
ON social_technical_printer_configs(catalog_variant_id, visibility, status, updated_at);
