CREATE TABLE IF NOT EXISTS analytics_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK(schema_version > 0),
    purpose TEXT NOT NULL,
    subject_key_hash TEXT,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','processed','anonymized','rejected')),
    retention_until TEXT NOT NULL,
    processed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_metric_facts (
    fact_key TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL REFERENCES analytics_events(event_id) ON DELETE RESTRICT,
    metric_name TEXT NOT NULL,
    dimension_key TEXT NOT NULL,
    value REAL NOT NULL,
    bucket_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_lineage (
    lineage_key TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL REFERENCES analytics_events(event_id) ON DELETE RESTRICT,
    derivative_type TEXT NOT NULL,
    derivative_key TEXT NOT NULL,
    transformation_version TEXT NOT NULL,
    output_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_event_id, derivative_type, derivative_key)
);

CREATE TABLE IF NOT EXISTS analytics_subject_controls (
    subject_key_hash TEXT PRIMARY KEY,
    purpose TEXT NOT NULL,
    consent_state TEXT NOT NULL CHECK(consent_state IN ('granted','withdrawn','not_required')),
    removal_requested_at TEXT,
    anonymized_at TEXT,
    deadline_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_moderation_cases (
    case_key TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL UNIQUE REFERENCES analytics_events(event_id) ON DELETE RESTRICT,
    entity_type TEXT NOT NULL,
    entity_reference_hash TEXT NOT NULL,
    detected_language TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    labels_json TEXT NOT NULL,
    context_sha256 TEXT NOT NULL,
    human_review_required INTEGER NOT NULL CHECK(human_review_required IN (0,1)),
    status TEXT NOT NULL CHECK(status IN ('awaiting_review','approved','rejected','appealed','closed')),
    reviewer_key_hash TEXT,
    rationale TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_moderation_appeals (
    appeal_key TEXT PRIMARY KEY,
    case_key TEXT NOT NULL REFERENCES analytics_moderation_cases(case_key) ON DELETE RESTRICT,
    appellant_key_hash TEXT NOT NULL,
    reason_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('open','upheld','denied')),
    reviewer_key_hash TEXT,
    resolution TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS analytics_model_registry (
    model_key TEXT NOT NULL,
    version TEXT NOT NULL,
    owner TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    dataset_license TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    bias_assessment_json TEXT NOT NULL,
    canary_percent INTEGER NOT NULL DEFAULT 0 CHECK(canary_percent >= 0 AND canary_percent <= 100),
    drift_score REAL NOT NULL DEFAULT 0,
    drift_threshold REAL NOT NULL DEFAULT 0.2,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
    kill_switch INTEGER NOT NULL DEFAULT 0 CHECK(kill_switch IN (0,1)),
    fallback_strategy TEXT NOT NULL,
    rollback_version TEXT,
    retention_until TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(model_key, version)
);

CREATE TABLE IF NOT EXISTS analytics_model_decisions (
    decision_key TEXT PRIMARY KEY,
    model_key TEXT NOT NULL,
    model_version TEXT NOT NULL,
    input_sha256 TEXT NOT NULL,
    output_json TEXT NOT NULL,
    fallback_used INTEGER NOT NULL CHECK(fallback_used IN (0,1)),
    subject_key_hash TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(model_key, model_version) REFERENCES analytics_model_registry(model_key, version) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS analytics_geometry_items (
    item_key TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_reference_hash TEXT NOT NULL,
    features_json TEXT NOT NULL,
    features_sha256 TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    source_event_id TEXT NOT NULL REFERENCES analytics_events(event_id) ON DELETE RESTRICT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_replay_runs (
    replay_key TEXT PRIMARY KEY,
    source_filter TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running','completed','failed')),
    processed_count INTEGER NOT NULL DEFAULT 0,
    unchanged_count INTEGER NOT NULL DEFAULT 0,
    output_sha256 TEXT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS analytics_retention_policies (
    purpose TEXT PRIMARY KEY,
    retention_days INTEGER NOT NULL CHECK(retention_days > 0),
    derivative_deadline_hours INTEGER NOT NULL CHECK(derivative_deadline_hours > 0),
    temporary_data INTEGER NOT NULL DEFAULT 0 CHECK(temporary_data IN (0,1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_status ON analytics_events(status, created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_events_subject ON analytics_events(subject_key_hash);
CREATE INDEX IF NOT EXISTS idx_analytics_metric_facts_name ON analytics_metric_facts(metric_name, bucket_at);
CREATE INDEX IF NOT EXISTS idx_analytics_moderation_status ON analytics_moderation_cases(status, created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_geometry_type ON analytics_geometry_items(entity_type, active);

INSERT INTO analytics_retention_policies(purpose, retention_days, derivative_deadline_hours, temporary_data)
VALUES
    ('product_impact', 730, 24, 0),
    ('safety_moderation', 365, 24, 0),
    ('recommendation', 90, 24, 0),
    ('geometry_search', 180, 24, 0),
    ('temporary_experiment', 7, 24, 1)
ON CONFLICT(purpose) DO NOTHING;

INSERT INTO analytics_model_registry(
    model_key, version, owner, dataset_name, dataset_version, dataset_license,
    metrics_json, bias_assessment_json, canary_percent, fallback_strategy,
    rollback_version, retention_until
) VALUES
    ('recommendation-baseline', '1.0.0', 'Produto e Dados', 'sanitized-events', 'v1', 'internal-authorized',
     '{"precision_at_10":0.0,"status":"baseline_without_external_dataset"}',
     '{"status":"human_reviewed_rules","protected_attributes_used":false}', 100,
     'stable_item_key_order', NULL, datetime('now', '+730 days')),
    ('geometry-baseline', '1.0.0', 'Engenharia de Busca', 'normalized-geometric-features', 'v1', 'internal-authorized',
     '{"distance":"normalized_l1","status":"deterministic_baseline"}',
     '{"status":"not_applicable_no_personal_attributes"}', 100,
     'stable_item_key_order', NULL, datetime('now', '+730 days'))
ON CONFLICT(model_key, version) DO NOTHING;
