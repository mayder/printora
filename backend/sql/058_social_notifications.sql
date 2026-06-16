CREATE TABLE IF NOT EXISTS social_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    actor_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    notification_type TEXT NOT NULL CHECK(notification_type IN ('comment', 'reaction', 'solution', 'follow', 'friend_request', 'friend_accept', 'content_update', 'community_post', 'digest')),
    entity_type TEXT NOT NULL CHECK(entity_type IN ('post', 'comment', 'profile', 'library_item', 'catalog_variant', 'community', 'collection', 'relationship')),
    entity_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    action_url TEXT,
    status TEXT NOT NULL DEFAULT 'unread' CHECK(status IN ('unread', 'read', 'archived')),
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_social_notifications_recipient
ON social_notifications(recipient_user_id, status, created_at);

CREATE INDEX IF NOT EXISTS idx_social_notifications_entity
ON social_notifications(entity_type, entity_id, created_at);

CREATE TABLE IF NOT EXISTS social_notification_preferences (
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL CHECK(notification_type IN ('comment', 'reaction', 'solution', 'follow', 'friend_request', 'friend_accept', 'content_update', 'community_post', 'digest')),
    in_app_enabled INTEGER NOT NULL DEFAULT 1 CHECK(in_app_enabled IN (0, 1)),
    digest_enabled INTEGER NOT NULL DEFAULT 0 CHECK(digest_enabled IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, notification_type)
);

CREATE TABLE IF NOT EXISTS social_content_follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('post', 'library_item', 'catalog_variant', 'community', 'collection')),
    entity_id INTEGER NOT NULL,
    muted INTEGER NOT NULL DEFAULT 0 CHECK(muted IN (0, 1)),
    digest_enabled INTEGER NOT NULL DEFAULT 0 CHECK(digest_enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_social_content_follows_entity
ON social_content_follows(entity_type, entity_id, muted);
