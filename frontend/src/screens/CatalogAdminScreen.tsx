import React from "react";
import { Database, Edit3, Filter, Plus, RefreshCw, Save, ShieldCheck } from "lucide-react";
import { socialApi, type CatalogAdminFilters } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogAdminSummary, CatalogTrustState, CatalogVariantDetail } from "../types";

type CatalogAdminScreenProps = ScreenPropsFor<"authUser" | "setError" | "showToast">;
type CatalogMode = "list" | "detail" | "create" | "edit";

const trustStates: CatalogTrustState[] = ["official", "community", "draft", "obsolete", "blocked"];

export function CatalogAdminScreen({ authUser, setError, showToast }: CatalogAdminScreenProps) {
  const isAdmin = authUser?.email.toLowerCase() === "breno@mayder.com.br";
  const [catalog, setCatalog] = React.useState<CatalogAdminSummary>({ variants: [] });
  const [filters, setFilters] = React.useState<CatalogAdminFilters>({});
  const [mode, setMode] = React.useState<CatalogMode>("list");
  const [selectedId, setSelectedId] = React.useState<number | null>(null);
  const [busy, setBusy] = React.useState(false);
  const selected = catalog.variants.find((item) => item.id === selectedId) ?? catalog.variants[0] ?? null;
  const modelOptions = React.useMemo(() => {
    const map = new Map<number, string>();
    catalog.variants.forEach((variant) => map.set(variant.model_id, `${variant.manufacturer_name} · ${variant.model_name}`));
    return Array.from(map.entries()).map(([id, label]) => ({ id, label }));
  }, [catalog.variants]);

  async function loadCatalog(nextFilters = filters) {
    if (!isAdmin) return;
    setBusy(true);
    try {
      const payload = await socialApi.adminCatalog(nextFilters);
      setCatalog(payload);
      setSelectedId((current) => current ?? payload.variants[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar catálogo administrativo");
    } finally {
      setBusy(false);
    }
  }

  React.useEffect(() => {
    void loadCatalog();
  }, [isAdmin]);

  function updateFilter(key: keyof CatalogAdminFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function applyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadCatalog(filters);
    setMode("list");
  }

  async function submitVariant(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const payload = {
        name: String(form.get("name") || ""),
        build_volume: parseJsonObject(String(form.get("build_volume") || "{}"), "volume útil"),
        components: parseJsonObject(String(form.get("components") || "{}"), "componentes"),
        firmware_family: String(form.get("firmware_family") || "") || null,
        trust_state: String(form.get("trust_state") || "draft") as CatalogTrustState,
        source: String(form.get("source") || "admin_review"),
      };
      if (mode === "create") {
        await socialApi.createCatalogVariant({
          ...payload,
          model_id: Number(form.get("model_id")),
          slug: String(form.get("slug") || "") || null,
        });
      } else if (selected) {
        await socialApi.updateCatalogVariant(selected.id, payload);
      }
      await loadCatalog();
      setMode("list");
      showToast({ tone: "success", title: "Catálogo atualizado" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar catálogo");
    } finally {
      setBusy(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="catalog-admin-screen">
        <section className="catalog-admin-empty">
          <ShieldCheck size={22} />
          <h2>Curadoria restrita</h2>
          <p>Usuário comum pode consultar e vincular variantes, mas não edita o catálogo canônico.</p>
        </section>
      </div>
    );
  }

  return (
    <div className="catalog-admin-screen">
      <section className="catalog-admin-toolbar">
        <div>
          <span className="eyebrow">Catálogo mestre</span>
          <h2>Curadoria de impressoras e componentes</h2>
        </div>
        <div className="catalog-admin-actions">
          <button type="button" className="secondary-action" onClick={() => void loadCatalog()} disabled={busy}>
            <RefreshCw size={16} />
            Atualizar
          </button>
          <button type="button" className="primary-action" onClick={() => setMode("create")} disabled={busy || modelOptions.length === 0}>
            <Plus size={16} />
            Nova variante
          </button>
        </div>
      </section>

      <form className="catalog-filter-panel" onSubmit={applyFilters}>
        <Filter size={17} />
        <input placeholder="Fabricante" value={filters.manufacturer ?? ""} onChange={(event) => updateFilter("manufacturer", event.target.value)} />
        <input placeholder="Modelo" value={filters.model ?? ""} onChange={(event) => updateFilter("model", event.target.value)} />
        <input placeholder="Variante" value={filters.variant ?? ""} onChange={(event) => updateFilter("variant", event.target.value)} />
        <input placeholder="Componente" value={filters.component ?? ""} onChange={(event) => updateFilter("component", event.target.value)} />
        <select value={filters.trust_state ?? ""} onChange={(event) => updateFilter("trust_state", event.target.value)}>
          <option value="">Todos estados</option>
          {trustStates.map((state) => <option key={state} value={state}>{state}</option>)}
        </select>
        <button type="submit" className="secondary-action" disabled={busy}>Filtrar</button>
      </form>

      <section className="catalog-admin-layout">
        <VariantList variants={catalog.variants} selectedId={selectedId} onSelect={(variant) => { setSelectedId(variant.id); setMode("detail"); }} />
        {mode === "create" ? (
          <VariantForm mode="create" modelOptions={modelOptions} busy={busy} onSubmit={submitVariant} />
        ) : mode === "edit" && selected ? (
          <VariantForm mode="edit" variant={selected} modelOptions={modelOptions} busy={busy} onSubmit={submitVariant} />
        ) : (
          <VariantDetail variant={selected} onEdit={() => setMode("edit")} />
        )}
      </section>
    </div>
  );
}

function VariantList({ variants, selectedId, onSelect }: { variants: CatalogVariantDetail[]; selectedId: number | null; onSelect: (variant: CatalogVariantDetail) => void }) {
  return (
    <section className="catalog-list-panel">
      {variants.map((variant) => (
        <button key={variant.id} type="button" className={`catalog-list-row ${selectedId === variant.id ? "active" : ""}`} onClick={() => onSelect(variant)}>
          <strong>{variant.manufacturer_name} · {variant.model_name}</strong>
          <span>{variant.name}</span>
          <small>{variant.kinematics} · {variant.firmware_family ?? "-"} · {variant.trust_state}</small>
        </button>
      ))}
      {variants.length === 0 ? <p className="muted">Nenhuma variante encontrada.</p> : null}
    </section>
  );
}

function VariantDetail({ variant, onEdit }: { variant: CatalogVariantDetail | null; onEdit: () => void }) {
  if (!variant) {
    return <section className="catalog-detail-panel"><p className="muted">Selecione uma variante.</p></section>;
  }
  return (
    <section className="catalog-detail-panel">
      <header>
        <Database size={18} />
        <h3>{variant.name}</h3>
        <button type="button" className="secondary-action" onClick={onEdit}>
          <Edit3 size={15} />
          Curar
        </button>
      </header>
      <dl className="catalog-detail-grid">
        <div><dt>Fabricante</dt><dd>{variant.manufacturer_name}</dd></div>
        <div><dt>Modelo</dt><dd>{variant.model_name}</dd></div>
        <div><dt>Variante</dt><dd>{variant.slug}</dd></div>
        <div><dt>Cinemática</dt><dd>{variant.kinematics}</dd></div>
        <div><dt>Firmware</dt><dd>{variant.firmware_family ?? "-"}</dd></div>
        <div><dt>Estado</dt><dd>{variant.trust_state}</dd></div>
        <div><dt>Origem</dt><dd>{variant.source}</dd></div>
      </dl>
      <JsonBlock title="Volume útil" value={variant.build_volume} />
      <JsonBlock title="Componentes" value={variant.components} />
    </section>
  );
}

function VariantForm({ mode, variant, modelOptions, busy, onSubmit }: { mode: "create" | "edit"; variant?: CatalogVariantDetail; modelOptions: Array<{ id: number; label: string }>; busy: boolean; onSubmit: (event: React.FormEvent<HTMLFormElement>) => void }) {
  return (
    <form className="catalog-detail-panel catalog-form" onSubmit={onSubmit}>
      <header>
        <Save size={18} />
        <h3>{mode === "create" ? "Criar variante" : "Editar curadoria"}</h3>
      </header>
      {mode === "create" ? (
        <>
          <label>Modelo<select name="model_id" required>{modelOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>
          <label>Slug<input name="slug" maxLength={120} /></label>
        </>
      ) : null}
      <label>Nome<input name="name" defaultValue={variant?.name ?? ""} required maxLength={160} /></label>
      <label>Firmware<input name="firmware_family" defaultValue={variant?.firmware_family ?? "klipper"} maxLength={80} /></label>
      <label>Estado<select name="trust_state" defaultValue={variant?.trust_state ?? "draft"}>{trustStates.map((state) => <option key={state} value={state}>{state}</option>)}</select></label>
      <label>Origem<input name="source" defaultValue={variant?.source ?? "admin_review"} maxLength={120} /></label>
      <label>Volume útil JSON<textarea name="build_volume" defaultValue={JSON.stringify(variant?.build_volume ?? {}, null, 2)} /></label>
      <label>Componentes JSON<textarea name="components" defaultValue={JSON.stringify(variant?.components ?? {}, null, 2)} /></label>
      <button type="submit" className="primary-action" disabled={busy}>Salvar</button>
    </form>
  );
}

function JsonBlock({ title, value }: { title: string; value: Record<string, unknown> }) {
  return (
    <div className="catalog-json-block">
      <strong>{title}</strong>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </div>
  );
}

function parseJsonObject(value: string, label: string): Record<string, unknown> {
  const parsed = JSON.parse(value || "{}") as unknown;
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} deve ser um objeto JSON`);
  }
  return parsed as Record<string, unknown>;
}
