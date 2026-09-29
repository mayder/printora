CREATE TABLE IF NOT EXISTS social_quality_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('post', 'library_item', 'technical_config', 'material_profile', 'catalog_variant', 'community', 'profile')),
    entity_id INTEGER NOT NULL,
    signal_type TEXT NOT NULL CHECK(signal_type IN ('download', 'favorite', 'solution', 'reaction', 'curation', 'report', 'print_success')),
    actor_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    target_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    source_table TEXT NOT NULL,
    source_id TEXT NOT NULL,
    weight INTEGER NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(signal_type, source_table, source_id)
);

CREATE INDEX IF NOT EXISTS idx_social_quality_signals_entity
ON social_quality_signals(entity_type, entity_id, signal_type);

CREATE INDEX IF NOT EXISTS idx_social_quality_signals_target
ON social_quality_signals(target_user_id, signal_type, created_at);

CREATE TABLE IF NOT EXISTS social_user_reputation_snapshots (
    user_id INTEGER PRIMARY KEY REFERENCES auth_users(id) ON DELETE CASCADE,
    contribution_count INTEGER NOT NULL DEFAULT 0,
    reputation_score INTEGER NOT NULL DEFAULT 0,
    breakdown_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_user_reputation_score
ON social_user_reputation_snapshots(reputation_score DESC, contribution_count DESC);
