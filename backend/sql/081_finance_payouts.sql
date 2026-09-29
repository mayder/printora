CREATE TABLE IF NOT EXISTS finance_reconciliation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    currency TEXT NOT NULL,
    ledger_clearing_minor INTEGER NOT NULL,
    provider_reported_minor INTEGER NOT NULL,
    difference_minor INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('passed', 'blocked')),
    evidence_sha256 TEXT NOT NULL,
    executed_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    seller_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    currency TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    status TEXT NOT NULL CHECK(status IN ('requested', 'approved', 'blocked', 'paid', 'cancelled')),
    idempotency_key TEXT NOT NULL UNIQUE,
    command_digest TEXT NOT NULL,
    requested_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    approved_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    paid_ledger_transaction_id INTEGER UNIQUE REFERENCES finance_ledger_transactions(id) ON DELETE RESTRICT,
    reconciliation_run_id INTEGER REFERENCES finance_reconciliation_runs(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TEXT,
    paid_at TEXT,
    CHECK(approved_by_user_id IS NULL OR approved_by_user_id <> requested_by_user_id)
);

CREATE TABLE IF NOT EXISTS finance_closings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    currency TEXT NOT NULL,
    period_key TEXT NOT NULL,
    reconciliation_run_id INTEGER NOT NULL REFERENCES finance_reconciliation_runs(id) ON DELETE RESTRICT,
    ledger_transaction_count INTEGER NOT NULL,
    ledger_imbalance_count INTEGER NOT NULL,
    open_dispute_count INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('closed', 'blocked')),
    closed_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(currency, period_key)
);

CREATE INDEX IF NOT EXISTS idx_finance_payouts_seller ON finance_payouts(seller_user_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_finance_reconciliation_status ON finance_reconciliation_runs(currency, status, created_at);

CREATE TRIGGER IF NOT EXISTS finance_reconciliation_immutable_update BEFORE UPDATE ON finance_reconciliation_runs
BEGIN SELECT RAISE(ABORT, 'finance reconciliation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS finance_reconciliation_immutable_delete BEFORE DELETE ON finance_reconciliation_runs
BEGIN SELECT RAISE(ABORT, 'finance reconciliation cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS finance_payouts_no_delete BEFORE DELETE ON finance_payouts
BEGIN SELECT RAISE(ABORT, 'finance payout cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS finance_closings_immutable_update BEFORE UPDATE ON finance_closings
BEGIN SELECT RAISE(ABORT, 'finance closing is immutable'); END;
CREATE TRIGGER IF NOT EXISTS finance_closings_immutable_delete BEFORE DELETE ON finance_closings
BEGIN SELECT RAISE(ABORT, 'finance closing cannot be deleted'); END;
