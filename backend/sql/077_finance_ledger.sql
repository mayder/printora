CREATE TABLE IF NOT EXISTS finance_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    account_type TEXT NOT NULL CHECK(account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    currency TEXT NOT NULL CHECK(length(currency) = 3 AND currency = upper(currency)),
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_ledger_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_key TEXT NOT NULL UNIQUE,
    command_digest TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    currency TEXT NOT NULL CHECK(length(currency) = 3 AND currency = upper(currency)),
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'posted')),
    correlation_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    posted_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES finance_ledger_transactions(id) ON DELETE RESTRICT,
    account_id INTEGER NOT NULL REFERENCES finance_accounts(id) ON DELETE RESTRICT,
    side TEXT NOT NULL CHECK(side IN ('debit', 'credit')),
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    currency TEXT NOT NULL CHECK(length(currency) = 3 AND currency = upper(currency)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_finance_ledger_entries_transaction
ON finance_ledger_entries(transaction_id, side);

CREATE INDEX IF NOT EXISTS idx_finance_ledger_entries_account
ON finance_ledger_entries(account_id, created_at);

CREATE TRIGGER IF NOT EXISTS finance_ledger_entry_currency_guard
BEFORE INSERT ON finance_ledger_entries
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM finance_ledger_transactions transaction_row
        JOIN finance_accounts account_row ON account_row.id = NEW.account_id
        WHERE transaction_row.id = NEW.transaction_id
          AND transaction_row.status = 'draft'
          AND transaction_row.currency = NEW.currency
          AND account_row.currency = NEW.currency
          AND account_row.is_active = 1
    ) THEN RAISE(ABORT, 'finance ledger currency/account guard') END;
END;

CREATE TRIGGER IF NOT EXISTS finance_ledger_posting_balance_guard
BEFORE UPDATE OF status ON finance_ledger_transactions
WHEN NEW.status = 'posted' AND OLD.status = 'draft'
BEGIN
    SELECT CASE WHEN (
        SELECT COUNT(*) FROM finance_ledger_entries WHERE transaction_id = OLD.id
    ) < 2 THEN RAISE(ABORT, 'finance ledger requires at least two entries') END;
    SELECT CASE WHEN (
        SELECT COALESCE(SUM(CASE WHEN side = 'debit' THEN amount_minor ELSE -amount_minor END), 0)
        FROM finance_ledger_entries WHERE transaction_id = OLD.id
    ) <> 0 THEN RAISE(ABORT, 'finance ledger transaction is not balanced') END;
END;

CREATE TRIGGER IF NOT EXISTS finance_ledger_transactions_immutable
BEFORE UPDATE ON finance_ledger_transactions
WHEN OLD.status = 'posted'
BEGIN
    SELECT RAISE(ABORT, 'posted finance ledger transaction is immutable');
END;

CREATE TRIGGER IF NOT EXISTS finance_ledger_transactions_no_delete
BEFORE DELETE ON finance_ledger_transactions
BEGIN
    SELECT RAISE(ABORT, 'finance ledger transaction cannot be deleted');
END;

CREATE TRIGGER IF NOT EXISTS finance_ledger_entries_immutable_update
BEFORE UPDATE ON finance_ledger_entries
BEGIN
    SELECT RAISE(ABORT, 'finance ledger entry is immutable');
END;

CREATE TRIGGER IF NOT EXISTS finance_ledger_entries_immutable_delete
BEFORE DELETE ON finance_ledger_entries
BEGIN
    SELECT RAISE(ABORT, 'finance ledger entry cannot be deleted');
END;
