UPDATE catalog_manufacturers
SET source = CASE
      WHEN source LIKE '%uncertain%' THEN 'catalog_seed_uncertain'
      ELSE 'catalog_seed'
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE source LIKE '%pkg49%';

UPDATE catalog_printer_models
SET source = CASE
      WHEN source LIKE '%uncertain%' THEN 'catalog_seed_uncertain'
      ELSE 'catalog_seed'
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE source LIKE '%pkg49%';

UPDATE catalog_printer_variants
SET source = CASE
      WHEN source LIKE '%uncertain%' THEN 'catalog_seed_uncertain'
      ELSE 'catalog_seed'
    END,
    updated_at = CURRENT_TIMESTAMP
WHERE source LIKE '%pkg49%';
