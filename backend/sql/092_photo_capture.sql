CREATE TABLE photo_capture_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES print_projects(id),
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'review', 'ready', 'cancelled', 'expired')),
    target_photo_count INTEGER NOT NULL DEFAULT 24 CHECK(target_photo_count BETWEEN 12 AND 80),
    scale_method TEXT NOT NULL DEFAULT 'none' CHECK(scale_method IN ('none', 'known_measurement', 'marker')),
    scale_value_mm REAL,
    scale_uncertainty_mm REAL,
    scale_confirmed_at TEXT,
    consent_confirmed_at TEXT,
    completed_at TEXT,
    expires_at TEXT NOT NULL DEFAULT (datetime('now', '+30 days')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE photo_capture_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES photo_capture_sessions(id),
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    capture_index INTEGER NOT NULL CHECK(capture_index BETWEEN 1 AND 80),
    height_band TEXT NOT NULL CHECK(height_band IN ('low', 'middle', 'high')),
    file_name TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    quality_status TEXT NOT NULL CHECK(quality_status IN ('accepted', 'needs_review')),
    quality_json TEXT NOT NULL DEFAULT '{}',
    upload_idempotency_key TEXT,
    is_current INTEGER NOT NULL DEFAULT 1 CHECK(is_current IN (0, 1)),
    replaced_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_photo_capture_slot ON photo_capture_photos(session_id, capture_index) WHERE is_current = 1;
CREATE UNIQUE INDEX idx_photo_capture_checksum ON photo_capture_photos(session_id, sha256);
CREATE UNIQUE INDEX idx_photo_capture_idempotency ON photo_capture_photos(session_id, upload_idempotency_key)
WHERE upload_idempotency_key IS NOT NULL;
CREATE INDEX idx_photo_capture_owner ON photo_capture_sessions(owner_user_id, updated_at DESC);
