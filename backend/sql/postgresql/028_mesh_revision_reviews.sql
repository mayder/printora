CREATE TABLE IF NOT EXISTS public.mesh_revision_reviews (
    id BIGSERIAL PRIMARY KEY,
    revision_id BIGINT NOT NULL REFERENCES public.mesh_revisions(id),
    reconstruction_job_id BIGINT NOT NULL REFERENCES public.photo_reconstruction_jobs(id),
    owner_user_id BIGINT NOT NULL REFERENCES public.auth_users(id),
    decision TEXT NOT NULL,
    intended_use TEXT NOT NULL,
    known_axis TEXT,
    known_dimension_mm DOUBLE PRECISION,
    model_dimension_mm DOUBLE PRECISION,
    deviation_percent DOUBLE PRECISION,
    revision_sha256 TEXT NOT NULL,
    review_manifest_json TEXT NOT NULL DEFAULT '{}',
    qualification_json TEXT NOT NULL DEFAULT '{}',
    project_file_id BIGINT REFERENCES public.print_project_files(id),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_user_id, idempotency_key),
    CHECK(decision IN ('approved_for_slicing', 'rejected')),
    CHECK(intended_use IN ('decorative', 'prototype', 'mechanical')),
    CHECK(known_axis IS NULL OR known_axis IN ('x', 'y', 'z'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mesh_revision_one_approval
ON public.mesh_revision_reviews(revision_id)
WHERE decision = 'approved_for_slicing';

CREATE INDEX IF NOT EXISTS idx_mesh_revision_reviews_job
ON public.mesh_revision_reviews(reconstruction_job_id, created_at DESC, id DESC);
