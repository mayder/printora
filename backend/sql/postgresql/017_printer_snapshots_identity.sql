-- PKG-96: corrige a identidade ausente de printer_snapshots no baseline legado.
-- Ordem: aplicado automaticamente após 016_analytics_intelligence.sql.
-- Impacto: lock curto somente na tabela de snapshots; não altera dados existentes.
-- Validação: inserir snapshot pela API e confirmar id, printer_id e payload.
-- Rollback: remover apenas o DEFAULT; preservar sequência e snapshots para evitar perda.

LOCK TABLE public.printer_snapshots IN SHARE ROW EXCLUSIVE MODE;

CREATE SEQUENCE IF NOT EXISTS public.printer_snapshots_id_seq;

DO $$
DECLARE
    snapshots_owner name;
BEGIN
    SELECT pg_get_userbyid(relowner)
    INTO snapshots_owner
    FROM pg_class
    WHERE oid = 'public.printer_snapshots'::regclass;

    EXECUTE format(
        'ALTER SEQUENCE public.printer_snapshots_id_seq OWNER TO %I',
        snapshots_owner
    );
END
$$;

ALTER SEQUENCE public.printer_snapshots_id_seq
    OWNED BY public.printer_snapshots.id;

ALTER TABLE public.printer_snapshots
    ALTER COLUMN id SET DEFAULT nextval('public.printer_snapshots_id_seq'::regclass);

SELECT setval(
    'public.printer_snapshots_id_seq',
    GREATEST(COALESCE((SELECT MAX(id) FROM public.printer_snapshots), 0), 1),
    EXISTS (SELECT 1 FROM public.printer_snapshots)
);
