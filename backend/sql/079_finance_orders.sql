CREATE TABLE IF NOT EXISTS commerce_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    buyer_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE RESTRICT,
    idempotency_key TEXT NOT NULL UNIQUE,
    command_digest TEXT NOT NULL,
    currency TEXT NOT NULL CHECK(length(currency) = 3 AND currency = upper(currency)),
    subtotal_minor INTEGER NOT NULL CHECK(subtotal_minor >= 0),
    fee_minor INTEGER NOT NULL DEFAULT 0 CHECK(fee_minor >= 0),
    tax_minor INTEGER NOT NULL DEFAULT 0 CHECK(tax_minor >= 0),
    total_minor INTEGER NOT NULL CHECK(total_minor >= 0),
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN (
        'draft', 'pending_payment', 'paid', 'cancelled', 'partially_refunded',
        'refunded', 'disputed'
    )),
    country_code TEXT NOT NULL DEFAULT 'BR',
    tax_status TEXT NOT NULL DEFAULT 'not_configured' CHECK(tax_status IN ('not_configured', 'prepared', 'reviewed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commerce_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES commerce_orders(id) ON DELETE RESTRICT,
    source_project_id INTEGER NOT NULL REFERENCES print_projects(id) ON DELETE RESTRICT,
    source_project_version_id INTEGER REFERENCES print_project_versions(id) ON DELETE RESTRICT,
    seller_user_id INTEGER REFERENCES auth_users(id) ON DELETE RESTRICT,
    title_snapshot TEXT NOT NULL,
    license_snapshot TEXT NOT NULL,
    terms_snapshot TEXT NOT NULL,
    project_snapshot_json TEXT NOT NULL,
    unit_price_minor INTEGER NOT NULL CHECK(unit_price_minor > 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0 AND quantity <= 100),
    currency TEXT NOT NULL CHECK(length(currency) = 3 AND currency = upper(currency)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_commerce_orders_buyer
ON commerce_orders(buyer_user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_commerce_orders_status
ON commerce_orders(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_commerce_order_items_order
ON commerce_order_items(order_id, id);

CREATE TRIGGER IF NOT EXISTS commerce_order_amounts_immutable
BEFORE UPDATE OF currency, subtotal_minor, fee_minor, tax_minor, total_minor, country_code, tax_status
ON commerce_orders
BEGIN SELECT RAISE(ABORT, 'commerce order monetary snapshot is immutable'); END;

CREATE TRIGGER IF NOT EXISTS commerce_orders_no_delete
BEFORE DELETE ON commerce_orders
BEGIN SELECT RAISE(ABORT, 'commerce order cannot be deleted'); END;

CREATE TRIGGER IF NOT EXISTS commerce_order_items_immutable_update
BEFORE UPDATE ON commerce_order_items
BEGIN SELECT RAISE(ABORT, 'commerce order item is immutable'); END;

CREATE TRIGGER IF NOT EXISTS commerce_order_items_immutable_delete
BEFORE DELETE ON commerce_order_items
BEGIN SELECT RAISE(ABORT, 'commerce order item cannot be deleted'); END;
