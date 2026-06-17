ALTER TABLE social_library_items ADD COLUMN content_class TEXT NOT NULL DEFAULT 'community'
    CHECK(content_class IN ('community', 'curated', 'premium', 'sponsored'));

ALTER TABLE social_library_items ADD COLUMN commercial_status TEXT NOT NULL DEFAULT 'none'
    CHECK(commercial_status IN ('none', 'pending_review', 'approved', 'rejected'));

ALTER TABLE social_library_items ADD COLUMN commercial_metadata_json TEXT NOT NULL DEFAULT '{}';

ALTER TABLE social_library_items ADD COLUMN promotion_disclosure TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS social_library_commercial_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES social_library_items(id) ON DELETE CASCADE,
    reviewer_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK(status IN ('pending_review', 'approved', 'rejected')),
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_social_library_commercial_reviews_item
ON social_library_commercial_reviews(item_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_library_items_content_class
ON social_library_items(content_class, commercial_status, visibility, status);
