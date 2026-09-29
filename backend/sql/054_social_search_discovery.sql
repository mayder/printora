CREATE TABLE IF NOT EXISTS social_content_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    label TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'curated', 'blocked')),
    source TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug)
);

CREATE TABLE IF NOT EXISTS social_content_tag_links (
    tag_id INTEGER NOT NULL REFERENCES social_content_tags(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('community', 'post', 'library_item', 'technical_config', 'material_profile', 'catalog_variant')),
    entity_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tag_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS social_search_index (
    entity_type TEXT NOT NULL CHECK(entity_type IN ('community', 'post', 'library_item', 'technical_config', 'material_profile', 'catalog_variant')),
    entity_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    tags_json TEXT NOT NULL DEFAULT '[]',
    community_id INTEGER REFERENCES social_communities(id) ON DELETE SET NULL,
    catalog_variant_id INTEGER REFERENCES catalog_printer_variants(id) ON DELETE SET NULL,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    visibility TEXT NOT NULL DEFAULT 'public',
    popularity_score INTEGER NOT NULL DEFAULT 0,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_social_search_index_type
ON social_search_index(entity_type, visibility, source_updated_at);

CREATE INDEX IF NOT EXISTS idx_social_search_index_community
ON social_search_index(community_id, visibility, source_updated_at);

CREATE INDEX IF NOT EXISTS idx_social_search_index_variant
ON social_search_index(catalog_variant_id, visibility, source_updated_at);

CREATE INDEX IF NOT EXISTS idx_social_tag_links_entity
ON social_content_tag_links(entity_type, entity_id);
