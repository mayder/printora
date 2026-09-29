ALTER TABLE slicing_jobs ADD COLUMN gcode_approved_at TEXT;
ALTER TABLE slicing_jobs ADD COLUMN gcode_approved_checksum TEXT;
ALTER TABLE slicing_jobs ADD COLUMN reprint_of_job_id INTEGER REFERENCES slicing_jobs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_reprint_source
ON slicing_jobs(reprint_of_job_id, created_at DESC);
