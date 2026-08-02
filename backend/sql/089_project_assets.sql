ALTER TABLE print_project_files ADD COLUMN piece_name TEXT NOT NULL DEFAULT '';
ALTER TABLE print_project_files ADD COLUMN variant_name TEXT NOT NULL DEFAULT '';
ALTER TABLE print_project_files ADD COLUMN assembly_name TEXT NOT NULL DEFAULT '';
ALTER TABLE print_project_files ADD COLUMN display_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE print_project_files ADD COLUMN unit TEXT NOT NULL DEFAULT 'mm' CHECK(unit IN ('mm', 'cm', 'in'));
ALTER TABLE print_project_files ADD COLUMN inspection_status TEXT NOT NULL DEFAULT 'pending'
    CHECK(inspection_status IN ('pending', 'ready', 'limited', 'failed', 'not_applicable'));
ALTER TABLE print_project_files ADD COLUMN inspection_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE print_project_files ADD COLUMN upload_idempotency_key TEXT;

ALTER TABLE print_project_versions ADD COLUMN manifest_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE print_project_versions ADD COLUMN manifest_sha256 TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_print_project_files_upload_idempotency
ON print_project_files(project_id, upload_idempotency_key)
WHERE upload_idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_print_project_files_structure
ON print_project_files(project_id, assembly_name, variant_name, display_order, id);

CREATE INDEX IF NOT EXISTS idx_print_project_versions_manifest
ON print_project_versions(project_id, manifest_sha256);
