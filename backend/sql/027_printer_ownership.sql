ALTER TABLE printers ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE printers ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_printers_owner ON printers(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_printers_organization ON printers(organization_id);
