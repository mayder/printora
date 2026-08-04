-- Corrige a identidade ausente nas tabelas centrais de projetos importadas do
-- baseline legado. O lock impede concorrencia entre MAX(id) e o ajuste das
-- sequencias; nenhuma linha existente e alterada ou removida.

DO $$
DECLARE
    target_table text;
    target_sequence text;
    table_owner name;
BEGIN
    LOCK TABLE
        public.print_projects,
        public.print_project_files,
        public.print_project_versions,
        public.print_project_community_shares,
        public.print_project_saves,
        public.print_project_publication_reviews
    IN SHARE ROW EXCLUSIVE MODE;

    FOREACH target_table IN ARRAY ARRAY[
        'print_projects',
        'print_project_files',
        'print_project_versions',
        'print_project_community_shares',
        'print_project_saves',
        'print_project_publication_reviews'
    ]
    LOOP
        target_sequence := target_table || '_id_seq';

        EXECUTE format(
            'CREATE SEQUENCE IF NOT EXISTS public.%I',
            target_sequence
        );

        SELECT pg_get_userbyid(relowner)
        INTO table_owner
        FROM pg_class
        WHERE oid = format('public.%I', target_table)::regclass;

        EXECUTE format(
            'ALTER SEQUENCE public.%I OWNER TO %I',
            target_sequence,
            table_owner
        );
        EXECUTE format(
            'ALTER SEQUENCE public.%I OWNED BY public.%I.id',
            target_sequence,
            target_table
        );
        EXECUTE format(
            'ALTER TABLE public.%I ALTER COLUMN id SET DEFAULT nextval(%L::regclass)',
            target_table,
            'public.' || target_sequence
        );
        EXECUTE format(
            'SELECT setval(%L::regclass, GREATEST(COALESCE(MAX(id), 0), 1), COUNT(*) > 0) FROM public.%I',
            'public.' || target_sequence,
            target_table
        );
    END LOOP;
END
$$;
