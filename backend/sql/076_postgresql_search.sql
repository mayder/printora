CREATE TABLE IF NOT EXISTS search_documents (
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    tags_json TEXT NOT NULL DEFAULT '[]',
    community_id INTEGER,
    catalog_variant_id INTEGER,
    owner_user_id INTEGER,
    visibility TEXT NOT NULL DEFAULT 'public',
    popularity_score INTEGER NOT NULL DEFAULT 0,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    PRIMARY KEY(entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_search_documents_filters
ON search_documents(is_active, entity_type, visibility, source_updated_at);
