CREATE TABLE IF NOT EXISTS social_user_safety_settings (
    user_id INTEGER PRIMARY KEY REFERENCES auth_users(id) ON DELETE CASCADE,
    profile_discoverable INTEGER NOT NULL DEFAULT 1 CHECK(profile_discoverable IN (0, 1)),
    followers_visibility TEXT NOT NULL DEFAULT 'public' CHECK(followers_visibility IN ('public', 'followers', 'friends', 'private')),
    messages_from TEXT NOT NULL DEFAULT 'friends' CHECK(messages_from IN ('public', 'followers', 'friends', 'none')),
    allow_content_mentions INTEGER NOT NULL DEFAULT 1 CHECK(allow_content_mentions IN (0, 1)),
    allow_download_tracking INTEGER NOT NULL DEFAULT 1 CHECK(allow_download_tracking IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_rate_limit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    subject_hash TEXT NOT NULL,
    allowed INTEGER NOT NULL CHECK(allowed IN (0, 1)),
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_rate_limit_events_actor_action
ON social_rate_limit_events(actor_user_id, action, created_at);

CREATE INDEX IF NOT EXISTS idx_social_rate_limit_events_subject_action
ON social_rate_limit_events(subject_hash, action, created_at);

CREATE TABLE IF NOT EXISTS social_abuse_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    target_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    severity INTEGER NOT NULL DEFAULT 1 CHECK(severity BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'reviewing', 'resolved', 'dismissed')),
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_social_abuse_signals_status
ON social_abuse_signals(status, severity, created_at);

CREATE INDEX IF NOT EXISTS idx_social_abuse_signals_subject
ON social_abuse_signals(subject_user_id, action, status);
