ALTER TABLE catalog_printer_models ADD COLUMN detail_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE catalog_printer_models ADD COLUMN source_links_json TEXT NOT NULL DEFAULT '{}';

UPDATE catalog_manufacturers
SET logo_url = CASE slug
  WHEN 'rat-rig' THEN NULL
  WHEN 'blv-projects' THEN NULL
  WHEN 'doron' THEN NULL
  WHEN 'magpie-printer' THEN NULL
  WHEN 'icarus3d' THEN NULL
  ELSE logo_url
END
WHERE slug IN ('rat-rig', 'blv-projects', 'doron', 'magpie-printer', 'icarus3d');

UPDATE catalog_printer_models
SET image_url = NULL
WHERE slug IN ('v-core-3', 'v-core-4', 'v-minion', 'doron-velta', 'magpie', 'dynasty');

UPDATE catalog_manufacturers
SET repository_url = CASE slug
  WHEN 'snakeoilxy' THEN 'https://github.com/SnakeOilXY/SnakeOil-XY'
  ELSE repository_url
END,
logo_url = CASE slug
  WHEN 'snakeoilxy' THEN 'https://github.com/SnakeOilXY.png'
  ELSE logo_url
END
WHERE slug = 'snakeoilxy';

INSERT INTO catalog_manufacturers (slug, name, trust_state, source, website_url, repository_url, logo_url, summary)
VALUES
  ('maybecube', 'MaybeCube', 'draft', 'catalog_seed_uncertain', NULL, 'https://github.com/martinbudden/MaybeCube', NULL, 'Projeto CoreXY aberto e configurável publicado no GitHub; precisa de revisão técnica antes de promoção.'),
  ('rolohaun-design', 'Rolohaun Design', 'community', 'catalog_seed', 'https://www.printables.com/@rolohaun', 'https://github.com/rolohaun', NULL, 'Autor dos projetos Rook/Bastion, com arquivos públicos em GitHub e Printables.'),
  ('mszturc', 'MSzturc', 'community', 'catalog_seed', NULL, 'https://github.com/MSzturc', 'https://github.com/MSzturc.png', 'Autor do projeto T250, impressora aberta de alta velocidade publicada com BOM, configs e documentação.'),
  ('tiny3dp', 'Tiny3DP', 'draft', 'catalog_seed_uncertain', 'https://www.instagram.com/tiny3dp/', 'https://github.com/c-bata/SM-100', 'https://github.com/c-bata.png', 'Autor do SM-100, CoreXY compacto experimental para espaços pequenos.'),
  ('open-lab-starter-kit', 'Open Lab Starter Kit', 'community', 'catalog_seed', 'https://www.inmachines.net/', 'https://github.com/Open-Lab-Starter-Kit', 'https://github.com/Open-Lab-Starter-Kit.png', 'Família de máquinas open source OLSK com versões Small e Large de impressoras 3D.'),
  ('babycube', 'BabyCube', 'community', 'catalog_seed', NULL, 'https://github.com/martinbudden/BabyCube', NULL, 'Projeto CoreXY compacto de Martin Budden, com instruções de montagem e BOM publicados.')
ON CONFLICT(slug) DO UPDATE SET
  name = excluded.name,
  trust_state = excluded.trust_state,
  source = excluded.source,
  website_url = excluded.website_url,
  repository_url = excluded.repository_url,
  logo_url = excluded.logo_url,
  summary = excluded.summary,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_models (
  manufacturer_id, slug, name, kinematics, trust_state, source, website_url, repository_url, documentation_url, bom_url, description, curation_notes, detail_json, source_links_json
)
SELECT mf.id, seed.slug, seed.name, seed.kinematics, seed.trust_state, seed.source, seed.website_url, seed.repository_url, seed.documentation_url, seed.bom_url, seed.description, seed.curation_notes, seed.detail_json, seed.source_links_json
FROM (
  SELECT 'rat-rig' AS manufacturer_slug, 'v-chonk' AS slug, 'V-Chonk' AS name, 'corexy' AS kinematics, 'draft' AS trust_state, 'catalog_seed_uncertain' AS source,
         'https://github.com/Rat-Rig/V-Chonk' AS website_url, 'https://github.com/Rat-Rig/V-Chonk' AS repository_url, NULL AS documentation_url, NULL AS bom_url,
         'Rat Rig V-Chonk é uma impressora CoreXY quase totalmente impressa em 3D, catalogada como beta/draft até revisão completa.' AS description,
         'GitHub indica v0.4 BETA e volume cúbico de 180 mm; manter como draft até revisar BOM e estado de release.' AS curation_notes,
         '{"release":"v0.4 beta","frame":"quase totalmente impresso em 3D","motion":"CoreXY","volume":"180 x 180 x 180 mm","license":"CC-BY-SA-4.0","confidence":"fonte primaria GitHub"}' AS detail_json,
         '{"github":"https://github.com/Rat-Rig/V-Chonk"}' AS source_links_json
  UNION ALL SELECT 'annex-engineering', 'k1', 'K1 / Masherbrum', 'corexy', 'community', 'catalog_seed',
         'https://github.com/Annex-Engineering/Masherbrum-K1', 'https://github.com/Annex-Engineering/Masherbrum-K1', NULL, NULL,
         'Masherbrum/K1 é uma impressora FDM de formato médio da Annex Engineering, direct drive e fechada.',
         'Fonte primária GitHub confirmada; revisar variações e BOM antes de promover para official.',
         '{"release":"projeto publico","frame":"formato medio fechado","motion":"CoreXY/CartesianXY conforme documentacao Annex","extrusion":"direct drive","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/Annex-Engineering/Masherbrum-K1"}'
  UNION ALL SELECT 'annex-engineering', 'k2', 'K2 / Chhogori', 'corexy', 'community', 'catalog_seed',
         'https://github.com/Annex-Engineering/Chhogori-K2', 'https://github.com/Annex-Engineering/Chhogori-K2', NULL, NULL,
         'Chhogori/K2 é uma impressora FDM de formato médio da Annex Engineering, direct drive e fechada.',
         'Atualiza o cadastro K2 para a fonte primária Chhogori-K2; revisar variações e BOM antes de official.',
         '{"release":"projeto publico","frame":"formato medio fechado","motion":"CoreXY/CartesianXY conforme documentacao Annex","extrusion":"direct drive","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/Annex-Engineering/Chhogori-K2"}'
  UNION ALL SELECT 'rolohaun-design', 'bastion', 'Bastion', 'corexy', 'community', 'catalog_seed',
         'https://www.printables.com/model/748800-bastion-3d-printer', NULL, NULL, NULL,
         'Bastion é a evolução do Rook 180, publicada no Printables como impressora CoreXY de frame impresso.',
         'Fonte primária pública em Printables; GitHub específico não confirmado neste seed.',
         '{"release":"publicado no Printables","frame":"frame impresso","motion":"CoreXY","lineage":"evolucao do Rook 180","confidence":"fonte primaria Printables"}',
         '{"printables":"https://www.printables.com/model/748800-bastion-3d-printer"}'
  UNION ALL SELECT 'maybecube', 'maybecube', 'MaybeCube', 'corexy', 'draft', 'catalog_seed_uncertain',
         'https://github.com/martinbudden/MaybeCube', 'https://github.com/martinbudden/MaybeCube', NULL, NULL,
         'MaybeCube é uma impressora CoreXY aberta e configurável, publicada no GitHub.',
         'GitHub confirma projeto e dimensões gerais; manter draft até revisar BOM e variantes.',
         '{"release":"projeto publico","frame":"configuravel","motion":"CoreXY","standard":"MC350","build_volume":"aprox. 225 x 225 x 200 mm no MC350","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/martinbudden/MaybeCube"}'
  UNION ALL SELECT 'babycube', 'babycube', 'BabyCube', 'corexy', 'community', 'catalog_seed',
         'https://github.com/martinbudden/BabyCube', 'https://github.com/martinbudden/BabyCube', NULL, NULL,
         'BabyCube é uma impressora CoreXY compacta com frame impresso, instruções de montagem e BOM publicados.',
         'Fonte primária informa volume alvo de aproximadamente 75 mm; revisar variantes antes de promoção para official.',
         '{"release":"projeto publico","frame":"impresso em 3D","motion":"CoreXY","build_volume":"aprox. 75 x 75 x 75 mm","envelope":"aprox. 248 x 272 x 211 mm sem spool holder","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/martinbudden/BabyCube"}'
  UNION ALL SELECT 'mszturc', 't250', 'T250', 'corexy', 'community', 'catalog_seed',
         'https://github.com/MSzturc/T250', 'https://github.com/MSzturc/T250', NULL, 'https://github.com/MSzturc/T250/tree/main/BOM',
         'T250 é uma impressora 3D aberta de alto desempenho, construída para velocidade e qualidade de impressão.',
         'GitHub informa volume, firmware THEOS/Klipper e recursos; manter community até revisar hardware por versão.',
         '{"release":"v1.0-final no repositorio","motion":"CoreXY","build_volume":"192 x 212 x 175 mm","firmware":"THEOS / Klipper","focus":"alta velocidade","license":"CC-BY-NC-SA-4.0","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/MSzturc/T250","bom":"https://github.com/MSzturc/T250/tree/main/BOM"}'
  UNION ALL SELECT 'tiny3dp', 'sm-100', 'SM-100', 'corexy', 'draft', 'catalog_seed_uncertain',
         'https://github.com/c-bata/SM-100', 'https://github.com/c-bata/SM-100', NULL, NULL,
         'SM-100 é uma impressora CoreXY compacta open source desenhada para apartamentos pequenos.',
         'Repositório marca a versão como experimental e ainda sem BOM/manual completos; manter draft.',
         '{"release":"experimental","motion":"CoreXY","status":"BOM e instrucoes completas ainda planejadas","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/c-bata/SM-100","instagram":"https://www.instagram.com/tiny3dp/"}'
  UNION ALL SELECT 'open-lab-starter-kit', 'olsk-small-3d-printer', 'OLSK Small 3D Printer', 'corexy', 'community', 'catalog_seed',
         'https://github.com/Open-Lab-Starter-Kit/OLSK-Small-3D-Printer', 'https://github.com/Open-Lab-Starter-Kit/OLSK-Small-3D-Printer', 'https://open-lab-starter-kit.github.io/OLSK-Small-3D-Printer/Assembly_Manual/', 'https://github.com/Open-Lab-Starter-Kit/OLSK-Small-3D-Printer/blob/main/OLSK_Small_3D_Printer_V3-BOM.xlsx',
         'OLSK Small é uma impressora CoreXY open source de mesa, fechada, com Klipper customizado e documentação pública.',
         'Fonte primária GitHub traz especificações V3, BOM, firmware e manual; revisar nomes de versões antes de official.',
         '{"release":"V3","motion":"CoreXY","build_volume":"235 x 235 x 235 mm","firmware":"Klipper customizado","features":"scanner eddy current, acelerometro, tela 7 polegadas","license":"CERN-OHL-W-2.0 / CC-BY-SA-4.0","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/Open-Lab-Starter-Kit/OLSK-Small-3D-Printer","manual":"https://open-lab-starter-kit.github.io/OLSK-Small-3D-Printer/Assembly_Manual/","bom":"https://github.com/Open-Lab-Starter-Kit/OLSK-Small-3D-Printer/blob/main/OLSK_Small_3D_Printer_V3-BOM.xlsx"}'
  UNION ALL SELECT 'open-lab-starter-kit', 'olsk-large-3d-printer', 'OLSK Large 3D Printer', 'corexy_flying_gantry', 'community', 'catalog_seed',
         'https://github.com/Open-Lab-Starter-Kit/OLSK-Large-3D-Printer', 'https://github.com/Open-Lab-Starter-Kit/OLSK-Large-3D-Printer', 'https://open-lab-starter-kit.github.io/OLSK-Large-3D-Printer/Assembly_Manual/', NULL,
         'OLSK Large é uma impressora 3D open source de grande formato com CoreXY flying gantry e Klipper customizado.',
         'Fonte primária GitHub traz volume e especificações V3; revisar BOM linkado antes de official.',
         '{"release":"V3","motion":"CoreXY flying gantry","build_volume":"1000 x 1000 x 1300 mm","firmware":"Klipper customizado","features":"quad point self-leveling, camara fechada, scanner eddy current","confidence":"fonte primaria GitHub"}',
         '{"github":"https://github.com/Open-Lab-Starter-Kit/OLSK-Large-3D-Printer","manual":"https://open-lab-starter-kit.github.io/OLSK-Large-3D-Printer/Assembly_Manual/"}'
) seed
JOIN catalog_manufacturers mf ON mf.slug = seed.manufacturer_slug
ON CONFLICT(manufacturer_id, slug) DO UPDATE SET
  name = excluded.name,
  kinematics = excluded.kinematics,
  trust_state = excluded.trust_state,
  source = excluded.source,
  website_url = excluded.website_url,
  repository_url = excluded.repository_url,
  documentation_url = excluded.documentation_url,
  bom_url = excluded.bom_url,
  description = excluded.description,
  curation_notes = excluded.curation_notes,
  detail_json = excluded.detail_json,
  source_links_json = excluded.source_links_json,
  updated_at = CURRENT_TIMESTAMP;

UPDATE catalog_printer_models
SET detail_json = CASE slug
  WHEN 'v-core-3' THEN '{"release":"linha V-Core 3","frame":"aluminio modular","motion":"CoreXY","known_sizes":"300, 400 e 500 mm no seed","firmware":"Klipper/RatOS em builds comuns","confidence":"site e GitHub publicos"}'
  WHEN 'v-core-4' THEN '{"release":"linha V-Core 4","frame":"aluminio modular","motion":"CoreXY","known_sizes":"300, 400 e 500 mm no seed","firmware":"Klipper/RatOS em builds comuns","confidence":"site/wiki publicos"}'
  WHEN 'vzbot' THEN '{"release":"Vz-235 e Vz-330","origin":"base TronXY X5S/X5SA no Vz-330","motion":"CoreXY/AWD em builds especificos","focus":"alta velocidade","confidence":"site, docs e GitHub publicos"}'
  WHEN 'k3' THEN '{"release":"Gasherbrum K3 release 1.1","frame":"pequeno formato, aberto ou fechado","motion":"CartesianXY/CoreXY conforme repositorio","extrusion":"direct drive","confidence":"GitHub Annex"}'
  WHEN 'salad-fork' THEN '{"release":"projeto Printers For Ants","frame":"1515 reduzido tipo Trident","motion":"CoreXY","known_sizes":"120, 160 e 180 mm","probe":"Klicky default, Boop opcional segundo README","confidence":"GitHub PrintersForAnts"}'
  WHEN 'railcore-ii' THEN '{"release":"RailCore II 300ZL/ZLT","motion":"CoreXY","license":"CC-Attribution Only conforme repositorio de partes","documentation":"railcore.github.io","confidence":"GitHub RailCore"}'
  WHEN 'rook-mk1' THEN '{"release":"Rook MK1","frame":"majoritariamente impresso em 3D","motion":"CoreXY","status":"GitHub original aponta para Printables atualizado","confidence":"GitHub/Printables"}'
  WHEN 'snakeoilxy' THEN '{"release":"projeto publico","motion":"CoreXY","license":"open source conforme repositorio","inspiration":"HevORT, Voron, Annex Engineering e EVA2","confidence":"GitHub SnakeOilXY"}'
  ELSE detail_json
END,
source_links_json = CASE slug
  WHEN 'v-core-3' THEN '{"github":"https://github.com/Rat-Rig/V-core-3","manufacturer":"https://ratrig.com/","wiki":"https://wiki.ratrig.com/"}'
  WHEN 'v-core-4' THEN '{"manufacturer":"https://ratrig.com/3d-printers/v-core4","wiki":"https://wiki.ratrig.com/","github_org":"https://github.com/Rat-Rig"}'
  WHEN 'vzbot' THEN '{"site":"https://vzbot.org/","docs":"https://docs.vzbot.org/","github_vz330":"https://github.com/VzBoT3D/VzBoT-Vz330","github_vz235":"https://github.com/VzBoT3D/VzBoT-Vz235","discord":"https://discord.gg/vzbot"}'
  WHEN 'k3' THEN '{"github":"https://github.com/Annex-Engineering/Gasherbrum-K3"}'
  WHEN 'salad-fork' THEN '{"github":"https://github.com/PrintersForAnts/Salad_Fork","site":"https://3dprintersforants.com/"}'
  WHEN 'railcore-ii' THEN '{"parts":"https://github.com/railcore/parts","docs":"https://railcore.github.io/","hardware":"https://railcore.org/hardware/"}'
  WHEN 'rook-mk1' THEN '{"github_outdated":"https://github.com/rolohaun/Rook","printables":"https://www.printables.com/model/387431-rook-mk1-3d-printer"}'
  WHEN 'snakeoilxy' THEN '{"github":"https://github.com/SnakeOilXY/SnakeOil-XY"}'
  ELSE source_links_json
END
WHERE slug IN ('v-core-3', 'v-core-4', 'vzbot', 'k3', 'salad-fork', 'railcore-ii', 'rook-mk1', 'snakeoilxy');

INSERT INTO catalog_printer_variants (
  model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source
)
SELECT m.id, seed.slug, seed.name, seed.build_volume_json, seed.components_json, 'klipper', seed.trust_state, seed.source
FROM (
  SELECT 'rat-rig' AS manufacturer_slug, 'v-chonk' AS model_slug, 'v-chonk-180-beta' AS slug, 'RatRig V-Chonk 180mm beta' AS name,
         '{"x":180,"y":180,"z":180}' AS build_volume_json,
         '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"180mm","kinematics":"corexy"}' AS components_json,
         'draft' AS trust_state, 'catalog_seed_uncertain' AS source
  UNION ALL SELECT 'annex-engineering', 'k1', 'annex-k1-draft', 'Annex K1 draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"Annex conforme build","extruder":"direct drive conforme projeto","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'annex-engineering', 'k2', 'annex-k2-draft', 'Annex K2 draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"Annex conforme build","extruder":"direct drive conforme projeto","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'rolohaun-design', 'bastion', 'bastion-draft', 'Bastion draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'maybecube', 'maybecube', 'maybecube-mc350-draft', 'MaybeCube MC350 draft', '{"x":225,"y":225,"z":200}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"MC350 aprox. 225x225","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'babycube', 'babycube', 'babycube-75-draft', 'BabyCube 75mm draft', '{"x":75,"y":75,"z":75}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"NEMA 17 conforme projeto","hotend":"definir na curadoria","probe":"sensorless homing conforme projeto","bed":"75mm estimado","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'mszturc', 't250', 't250-v1', 'T250 v1 192x212x175', '{"x":192,"y":212,"z":175}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"sensor de distancia para Z tilt conforme README","bed":"192x212","kinematics":"corexy"}', 'community', 'catalog_seed'
  UNION ALL SELECT 'tiny3dp', 'sm-100', 'sm-100-experimental', 'SM-100 experimental', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"Bowden conforme README","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'open-lab-starter-kit', 'olsk-small-3d-printer', 'olsk-small-v3', 'OLSK Small V3', '{"x":235,"y":235,"z":235}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"V6 standard nozzle compatibility","extruder":"definir na curadoria","hotend":"V6 standard compatible","probe":"Eddy Current Surface Scanner","bed":"235x235","kinematics":"corexy"}', 'community', 'catalog_seed'
  UNION ALL SELECT 'open-lab-starter-kit', 'olsk-large-3d-printer', 'olsk-large-v3', 'OLSK Large V3', '{"x":1000,"y":1000,"z":1300}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"large melt zone V6 nozzle compatible","extruder":"definir na curadoria","hotend":"60mm3/s conforme README","probe":"Eddy Current Surface Scanner","bed":"1000x1000","kinematics":"corexy_flying_gantry"}', 'community', 'catalog_seed'
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
