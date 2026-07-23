CREATE TABLE IF NOT EXISTS public.search_documents (
    entity_type TEXT NOT NULL,
    entity_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    tags_json TEXT NOT NULL DEFAULT '[]',
    community_id BIGINT,
    catalog_variant_id BIGINT,
    owner_user_id BIGINT,
    visibility TEXT NOT NULL DEFAULT 'public',
    popularity_score BIGINT NOT NULL DEFAULT 0,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active boolean NOT NULL DEFAULT true,
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(body, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(tags_json, '')), 'C')
    ) STORED,
    PRIMARY KEY(entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_search_documents_vector
ON public.search_documents USING GIN(search_vector);

CREATE INDEX IF NOT EXISTS idx_search_documents_filters
ON public.search_documents(is_active, entity_type, visibility, source_updated_at);

CREATE SEQUENCE IF NOT EXISTS public.search_outbox_sequence;

CREATE OR REPLACE FUNCTION public.printora_emit_search_source_changed()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    event_sequence bigint;
    source_id text;
BEGIN
    IF TG_OP = 'DELETE' THEN
        source_id := OLD.id::text;
    ELSE
        source_id := NEW.id::text;
    END IF;
    event_sequence := nextval('public.search_outbox_sequence');
    INSERT INTO public.outbox_events (
        event_id, aggregate_type, aggregate_id, event_type, schema_version,
        ordering_key, sequence_no, payload_json, headers_json
    )
    VALUES (
        'search-source:' || event_sequence,
        'search_source',
        TG_TABLE_NAME || ':' || source_id,
        'search.source.changed',
        1,
        'search:index',
        event_sequence,
        jsonb_build_object('source', TG_TABLE_NAME, 'source_id', source_id, 'operation', lower(TG_OP))::text,
        jsonb_build_object('owner_type', 'search_index', 'owner_id', 'global')::text
    );
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trg_search_social_communities ON public.social_communities;
CREATE TRIGGER trg_search_social_communities AFTER INSERT OR UPDATE OR DELETE ON public.social_communities
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_social_feed_items ON public.social_feed_items;
CREATE TRIGGER trg_search_social_feed_items AFTER INSERT OR UPDATE OR DELETE ON public.social_feed_items
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_social_library_items ON public.social_library_items;
CREATE TRIGGER trg_search_social_library_items AFTER INSERT OR UPDATE OR DELETE ON public.social_library_items
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_social_library_files ON public.social_library_files;
CREATE TRIGGER trg_search_social_library_files AFTER INSERT OR UPDATE OR DELETE ON public.social_library_files
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_social_technical_configs ON public.social_technical_printer_configs;
CREATE TRIGGER trg_search_social_technical_configs AFTER INSERT OR UPDATE OR DELETE ON public.social_technical_printer_configs
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_social_material_profiles ON public.social_material_profiles;
CREATE TRIGGER trg_search_social_material_profiles AFTER INSERT OR UPDATE OR DELETE ON public.social_material_profiles
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_social_slicing_profiles ON public.social_slicing_profiles;
CREATE TRIGGER trg_search_social_slicing_profiles AFTER INSERT OR UPDATE OR DELETE ON public.social_slicing_profiles
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();

DROP TRIGGER IF EXISTS trg_search_catalog_variants ON public.catalog_printer_variants;
CREATE TRIGGER trg_search_catalog_variants AFTER INSERT OR UPDATE OR DELETE ON public.catalog_printer_variants
FOR EACH ROW EXECUTE FUNCTION public.printora_emit_search_source_changed();
