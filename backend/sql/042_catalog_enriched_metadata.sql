ALTER TABLE catalog_manufacturers ADD COLUMN logo_url TEXT;
ALTER TABLE catalog_manufacturers ADD COLUMN discord_url TEXT;
ALTER TABLE catalog_manufacturers ADD COLUMN reddit_url TEXT;
ALTER TABLE catalog_manufacturers ADD COLUMN summary TEXT;

ALTER TABLE catalog_printer_models ADD COLUMN image_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN discord_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN reddit_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN forum_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN curation_notes TEXT;

UPDATE catalog_manufacturers
SET website_url = CASE slug
  WHEN 'voron-design' THEN 'https://vorondesign.com/'
  WHEN 'rat-rig' THEN 'https://ratrig.com/'
  WHEN 'vzbot' THEN 'https://vzbot.org/'
  WHEN 'annex-engineering' THEN 'https://annex-engineering.eu/'
  WHEN 'hevort' THEN 'https://hevort.com/'
  WHEN 'printers-for-ants' THEN 'https://3dprintersforants.com/'
  WHEN 'zero-g' THEN 'https://zerog.one/'
  WHEN 'railcore-labs' THEN 'https://railcore.org/'
  WHEN 'seckit' THEN 'https://seckit3dp.design/'
  WHEN 'blv-projects' THEN 'https://www.blvprojects.com/blv-mgn-cube-3d-printer'
  WHEN 'rook' THEN 'https://www.printables.com/model/387431-rook-mk1-3d-printer'
  ELSE website_url
END,
repository_url = CASE slug
  WHEN 'voron-design' THEN 'https://github.com/VoronDesign'
  WHEN 'rat-rig' THEN 'https://github.com/Rat-Rig'
  WHEN 'vzbot' THEN 'https://github.com/VzBoT3D'
  WHEN 'annex-engineering' THEN 'https://github.com/Annex-Engineering'
  WHEN 'hevort' THEN 'https://github.com/MirageC79/HevORT'
  WHEN 'printers-for-ants' THEN 'https://github.com/PrintersForAnts'
  WHEN 'zero-g' THEN 'https://github.com/ZeroGDesign'
  WHEN 'railcore-labs' THEN 'https://github.com/railcore'
  WHEN 'seckit' THEN 'https://github.com/SecKit'
  WHEN 'blv-projects' THEN 'https://github.com/BenLevi'
  WHEN 'hypercube' THEN 'https://www.thingiverse.com/thing:2254103'
  WHEN 'd-bot' THEN 'https://www.thingiverse.com/thing:1001065'
  WHEN 'v-king' THEN 'https://www.thingiverse.com/thing:1681682'
  WHEN 'croxy' THEN 'https://github.com/CroXY3D'
  WHEN 'rook' THEN 'https://github.com/rolohaun/Rook'
  WHEN 'positron' THEN 'https://github.com/KRALYN/PositronV3'
  WHEN 'the-100' THEN 'https://github.com/MSzturc/the100'
  WHEN 'doron' THEN 'https://github.com/Fabreeko/Doron-Velta'
  WHEN 'snakeoilxy' THEN 'https://github.com/ChipCE/SnakeOil-XY'
  ELSE repository_url
END,
documentation_url = CASE slug
  WHEN 'voron-design' THEN 'https://docs.vorondesign.com/'
  WHEN 'rat-rig' THEN 'https://wiki.ratrig.com/'
  WHEN 'vzbot' THEN 'https://docs.vzbot.org/'
  WHEN 'hevort' THEN 'https://miragec79.github.io/HevORT/'
  WHEN 'zero-g' THEN 'https://docs.zerog.one/'
  WHEN 'railcore-labs' THEN 'https://railcore.github.io/'
  ELSE documentation_url
END,
logo_url = CASE slug
  WHEN 'voron-design' THEN 'https://github.com/VoronDesign.png'
  WHEN 'rat-rig' THEN 'https://github.com/Rat-Rig.png'
  WHEN 'vzbot' THEN 'https://github.com/VzBoT3D.png'
  WHEN 'annex-engineering' THEN 'https://github.com/Annex-Engineering.png'
  WHEN 'hevort' THEN 'https://github.com/MirageC79.png'
  WHEN 'printers-for-ants' THEN 'https://github.com/PrintersForAnts.png'
  WHEN 'zero-g' THEN 'https://github.com/ZeroGDesign.png'
  WHEN 'railcore-labs' THEN 'https://github.com/railcore.png'
  WHEN 'seckit' THEN 'https://github.com/SecKit.png'
  WHEN 'blv-projects' THEN 'https://github.com/BenLevi.png'
  WHEN 'croxy' THEN 'https://github.com/CroXY3D.png'
  WHEN 'rook' THEN 'https://github.com/rolohaun.png'
  WHEN 'positron' THEN 'https://github.com/KRALYN.png'
  WHEN 'the-100' THEN 'https://github.com/MSzturc.png'
  WHEN 'doron' THEN 'https://github.com/Fabreeko.png'
  WHEN 'snakeoilxy' THEN 'https://github.com/ChipCE.png'
  WHEN 'jubilee-machine' THEN 'https://github.com/machineagency.png'
  ELSE logo_url
END,
discord_url = CASE slug
  WHEN 'voron-design' THEN 'https://discord.gg/voron'
  WHEN 'rat-rig' THEN 'https://discord.gg/ratrig'
  WHEN 'vzbot' THEN 'https://discord.gg/vzbot'
  ELSE discord_url
END,
reddit_url = CASE slug
  WHEN 'voron-design' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'rat-rig' THEN 'https://www.reddit.com/r/ratrig/'
  WHEN 'vzbot' THEN 'https://www.reddit.com/r/VzBot/'
  ELSE reddit_url
END,
summary = CASE slug
  WHEN 'voron-design' THEN 'Projeto comunitário de impressoras DIY CoreXY/CoreXZ com documentação, GitHub e comunidade próprios.'
  WHEN 'rat-rig' THEN 'Fabricante português de kits modulares, incluindo V-Core e V-Minion, com documentação pública e ecossistema RatOS.'
  WHEN 'vzbot' THEN 'Projeto DIY de impressoras CoreXY de alta velocidade, com Vz-235 e Vz-330 documentadas em site, GitHub e Discord.'
  WHEN 'annex-engineering' THEN 'Coletivo DIY com projetos como K3 e toolheads/extrusores; dados variam por projeto e revisão.'
  WHEN 'hevort' THEN 'Projeto DIY CoreXY avançado com foco em rigidez, volume grande e mesa autonivelante.'
  WHEN 'printers-for-ants' THEN 'Família de impressoras compactas inspiradas em Voron, como Micron, Salad Fork e outros modelos pequenos.'
  WHEN 'zero-g' THEN 'Projetos de conversão CoreXY para plataformas Ender 5, incluindo Mercury One e Hydra.'
  WHEN 'railcore-labs' THEN 'Projeto RepRap CoreXY RailCore II com documentação e repositórios públicos.'
  WHEN 'seckit' THEN 'Projetos e kits CoreXY como SK-Go e SK-Tank, com repositórios públicos de recursos.'
  WHEN 'blv-projects' THEN 'Projeto BLV MGN Cube, CoreXY aberto criado por Ben Levi e replicado em kits/comunidade.'
  WHEN 'rook' THEN 'Projeto de impressora CoreXY compacta de baixo custo, distribuído por GitHub/Printables.'
  ELSE summary
END
WHERE slug IN (
  'voron-design', 'rat-rig', 'vzbot', 'annex-engineering', 'hevort', 'printers-for-ants',
  'zero-g', 'railcore-labs', 'seckit', 'blv-projects', 'hypercube', 'd-bot', 'v-king',
  'croxy', 'rook', 'positron', 'the-100', 'doron', 'snakeoilxy', 'jubilee-machine'
);

UPDATE catalog_printer_models
SET website_url = CASE slug
  WHEN 'voron-0-1' THEN 'https://vorondesign.com/voron0.1'
  WHEN 'voron-0-2' THEN 'https://vorondesign.com/voron0.2'
  WHEN 'voron-1-8' THEN 'https://vorondesign.com/voron1.8'
  WHEN 'voron-2-4' THEN 'https://vorondesign.com/voron2.4'
  WHEN 'voron-trident' THEN 'https://vorondesign.com/voron_trident'
  WHEN 'voron-switchwire' THEN 'https://vorondesign.com/voron_switchwire'
  WHEN 'v-core-3' THEN 'https://ratrig.com/3d-printers/v-core3'
  WHEN 'v-core-4' THEN 'https://ratrig.com/3d-printers/v-core4'
  WHEN 'v-minion' THEN 'https://ratrig.com/3d-printers/v-minion'
  WHEN 'vzbot' THEN 'https://vzbot.org/'
  WHEN 'k3' THEN 'https://github.com/Annex-Engineering/Gasherbrum-K3'
  WHEN 'hevort' THEN 'https://hevort.com/'
  WHEN 'micron-plus' THEN 'https://3dprintersforants.com/'
  WHEN 'salad-fork' THEN 'https://3dprintersforants.com/'
  WHEN 'mercury-one-1' THEN 'https://zerog.one/'
  WHEN 'hydra' THEN 'https://zerog.one/'
  WHEN 'railcore-ii' THEN 'https://railcore.org/'
  WHEN 'sk-go' THEN 'https://seckit3dp.design/'
  WHEN 'tank' THEN 'https://seckit3dp.design/'
  WHEN 'blv-mgn-cube' THEN 'https://www.blvprojects.com/blv-mgn-cube-3d-printer'
  WHEN 'rook-mk1' THEN 'https://www.printables.com/model/387431-rook-mk1-3d-printer'
  ELSE website_url
END,
repository_url = CASE slug
  WHEN 'voron-0-1' THEN 'https://github.com/VoronDesign/Voron-0'
  WHEN 'voron-0-2' THEN 'https://github.com/VoronDesign/Voron-0'
  WHEN 'voron-1-8' THEN 'https://github.com/VoronDesign/Voron-1'
  WHEN 'voron-2-4' THEN 'https://github.com/VoronDesign/Voron-2'
  WHEN 'voron-trident' THEN 'https://github.com/VoronDesign/Voron-Trident'
  WHEN 'voron-switchwire' THEN 'https://github.com/VoronDesign/Voron-Switchwire'
  WHEN 'voron-legacy' THEN 'https://github.com/VoronDesign/Voron-Legacy'
  WHEN 'voron-phoenix' THEN 'https://github.com/VoronDesign/Voron-Phoenix'
  WHEN 'v-core-3' THEN 'https://github.com/Rat-Rig/V-core-3'
  WHEN 'v-minion' THEN 'https://github.com/Rat-Rig/V-Minion'
  WHEN 'vzbot' THEN 'https://github.com/VzBoT3D/VzBoT-Vz330'
  WHEN 'k3' THEN 'https://github.com/Annex-Engineering/Gasherbrum-K3'
  WHEN 'hevort' THEN 'https://github.com/MirageC79/HevORT'
  WHEN 'micron-plus' THEN 'https://github.com/PrintersForAnts/Micron'
  WHEN 'salad-fork' THEN 'https://github.com/PrintersForAnts/Salad_Fork'
  WHEN 'mercury-one-1' THEN 'https://github.com/ZeroGDesign/Mercury-OUTDATED'
  WHEN 'hydra' THEN 'https://github.com/ZeroGDesign/Hydra'
  WHEN 'railcore-ii' THEN 'https://github.com/railcore/parts'
  WHEN 'sk-go' THEN 'https://github.com/SecKit/SK-Go_SK-Mini'
  WHEN 'tank' THEN 'https://github.com/SecKit/SK-Tank'
  WHEN 'blv-mgn-cube' THEN 'https://github.com/FYSETC/FYSETC-BLV-MGN-CUBE'
  WHEN 'rook-mk1' THEN 'https://github.com/rolohaun/Rook'
  WHEN 'positron-v3' THEN 'https://github.com/KRALYN/PositronV3'
  WHEN 'the-100' THEN 'https://github.com/MSzturc/the100'
  WHEN 'doron-velta' THEN 'https://github.com/Fabreeko/Doron-Velta'
  WHEN 'snakeoilxy' THEN 'https://github.com/ChipCE/SnakeOil-XY'
  ELSE repository_url
END,
documentation_url = CASE slug
  WHEN 'voron-0-1' THEN 'https://docs.vorondesign.com/'
  WHEN 'voron-0-2' THEN 'https://docs.vorondesign.com/'
  WHEN 'voron-1-8' THEN 'https://docs.vorondesign.com/'
  WHEN 'voron-2-4' THEN 'https://docs.vorondesign.com/build/startup/'
  WHEN 'voron-trident' THEN 'https://docs.vorondesign.com/build/startup/'
  WHEN 'voron-switchwire' THEN 'https://docs.vorondesign.com/build/startup/'
  WHEN 'v-core-4' THEN 'https://wiki.ratrig.com/'
  WHEN 'vzbot' THEN 'https://docs.vzbot.org/'
  WHEN 'hevort' THEN 'https://miragec79.github.io/HevORT/'
  WHEN 'mercury-one-1' THEN 'https://docs.zerog.one/'
  WHEN 'hydra' THEN 'https://docs.zerog.one/'
  WHEN 'railcore-ii' THEN 'https://railcore.github.io/'
  WHEN 'tank' THEN 'https://sites.google.com/view/seckit-wiki/sk-tank-350x350x400'
  ELSE documentation_url
END,
bom_url = CASE slug
  WHEN 'voron-0-2' THEN 'https://vorondesign.com/sourcing_guide?model=V0.2'
  WHEN 'voron-2-4' THEN 'https://vorondesign.com/sourcing_guide?model=V2.4'
  WHEN 'voron-trident' THEN 'https://vorondesign.com/sourcing_guide?model=Trident'
  WHEN 'voron-switchwire' THEN 'https://vorondesign.com/sourcing_guide?model=Switchwire'
  WHEN 'vzbot' THEN 'https://docs.vzbot.org/'
  WHEN 'salad-fork' THEN 'https://github.com/PrintersForAnts/Salad_Fork'
  WHEN 'railcore-ii' THEN 'https://github.com/railcore/parts'
  ELSE bom_url
END,
discord_url = CASE slug
  WHEN 'voron-0-1' THEN 'https://discord.gg/voron'
  WHEN 'voron-0-2' THEN 'https://discord.gg/voron'
  WHEN 'voron-1-8' THEN 'https://discord.gg/voron'
  WHEN 'voron-2-4' THEN 'https://discord.gg/voron'
  WHEN 'voron-trident' THEN 'https://discord.gg/voron'
  WHEN 'voron-switchwire' THEN 'https://discord.gg/voron'
  WHEN 'vzbot' THEN 'https://discord.gg/vzbot'
  ELSE discord_url
END,
reddit_url = CASE slug
  WHEN 'voron-0-1' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'voron-0-2' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'voron-1-8' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'voron-2-4' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'voron-trident' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'voron-switchwire' THEN 'https://www.reddit.com/r/VORONDesign/'
  WHEN 'v-core-3' THEN 'https://www.reddit.com/r/ratrig/'
  WHEN 'v-core-4' THEN 'https://www.reddit.com/r/ratrig/'
  WHEN 'vzbot' THEN 'https://www.reddit.com/r/VzBot/'
  ELSE reddit_url
END,
image_url = CASE slug
  WHEN 'voron-2-4' THEN 'https://github.com/VoronDesign.png'
  WHEN 'v-core-3' THEN 'https://github.com/Rat-Rig.png'
  WHEN 'v-core-4' THEN 'https://github.com/Rat-Rig.png'
  WHEN 'vzbot' THEN 'https://github.com/VzBoT3D.png'
  WHEN 'k3' THEN 'https://github.com/Annex-Engineering.png'
  WHEN 'salad-fork' THEN 'https://github.com/PrintersForAnts.png'
  WHEN 'railcore-ii' THEN 'https://github.com/railcore.png'
  ELSE image_url
END,
description = CASE slug
  WHEN 'vzbot' THEN 'CoreXY de alta velocidade derivado inicialmente da plataforma TronXY X5S/X5SA, com versões Vz-235 e Vz-330.'
  WHEN 'k3' THEN 'Gasherbrum/K3 é uma impressora FDM compacta de acionamento direto da Annex Engineering.'
  WHEN 'salad-fork' THEN 'Impressora compacta da família Printers For Ants, baseada em arquitetura tipo Trident reduzida para extrusões 1515.'
  WHEN 'railcore-ii' THEN 'RailCore II é uma impressora RepRap CoreXY com partes e configurações públicas.'
  WHEN 'sk-go' THEN 'SK-Go é a linha CoreXY da SecKit; variações e volumes dependem da revisão e configuração escolhida.'
  WHEN 'tank' THEN 'SK-Tank é uma CoreXY all-metal da SecKit, mantida como community/draft até revisão completa.'
  WHEN 'rook-mk1' THEN 'Rook MK1 é uma CoreXY compacta e econômica; o GitHub original aponta para arquivos atualizados no Printables.'
  ELSE description
END,
curation_notes = CASE slug
  WHEN 'v-core-4' THEN 'Site e wiki oficiais confirmados; repositório público específico do V-Core 4 não foi usado como fonte primária neste seed.'
  WHEN 'annex-engineering-printer' THEN 'Nome mantido como draft até separar projetos Annex específicos com fonte primária.'
  WHEN 'croxy' THEN 'Mantido como draft: confirmar repositório/modelo oficial antes de promover.'
  WHEN 'snakeoilxy' THEN 'Mantido como draft: confirmar volume e revisão antes de promover.'
  ELSE curation_notes
END
WHERE slug IN (
  'voron-0-1', 'voron-0-2', 'voron-1-8', 'voron-2-4', 'voron-trident', 'voron-switchwire',
  'voron-legacy', 'voron-phoenix', 'v-core-3', 'v-core-4', 'v-minion', 'vzbot', 'k3',
  'hevort', 'micron-plus', 'salad-fork', 'mercury-one-1', 'hydra', 'railcore-ii',
  'sk-go', 'tank', 'blv-mgn-cube', 'rook-mk1', 'positron-v3', 'the-100', 'doron-velta',
  'snakeoilxy', 'croxy'
);

INSERT INTO catalog_manufacturers (slug, name, trust_state, source, website_url, repository_url, logo_url, discord_url, summary)
VALUES
  ('magpie-printer', 'Magpie Printer', 'draft', 'catalog_seed_uncertain', NULL, 'https://github.com/magpie-printer/magpie', 'https://github.com/magpie-printer.png', 'https://discord.com/invite/zkxYRuTDAA', 'Projeto comunitário de impressora DIY encontrado com GitHub e Discord públicos; precisa de revisão técnica antes de promoção.'),
  ('icarus3d', 'Icarus3D', 'draft', 'catalog_seed_uncertain', NULL, 'https://github.com/Icarus3D/Dynasty-3D-Printer', 'https://github.com/Icarus3D.png', NULL, 'Projeto Dynasty CoreXY publicado no GitHub; precisa de revisão técnica antes de promoção.')
ON CONFLICT(slug) DO UPDATE SET
  name = excluded.name,
  trust_state = excluded.trust_state,
  source = excluded.source,
  website_url = excluded.website_url,
  repository_url = excluded.repository_url,
  logo_url = excluded.logo_url,
  discord_url = excluded.discord_url,
  summary = excluded.summary,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_models (
  manufacturer_id, slug, name, kinematics, trust_state, source, website_url, repository_url, documentation_url, discord_url, reddit_url, description, curation_notes
)
SELECT mf.id, seed.slug, seed.name, seed.kinematics, seed.trust_state, seed.source, seed.website_url, seed.repository_url, seed.documentation_url, seed.discord_url, seed.reddit_url, seed.description, seed.curation_notes
FROM (
  SELECT 'printers-for-ants' AS manufacturer_slug, 'f-zero' AS slug, 'F-Zero' AS name, 'corexy' AS kinematics, 'community' AS trust_state, 'catalog_seed' AS source, 'https://3dprintersforants.com/' AS website_url, 'https://github.com/PrintersForAnts' AS repository_url, NULL AS documentation_url, NULL AS discord_url, 'https://www.reddit.com/r/VORONDesign/' AS reddit_url, 'V0 mod com gantry voador e nivelamento por quatro pontos, catalogado como família Printers For Ants.' AS description, 'Volume e componentes dependem da revisão; manter variações como draft até fonte primária específica.' AS curation_notes
  UNION ALL SELECT 'printers-for-ants', 'tri-zero', 'Tri-Zero', 'corexy', 'community', 'catalog_seed', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto compacto da família Printers For Ants.', 'Confirmar revisão, volume e BOM antes de promover variações.'
  UNION ALL SELECT 'printers-for-ants', 'hex-zero', 'Hex-Zero', 'corexy', 'community', 'catalog_seed', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto compacto da família Printers For Ants.', 'Confirmar revisão, volume e BOM antes de promover variações.'
  UNION ALL SELECT 'printers-for-ants', 'tiny-m', 'Tiny-M', 'corexy', 'community', 'catalog_seed', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto compacto listado no site Printers For Ants.', 'Confirmar revisão, volume e BOM antes de promover variações.'
  UNION ALL SELECT 'printers-for-ants', 'tiny-t', 'Tiny-T', 'corexy', 'community', 'catalog_seed', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto compacto listado no site Printers For Ants.', 'Confirmar revisão, volume e BOM antes de promover variações.'
  UNION ALL SELECT 'printers-for-ants', 'stealth-fork', 'Stealth Fork', 'corexy', 'draft', 'catalog_seed_uncertain', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts/StealthFork', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Design experimental que combina características do Micron e Salad Fork.', 'GitHub indica beta/experimental; manter como draft.'
  UNION ALL SELECT 'printers-for-ants', 'dueling-zero', 'Dueling Zero', 'corexy', 'draft', 'catalog_seed_uncertain', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto listado no site Printers For Ants.', 'Confirmar status e revisão antes de promover.'
  UNION ALL SELECT 'printers-for-ants', 'pandoras-box', 'Pandora''s Box', 'corexy', 'draft', 'catalog_seed_uncertain', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto listado no site Printers For Ants.', 'Confirmar status e revisão antes de promover.'
  UNION ALL SELECT 'printers-for-ants', 'crucible', 'Crucible', 'corexy', 'draft', 'catalog_seed_uncertain', 'https://3dprintersforants.com/', 'https://github.com/PrintersForAnts', NULL, NULL, 'https://www.reddit.com/r/VORONDesign/', 'Projeto listado no site Printers For Ants.', 'Confirmar status e revisão antes de promover.'
  UNION ALL SELECT 'magpie-printer', 'magpie', 'Magpie', 'corexy', 'draft', 'catalog_seed_uncertain', NULL, 'https://github.com/magpie-printer/magpie', NULL, 'https://discord.com/invite/zkxYRuTDAA', NULL, 'Projeto DIY publicado com GitHub e Discord; aguardando revisão técnica.', 'Não promover sem revisar volume, cinemática e BOM.'
  UNION ALL SELECT 'icarus3d', 'dynasty', 'Dynasty', 'corexy', 'draft', 'catalog_seed_uncertain', NULL, 'https://github.com/Icarus3D/Dynasty-3D-Printer', NULL, NULL, NULL, 'Projeto CoreXY DIY publicado no GitHub.', 'Não promover sem revisar volume, cinemática e BOM.'
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
  discord_url = excluded.discord_url,
  reddit_url = excluded.reddit_url,
  description = excluded.description,
  curation_notes = excluded.curation_notes,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO catalog_printer_variants (
  model_id, slug, name, build_volume_json, components_json, firmware_family, trust_state, source
)
SELECT m.id, seed.slug, seed.name, seed.build_volume_json, seed.components_json, 'klipper', seed.trust_state, seed.source
FROM (
  SELECT 'printers-for-ants' AS manufacturer_slug, 'salad-fork' AS model_slug, 'salad-fork-120' AS slug, 'Salad Fork 120mm' AS name, '{"x":120,"y":120,"z":120}' AS build_volume_json, '{"mainboard":"placa Klipper compacta conforme build","mcu":"RP2040/STM32 conforme placa","toolhead":"Mini Stealthburner/Dragonburner conforme build","extruder":"Sherpa Mini/Clockwork 2 conforme build","hotend":"Revo/V6 conforme build","probe":"Klicky/Boop conforme build","bed":"120mm","kinematics":"corexy"}' AS components_json, 'community' AS trust_state, 'catalog_seed' AS source
  UNION ALL SELECT 'printers-for-ants', 'salad-fork', 'salad-fork-180', 'Salad Fork 180mm', '{"x":180,"y":180,"z":180}', '{"mainboard":"placa Klipper compacta conforme build","mcu":"RP2040/STM32 conforme placa","toolhead":"Mini Stealthburner/Dragonburner conforme build","extruder":"Sherpa Mini/Clockwork 2 conforme build","hotend":"Revo/V6 conforme build","probe":"Klicky/Boop conforme build","bed":"180mm","kinematics":"corexy"}', 'community', 'catalog_seed'
  UNION ALL SELECT 'printers-for-ants', 'f-zero', 'f-zero-draft', 'F-Zero draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'tri-zero', 'tri-zero-draft', 'Tri-Zero draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'hex-zero', 'hex-zero-draft', 'Hex-Zero draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'tiny-m', 'tiny-m-draft', 'Tiny-M draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'tiny-t', 'tiny-t-draft', 'Tiny-T draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'stealth-fork', 'stealth-fork-beta', 'Stealth Fork beta', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'dueling-zero', 'dueling-zero-draft', 'Dueling Zero draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'pandoras-box', 'pandoras-box-draft', 'Pandora''s Box draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'printers-for-ants', 'crucible', 'crucible-draft', 'Crucible draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'magpie-printer', 'magpie', 'magpie-draft', 'Magpie draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
  UNION ALL SELECT 'icarus3d', 'dynasty', 'dynasty-draft', 'Dynasty draft', '{}', '{"mainboard":"definir na curadoria","mcu":"definir na curadoria","toolhead":"definir na curadoria","extruder":"definir na curadoria","hotend":"definir na curadoria","probe":"definir na curadoria","bed":"definir na curadoria","kinematics":"corexy"}', 'draft', 'catalog_seed_uncertain'
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
