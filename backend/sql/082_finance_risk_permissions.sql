ALTER TABLE finance_payouts ADD COLUMN paid_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT;

CREATE TABLE IF NOT EXISTS finance_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    role TEXT NOT NULL CHECK(role IN (
        'finance_operator', 'finance_approver', 'finance_risk',
        'finance_support', 'finance_auditor'
    )),
    granted_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role)
);

CREATE TABLE IF NOT EXISTS finance_risk_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    order_id INTEGER NOT NULL UNIQUE REFERENCES commerce_orders(id) ON DELETE RESTRICT,
    payment_intent_id INTEGER REFERENCES payment_intents(id) ON DELETE RESTRICT,
    buyer_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    score_basis_points INTEGER NOT NULL CHECK(score_basis_points >= 0 AND score_basis_points <= 10000),
    risk_level TEXT NOT NULL CHECK(risk_level IN ('low', 'medium', 'high')),
    reason_codes_json TEXT NOT NULL,
    recommended_action TEXT NOT NULL CHECK(recommended_action IN ('allow', 'review', 'block')),
    status TEXT NOT NULL CHECK(status IN ('approved', 'review_required', 'rejected', 'appealed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_risk_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_case_id INTEGER NOT NULL REFERENCES finance_risk_cases(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK(decision IN ('approve', 'reject', 'appeal')),
    reason TEXT NOT NULL,
    decided_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    subject_type TEXT NOT NULL,
    subject_public_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    retention_until TEXT NOT NULL DEFAULT (datetime('now', '+180 days')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_finance_roles_user ON finance_role_assignments(user_id, role, is_active);
CREATE INDEX IF NOT EXISTS idx_finance_risk_status ON finance_risk_cases(status, risk_level, created_at);
CREATE INDEX IF NOT EXISTS idx_finance_audit_retention ON finance_audit_events(retention_until, created_at);

CREATE TRIGGER IF NOT EXISTS finance_risk_decisions_immutable_update BEFORE UPDATE ON finance_risk_decisions
BEGIN SELECT RAISE(ABORT, 'finance risk decision is immutable'); END;
CREATE TRIGGER IF NOT EXISTS finance_risk_decisions_immutable_delete BEFORE DELETE ON finance_risk_decisions
BEGIN SELECT RAISE(ABORT, 'finance risk decision cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS finance_audit_events_immutable_update BEFORE UPDATE ON finance_audit_events
BEGIN SELECT RAISE(ABORT, 'finance audit event is immutable'); END;
CREATE TRIGGER IF NOT EXISTS finance_audit_events_immutable_delete BEFORE DELETE ON finance_audit_events
BEGIN SELECT RAISE(ABORT, 'finance audit event cannot be deleted'); END;
