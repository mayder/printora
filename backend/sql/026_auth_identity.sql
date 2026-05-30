CREATE TABLE IF NOT EXISTS auth_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    whatsapp TEXT,
    telegram TEXT,
    social_links_json TEXT NOT NULL DEFAULT '{}',
    mfa_enabled INTEGER NOT NULL DEFAULT 0,
    mfa_secret_protected TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email)
);

CREATE TABLE IF NOT EXISTS auth_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS auth_organization_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'operator')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(organization_id) REFERENCES auth_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    UNIQUE(organization_id, user_id)
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT,
    FOREIGN KEY(user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    UNIQUE(token_hash)
);

CREATE TABLE IF NOT EXISTS auth_mfa_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    challenge_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    UNIQUE(challenge_hash)
);

CREATE TABLE IF NOT EXISTS auth_step_up_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    purpose TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    UNIQUE(token_hash)
);

CREATE TABLE IF NOT EXISTS agent_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    owner_user_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    credential_hash TEXT NOT NULL,
    credential_prefix TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TEXT,
    FOREIGN KEY(organization_id) REFERENCES auth_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(owner_user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    UNIQUE(credential_hash)
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_members_user ON auth_organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_members_org ON auth_organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_expires ON auth_sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_agent_credentials_owner ON agent_credentials(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_agent_credentials_org ON agent_credentials(organization_id);
