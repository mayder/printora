DO $$
DECLARE column_record RECORD;
BEGIN
    FOR column_record IN
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name LIKE 'manufacturing\_%' ESCAPE '\'
          AND data_type IN ('timestamp with time zone', 'timestamp without time zone')
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ALTER COLUMN %I TYPE TEXT USING %I::text',
            column_record.table_schema, column_record.table_name,
            column_record.column_name, column_record.column_name
        );
    END LOOP;
END $$;
