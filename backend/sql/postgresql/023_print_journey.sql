ALTER TABLE slicing_jobs ADD COLUMN IF NOT EXISTS gcode_approved_at TIMESTAMPTZ;
ALTER TABLE slicing_jobs ADD COLUMN IF NOT EXISTS gcode_approved_checksum TEXT;
ALTER TABLE slicing_jobs ADD COLUMN IF NOT EXISTS reprint_of_job_id BIGINT REFERENCES slicing_jobs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_reprint_source
ON slicing_jobs(reprint_of_job_id, created_at DESC);
