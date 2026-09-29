CREATE TABLE IF NOT EXISTS catalog_manufacturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    trust_state TEXT NOT NULL DEFAULT 'official' CHECK(trust_state IN ('official', 'community', 'draft', 'obsolete', 'blocked')),
    source TEXT NOT NULL DEFAULT 'printora_seed',
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug)
);

CREATE TABLE IF NOT EXISTS catalog_printer_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_id INTEGER NOT NULL REFERENCES catalog_manufacturers(id) ON DELETE RESTRICT,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    kinematics TEXT NOT NULL,
    trust_state TEXT NOT NULL DEFAULT 'official' CHECK(trust_state IN ('official', 'community', 'draft', 'obsolete', 'blocked')),
    source TEXT NOT NULL DEFAULT 'printora_seed',
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer_id, slug)
);

CREATE TABLE IF NOT EXISTS catalog_printer_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL REFERENCES catalog_printer_models(id) ON DELETE RESTRICT,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    build_volume_json TEXT NOT NULL DEFAULT '{}',
    components_json TEXT NOT NULL DEFAULT '{}',
    firmware_family TEXT,
    trust_state TEXT NOT NULL DEFAULT 'official' CHECK(trust_state IN ('official', 'community', 'draft', 'obsolete', 'blocked')),
    source TEXT NOT NULL DEFAULT 'printora_seed',
    created_by_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, slug)
);

CREATE TABLE IF NOT EXISTS catalog_audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    actor_user_id INTEGER REFERENCES auth_users(id) ON DELETE SET NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES auth_users(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    display_name TEXT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    location TEXT,
    social_links_json TEXT NOT NULL DEFAULT '{}',
    visibility TEXT NOT NULL DEFAULT 'public' CHECK(visibility IN ('public', 'unlisted', 'private')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug)
);

CREATE TABLE IF NOT EXISTS social_profile_slug_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    replaced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug)
);

CREATE TABLE IF NOT EXISTS social_communities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('manufacturer', 'model', 'variant')),
    manufacturer_id INTEGER REFERENCES catalog_manufacturers(id) ON DELETE RESTRICT,
    model_id INTEGER REFERENCES catalog_printer_models(id) ON DELETE RESTRICT,
    variant_id INTEGER REFERENCES catalog_printer_variants(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'uncurated', 'obsolete', 'merged')),
    merged_into_id INTEGER REFERENCES social_communities(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug)
);

CREATE TABLE IF NOT EXISTS social_community_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    community_id INTEGER NOT NULL REFERENCES social_communities(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    printer_id INTEGER REFERENCES printers(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'public_printer',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(community_id, user_id, printer_id)
);

CREATE TABLE IF NOT EXISTS social_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    target_user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK(relation_type IN ('follow', 'friend', 'block')),
    status TEXT NOT NULL CHECK(status IN ('active', 'pending', 'accepted', 'ended')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TEXT,
    CHECK(actor_user_id != target_user_id),
    UNIQUE(actor_user_id, target_user_id, relation_type)
);

ALTER TABLE printers ADD COLUMN catalog_variant_id INTEGER REFERENCES catalog_printer_variants(id) ON DELETE SET NULL;
ALTER TABLE printers ADD COLUMN public_profile_enabled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE printers ADD COLUMN public_name TEXT;
ALTER TABLE printers ADD COLUMN public_description TEXT;
ALTER TABLE printers ADD COLUMN public_mods_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE printers ADD COLUMN public_images_json TEXT NOT NULL DEFAULT '[]';

INSERT INTO catalog_manufacturers (slug, name, trust_state, source)
VALUES ('voron-design', 'Voron Design', 'official', 'printora_seed')
ON CONFLICT(slug) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_models (manufacturer_id, slug, name, kinematics, trust_state, source)
SELECT id, 'voron-0-2', 'Voron 0.2', 'corexy', 'official', 'printora_seed'
FROM catalog_manufacturers WHERE slug = 'voron-design'
ON CONFLICT(manufacturer_id, slug) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_models (manufacturer_id, slug, name, kinematics, trust_state, source)
SELECT id, 'voron-2-4', 'Voron 2.4', 'corexy', 'official', 'printora_seed'
FROM catalog_manufacturers WHERE slug = 'voron-design'
ON CONFLICT(manufacturer_id, slug) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_variants (model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source)
SELECT id, 'voron-0-2-r1-120', 'Voron 0.2 R1 120mm',
       '{"x":120,"y":120,"z":120}',
       '{"mainboard":"BTT SKR Pico","mcu":"RP2040","toolhead":"Mini Stealthburner","extruder":"Clockwork 2","hotend":"V6/Revo Voron","probe":"Klicky/Probe opcional","bed":"120mm","kinematics":"corexy"}',
       'klipper', 'official', 'printora_seed'
FROM catalog_printer_models WHERE slug = 'voron-0-2'
ON CONFLICT(model_id, slug) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_variants (model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source)
SELECT id, 'voron-2-4-r2-300', 'Voron 2.4 R2 300mm',
       '{"x":300,"y":300,"z":300}',
       '{"mainboard":"BTT Octopus/Octopus Pro","mcu":"STM32/RP2040 conforme placa","toolhead":"Stealthburner","extruder":"Clockwork 2","hotend":"Dragon/Revo/V6","probe":"Tap/Klicky/Indutivo","bed":"300mm","kinematics":"corexy"}',
       'klipper', 'official', 'printora_seed'
FROM catalog_printer_models WHERE slug = 'voron-2-4'
ON CONFLICT(model_id, slug) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_variants (model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source)
SELECT id, 'voron-2-4-r2-350', 'Voron 2.4 R2 350mm',
       '{"x":350,"y":350,"z":350}',
       '{"mainboard":"BTT Octopus/Octopus Pro","mcu":"STM32/RP2040 conforme placa","toolhead":"Stealthburner","extruder":"Clockwork 2","hotend":"Dragon/Revo/V6","probe":"Tap/Klicky/Indutivo","bed":"350mm","kinematics":"corexy"}',
       'klipper', 'official', 'printora_seed'
FROM catalog_printer_models WHERE slug = 'voron-2-4'
ON CONFLICT(model_id, slug) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_catalog_models_manufacturer ON catalog_printer_models(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_catalog_variants_model ON catalog_printer_variants(model_id);
CREATE INDEX IF NOT EXISTS idx_printers_catalog_variant ON printers(catalog_variant_id);
CREATE INDEX IF NOT EXISTS idx_printers_public ON printers(public_profile_enabled, catalog_variant_id);
CREATE INDEX IF NOT EXISTS idx_social_profiles_visibility ON social_profiles(visibility);
CREATE INDEX IF NOT EXISTS idx_social_community_members_user ON social_community_members(user_id, active);
CREATE INDEX IF NOT EXISTS idx_social_relationships_actor ON social_relationships(actor_user_id, relation_type, status);
CREATE INDEX IF NOT EXISTS idx_social_relationships_target ON social_relationships(target_user_id, relation_type, status);
