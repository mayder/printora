ALTER TABLE print_projects ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE print_projects ADD COLUMN currency TEXT NOT NULL DEFAULT 'BRL';
ALTER TABLE print_projects ADD COLUMN commercial_terms TEXT NOT NULL DEFAULT '';
ALTER TABLE print_projects ADD COLUMN promotion_disclosure TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS print_project_publication_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES print_projects(id) ON DELETE CASCADE,
    reviewer_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK(status IN ('pending_review', 'approved', 'rejected')),
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_print_project_publication_reviews_project
ON print_project_publication_reviews(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_print_projects_publication_commercial
ON print_projects(publication_status, commercial_class, visibility, updated_at);
