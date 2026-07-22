CREATE TABLE IF NOT EXISTS public.outbox_events (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    ordering_key TEXT NOT NULL,
    sequence_no BIGINT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    headers_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 12,
    available_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lease_owner TEXT,
    lease_token TEXT,
    lease_expires_at TEXT,
    published_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ordering_key, sequence_no)
);

CREATE INDEX IF NOT EXISTS idx_outbox_events_dispatch
ON public.outbox_events(status, available_at, id);
CREATE INDEX IF NOT EXISTS idx_outbox_events_lease
ON public.outbox_events(lease_expires_at, status);

CREATE TABLE IF NOT EXISTS public.inbox_receipts (
    id BIGSERIAL PRIMARY KEY,
    consumer_name TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    payload_sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    result_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT,
    UNIQUE(consumer_name, event_id)
);

CREATE INDEX IF NOT EXISTS idx_inbox_receipts_consumer_status
ON public.inbox_receipts(consumer_name, status, received_at);

CREATE TABLE IF NOT EXISTS public.durable_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_key TEXT NOT NULL UNIQUE,
    queue_name TEXT NOT NULL,
    job_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    ordering_key TEXT,
    owner_type TEXT,
    owner_id TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    priority INTEGER NOT NULL DEFAULT 100,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 8,
    available_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lease_owner TEXT,
    lease_token TEXT,
    lease_expires_at TEXT,
    heartbeat_at TEXT,
    result_json TEXT,
    error_message TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_durable_jobs_claim
ON public.durable_jobs(queue_name, status, priority, available_at, id);
CREATE INDEX IF NOT EXISTS idx_durable_jobs_lease
ON public.durable_jobs(status, lease_expires_at);
CREATE INDEX IF NOT EXISTS idx_durable_jobs_owner
ON public.durable_jobs(owner_type, owner_id, created_at);

CREATE TABLE IF NOT EXISTS public.idempotency_records (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_sha256 TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'processing',
    response_status INTEGER,
    response_headers_json TEXT NOT NULL DEFAULT '{}',
    response_body_json TEXT,
    lock_token TEXT,
    lock_expires_at TEXT,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scope, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_records_expiry
ON public.idempotency_records(expires_at, state);

CREATE TABLE IF NOT EXISTS public.realtime_sessions (
    session_id TEXT PRIMARY KEY,
    agent_id BIGINT NOT NULL REFERENCES public.printer_agents(id) ON DELETE CASCADE,
    printer_id BIGINT NOT NULL REFERENCES public.printers(id) ON DELETE CASCADE,
    instance_id TEXT NOT NULL,
    protocol_version INTEGER NOT NULL,
    connected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    heartbeat_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    disconnected_at TEXT,
    last_acknowledged_job_id BIGINT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_realtime_sessions_agent
ON public.realtime_sessions(agent_id, expires_at, disconnected_at);
CREATE INDEX IF NOT EXISTS idx_realtime_sessions_instance
ON public.realtime_sessions(instance_id, expires_at, disconnected_at);

CREATE TABLE IF NOT EXISTS public.worker_controls (
    queue_name TEXT PRIMARY KEY,
    desired_state TEXT NOT NULL DEFAULT 'running',
    max_concurrency INTEGER NOT NULL DEFAULT 1,
    updated_by TEXT NOT NULL DEFAULT 'bootstrap',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.worker_instances (
    worker_id TEXT PRIMARY KEY,
    queue_name TEXT NOT NULL,
    release_sha TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'starting',
    concurrency INTEGER NOT NULL DEFAULT 1,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    heartbeat_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stopped_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_worker_instances_queue_state
ON public.worker_instances(queue_name, state, heartbeat_at);

INSERT INTO public.worker_controls (queue_name, desired_state, max_concurrency)
VALUES ('critical', 'running', 2), ('default', 'running', 2), ('bulk', 'running', 1)
ON CONFLICT (queue_name) DO NOTHING;

INSERT INTO public.worker_controls (queue_name, desired_state, max_concurrency)
VALUES ('outbox', 'running', 1)
ON CONFLICT (queue_name) DO NOTHING;
