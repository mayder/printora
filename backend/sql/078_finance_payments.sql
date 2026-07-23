CREATE TABLE IF NOT EXISTS payment_intents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    order_id INTEGER,
    provider TEXT NOT NULL,
    provider_intent_id TEXT NOT NULL UNIQUE,
    idempotency_key TEXT NOT NULL UNIQUE,
    command_digest TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    currency TEXT NOT NULL CHECK(length(currency) = 3 AND currency = upper(currency)),
    status TEXT NOT NULL CHECK(status IN (
        'requires_action', 'authorized', 'captured', 'cancelled', 'partially_refunded',
        'refunded', 'disputed', 'failed'
    )),
    hosted_checkout_url TEXT NOT NULL,
    latest_provider_event_at TEXT,
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_webhook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    provider_event_id TEXT NOT NULL,
    provider_intent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_created_at TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    signature_verified INTEGER NOT NULL CHECK(signature_verified IN (0, 1)),
    processing_status TEXT NOT NULL CHECK(processing_status IN ('processed', 'ignored_out_of_order', 'rejected')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_event_id)
);

CREATE INDEX IF NOT EXISTS idx_payment_intents_status
ON payment_intents(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_payment_webhook_events_intent
ON payment_webhook_events(provider_intent_id, event_created_at);

CREATE TRIGGER IF NOT EXISTS payment_webhook_events_immutable_update
BEFORE UPDATE ON payment_webhook_events
BEGIN SELECT RAISE(ABORT, 'payment webhook event is immutable'); END;

CREATE TRIGGER IF NOT EXISTS payment_webhook_events_immutable_delete
BEFORE DELETE ON payment_webhook_events
BEGIN SELECT RAISE(ABORT, 'payment webhook event cannot be deleted'); END;
