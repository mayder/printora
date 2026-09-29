CREATE TABLE IF NOT EXISTS manufacturing_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    order_id INTEGER NOT NULL REFERENCES commerce_orders(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK(version > 0),
    idempotency_key TEXT NOT NULL UNIQUE,
    material_snapshot_json TEXT NOT NULL,
    machine_snapshot_json TEXT NOT NULL,
    file_snapshot_json TEXT NOT NULL,
    license_snapshot TEXT NOT NULL,
    tolerance_snapshot_json TEXT NOT NULL,
    finish_snapshot_json TEXT NOT NULL,
    shipping_snapshot_json TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK(amount_minor >= 0),
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    lead_time_days INTEGER NOT NULL CHECK(lead_time_days > 0),
    status TEXT NOT NULL CHECK(status IN ('offered','accepted','rejected','expired')),
    created_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    accepted_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    accepted_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(order_id, version)
);

CREATE TABLE IF NOT EXISTS manufacturing_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    role TEXT NOT NULL CHECK(role IN ('production_operator','quality_inspector','quality_approver','logistics_operator','safety_manager')),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    assigned_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role)
);

CREATE TABLE IF NOT EXISTS manufacturing_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_key TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL CHECK(resource_type IN ('capacity','material')),
    available_units INTEGER NOT NULL CHECK(available_units >= 0),
    unit TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    quote_id INTEGER NOT NULL UNIQUE REFERENCES manufacturing_quotes(id) ON DELETE RESTRICT,
    order_id INTEGER NOT NULL UNIQUE REFERENCES commerce_orders(id) ON DELETE RESTRICT,
    state TEXT NOT NULL CHECK(state IN ('reserved','queued','producing','paused','failed','quality_pending','rework','quality_approved','packed','shipped','delivered','cancelled','recalled')),
    assigned_operator_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturing_order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    resource_id INTEGER NOT NULL REFERENCES manufacturing_resources(id) ON DELETE RESTRICT,
    units INTEGER NOT NULL CHECK(units > 0),
    idempotency_key TEXT NOT NULL UNIQUE,
    released_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturing_order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    actor_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_quality_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturing_order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    check_key TEXT NOT NULL,
    specification_json TEXT NOT NULL,
    measurement_json TEXT,
    result TEXT NOT NULL CHECK(result IN ('pending','passed','failed')),
    evidence_object_key TEXT,
    inspected_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    approved_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturing_order_id, check_key)
);

CREATE TABLE IF NOT EXISTS manufacturing_shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    manufacturing_order_id INTEGER NOT NULL UNIQUE REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    carrier TEXT NOT NULL,
    tracking_token_hash TEXT NOT NULL,
    address_ciphertext TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('packed','in_transit','exception','delivered','returned')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_tracking_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id INTEGER NOT NULL REFERENCES manufacturing_shipments(id) ON DELETE RESTRICT,
    provider_event_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(shipment_id, provider_event_id)
);

CREATE TABLE IF NOT EXISTS manufacturing_custody_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturing_order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    event_key TEXT NOT NULL UNIQUE,
    subject_type TEXT NOT NULL CHECK(subject_type IN ('file','material','part','package')),
    subject_reference_hash TEXT NOT NULL,
    custody_state TEXT NOT NULL,
    actor_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    manufacturing_order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    incident_type TEXT NOT NULL CHECK(incident_type IN ('quality','unsafe_product','logistics','privacy')),
    severity TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical')),
    status TEXT NOT NULL CHECK(status IN ('open','contained','resolved','recalled')),
    evidence_reference_hash TEXT NOT NULL,
    finance_command_key TEXT UNIQUE,
    created_by_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manufacturing_recall_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL REFERENCES manufacturing_incidents(id) ON DELETE RESTRICT,
    manufacturing_order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id) ON DELETE RESTRICT,
    notification_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('identified','notified','returned','resolved')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(incident_id, manufacturing_order_id)
);

CREATE TRIGGER IF NOT EXISTS manufacturing_quotes_immutable_update BEFORE UPDATE ON manufacturing_quotes
WHEN OLD.status = 'accepted' BEGIN SELECT RAISE(ABORT, 'accepted manufacturing quote is immutable'); END;
CREATE TRIGGER IF NOT EXISTS manufacturing_quotes_no_delete BEFORE DELETE ON manufacturing_quotes
BEGIN SELECT RAISE(ABORT, 'manufacturing quote cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS manufacturing_events_no_update BEFORE UPDATE ON manufacturing_events
BEGIN SELECT RAISE(ABORT, 'manufacturing event is immutable'); END;
CREATE TRIGGER IF NOT EXISTS manufacturing_events_no_delete BEFORE DELETE ON manufacturing_events
BEGIN SELECT RAISE(ABORT, 'manufacturing event cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS manufacturing_custody_no_update BEFORE UPDATE ON manufacturing_custody_events
BEGIN SELECT RAISE(ABORT, 'custody event is immutable'); END;
CREATE TRIGGER IF NOT EXISTS manufacturing_custody_no_delete BEFORE DELETE ON manufacturing_custody_events
BEGIN SELECT RAISE(ABORT, 'custody event cannot be deleted'); END;
