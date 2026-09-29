CREATE TABLE IF NOT EXISTS social_feed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    community_id INTEGER NOT NULL REFERENCES social_communities(id) ON DELETE CASCADE,
    author_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    content_type TEXT NOT NULL CHECK(content_type IN ('technical_post', 'question', 'mod', 'print_result', 'file_announcement', 'curation_notice')),
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    component TEXT,
    material TEXT,
    firmware_family TEXT,
    problem_tag TEXT,
    pinned INTEGER NOT NULL DEFAULT 0,
    visibility TEXT NOT NULL DEFAULT 'public' CHECK(visibility IN ('public', 'private')),
    source_type TEXT NOT NULL DEFAULT 'community',
    source_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_social_feed_items_community_public ON social_feed_items(community_id, visibility, pinned, created_at);
CREATE INDEX IF NOT EXISTS idx_social_feed_items_type ON social_feed_items(content_type);
CREATE INDEX IF NOT EXISTS idx_social_feed_items_filters ON social_feed_items(component, material, firmware_family, problem_tag);
