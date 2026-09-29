-- The shared database adapter stores application timestamps as ISO text so
-- the same repository contract works in SQLite and PostgreSQL. Photo capture
-- was initially declared with TIMESTAMPTZ and rejected the adapter values.
-- Align only this bounded domain; photo contents and ownership are unchanged.
DO $$
DECLARE column_record RECORD;
BEGIN
    FOR column_record IN
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name IN ('photo_capture_sessions', 'photo_capture_photos')
          AND data_type IN ('timestamp with time zone', 'timestamp without time zone')
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ALTER COLUMN %I TYPE TEXT USING %I::text',
            column_record.table_schema,
            column_record.table_name,
            column_record.column_name,
            column_record.column_name
        );
    END LOOP;
END $$;
