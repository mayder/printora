CREATE TABLE IF NOT EXISTS public.mesh_revisions (
    id BIGSERIAL PRIMARY KEY,
    reconstruction_job_id BIGINT NOT NULL REFERENCES public.photo_reconstruction_jobs(id),
    source_artifact_id BIGINT NOT NULL REFERENCES public.photo_reconstruction_artifacts(id),
    parent_revision_id BIGINT REFERENCES public.mesh_revisions(id),
    owner_user_id BIGINT NOT NULL REFERENCES public.auth_users(id),
    durable_job_id BIGINT REFERENCES public.durable_jobs(id),
    operation TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    request_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    output_format TEXT,
    storage_key TEXT,
    sha256 TEXT,
    size_bytes BIGINT,
    unit TEXT NOT NULL DEFAULT 'unknown',
    manifest_json TEXT NOT NULL DEFAULT '{}',
    qualification_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_mesh_revisions_job
ON public.mesh_revisions(reconstruction_job_id, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_mesh_revisions_status
ON public.mesh_revisions(status, updated_at, id);
