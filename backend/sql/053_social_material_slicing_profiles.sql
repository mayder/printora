CREATE TABLE IF NOT EXISTS social_material_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    printer_id INTEGER REFERENCES printers(id) ON DELETE SET NULL,
    catalog_variant_id INTEGER REFERENCES catalog_printer_variants(id) ON DELETE SET NULL,
    community_id INTEGER REFERENCES social_communities(id) ON DELETE SET NULL,
    linked_library_item_id INTEGER REFERENCES social_library_items(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    visibility TEXT NOT NULL CHECK(visibility IN ('private', 'community', 'public')),
    material_brand TEXT NOT NULL DEFAULT '',
    material_type TEXT NOT NULL,
    nozzle_diameter_mm REAL,
    bed_temperature_c INTEGER,
    nozzle_temperature_c INTEGER,
    flow_percent REAL,
    notes TEXT NOT NULL DEFAULT '',
    version_label TEXT NOT NULL DEFAULT 'v1',
    compatibility_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_slicing_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_profile_id INTEGER NOT NULL UNIQUE REFERENCES social_material_profiles(id) ON DELETE CASCADE,
    layer_height_mm REAL,
    speed_mm_s INTEGER,
    infill_percent INTEGER,
    supports_enabled INTEGER NOT NULL DEFAULT 0,
    goal TEXT NOT NULL DEFAULT 'quality' CHECK(goal IN ('quality', 'strength', 'speed', 'prototype')),
    settings_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_material_profiles_owner
ON social_material_profiles(owner_user_id, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_social_material_profiles_community
ON social_material_profiles(community_id, visibility, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_social_material_profiles_variant
ON social_material_profiles(catalog_variant_id, material_type, nozzle_diameter_mm, status);
