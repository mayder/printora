ALTER TABLE setup_ssh_runs ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE setup_ssh_runs ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;
ALTER TABLE setup_can_runs ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE setup_can_runs ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;
ALTER TABLE setup_firmware_runs ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE setup_firmware_runs ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;
ALTER TABLE setup_flash_runs ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE setup_flash_runs ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;
ALTER TABLE setup_final_validation_runs ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE setup_final_validation_runs ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;
ALTER TABLE app_update_runs ADD COLUMN owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL;
ALTER TABLE app_update_runs ADD COLUMN organization_id INTEGER REFERENCES auth_organizations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_setup_ssh_runs_owner ON setup_ssh_runs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_setup_can_runs_owner ON setup_can_runs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_setup_firmware_runs_owner ON setup_firmware_runs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_setup_flash_runs_owner ON setup_flash_runs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_setup_final_validation_runs_owner ON setup_final_validation_runs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_app_update_runs_owner ON app_update_runs(owner_user_id);
