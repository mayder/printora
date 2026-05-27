ALTER TABLE maintenance_tasks ADD COLUMN is_applicable INTEGER NOT NULL DEFAULT 1;
ALTER TABLE maintenance_tasks ADD COLUMN not_applicable_at TEXT;

CREATE INDEX IF NOT EXISTS idx_maintenance_tasks_printer_applicable
ON maintenance_tasks(printer_id, is_applicable);
