ALTER TABLE print_project_files ADD COLUMN quarantine_key TEXT;
ALTER TABLE print_project_files ADD COLUMN uploaded_size_bytes INTEGER;
ALTER TABLE print_project_files ADD COLUMN uploaded_at TEXT;
ALTER TABLE print_project_files ADD COLUMN rejection_reason TEXT;
ALTER TABLE print_project_files ADD COLUMN is_primary_preview INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_print_project_files_checksum
ON print_project_files(sha256, validation_status);

CREATE INDEX IF NOT EXISTS idx_print_project_files_storage
ON print_project_files(project_id, quarantine_key, uploaded_at);
