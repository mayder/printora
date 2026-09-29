\set ON_ERROR_STOP on

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO printora_owner;

DO $$
DECLARE
    object_record record;
BEGIN
    FOR object_record IN
        SELECT format('%I.%I', schemaname, tablename) AS object_name
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %s OWNER TO printora_owner', object_record.object_name);
    END LOOP;

    FOR object_record IN
        SELECT format('%I.%I', sequence_schema, sequence_name) AS object_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE format('ALTER SEQUENCE %s OWNER TO printora_owner', object_record.object_name);
    END LOOP;
END
$$;

GRANT CONNECT ON DATABASE printora_cloud TO printora_app;
GRANT USAGE ON SCHEMA public TO printora_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO printora_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO printora_app;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'printora_analytics') THEN
        CREATE ROLE printora_analytics NOLOGIN;
    END IF;
END
$$;

GRANT printora_analytics TO printora_app;
GRANT CONNECT ON DATABASE printora_cloud TO printora_analytics;
GRANT USAGE ON SCHEMA public TO printora_analytics;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM printora_analytics;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM printora_analytics;
GRANT SELECT, INSERT, UPDATE ON TABLE
    analytics_events,
    analytics_metric_facts,
    analytics_lineage,
    analytics_subject_controls,
    analytics_moderation_cases,
    analytics_moderation_appeals,
    analytics_model_registry,
    analytics_model_decisions,
    analytics_geometry_items,
    analytics_replay_runs,
    analytics_retention_policies
TO printora_analytics;

ALTER DEFAULT PRIVILEGES FOR ROLE printora_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO printora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE printora_owner IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO printora_app;
