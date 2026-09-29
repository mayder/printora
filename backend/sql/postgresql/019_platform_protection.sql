ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS mfa_pending_secret_protected TEXT;
ALTER TABLE operation_action_previews ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS auth_account_requests (
    id BIGSERIAL PRIMARY KEY,
    request_key TEXT NOT NULL UNIQUE,
    user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    request_type TEXT NOT NULL CHECK(request_type IN ('export', 'deletion')),
    status TEXT NOT NULL CHECK(status IN ('processing', 'ready', 'completed', 'failed', 'cancelled')),
    artifact_sha256 TEXT,
    failure_code TEXT,
    effective_at TIMESTAMPTZ,
    retention_until TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '180 days'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_auth_account_requests_user
ON auth_account_requests(user_id, request_type, created_at);

CREATE INDEX IF NOT EXISTS idx_auth_account_requests_retention
ON auth_account_requests(retention_until, status);

CREATE TABLE IF NOT EXISTS social_moderation_appeals (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT NOT NULL REFERENCES social_moderation_reports(id) ON DELETE RESTRICT,
    appellant_user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'upheld', 'overturned')),
    reviewed_by_user_id BIGINT REFERENCES auth_users(id) ON DELETE RESTRICT,
    resolution_note TEXT,
    retention_until TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '180 days'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    UNIQUE(report_id, appellant_user_id)
);

CREATE INDEX IF NOT EXISTS idx_social_moderation_appeals_queue
ON social_moderation_appeals(status, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_print_delivery_active_preflight
ON print_gcode_deliveries(preflight_id)
WHERE status IN ('pending_remote', 'saved', 'printing');

CREATE TABLE IF NOT EXISTS security_operation_claims (
    id BIGSERIAL PRIMARY KEY,
    claim_key TEXT NOT NULL UNIQUE,
    operation_type TEXT NOT NULL,
    actor_user_id BIGINT REFERENCES auth_users(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'processing' CHECK(status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
