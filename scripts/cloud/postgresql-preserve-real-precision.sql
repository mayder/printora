\set ON_ERROR_STOP on

ALTER TABLE maintenance_events
    ALTER COLUMN print_hours_at TYPE double precision;
ALTER TABLE maintenance_tasks
    ALTER COLUMN interval_value TYPE double precision,
    ALTER COLUMN last_done_print_hours TYPE double precision,
    ALTER COLUMN current_print_hours TYPE double precision;
ALTER TABLE social_material_profiles
    ALTER COLUMN nozzle_diameter_mm TYPE double precision,
    ALTER COLUMN flow_percent TYPE double precision;
ALTER TABLE social_slicing_profiles
    ALTER COLUMN layer_height_mm TYPE double precision;
ALTER TABLE z_offset_records
    ALTER COLUMN offset_value TYPE double precision,
    ALTER COLUMN previous_offset_value TYPE double precision,
    ALTER COLUMN delta_value TYPE double precision;
