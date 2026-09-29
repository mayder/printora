-- The shared adapter intentionally normalizes SQLite-compatible application
-- timestamps as ISO text. Finance tables were initially declared TIMESTAMPTZ,
-- which rejected those values at runtime. Align only this bounded domain with
-- the adapter contract; monetary, identity and audit contents are unchanged.
DO $$
DECLARE column_record RECORD;
BEGIN
    FOR column_record IN
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND data_type IN ('timestamp with time zone', 'timestamp without time zone')
          AND (
              table_name LIKE 'finance\_%' ESCAPE '\'
              OR table_name LIKE 'payment\_%' ESCAPE '\'
              OR table_name LIKE 'commerce\_%' ESCAPE '\'
          )
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
