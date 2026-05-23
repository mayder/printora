ALTER TABLE maintenance_tasks ADD COLUMN interval_kind TEXT NOT NULL DEFAULT 'days';
ALTER TABLE maintenance_tasks ADD COLUMN interval_value REAL;
ALTER TABLE maintenance_tasks ADD COLUMN last_done_print_hours REAL;
ALTER TABLE maintenance_tasks ADD COLUMN last_print_hours_read_at TEXT;
ALTER TABLE maintenance_tasks ADD COLUMN current_print_hours REAL;
ALTER TABLE maintenance_tasks ADD COLUMN current_print_hours_read_at TEXT;
ALTER TABLE maintenance_tasks ADD COLUMN current_print_hours_source TEXT;

ALTER TABLE maintenance_events ADD COLUMN print_hours_at REAL;
ALTER TABLE maintenance_events ADD COLUMN print_hours_read_at TEXT;

UPDATE maintenance_tasks
SET interval_kind = 'days',
    interval_value = interval_days
WHERE interval_value IS NULL;

CREATE INDEX IF NOT EXISTS idx_maintenance_tasks_interval_kind
ON maintenance_tasks(printer_id, interval_kind, is_active);
