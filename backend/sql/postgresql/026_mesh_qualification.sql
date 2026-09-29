CREATE TABLE IF NOT EXISTS public.mesh_qualifications (
    id BIGSERIAL PRIMARY KEY,
    reconstruction_artifact_id BIGINT NOT NULL UNIQUE REFERENCES public.photo_reconstruction_artifacts(id),
    source_sha256 TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    status TEXT NOT NULL,
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mesh_qualifications_status
ON public.mesh_qualifications(status, created_at DESC, id DESC);
