CREATE TABLE IF NOT EXISTS public.cloud_object_download_tokens (
    id BIGSERIAL PRIMARY KEY,
    token_sha256 TEXT NOT NULL UNIQUE,
    object_id BIGINT NOT NULL REFERENCES public.cloud_objects(id) ON DELETE RESTRICT,
    issued_to_user_id BIGINT NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(token_sha256) = 64),
    CHECK(status IN ('active', 'used', 'revoked', 'expired'))
);

CREATE INDEX IF NOT EXISTS idx_cloud_object_download_tokens_expiry
ON public.cloud_object_download_tokens(status, expires_at);
