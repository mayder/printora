INSERT INTO catalog_printer_models (manufacturer_id, slug, name, kinematics, trust_state, source)
SELECT id, 'voron-phoenix', 'Voron Phoenix', 'corexy', 'draft', 'printora_seed_catalog_uncertain'
FROM catalog_manufacturers
WHERE slug = 'voron-design'
ON CONFLICT(manufacturer_id, slug) DO UPDATE SET
  name = excluded.name,
  kinematics = excluded.kinematics,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;

UPDATE catalog_printer_models
SET description = 'Projeto Voron de grande formato mantido como draft até validação completa de documentação, volumes e BOM.',
    repository_url = 'https://github.com/VoronDesign/Voron-Phoenix',
    documentation_url = 'https://docs.vorondesign.com/',
    updated_at = CURRENT_TIMESTAMP
WHERE slug = 'voron-phoenix'
  AND manufacturer_id IN (SELECT id FROM catalog_manufacturers WHERE slug = 'voron-design');

INSERT INTO catalog_printer_variants (
  model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source
)
SELECT m.id, seed.slug, seed.name, seed.build_volume_json, seed.components_json, 'klipper', 'draft', 'printora_seed_catalog_uncertain'
FROM (
  SELECT 'voron-phoenix-500' AS slug, 'Voron Phoenix 500mm draft' AS name,
         '{"x":500,"y":500,"z":500}' AS build_volume_json,
         '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"Stealthburner/definir na curadoria","extruder":"Clockwork/definir na curadoria","hotend":"definir na curadoria","probe":"Tap/Klicky/definir na curadoria","bed":"500mm estimado","kinematics":"corexy"}' AS components_json
  UNION ALL SELECT 'voron-phoenix-600', 'Voron Phoenix 600mm draft',
         '{"x":600,"y":600,"z":600}',
         '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"Stealthburner/definir na curadoria","extruder":"Clockwork/definir na curadoria","hotend":"definir na curadoria","probe":"Tap/Klicky/definir na curadoria","bed":"600mm estimado","kinematics":"corexy"}'
) seed
JOIN catalog_printer_models m ON m.slug = 'voron-phoenix'
JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id AND mf.slug = 'voron-design'
ON CONFLICT(model_id, slug) DO UPDATE SET
  name = excluded.name,
  build_volume_json = excluded.build_volume_json,
  components_json = excluded.components_json,
  firmware_family = excluded.firmware_family,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;
