CREATE TABLE IF NOT EXISTS finance_payment_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_intent_id INTEGER NOT NULL REFERENCES payment_intents(id) ON DELETE RESTRICT,
    command_type TEXT NOT NULL CHECK(command_type IN ('capture', 'cancel', 'refund', 'open_dispute', 'resolve_dispute_won', 'resolve_dispute_lost')),
    idempotency_key TEXT NOT NULL UNIQUE,
    command_digest TEXT NOT NULL,
    amount_minor INTEGER,
    result_status TEXT NOT NULL,
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    payment_intent_id INTEGER NOT NULL REFERENCES payment_intents(id) ON DELETE RESTRICT,
    order_id INTEGER REFERENCES commerce_orders(id) ON DELETE RESTRICT,
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    currency TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('succeeded')),
    command_id INTEGER NOT NULL UNIQUE REFERENCES finance_payment_commands(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_refund_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refund_id INTEGER NOT NULL REFERENCES payment_refunds(id) ON DELETE RESTRICT,
    seller_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    currency TEXT NOT NULL,
    UNIQUE(refund_id, seller_user_id)
);

CREATE TABLE IF NOT EXISTS payment_disputes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    payment_intent_id INTEGER NOT NULL REFERENCES payment_intents(id) ON DELETE RESTRICT,
    order_id INTEGER REFERENCES commerce_orders(id) ON DELETE RESTRICT,
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    currency TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('open', 'won', 'lost')),
    opened_command_id INTEGER NOT NULL UNIQUE REFERENCES finance_payment_commands(id) ON DELETE RESTRICT,
    resolved_command_id INTEGER UNIQUE REFERENCES finance_payment_commands(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_finance_payment_commands_intent
ON finance_payment_commands(payment_intent_id, created_at);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_intent
ON payment_refunds(payment_intent_id, created_at);
CREATE INDEX IF NOT EXISTS idx_payment_disputes_intent
ON payment_disputes(payment_intent_id, status);

CREATE TRIGGER IF NOT EXISTS finance_payment_commands_immutable_update BEFORE UPDATE ON finance_payment_commands
BEGIN SELECT RAISE(ABORT, 'finance payment command is immutable'); END;
CREATE TRIGGER IF NOT EXISTS finance_payment_commands_immutable_delete BEFORE DELETE ON finance_payment_commands
BEGIN SELECT RAISE(ABORT, 'finance payment command cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS payment_refunds_immutable_update BEFORE UPDATE ON payment_refunds
BEGIN SELECT RAISE(ABORT, 'payment refund is immutable'); END;
CREATE TRIGGER IF NOT EXISTS payment_refunds_immutable_delete BEFORE DELETE ON payment_refunds
BEGIN SELECT RAISE(ABORT, 'payment refund cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS payment_refund_allocations_immutable_update BEFORE UPDATE ON payment_refund_allocations
BEGIN SELECT RAISE(ABORT, 'payment refund allocation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS payment_refund_allocations_immutable_delete BEFORE DELETE ON payment_refund_allocations
BEGIN SELECT RAISE(ABORT, 'payment refund allocation cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS payment_disputes_no_delete BEFORE DELETE ON payment_disputes
BEGIN SELECT RAISE(ABORT, 'payment dispute cannot be deleted'); END;
