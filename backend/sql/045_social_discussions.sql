ALTER TABLE social_feed_items ADD COLUMN attachments_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE social_feed_items ADD COLUMN solution_comment_id INTEGER;
ALTER TABLE social_feed_items ADD COLUMN edit_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE social_feed_items ADD COLUMN deleted_at TEXT;

CREATE TABLE IF NOT EXISTS social_discussion_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id INTEGER NOT NULL REFERENCES social_feed_items(id) ON DELETE CASCADE,
    author_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    parent_comment_id INTEGER REFERENCES social_discussion_comments(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    attachments_json TEXT NOT NULL DEFAULT '[]',
    edit_count INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_discussion_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL CHECK(target_type IN ('post', 'comment')),
    target_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    reaction_type TEXT NOT NULL CHECK(reaction_type IN ('like', 'useful', 'thanks')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(target_type, target_id, user_id, reaction_type)
);

CREATE TABLE IF NOT EXISTS social_discussion_edit_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL CHECK(target_type IN ('post', 'comment')),
    target_id INTEGER NOT NULL,
    actor_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK(action IN ('created', 'updated', 'deleted', 'solution_marked', 'solution_cleared')),
    previous_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_comments_feed ON social_discussion_comments(feed_item_id, parent_comment_id, deleted_at, created_at);
CREATE INDEX IF NOT EXISTS idx_social_reactions_target ON social_discussion_reactions(target_type, target_id, reaction_type);
CREATE INDEX IF NOT EXISTS idx_social_edit_history_target ON social_discussion_edit_history(target_type, target_id, created_at);
