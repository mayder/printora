ALTER TABLE social_library_files ADD COLUMN storage_key TEXT;
ALTER TABLE social_library_files ADD COLUMN quarantine_key TEXT;
ALTER TABLE social_library_files ADD COLUMN uploaded_size_bytes INTEGER;
ALTER TABLE social_library_files ADD COLUMN uploaded_at TEXT;
ALTER TABLE social_library_files ADD COLUMN rejection_reason TEXT;
ALTER TABLE social_library_files ADD COLUMN deduplicated_from_file_id INTEGER REFERENCES social_library_files(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_social_library_files_sha256 ON social_library_files(sha256);
CREATE INDEX IF NOT EXISTS idx_social_library_files_status ON social_library_files(validation_status, uploaded_at);
