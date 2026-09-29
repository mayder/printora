CREATE TABLE IF NOT EXISTS social_moderation_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('post', 'comment', 'profile', 'library_item', 'catalog_variant', 'community', 'tag')),
    entity_id INTEGER NOT NULL,
    reporter_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    reason TEXT NOT NULL CHECK(reason IN ('spam', 'unsafe', 'illegal', 'harassment', 'privacy', 'wrong_metadata', 'other')),
    detail TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'reviewing', 'resolved', 'dismissed')),
    assigned_moderator_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    resolution_note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    UNIQUE(entity_type, entity_id, reporter_user_id, reason)
);

CREATE INDEX IF NOT EXISTS idx_social_moderation_reports_queue
ON social_moderation_reports(status, created_at);

CREATE INDEX IF NOT EXISTS idx_social_moderation_reports_entity
ON social_moderation_reports(entity_type, entity_id, status);

CREATE TABLE IF NOT EXISTS social_moderation_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER REFERENCES social_moderation_reports(id) ON DELETE SET NULL,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('post', 'comment', 'profile', 'library_item', 'catalog_variant', 'community', 'tag')),
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('mark_reviewing', 'hide', 'remove', 'block', 'restore', 'dismiss', 'curate')),
    previous_state_json TEXT NOT NULL DEFAULT '{}',
    new_state_json TEXT NOT NULL DEFAULT '{}',
    moderator_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_moderation_actions_entity
ON social_moderation_actions(entity_type, entity_id, created_at);

