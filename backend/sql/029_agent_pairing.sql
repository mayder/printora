ALTER TABLE printers ADD COLUMN cloud_model TEXT;
ALTER TABLE printers ADD COLUMN cloud_tags_json TEXT NOT NULL DEFAULT '[]';

CREATE TABLE IF NOT EXISTS printer_pairing_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    organization_id INTEGER,
    owner_user_id INTEGER,
    created_by_user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    token_prefix TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(organization_id) REFERENCES auth_organizations(id) ON DELETE SET NULL,
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id) ON DELETE SET NULL,
    FOREIGN KEY(created_by_user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    UNIQUE(token_hash)
);

CREATE TABLE IF NOT EXISTS printer_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    organization_id INTEGER,
    owner_user_id INTEGER,
    stable_id TEXT NOT NULL,
    credential_hash TEXT NOT NULL,
    credential_prefix TEXT NOT NULL,
    agent_version TEXT,
    platform TEXT,
    capabilities_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    paired_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT,
    revoked_at TEXT,
    rotated_at TEXT,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(organization_id) REFERENCES auth_organizations(id) ON DELETE SET NULL,
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id) ON DELETE SET NULL,
    UNIQUE(stable_id),
    UNIQUE(credential_hash)
);

CREATE TABLE IF NOT EXISTS printer_agent_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    agent_id INTEGER,
    event_type TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(agent_id) REFERENCES printer_agents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pairing_tokens_printer ON printer_pairing_tokens(printer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_pairing_tokens_hash ON printer_pairing_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_printer_agents_printer ON printer_agents(printer_id, status);
CREATE INDEX IF NOT EXISTS idx_printer_agents_credential ON printer_agents(credential_hash);
CREATE INDEX IF NOT EXISTS idx_printer_agent_events_printer ON printer_agent_events(printer_id, created_at);
