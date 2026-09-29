ALTER TABLE social_library_items ADD COLUMN original_author_name TEXT;
ALTER TABLE social_library_items ADD COLUMN source_url TEXT;
ALTER TABLE social_library_items ADD COLUMN attribution_text TEXT;
ALTER TABLE social_library_items ADD COLUMN remix_source_item_id INTEGER REFERENCES social_library_items(id) ON DELETE SET NULL;
ALTER TABLE social_library_items ADD COLUMN publication_terms_accepted_at TEXT;

CREATE INDEX IF NOT EXISTS idx_social_library_items_remix_source ON social_library_items(remix_source_item_id);
