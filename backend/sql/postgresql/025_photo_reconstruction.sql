CREATE TABLE IF NOT EXISTS public.photo_reconstruction_jobs (
    id BIGSERIAL PRIMARY KEY,
    capture_session_id BIGINT NOT NULL REFERENCES public.photo_capture_sessions(id),
    project_id BIGINT NOT NULL REFERENCES public.print_projects(id),
    owner_user_id BIGINT NOT NULL REFERENCES public.auth_users(id),
    durable_job_id BIGINT REFERENCES public.durable_jobs(id),
    active_attempt_id BIGINT,
    run_generation INTEGER NOT NULL DEFAULT 1,
    engine_policy TEXT NOT NULL DEFAULT 'auto',
    engine_key TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    stage TEXT NOT NULL DEFAULT 'waiting',
    progress_percent INTEGER,
    idempotency_key TEXT NOT NULL,
    correlation_id TEXT NOT NULL UNIQUE,
    error_code TEXT,
    error_message TEXT,
    estimated_cost_cents INTEGER,
    actual_cost_cents INTEGER,
    cancel_requested_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_user_id, idempotency_key),
    UNIQUE(capture_session_id)
);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_owner
ON public.photo_reconstruction_jobs(owner_user_id, updated_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_status
ON public.photo_reconstruction_jobs(status, stage, updated_at);

CREATE TABLE IF NOT EXISTS public.photo_reconstruction_attempts (
    id BIGSERIAL PRIMARY KEY,
    reconstruction_job_id BIGINT NOT NULL REFERENCES public.photo_reconstruction_jobs(id),
    attempt_number INTEGER NOT NULL,
    engine_key TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    stage TEXT NOT NULL DEFAULT 'preparing',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    error_code TEXT,
    error_message TEXT,
    estimated_cost_cents INTEGER,
    actual_cost_cents INTEGER,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    UNIQUE(reconstruction_job_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_attempts_job
ON public.photo_reconstruction_attempts(reconstruction_job_id, attempt_number DESC);

CREATE TABLE IF NOT EXISTS public.photo_reconstruction_artifacts (
    id BIGSERIAL PRIMARY KEY,
    reconstruction_job_id BIGINT NOT NULL REFERENCES public.photo_reconstruction_jobs(id),
    attempt_id BIGINT NOT NULL REFERENCES public.photo_reconstruction_attempts(id),
    artifact_type TEXT NOT NULL,
    file_format TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'unknown',
    observed_ratio DOUBLE PRECISION,
    inferred_ratio DOUBLE PRECISION,
    provenance_json TEXT NOT NULL DEFAULT '{}',
    is_canonical INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reconstruction_job_id, artifact_type, sha256)
);

CREATE INDEX IF NOT EXISTS idx_photo_reconstruction_artifacts_job
ON public.photo_reconstruction_artifacts(reconstruction_job_id, is_canonical, artifact_type, id);

CREATE TABLE IF NOT EXISTS public.photo_reconstruction_engine_health (
    engine_key TEXT PRIMARY KEY,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    circuit_open_until TEXT,
    last_success_at TEXT,
    last_failure_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
