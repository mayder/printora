CREATE TABLE IF NOT EXISTS slicing_profile_bundles (
    id BIGSERIAL PRIMARY KEY,
    owner_user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    engine TEXT NOT NULL DEFAULT 'orcaslicer',
    engine_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    source_format TEXT NOT NULL DEFAULT 'orca-native',
    compatibility_json TEXT NOT NULL DEFAULT '{}',
    current_revision_id BIGINT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS slicing_profile_revisions (
    id BIGSERIAL PRIMARY KEY,
    bundle_id BIGINT NOT NULL REFERENCES slicing_profile_bundles(id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL,
    parent_revision_id BIGINT REFERENCES slicing_profile_revisions(id) ON DELETE RESTRICT,
    native_bundle_json JSONB NOT NULL,
    canonical_json JSONB NOT NULL,
    sha256 TEXT NOT NULL,
    overrides_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    loss_report_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by_user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bundle_id, revision_number),
    UNIQUE(bundle_id, sha256)
);

CREATE INDEX IF NOT EXISTS idx_slicing_profile_bundles_owner
ON slicing_profile_bundles(owner_user_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_slicing_profile_revisions_bundle
ON slicing_profile_revisions(bundle_id, revision_number DESC);

ALTER TABLE slicing_jobs ADD COLUMN IF NOT EXISTS slicing_profile_revision_id BIGINT REFERENCES slicing_profile_revisions(id) ON DELETE RESTRICT;
ALTER TABLE slicing_jobs ADD COLUMN IF NOT EXISTS slicing_profile_sha256 TEXT;
ALTER TABLE slicing_jobs ADD COLUMN IF NOT EXISTS slicing_profile_engine_version TEXT;

CREATE INDEX IF NOT EXISTS idx_slicing_jobs_profile_revision
ON slicing_jobs(slicing_profile_revision_id, created_at DESC);
