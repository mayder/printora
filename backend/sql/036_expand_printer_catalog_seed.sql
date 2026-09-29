INSERT INTO catalog_manufacturers (slug, name, trust_state, source)
VALUES
  ('rat-rig', 'RatRig', 'official', 'printora_seed_pkg49'),
  ('vzbot', 'VzBot', 'community', 'printora_seed_pkg49'),
  ('annex-engineering', 'Annex Engineering', 'community', 'printora_seed_pkg49'),
  ('hevort', 'HevORT', 'community', 'printora_seed_pkg49'),
  ('jubilee', 'Jubilee', 'community', 'printora_seed_pkg49'),
  ('printers-for-ants', 'Printers For Ants', 'community', 'printora_seed_pkg49')
ON CONFLICT(slug) DO UPDATE SET
  name = excluded.name,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_models (manufacturer_id, slug, name, kinematics, trust_state, source)
SELECT mf.id, seed.slug, seed.name, seed.kinematics, seed.trust_state, 'printora_seed_pkg49'
FROM (
  SELECT 'voron-design' AS manufacturer_slug, 'voron-trident' AS slug, 'Voron Trident' AS name, 'corexy' AS kinematics, 'official' AS trust_state
  UNION ALL SELECT 'voron-design', 'voron-switchwire', 'Voron Switchwire', 'corexz', 'official'
  UNION ALL SELECT 'rat-rig', 'v-core-3', 'V-Core 3', 'corexy', 'official'
  UNION ALL SELECT 'rat-rig', 'v-minion', 'V-Minion', 'cartesian_bedslinger', 'community'
  UNION ALL SELECT 'vzbot', 'vzbot', 'VzBot', 'corexy', 'community'
  UNION ALL SELECT 'annex-engineering', 'k3', 'K3', 'corexy', 'community'
  UNION ALL SELECT 'hevort', 'hevort', 'HevORT', 'corexy', 'community'
  UNION ALL SELECT 'jubilee', 'jubilee', 'Jubilee', 'toolchanger_corexy', 'community'
  UNION ALL SELECT 'printers-for-ants', 'micron-plus', 'Micron+', 'corexy', 'community'
  UNION ALL SELECT 'printers-for-ants', 'salad-fork', 'Salad Fork', 'corexy', 'community'
) seed
JOIN catalog_manufacturers mf ON mf.slug = seed.manufacturer_slug
ON CONFLICT(manufacturer_id, slug) DO UPDATE SET
  name = excluded.name,
  kinematics = excluded.kinematics,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_variants (
  model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source
)
SELECT m.id, seed.slug, seed.name, seed.build_volume_json, seed.components_json, 'klipper', seed.trust_state, seed.source
FROM (
  SELECT 'voron-2-4' AS model_slug, 'voron-2-4-r2-250' AS slug, 'Voron 2.4 R2 250mm' AS name,
         '{"x":250,"y":250,"z":250}' AS build_volume_json,
         '{"mainboard":"BTT Octopus/Octopus Pro","mcu":"STM32/RP2040 conforme placa","toolhead":"Stealthburner","extruder":"Clockwork 2","hotend":"Dragon/Revo/V6","probe":"Tap/Klicky/Indutivo","bed":"250mm","kinematics":"corexy"}' AS components_json,
         'official' AS trust_state, 'printora_seed_pkg49' AS source
  UNION ALL SELECT 'voron-trident', 'voron-trident-250', 'Voron Trident 250mm', '{"x":250,"y":250,"z":250}', '{"mainboard":"BTT Octopus/Octopus Pro","mcu":"STM32 conforme placa","toolhead":"Stealthburner","extruder":"Clockwork 2","hotend":"Dragon/Revo/V6","probe":"Tap/Klicky/Indutivo","bed":"250mm fixa","kinematics":"corexy"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'voron-trident', 'voron-trident-300', 'Voron Trident 300mm', '{"x":300,"y":300,"z":250}', '{"mainboard":"BTT Octopus/Octopus Pro","mcu":"STM32 conforme placa","toolhead":"Stealthburner","extruder":"Clockwork 2","hotend":"Dragon/Revo/V6","probe":"Tap/Klicky/Indutivo","bed":"300mm fixa","kinematics":"corexy"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'voron-trident', 'voron-trident-350', 'Voron Trident 350mm', '{"x":350,"y":350,"z":250}', '{"mainboard":"BTT Octopus/Octopus Pro","mcu":"STM32 conforme placa","toolhead":"Stealthburner","extruder":"Clockwork 2","hotend":"Dragon/Revo/V6","probe":"Tap/Klicky/Indutivo","bed":"350mm fixa","kinematics":"corexy"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'voron-switchwire', 'voron-switchwire-250', 'Voron Switchwire 250mm', '{"x":250,"y":210,"z":250}', '{"mainboard":"BTT SKR/Octopus conforme build","mcu":"STM32/RP2040 conforme placa","toolhead":"Stealthburner/Afterburner","extruder":"Clockwork/BMG conforme build","hotend":"V6/Revo/Dragon","probe":"Klicky/Indutivo","bed":"250x210mm","kinematics":"corexz"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'v-core-3', 'v-core-3-300', 'RatRig V-Core 3 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"BTT Octopus/Octopus Pro comum","mcu":"STM32 conforme placa","toolhead":"toolhead RatRig ou EVA/Orbiter conforme build","extruder":"Orbiter/BMG conforme build","hotend":"Rapido/Dragon/Revo conforme build","probe":"SuperPinda/Tap/Klicky conforme build","bed":"300mm","kinematics":"corexy"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'v-core-3', 'v-core-3-400', 'RatRig V-Core 3 400mm', '{"x":400,"y":400,"z":400}', '{"mainboard":"BTT Octopus/Octopus Pro comum","mcu":"STM32 conforme placa","toolhead":"toolhead RatRig ou EVA/Orbiter conforme build","extruder":"Orbiter/BMG conforme build","hotend":"Rapido/Dragon/Revo conforme build","probe":"SuperPinda/Tap/Klicky conforme build","bed":"400mm","kinematics":"corexy"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'v-core-3', 'v-core-3-500', 'RatRig V-Core 3 500mm', '{"x":500,"y":500,"z":500}', '{"mainboard":"BTT Octopus/Octopus Pro comum","mcu":"STM32 conforme placa","toolhead":"toolhead RatRig ou EVA/Orbiter conforme build","extruder":"Orbiter/BMG conforme build","hotend":"Rapido/Dragon/Revo conforme build","probe":"SuperPinda/Tap/Klicky conforme build","bed":"500mm","kinematics":"corexy"}', 'official', 'printora_seed_pkg49'
  UNION ALL SELECT 'v-minion', 'v-minion-180', 'RatRig V-Minion 180mm', '{"x":180,"y":180,"z":180}', '{"mainboard":"placa 32-bit Klipper comum","mcu":"conforme placa","toolhead":"toolhead V-Minion/EVA conforme build","extruder":"Orbiter/BMG conforme build","hotend":"V6/Revo/Rapido conforme build","probe":"BLTouch/indutivo/manual conforme build","bed":"180mm","kinematics":"cartesian_bedslinger"}', 'community', 'printora_seed_pkg49'
  UNION ALL SELECT 'vzbot', 'vzbot-235', 'VzBot 235', '{"x":235,"y":235,"z":235}', '{"mainboard":"BTT Octopus/Manta comum","mcu":"STM32/RP2040 conforme placa","toolhead":"VzBot/CNC toolhead conforme build","extruder":"Sherpa/Orbiter conforme build","hotend":"Rapido/Dragon conforme build","probe":"Beacon/Tap/Klicky/Indutivo conforme build","bed":"235mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49'
  UNION ALL SELECT 'vzbot', 'vzbot-330', 'VzBot 330', '{"x":330,"y":330,"z":330}', '{"mainboard":"BTT Octopus/Manta comum","mcu":"STM32/RP2040 conforme placa","toolhead":"VzBot/CNC toolhead conforme build","extruder":"Sherpa/Orbiter conforme build","hotend":"Rapido/Dragon conforme build","probe":"Beacon/Tap/Klicky/Indutivo conforme build","bed":"330mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49'
  UNION ALL SELECT 'k3', 'annex-k3-180', 'Annex K3 180mm', '{"x":180,"y":180,"z":180}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"toolhead Annex conforme build","extruder":"Sherpa/Orbiter conforme build","hotend":"V6/Revo/Rapido conforme build","probe":"Klicky/Indutivo conforme build","bed":"180mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49'
  UNION ALL SELECT 'hevort', 'hevort-500', 'HevORT 500 draft', '{"x":500,"y":500,"z":500}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"500mm estimado por variante","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_uncertain'
  UNION ALL SELECT 'jubilee', 'jubilee-toolchanger', 'Jubilee Toolchanger draft', '{"x":300,"y":300,"z":300}', '{"mainboard":"Duet/placa Klipper conforme conversão","mcu":"definir na curadoria","toolhead":"multi-tool/toolchanger","extruder":"por ferramenta","hotend":"por ferramenta","probe":"definir na curadoria","bed":"300mm estimado","kinematics":"toolchanger_corexy"}', 'draft', 'printora_seed_pkg49_uncertain'
  UNION ALL SELECT 'micron-plus', 'micron-plus-180', 'Micron+ 180mm', '{"x":180,"y":180,"z":180}', '{"mainboard":"BTT SKR Pico/Manta comum","mcu":"RP2040/STM32 conforme placa","toolhead":"Mini Stealthburner","extruder":"Clockwork 2/Sherpa Mini conforme build","hotend":"Revo/V6 conforme build","probe":"Klicky/Beacon conforme build","bed":"180mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49'
  UNION ALL SELECT 'salad-fork', 'salad-fork-160', 'Salad Fork 160mm', '{"x":160,"y":160,"z":160}', '{"mainboard":"BTT SKR Pico/Manta comum","mcu":"RP2040/STM32 conforme placa","toolhead":"Mini Stealthburner/Dragonburner conforme build","extruder":"Sherpa Mini/Clockwork 2 conforme build","hotend":"Revo/V6 conforme build","probe":"Klicky/Beacon conforme build","bed":"160mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49'
) seed
JOIN catalog_printer_models m ON m.slug = seed.model_slug
ON CONFLICT(model_id, slug) DO UPDATE SET
  name = excluded.name,
  build_volume_json = excluded.build_volume_json,
  components_json = excluded.components_json,
  firmware_family = excluded.firmware_family,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;
