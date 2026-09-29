UPDATE catalog_printer_variants
SET trust_state = 'blocked',
    updated_at = datetime('now')
WHERE model_id IN (
  SELECT id
  FROM catalog_printer_models
  WHERE slug IN ('jubilee', 'jubilee-machine')
     OR kinematics = 'toolchanger_corexy'
);

UPDATE catalog_printer_models
SET trust_state = 'blocked',
    updated_at = datetime('now')
WHERE slug IN ('jubilee', 'jubilee-machine')
   OR kinematics = 'toolchanger_corexy';

UPDATE catalog_manufacturers
SET trust_state = 'blocked',
    updated_at = datetime('now')
WHERE slug IN ('jubilee', 'jubilee-machine');
