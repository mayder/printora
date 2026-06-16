ALTER TABLE social_library_files ADD COLUMN analysis_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE social_library_files ADD COLUMN thumbnail_svg TEXT;
ALTER TABLE social_library_files ADD COLUMN analyzed_at TEXT;

CREATE INDEX IF NOT EXISTS idx_social_library_files_analyzed ON social_library_files(analyzed_at, validation_status);
