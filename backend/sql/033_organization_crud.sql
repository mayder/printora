CREATE TABLE IF NOT EXISTS auth_organization_invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    created_by_user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    token_prefix TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',
    expires_at TEXT NOT NULL,
    accepted_by_user_id INTEGER,
    accepted_at TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(organization_id) REFERENCES auth_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(created_by_user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    FOREIGN KEY(accepted_by_user_id) REFERENCES auth_users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS auth_organization_printers (
    organization_id INTEGER NOT NULL,
    printer_id INTEGER NOT NULL,
    linked_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(organization_id, printer_id),
    FOREIGN KEY(organization_id) REFERENCES auth_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(linked_by_user_id) REFERENCES auth_users(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO auth_organization_printers (organization_id, printer_id, linked_by_user_id)
SELECT p.organization_id, p.id, COALESCE(p.owner_user_id, o.owner_user_id)
FROM printers p
JOIN auth_organizations o ON o.id = p.organization_id
WHERE p.organization_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_auth_org_invites_hash ON auth_organization_invites(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_org_invites_org ON auth_organization_invites(organization_id, created_at);
CREATE INDEX IF NOT EXISTS idx_auth_org_printers_printer ON auth_organization_printers(printer_id);
