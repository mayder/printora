ALTER TABLE catalog_manufacturers ADD COLUMN website_url TEXT;
ALTER TABLE catalog_manufacturers ADD COLUMN repository_url TEXT;
ALTER TABLE catalog_manufacturers ADD COLUMN documentation_url TEXT;

ALTER TABLE catalog_printer_models ADD COLUMN website_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN repository_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN documentation_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN bom_url TEXT;
ALTER TABLE catalog_printer_models ADD COLUMN description TEXT;

UPDATE catalog_manufacturers
SET website_url = CASE slug
  WHEN 'voron-design' THEN 'https://vorondesign.com/'
  WHEN 'rat-rig' THEN 'https://ratrig.com/'
  WHEN 'vzbot' THEN 'https://github.com/VzBoT3D'
  WHEN 'annex-engineering' THEN 'https://github.com/Annex-Engineering'
  WHEN 'hevort' THEN 'https://hevort.com/'
  WHEN 'jubilee' THEN 'https://jubilee3d.com/'
  WHEN 'printers-for-ants' THEN 'https://github.com/PrintersForAnts'
  WHEN 'zero-g' THEN 'https://zerog.one/'
  WHEN 'railcore-labs' THEN 'https://railcore.org/'
  WHEN 'seckit' THEN 'https://github.com/SecKit'
  WHEN 'blv-projects' THEN 'https://github.com/BenLevi'
  WHEN 'hypercube' THEN 'https://www.thingiverse.com/thing:2254103'
  WHEN 'd-bot' THEN 'https://www.thingiverse.com/thing:1001065'
  WHEN 'v-king' THEN 'https://www.thingiverse.com/thing:1681682'
  WHEN 'croxy' THEN 'https://github.com/CroXY3D'
  WHEN 'rook' THEN 'https://github.com/rolohaun/Rook'
  WHEN 'positron' THEN 'https://github.com/KRALYN/PositronV3'
  WHEN 'the-100' THEN 'https://github.com/MSzturc/the100'
  WHEN 'doron' THEN 'https://github.com/Doron-Design'
  ELSE website_url
END,
repository_url = CASE slug
  WHEN 'voron-design' THEN 'https://github.com/VoronDesign'
  WHEN 'vzbot' THEN 'https://github.com/VzBoT3D'
  WHEN 'annex-engineering' THEN 'https://github.com/Annex-Engineering'
  WHEN 'printers-for-ants' THEN 'https://github.com/PrintersForAnts'
  WHEN 'seckit' THEN 'https://github.com/SecKit'
  WHEN 'croxy' THEN 'https://github.com/CroXY3D'
  WHEN 'rook' THEN 'https://github.com/rolohaun/Rook'
  WHEN 'positron' THEN 'https://github.com/KRALYN/PositronV3'
  WHEN 'the-100' THEN 'https://github.com/MSzturc/the100'
  WHEN 'doron' THEN 'https://github.com/Doron-Design'
  ELSE repository_url
END,
documentation_url = CASE slug
  WHEN 'voron-design' THEN 'https://docs.vorondesign.com/'
  WHEN 'rat-rig' THEN 'https://docs.ratrig.com/'
  WHEN 'zero-g' THEN 'https://docs.zerog.one/'
  ELSE documentation_url
END
WHERE slug IN (
  'voron-design', 'rat-rig', 'vzbot', 'annex-engineering', 'hevort', 'jubilee',
  'printers-for-ants', 'zero-g', 'railcore-labs', 'seckit', 'blv-projects',
  'hypercube', 'd-bot', 'v-king', 'croxy', 'rook', 'positron', 'the-100', 'doron'
);

UPDATE catalog_printer_models
SET description = CASE slug
  WHEN 'voron-2-4' THEN 'CoreXY fechado de referência para alta temperatura e grande comunidade.'
  WHEN 'voron-trident' THEN 'CoreXY com mesa fixa e eixo Z por três fusos, comum em builds Klipper robustos.'
  WHEN 'voron-switchwire' THEN 'Conversão CoreXZ estilo Voron para formato bedslinger.'
  WHEN 'v-core-3' THEN 'CoreXY modular da RatRig, comum em volumes grandes.'
  WHEN 'v-core-4' THEN 'Evolução modular da linha V-Core para builds CoreXY recentes.'
  WHEN 'vzbot' THEN 'CoreXY DIY focado em alta velocidade, com variações fortemente dependentes do build.'
  WHEN 'k3' THEN 'Projeto compacto CoreXY da Annex Engineering.'
  WHEN 'mercury-one-1' THEN 'Conversão CoreXY da ZeroG para plataforma Ender 5.'
  WHEN 'hydra' THEN 'Conversão ZeroG para Ender 5 Plus e plataformas relacionadas.'
  WHEN 'railcore-ii' THEN 'CoreXY DIY com comunidade própria e variações 250/300.'
  WHEN 'hypercube-evolution' THEN 'Projeto CoreXY histórico, frequentemente customizado.'
  ELSE description
END,
website_url = CASE slug
  WHEN 'voron-2-4' THEN 'https://vorondesign.com/voron2.4'
  WHEN 'voron-trident' THEN 'https://vorondesign.com/voron_trident'
  WHEN 'voron-switchwire' THEN 'https://vorondesign.com/voron_switchwire'
  WHEN 'v-core-3' THEN 'https://ratrig.com/3d-printers/v-core3'
  WHEN 'v-core-4' THEN 'https://ratrig.com/3d-printers/v-core4'
  ELSE website_url
END,
repository_url = CASE slug
  WHEN 'voron-2-4' THEN 'https://github.com/VoronDesign/Voron-2'
  WHEN 'voron-trident' THEN 'https://github.com/VoronDesign/Voron-Trident'
  WHEN 'voron-switchwire' THEN 'https://github.com/VoronDesign/Voron-Switchwire'
  WHEN 'voron-0-2' THEN 'https://github.com/VoronDesign/Voron-0'
  WHEN 'voron-0-1' THEN 'https://github.com/VoronDesign/Voron-0'
  WHEN 'mercury-one-1' THEN 'https://github.com/ZeroGDesign/Mercury'
  WHEN 'hydra' THEN 'https://github.com/ZeroGDesign/Hydra'
  WHEN 'rook-mk1' THEN 'https://github.com/rolohaun/Rook'
  WHEN 'positron-v3' THEN 'https://github.com/KRALYN/PositronV3'
  WHEN 'the-100' THEN 'https://github.com/MSzturc/the100'
  ELSE repository_url
END,
documentation_url = CASE slug
  WHEN 'voron-2-4' THEN 'https://docs.vorondesign.com/build/startup/'
  WHEN 'voron-trident' THEN 'https://docs.vorondesign.com/build/startup/'
  WHEN 'voron-switchwire' THEN 'https://docs.vorondesign.com/build/startup/'
  WHEN 'mercury-one-1' THEN 'https://docs.zerog.one/'
  WHEN 'hydra' THEN 'https://docs.zerog.one/'
  ELSE documentation_url
END,
bom_url = CASE slug
  WHEN 'voron-2-4' THEN 'https://vorondesign.com/sourcing_guide?model=VT'
  WHEN 'voron-trident' THEN 'https://vorondesign.com/sourcing_guide?model=VTr'
  WHEN 'voron-switchwire' THEN 'https://vorondesign.com/sourcing_guide?model=VSW'
  ELSE bom_url
END
WHERE slug IN (
  'voron-2-4', 'voron-trident', 'voron-switchwire', 'voron-0-2', 'voron-0-1',
  'v-core-3', 'v-core-4', 'vzbot', 'k3', 'mercury-one-1', 'hydra',
  'railcore-ii', 'hypercube-evolution', 'rook-mk1', 'positron-v3', 'the-100'
);
