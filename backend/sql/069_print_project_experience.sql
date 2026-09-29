CREATE TABLE IF NOT EXISTS print_project_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES print_projects(id) ON DELETE CASCADE,
    save_kind TEXT NOT NULL DEFAULT 'reference' CHECK(save_kind IN ('reference', 'fork', 'copy')),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_user_id, project_id, save_kind)
);

CREATE INDEX IF NOT EXISTS idx_print_project_saves_owner
ON print_project_saves(owner_user_id, status, updated_at);

CREATE INDEX IF NOT EXISTS idx_print_project_saves_project
ON print_project_saves(project_id, status);
