INSERT INTO catalog_manufacturers (slug, name, trust_state, source)
VALUES
  ('zero-g', 'ZeroG', 'community', 'printora_seed_pkg49_breadth'),
  ('railcore-labs', 'RailCore Labs', 'community', 'printora_seed_pkg49_breadth'),
  ('seckit', 'SecKit', 'community', 'printora_seed_pkg49_breadth'),
  ('blv-projects', 'BLV Projects', 'community', 'printora_seed_pkg49_breadth'),
  ('hypercube', 'HyperCube', 'community', 'printora_seed_pkg49_breadth'),
  ('d-bot', 'D-Bot', 'community', 'printora_seed_pkg49_breadth'),
  ('v-king', 'V-King', 'community', 'printora_seed_pkg49_breadth'),
  ('croxy', 'CroXY', 'community', 'printora_seed_pkg49_breadth'),
  ('rook', 'Rook', 'community', 'printora_seed_pkg49_breadth'),
  ('positron', 'Positron', 'community', 'printora_seed_pkg49_breadth'),
  ('the-100', 'The 100', 'community', 'printora_seed_pkg49_breadth'),
  ('doron', 'Doron', 'community', 'printora_seed_pkg49_breadth'),
  ('snakeoilxy', 'SnakeOilXY', 'draft', 'printora_seed_pkg49_breadth_uncertain'),
  ('jubilee-machine', 'Machine Agency', 'community', 'printora_seed_pkg49_breadth')
ON CONFLICT(slug) DO UPDATE SET
  name = excluded.name,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_models (manufacturer_id, slug, name, kinematics, trust_state, source)
SELECT mf.id, seed.slug, seed.name, seed.kinematics, seed.trust_state, seed.source
FROM (
  SELECT 'voron-design' AS manufacturer_slug, 'voron-0-1' AS slug, 'Voron 0.1' AS name, 'corexy' AS kinematics, 'official' AS trust_state, 'printora_seed_pkg49_breadth' AS source
  UNION ALL SELECT 'voron-design', 'voron-1-8', 'Voron 1.8', 'corexy', 'official', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'voron-design', 'voron-legacy', 'Voron Legacy', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'rat-rig', 'v-core-4', 'V-Core 4', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'annex-engineering', 'k2', 'K2', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'annex-engineering', 'engineering-printer', 'Annex Engineering Printer', 'corexy', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'zero-g', 'mercury-one-1', 'Mercury One.1', 'corexy_conversion', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'zero-g', 'hydra', 'Hydra', 'corexy_conversion', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'railcore-labs', 'railcore-ii', 'RailCore II', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'seckit', 'sk-go', 'SK-Go', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'seckit', 'tank', 'Tank', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'blv-projects', 'blv-mgn-cube', 'BLV MGN Cube', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'hypercube', 'hypercube-evolution', 'HyperCube Evolution', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'd-bot', 'd-bot-corexy', 'D-Bot CoreXY', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'v-king', 'v-king-corexy', 'V-King CoreXY', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'croxy', 'croxy', 'CroXY', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'rook', 'rook-mk1', 'Rook MK1', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'positron', 'positron-v3', 'Positron V3', 'folding_cartesian', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'the-100', 'the-100', 'The 100', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'doron', 'doron-velta', 'Doron Velta', 'corexy', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'snakeoilxy', 'snakeoilxy', 'SnakeOilXY', 'corexy', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'jubilee-machine', 'jubilee', 'Jubilee', 'toolchanger_corexy', 'community', 'printora_seed_pkg49_breadth'
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
  SELECT 'voron-design' AS manufacturer_slug, 'voron-0-1' AS model_slug, 'voron-0-1-120' AS slug, 'Voron 0.1 120mm' AS name,
         '{"x":120,"y":120,"z":120}' AS build_volume_json,
         '{"mainboard":"BTT SKR Pico/SKR Mini comum","mcu":"RP2040/STM32 conforme placa","toolhead":"Mini Afterburner/Mini Stealthburner conforme build","extruder":"Clockwork/Mini extruder conforme build","hotend":"V6/Revo Voron conforme build","probe":"Klicky/indutivo/manual conforme build","bed":"120mm","kinematics":"corexy"}' AS components_json,
         'official' AS trust_state, 'printora_seed_pkg49_breadth' AS source
  UNION ALL SELECT 'voron-design', 'voron-1-8', 'voron-1-8-250', 'Voron 1.8 250mm', '{"x":250,"y":250,"z":250}', '{"mainboard":"BTT Octopus/SKR conforme build","mcu":"STM32/RP2040 conforme placa","toolhead":"Afterburner/Stealthburner conforme build","extruder":"Clockwork/BMG conforme build","hotend":"Dragon/Revo/V6 conforme build","probe":"Klicky/indutivo conforme build","bed":"250mm","kinematics":"corexy"}', 'official', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'voron-design', 'voron-1-8', 'voron-1-8-300', 'Voron 1.8 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"BTT Octopus/SKR conforme build","mcu":"STM32/RP2040 conforme placa","toolhead":"Afterburner/Stealthburner conforme build","extruder":"Clockwork/BMG conforme build","hotend":"Dragon/Revo/V6 conforme build","probe":"Klicky/indutivo conforme build","bed":"300mm","kinematics":"corexy"}', 'official', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'voron-design', 'voron-1-8', 'voron-1-8-350', 'Voron 1.8 350mm', '{"x":350,"y":350,"z":350}', '{"mainboard":"BTT Octopus/SKR conforme build","mcu":"STM32/RP2040 conforme placa","toolhead":"Afterburner/Stealthburner conforme build","extruder":"Clockwork/BMG conforme build","hotend":"Dragon/Revo/V6 conforme build","probe":"Klicky/indutivo conforme build","bed":"350mm","kinematics":"corexy"}', 'official', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'voron-design', 'voron-legacy', 'voron-legacy-250', 'Voron Legacy 250mm', '{"x":250,"y":250,"z":250}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"Afterburner/Stealthburner conforme build","extruder":"Clockwork/BMG conforme build","hotend":"V6/Revo/Dragon conforme build","probe":"Klicky/indutivo conforme build","bed":"250mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'rat-rig', 'v-core-4', 'v-core-4-300', 'RatRig V-Core 4 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"RatRig/BTT conforme kit","mcu":"STM32/RP2040 conforme placa","toolhead":"RatRig toolhead ou EVA conforme build","extruder":"Orbiter/BMG conforme build","hotend":"Rapido/Dragon/Revo conforme build","probe":"Beacon/SuperPinda/Tap/Klicky conforme build","bed":"300mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'rat-rig', 'v-core-4', 'v-core-4-400', 'RatRig V-Core 4 400mm', '{"x":400,"y":400,"z":400}', '{"mainboard":"RatRig/BTT conforme kit","mcu":"STM32/RP2040 conforme placa","toolhead":"RatRig toolhead ou EVA conforme build","extruder":"Orbiter/BMG conforme build","hotend":"Rapido/Dragon/Revo conforme build","probe":"Beacon/SuperPinda/Tap/Klicky conforme build","bed":"400mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'rat-rig', 'v-core-4', 'v-core-4-500', 'RatRig V-Core 4 500mm', '{"x":500,"y":500,"z":500}', '{"mainboard":"RatRig/BTT conforme kit","mcu":"STM32/RP2040 conforme placa","toolhead":"RatRig toolhead ou EVA conforme build","extruder":"Orbiter/BMG conforme build","hotend":"Rapido/Dragon/Revo conforme build","probe":"Beacon/SuperPinda/Tap/Klicky conforme build","bed":"500mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'annex-engineering', 'k2', 'annex-k2-300', 'Annex K2 300mm draft', '{"x":300,"y":300,"z":300}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"Annex conforme build","extruder":"Sherpa/Orbiter conforme build","hotend":"V6/Rapido/Revo conforme build","probe":"Klicky/indutivo conforme build","bed":"300mm estimado","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'zero-g', 'mercury-one-1', 'mercury-one-1-ender-5', 'ZeroG Mercury One.1 Ender 5 conversion', '{"x":235,"y":235,"z":250}', '{"mainboard":"placa Klipper conforme conversão","mcu":"conforme placa","toolhead":"Mercury/EVA conforme build","extruder":"Orbiter/BMG conforme build","hotend":"V6/Rapido/Revo conforme build","probe":"BLTouch/Klicky/Beacon conforme build","bed":"Ender 5 235mm","kinematics":"corexy_conversion"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'zero-g', 'hydra', 'hydra-ender-5-plus', 'ZeroG Hydra Ender 5 Plus conversion', '{"x":350,"y":350,"z":400}', '{"mainboard":"placa Klipper conforme conversão","mcu":"conforme placa","toolhead":"Hydra/Mercury conforme build","extruder":"Orbiter/BMG conforme build","hotend":"V6/Rapido/Revo conforme build","probe":"BLTouch/Klicky/Beacon conforme build","bed":"Ender 5 Plus 350mm","kinematics":"corexy_conversion"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'railcore-labs', 'railcore-ii', 'railcore-ii-250zl', 'RailCore II 250ZL', '{"x":250,"y":250,"z":330}', '{"mainboard":"Duet/placa Klipper conforme build","mcu":"conforme placa","toolhead":"RailCore/EVA conforme build","extruder":"BMG/Orbiter conforme build","hotend":"V6/Dragon/Rapido conforme build","probe":"BLTouch/indutivo conforme build","bed":"250mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'railcore-labs', 'railcore-ii', 'railcore-ii-300zl', 'RailCore II 300ZL', '{"x":300,"y":300,"z":330}', '{"mainboard":"Duet/placa Klipper conforme build","mcu":"conforme placa","toolhead":"RailCore/EVA conforme build","extruder":"BMG/Orbiter conforme build","hotend":"V6/Dragon/Rapido conforme build","probe":"BLTouch/indutivo conforme build","bed":"300mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'seckit', 'sk-go', 'seckit-sk-go-300', 'SecKit SK-Go 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"SK-Go/EVA conforme build","extruder":"BMG/Orbiter conforme build","hotend":"V6/Dragon/Rapido conforme build","probe":"BLTouch/Klicky/indutivo conforme build","bed":"300mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'seckit', 'tank', 'seckit-tank-400', 'SecKit Tank 400mm draft', '{"x":400,"y":400,"z":400}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"400mm estimado","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'blv-projects', 'blv-mgn-cube', 'blv-mgn-cube-300', 'BLV MGN Cube 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"BLV/EVA conforme build","extruder":"BMG/Orbiter conforme build","hotend":"V6/Dragon conforme build","probe":"BLTouch/indutivo conforme build","bed":"300mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'hypercube', 'hypercube-evolution', 'hypercube-evolution-300', 'HyperCube Evolution 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"RAMPS/32-bit Klipper conforme build","mcu":"AVR/STM32 conforme placa","toolhead":"HyperCube/EVA conforme build","extruder":"Bowden/BMG/Orbiter conforme build","hotend":"V6/Dragon conforme build","probe":"BLTouch/indutivo/manual conforme build","bed":"300mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'd-bot', 'd-bot-corexy', 'd-bot-corexy-300', 'D-Bot CoreXY 300mm', '{"x":300,"y":300,"z":300}', '{"mainboard":"RAMPS/32-bit Klipper conforme build","mcu":"AVR/STM32 conforme placa","toolhead":"D-Bot/EVA conforme build","extruder":"Bowden/BMG conforme build","hotend":"V6 conforme build","probe":"BLTouch/indutivo/manual conforme build","bed":"300mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'v-king', 'v-king-corexy', 'v-king-corexy-400', 'V-King CoreXY 400mm draft', '{"x":400,"y":400,"z":400}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"400mm estimado","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'croxy', 'croxy', 'croxy-300', 'CroXY 300mm draft', '{"x":300,"y":300,"z":300}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"300mm estimado","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'rook', 'rook-mk1', 'rook-mk1-180', 'Rook MK1 180mm', '{"x":180,"y":180,"z":180}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"Rook toolhead conforme build","extruder":"direct drive compacto conforme build","hotend":"V6/Revo conforme build","probe":"manual/indutivo conforme build","bed":"180mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'positron', 'positron-v3', 'positron-v3', 'Positron V3', '{"x":180,"y":180,"z":180}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"toolhead Positron conforme build","extruder":"compacto conforme build","hotend":"compacto conforme build","probe":"manual/definir na curadoria","bed":"180mm estimado","kinematics":"folding_cartesian"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'the-100', 'the-100', 'the-100-100', 'The 100 100mm', '{"x":100,"y":100,"z":100}', '{"mainboard":"placa Klipper 32-bit conforme build","mcu":"conforme placa","toolhead":"toolhead compacto conforme build","extruder":"direct drive compacto conforme build","hotend":"V6/Revo conforme build","probe":"manual/definir na curadoria","bed":"100mm","kinematics":"corexy"}', 'community', 'printora_seed_pkg49_breadth'
  UNION ALL SELECT 'doron', 'doron-velta', 'doron-velta-180', 'Doron Velta 180mm draft', '{"x":180,"y":180,"z":180}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"180mm estimado","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'snakeoilxy', 'snakeoilxy', 'snakeoilxy-250', 'SnakeOilXY 250mm draft', '{"x":250,"y":250,"z":250}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"250mm estimado","kinematics":"corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
  UNION ALL SELECT 'jubilee-machine', 'jubilee', 'jubilee-machine-toolchanger', 'Machine Agency Jubilee Toolchanger draft', '{"x":300,"y":300,"z":300}', '{"mainboard":"Duet/placa Klipper conforme conversão","mcu":"definir na curadoria","toolhead":"multi-tool/toolchanger","extruder":"por ferramenta","hotend":"por ferramenta","probe":"definir na curadoria","bed":"300mm estimado","kinematics":"toolchanger_corexy"}', 'draft', 'printora_seed_pkg49_breadth_uncertain'
) seed
JOIN catalog_manufacturers mf ON mf.slug = seed.manufacturer_slug
JOIN catalog_printer_models m ON m.manufacturer_id = mf.id AND m.slug = seed.model_slug
ON CONFLICT(model_id, slug) DO UPDATE SET
  name = excluded.name,
  build_volume_json = excluded.build_volume_json,
  components_json = excluded.components_json,
  firmware_family = excluded.firmware_family,
  trust_state = excluded.trust_state,
  source = excluded.source,
  updated_at = CURRENT_TIMESTAMP;
