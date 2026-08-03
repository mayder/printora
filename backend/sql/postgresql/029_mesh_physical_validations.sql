CREATE TABLE IF NOT EXISTS public.mesh_physical_validations (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES public.mesh_revision_reviews(id),
    history_id BIGINT NOT NULL REFERENCES public.print_job_history(id),
    owner_user_id BIGINT NOT NULL REFERENCES public.auth_users(id),
    outcome TEXT NOT NULL CHECK(outcome IN ('passed', 'needs_adjustment', 'failed')),
    instrument_label TEXT NOT NULL,
    expected_x_mm DOUBLE PRECISION,
    expected_y_mm DOUBLE PRECISION,
    expected_z_mm DOUBLE PRECISION,
    measured_x_mm DOUBLE PRECISION,
    measured_y_mm DOUBLE PRECISION,
    measured_z_mm DOUBLE PRECISION,
    error_x_percent DOUBLE PRECISION,
    error_y_percent DOUBLE PRECISION,
    error_z_percent DOUBLE PRECISION,
    max_error_percent DOUBLE PRECISION NOT NULL,
    printer_snapshot_json TEXT NOT NULL DEFAULT '{}',
    material_snapshot_json TEXT NOT NULL DEFAULT '{}',
    profile_snapshot_json TEXT NOT NULL DEFAULT '{}',
    revision_sha256 TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(history_id),
    UNIQUE(owner_user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_mesh_physical_validations_review
ON public.mesh_physical_validations(review_id, created_at DESC, id DESC);
