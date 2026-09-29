ALTER TABLE slicing_jobs ADD COLUMN print_project_id INTEGER REFERENCES print_projects(id) ON DELETE SET NULL;
ALTER TABLE slicing_jobs ADD COLUMN print_project_version_id INTEGER REFERENCES print_project_versions(id) ON DELETE SET NULL;
ALTER TABLE slicing_jobs ADD COLUMN selected_project_files_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE slicing_jobs ADD COLUMN project_snapshot_json TEXT NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_print_project
ON slicing_jobs(print_project_id, owner_user_id, created_at);
