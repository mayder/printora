CREATE TABLE IF NOT EXISTS material_spools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    material_profile_id INTEGER REFERENCES social_material_profiles(id) ON DELETE SET NULL,
    source TEXT NOT NULL DEFAULT 'local' CHECK(source IN ('local', 'spoolman')),
    external_id TEXT,
    name TEXT NOT NULL,
    material_type TEXT NOT NULL,
    brand TEXT NOT NULL DEFAULT '',
    color_name TEXT NOT NULL DEFAULT '',
    color_hex TEXT,
    lot_code TEXT NOT NULL DEFAULT '',
    initial_weight_g REAL CHECK(initial_weight_g IS NULL OR initial_weight_g >= 0),
    remaining_weight_g REAL CHECK(remaining_weight_g IS NULL OR remaining_weight_g >= 0),
    location TEXT NOT NULL DEFAULT '',
    storage_state TEXT NOT NULL DEFAULT 'unknown'
        CHECK(storage_state IN ('unknown', 'sealed', 'open', 'drying', 'dry')),
    opened_at TEXT,
    dried_at TEXT,
    expires_at TEXT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    last_synced_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(initial_weight_g IS NULL OR remaining_weight_g IS NULL OR remaining_weight_g <= initial_weight_g),
    UNIQUE(owner_user_id, source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_material_spools_owner_status
ON material_spools(owner_user_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_material_spools_profile
ON material_spools(material_profile_id, status);

CREATE TABLE IF NOT EXISTS material_consumptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    spool_id INTEGER NOT NULL REFERENCES material_spools(id) ON DELETE RESTRICT,
    slicing_job_id INTEGER REFERENCES slicing_jobs(id) ON DELETE SET NULL,
    print_history_id INTEGER REFERENCES print_job_history(id) ON DELETE SET NULL,
    idempotency_key TEXT NOT NULL,
    predicted_weight_g REAL CHECK(predicted_weight_g IS NULL OR predicted_weight_g >= 0),
    actual_weight_g REAL CHECK(actual_weight_g IS NULL OR actual_weight_g >= 0),
    status TEXT NOT NULL CHECK(status IN ('planned', 'confirmed', 'released')),
    remaining_weight_after_g REAL CHECK(remaining_weight_after_g IS NULL OR remaining_weight_after_g >= 0),
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TEXT,
    released_at TEXT,
    UNIQUE(owner_user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_material_consumptions_spool_created
ON material_consumptions(spool_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_material_consumptions_job
ON material_consumptions(slicing_job_id, print_history_id);

CREATE TABLE IF NOT EXISTS material_quality_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    spool_id INTEGER NOT NULL REFERENCES material_spools(id) ON DELETE RESTRICT,
    print_history_id INTEGER REFERENCES print_job_history(id) ON DELETE SET NULL,
    sample_type TEXT NOT NULL CHECK(sample_type IN ('dimensional', 'calibration')),
    metric_name TEXT NOT NULL,
    nominal_value_mm REAL NOT NULL CHECK(nominal_value_mm >= 0),
    measured_value_mm REAL NOT NULL CHECK(measured_value_mm >= 0),
    tolerance_mm REAL NOT NULL CHECK(tolerance_mm >= 0),
    result TEXT NOT NULL CHECK(result IN ('passed', 'failed')),
    photo_object_id INTEGER REFERENCES cloud_objects(id) ON DELETE SET NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_material_quality_spool_created
ON material_quality_samples(spool_id, created_at DESC);

CREATE TRIGGER IF NOT EXISTS material_consumptions_no_update
BEFORE UPDATE ON material_consumptions
BEGIN SELECT RAISE(ABORT, 'material consumption is immutable'); END;

CREATE TRIGGER IF NOT EXISTS material_consumptions_no_delete
BEFORE DELETE ON material_consumptions
BEGIN SELECT RAISE(ABORT, 'material consumption cannot be deleted'); END;

CREATE TRIGGER IF NOT EXISTS material_quality_no_update
BEFORE UPDATE ON material_quality_samples
BEGIN SELECT RAISE(ABORT, 'material quality sample is immutable'); END;

CREATE TRIGGER IF NOT EXISTS material_quality_no_delete
BEFORE DELETE ON material_quality_samples
BEGIN SELECT RAISE(ABORT, 'material quality sample cannot be deleted'); END;
