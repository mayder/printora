CREATE TABLE IF NOT EXISTS print_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    visibility TEXT NOT NULL DEFAULT 'private' CHECK(visibility IN ('private', 'unlisted', 'public')),
    lifecycle_status TEXT NOT NULL DEFAULT 'draft' CHECK(lifecycle_status IN ('draft', 'active', 'archived')),
    publication_status TEXT NOT NULL DEFAULT 'draft' CHECK(publication_status IN ('draft', 'in_review', 'approved', 'rejected', 'archived')),
    commercial_class TEXT NOT NULL DEFAULT 'free' CHECK(commercial_class IN ('free', 'curated', 'premium', 'sponsored')),
    license TEXT NOT NULL DEFAULT '',
    original_author_name TEXT NOT NULL DEFAULT '',
    attribution_text TEXT NOT NULL DEFAULT '',
    source_url TEXT,
    primary_file_id INTEGER,
    current_version_id INTEGER,
    tags_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS print_project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES print_projects(id) ON DELETE CASCADE,
    file_kind TEXT NOT NULL CHECK(file_kind IN ('stl', '3mf', 'zip', 'image', 'documentation', 'link', 'gcode', 'artifact')),
    file_role TEXT NOT NULL DEFAULT 'printable' CHECK(file_role IN ('primary', 'printable', 'optional_part', 'documentation', 'preview', 'external_reference', 'artifact')),
    file_name TEXT NOT NULL,
    external_url TEXT,
    storage_path TEXT,
    size_bytes INTEGER,
    sha256 TEXT,
    validation_status TEXT NOT NULL DEFAULT 'metadata_only' CHECK(validation_status IN ('metadata_only', 'quarantined', 'validated', 'rejected', 'analysis_failed')),
    can_slice INTEGER NOT NULL DEFAULT 0,
    analysis_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS print_project_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES print_projects(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    changelog TEXT NOT NULL DEFAULT '',
    project_snapshot_json TEXT NOT NULL DEFAULT '{}',
    files_snapshot_json TEXT NOT NULL DEFAULT '[]',
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS print_project_community_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES print_projects(id) ON DELETE CASCADE,
    community_id INTEGER NOT NULL REFERENCES social_communities(id) ON DELETE CASCADE,
    shared_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'removed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, community_id)
);

CREATE INDEX IF NOT EXISTS idx_print_projects_visibility
ON print_projects(visibility, lifecycle_status, publication_status, updated_at);

CREATE INDEX IF NOT EXISTS idx_print_projects_owner
ON print_projects(owner_user_id, lifecycle_status, updated_at);

CREATE INDEX IF NOT EXISTS idx_print_project_files_project
ON print_project_files(project_id, file_role, validation_status);

CREATE INDEX IF NOT EXISTS idx_print_project_versions_project
ON print_project_versions(project_id, created_at);

CREATE INDEX IF NOT EXISTS idx_print_project_shares_community
ON print_project_community_shares(community_id, status, updated_at);
