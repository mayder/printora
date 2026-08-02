CREATE TABLE IF NOT EXISTS photo_capture_sessions (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES print_projects(id),
    owner_user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'review', 'ready', 'cancelled', 'expired')),
    target_photo_count INTEGER NOT NULL DEFAULT 24 CHECK(target_photo_count BETWEEN 12 AND 80),
    scale_method TEXT NOT NULL DEFAULT 'none' CHECK(scale_method IN ('none', 'known_measurement', 'marker')),
    scale_value_mm DOUBLE PRECISION,
    scale_uncertainty_mm DOUBLE PRECISION,
    scale_confirmed_at TIMESTAMPTZ,
    consent_confirmed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS photo_capture_photos (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES photo_capture_sessions(id),
    owner_user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    capture_index INTEGER NOT NULL CHECK(capture_index BETWEEN 1 AND 80),
    height_band TEXT NOT NULL CHECK(height_band IN ('low', 'middle', 'high')),
    file_name TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    quality_status TEXT NOT NULL CHECK(quality_status IN ('accepted', 'needs_review')),
    quality_json TEXT NOT NULL DEFAULT '{}',
    upload_idempotency_key TEXT,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    replaced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_photo_capture_slot ON photo_capture_photos(session_id, capture_index) WHERE is_current = TRUE;
CREATE UNIQUE INDEX IF NOT EXISTS idx_photo_capture_checksum ON photo_capture_photos(session_id, sha256);
CREATE UNIQUE INDEX IF NOT EXISTS idx_photo_capture_idempotency ON photo_capture_photos(session_id, upload_idempotency_key)
WHERE upload_idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_photo_capture_owner ON photo_capture_sessions(owner_user_id, updated_at DESC);
