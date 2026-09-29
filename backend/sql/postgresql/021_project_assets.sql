ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS piece_name TEXT NOT NULL DEFAULT '';
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS variant_name TEXT NOT NULL DEFAULT '';
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS assembly_name TEXT NOT NULL DEFAULT '';
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS display_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS unit TEXT NOT NULL DEFAULT 'mm';
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS inspection_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS inspection_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE print_project_files ADD COLUMN IF NOT EXISTS upload_idempotency_key TEXT;

ALTER TABLE print_project_versions ADD COLUMN IF NOT EXISTS manifest_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE print_project_versions ADD COLUMN IF NOT EXISTS manifest_sha256 TEXT;

DO $$ BEGIN
    ALTER TABLE print_project_files ADD CONSTRAINT chk_print_project_file_unit CHECK (unit IN ('mm', 'cm', 'in'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE print_project_files ADD CONSTRAINT chk_print_project_file_inspection_status
        CHECK (inspection_status IN ('pending', 'ready', 'limited', 'failed', 'not_applicable'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_print_project_files_upload_idempotency
ON print_project_files(project_id, upload_idempotency_key)
WHERE upload_idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_print_project_files_structure
ON print_project_files(project_id, assembly_name, variant_name, display_order, id);

CREATE INDEX IF NOT EXISTS idx_print_project_versions_manifest
ON print_project_versions(project_id, manifest_sha256);
