CREATE TABLE IF NOT EXISTS public.cloud_objects (
    id BIGSERIAL PRIMARY KEY,
    bucket_name TEXT NOT NULL,
    object_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'quarantined',
    version_id TEXT,
    etag TEXT,
    owner_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bucket_name, object_key),
    CHECK(length(sha256) = 64),
    CHECK(size_bytes >= 0),
    CHECK(state IN ('quarantined', 'rejected', 'analyzed', 'promoted', 'missing', 'corrupt'))
);

CREATE INDEX IF NOT EXISTS idx_cloud_objects_owner_state
ON public.cloud_objects(owner_user_id, state, updated_at);

CREATE INDEX IF NOT EXISTS idx_cloud_objects_checksum
ON public.cloud_objects(sha256, size_bytes);

CREATE TABLE IF NOT EXISTS public.cloud_object_references (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT NOT NULL REFERENCES public.cloud_objects(id) ON DELETE RESTRICT,
    reference_type TEXT NOT NULL,
    reference_id BIGINT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reference_type, reference_id)
);

CREATE INDEX IF NOT EXISTS idx_cloud_object_references_object
ON public.cloud_object_references(object_id, reference_type);

CREATE TABLE IF NOT EXISTS public.cloud_object_upload_sessions (
    upload_id TEXT PRIMARY KEY,
    owner_user_id BIGINT NOT NULL,
    bucket_name TEXT NOT NULL,
    object_key TEXT NOT NULL,
    expected_size_bytes BIGINT NOT NULL,
    received_size_bytes BIGINT NOT NULL DEFAULT 0,
    expected_sha256 TEXT,
    state TEXT NOT NULL DEFAULT 'receiving',
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(expected_size_bytes > 0),
    CHECK(received_size_bytes >= 0),
    CHECK(state IN ('receiving', 'uploaded', 'validating', 'rejected', 'promoted', 'expired', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_cloud_object_upload_sessions_state
ON public.cloud_object_upload_sessions(state, expires_at);

CREATE TABLE IF NOT EXISTS public.cloud_object_reconciliation_runs (
    id BIGSERIAL PRIMARY KEY,
    mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    scanned_count BIGINT NOT NULL DEFAULT 0,
    missing_count BIGINT NOT NULL DEFAULT 0,
    corrupt_count BIGINT NOT NULL DEFAULT 0,
    orphan_count BIGINT NOT NULL DEFAULT 0,
    result_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    CHECK(mode IN ('manifest', 'incremental', 'restore', 'integrity')),
    CHECK(status IN ('running', 'passed', 'failed'))
);
