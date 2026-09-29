CREATE TABLE IF NOT EXISTS finance_compliance_controls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('pending', 'passed', 'blocked')),
    evidence_sha256 TEXT,
    reviewed_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    reviewed_at TEXT,
    expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_retention_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_class TEXT NOT NULL UNIQUE,
    retention_days INTEGER NOT NULL CHECK(retention_days > 0),
    legal_basis TEXT NOT NULL,
    deletion_mode TEXT NOT NULL CHECK(deletion_mode IN ('restricted_financial_record', 'anonymize_after_retention')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO finance_compliance_controls (control_key, status) VALUES
    ('pci_scope', 'pending'),
    ('lgpd', 'pending'),
    ('fiscal_br', 'pending'),
    ('legal_br', 'pending'),
    ('provider_continuity', 'pending'),
    ('chargeback_runbook', 'pending'),
    ('security_review', 'pending'),
    ('restore_test', 'pending');

INSERT OR IGNORE INTO finance_retention_policies (
    data_class, retention_days, legal_basis, deletion_mode
) VALUES
    ('ledger_and_orders', 3650, 'obrigação legal e exercício regular de direitos', 'restricted_financial_record'),
    ('payment_webhook_digests', 730, 'prevenção a fraude e defesa em disputa', 'restricted_financial_record'),
    ('finance_audit', 180, 'segurança e prestação de contas', 'anonymize_after_retention'),
    ('risk_evidence', 730, 'prevenção a fraude e recurso', 'anonymize_after_retention');

CREATE TRIGGER IF NOT EXISTS finance_retention_policies_immutable_update BEFORE UPDATE ON finance_retention_policies
BEGIN SELECT RAISE(ABORT, 'finance retention policy is immutable'); END;
CREATE TRIGGER IF NOT EXISTS finance_retention_policies_immutable_delete BEFORE DELETE ON finance_retention_policies
BEGIN SELECT RAISE(ABORT, 'finance retention policy cannot be deleted'); END;
