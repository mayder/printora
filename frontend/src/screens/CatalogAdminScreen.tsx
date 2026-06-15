import React from "react";
import { Boxes, Database, ExternalLink, FileText, Filter, GitBranch, Plus, RefreshCw, Save, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { socialApi, type CatalogAdminFilters } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogAdminSummary, CatalogModelAdmin, CatalogTrustState, CatalogVariant } from "../types";

type CatalogAdminScreenProps = ScreenPropsFor<"authUser" | "setError" | "showToast">;
type CatalogMode = "detail" | "create-variation" | "edit-variation";

const emptyCatalog: CatalogAdminSummary = { models: [], manufacturer_count: 0, model_count: 0, variant_count: 0 };
const trustStates: CatalogTrustState[] = ["official", "community", "draft", "obsolete", "blocked"];

export function CatalogAdminScreen({ authUser, setError, showToast }: CatalogAdminScreenProps) {
  const isAdmin = authUser?.email.toLowerCase() === "breno@mayder.com.br";
  const [catalog, setCatalog] = React.useState<CatalogAdminSummary>(emptyCatalog);
  const [filters, setFilters] = React.useState<CatalogAdminFilters>({});
  const [mode, setMode] = React.useState<CatalogMode>("detail");
  const [selectedModelId, setSelectedModelId] = React.useState<number | null>(null);
  const [selectedVariationId, setSelectedVariationId] = React.useState<number | null>(null);
  const [busy, setBusy] = React.useState(false);
  const selectedModel = catalog.models.find((item) => item.id === selectedModelId) ?? catalog.models[0] ?? null;
  const selectedVariation = selectedModel?.variants.find((item) => item.id === selectedVariationId) ?? selectedModel?.variants[0] ?? null;
  const modelOptions = catalog.models.map((model) => ({ id: model.id, label: `${model.manufacturer_name} · ${model.name}` }));

  async function loadCatalog(nextFilters = filters) {
    if (!isAdmin) return;
    setBusy(true);
    try {
      const payload = await socialApi.adminCatalog(nextFilters);
      setCatalog(payload);
      setSelectedModelId((current) => current && payload.models.some((model) => model.id === current) ? current : payload.models[0]?.id ?? null);
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
    setMode("detail");
  }

  async function submitVariation(event: React.FormEvent<HTMLFormElement>) {
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
        source: "admin_review",
      };
      if (mode === "create-variation") {
        await socialApi.createCatalogVariant({
          ...payload,
          model_id: Number(form.get("model_id")),
          slug: String(form.get("slug") || "") || null,
        });
      } else if (selectedVariation) {
        await socialApi.updateCatalogVariant(selectedVariation.id, payload);
      }
      await loadCatalog();
      setMode("detail");
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
          <p>Usuário comum pode consultar e vincular modelos, mas não edita o catálogo canônico.</p>
        </section>
      </div>
    );
  }

  return (
    <div className="catalog-admin-screen">
      <section className="catalog-admin-toolbar">
        <div className="catalog-admin-title">
          <span className="eyebrow">Catálogo mestre</span>
          <h2>Impressoras DIY e componentes</h2>
          <p>{catalog.manufacturer_count} fabricantes · {catalog.model_count} modelos · {catalog.variant_count} variações técnicas</p>
        </div>
        <div className="catalog-admin-actions">
          <button type="button" className="secondary-action" onClick={() => void loadCatalog()} disabled={busy}>
            <RefreshCw size={16} />
            Atualizar
          </button>
          <button type="button" className="primary-action" onClick={() => setMode("create-variation")} disabled={busy || modelOptions.length === 0}>
            <Plus size={16} />
            Nova variação
          </button>
        </div>
      </section>

      <form className="catalog-filter-panel" onSubmit={applyFilters}>
        <Filter size={17} />
        <input placeholder="Fabricante" value={filters.manufacturer ?? ""} onChange={(event) => updateFilter("manufacturer", event.target.value)} />
        <input placeholder="Modelo" value={filters.model ?? ""} onChange={(event) => updateFilter("model", event.target.value)} />
        <input placeholder="Tamanho ou versão" value={filters.variant ?? ""} onChange={(event) => updateFilter("variant", event.target.value)} />
        <input placeholder="Componente" value={filters.component ?? ""} onChange={(event) => updateFilter("component", event.target.value)} />
        <select value={filters.trust_state ?? ""} onChange={(event) => updateFilter("trust_state", event.target.value)}>
          <option value="">Todos estados</option>
          {trustStates.map((state) => <option key={state} value={state}>{state}</option>)}
        </select>
        <button type="submit" className="secondary-action" disabled={busy}>Filtrar</button>
      </form>

      <section className="catalog-admin-layout">
        <ModelList models={catalog.models} selectedModelId={selectedModel?.id ?? null} onSelect={(model) => { setSelectedModelId(model.id); setSelectedVariationId(null); setMode("detail"); }} />
        {mode === "create-variation" ? (
          <VariationForm mode="create-variation" modelOptions={modelOptions} busy={busy} onSubmit={submitVariation} />
        ) : mode === "edit-variation" && selectedVariation ? (
          <VariationForm mode="edit-variation" variation={selectedVariation} modelOptions={modelOptions} busy={busy} onSubmit={submitVariation} />
        ) : (
          <ModelDetail model={selectedModel} onEditVariation={(variation) => { setSelectedVariationId(variation.id); setMode("edit-variation"); }} />
        )}
      </section>
    </div>
  );
}

function ModelList({ models, selectedModelId, onSelect }: { models: CatalogModelAdmin[]; selectedModelId: number | null; onSelect: (model: CatalogModelAdmin) => void }) {
  return (
    <section className="catalog-list-panel">
      <header className="catalog-list-heading">
        <strong>Modelos</strong>
        <span>{models.length} itens</span>
      </header>
      {models.map((model) => (
        <button key={model.id} type="button" className={`catalog-list-row ${selectedModelId === model.id ? "active" : ""}`} onClick={() => onSelect(model)}>
          <span className="catalog-row-maker">{model.manufacturer_name}</span>
          <strong className="catalog-row-variant">{model.name}</strong>
          <span className="catalog-row-meta">
            <span>{model.kinematics}</span>
            <span>{model.variants.length} variações</span>
            <span className={`catalog-state state-${model.trust_state}`}>{model.trust_state}</span>
          </span>
        </button>
      ))}
      {models.length === 0 ? <p className="muted">Nenhum modelo encontrado.</p> : null}
    </section>
  );
}

function ModelDetail({ model, onEditVariation }: { model: CatalogModelAdmin | null; onEditVariation: (variation: CatalogVariant) => void }) {
  if (!model) {
    return <section className="catalog-detail-panel"><p className="muted">Selecione um modelo.</p></section>;
  }
  return (
    <section className="catalog-detail-panel">
      <header className="catalog-detail-heading">
        <div>
          <span className="eyebrow">{model.manufacturer_name}</span>
          <h3>{model.name}</h3>
          <p>{model.description ?? "Modelo DIY com configuração dependente da curadoria e do build real."}</p>
        </div>
        <span className={`catalog-state state-${model.trust_state}`}>{model.trust_state}</span>
      </header>

      <section className="catalog-link-strip">
        <CatalogLink icon={ExternalLink} label="Site fabricante" url={model.manufacturer_website_url} />
        <CatalogLink icon={GitBranch} label="Git fabricante" url={model.manufacturer_repository_url} />
        <CatalogLink icon={ExternalLink} label="Site modelo" url={model.website_url} />
        <CatalogLink icon={GitBranch} label="Git modelo" url={model.repository_url} />
        <CatalogLink icon={FileText} label="Documentação" url={model.documentation_url ?? model.manufacturer_documentation_url} />
        <CatalogLink icon={Boxes} label="BOM" url={model.bom_url} />
      </section>

      <dl className="catalog-detail-grid">
        <div><dt>Fabricante</dt><dd>{model.manufacturer_name}</dd></div>
        <div><dt>Modelo</dt><dd>{model.name}</dd></div>
        <div><dt>Cinemática</dt><dd>{model.kinematics}</dd></div>
        <div><dt>Estado</dt><dd>{model.trust_state}</dd></div>
        <div><dt>Variações</dt><dd>{model.variants.length}</dd></div>
      </dl>

      <section className="catalog-variations-panel">
        <header>
          <Database size={17} />
          <strong>Variações de tamanho e configuração</strong>
        </header>
        <div className="catalog-variation-table">
          <div className="catalog-variation-head">
            <span>Nome</span>
            <span>Volume</span>
            <span>Firmware</span>
            <span>Estado</span>
            <span>Ação</span>
          </div>
          {model.variants.map((variation) => (
            <div className="catalog-variation-row" key={variation.id}>
              <strong>{variation.name}</strong>
              <span>{formatVolume(variation.build_volume)}</span>
              <span>{variation.firmware_family ?? "-"}</span>
              <span className={`catalog-state state-${variation.trust_state}`}>{variation.trust_state}</span>
              <button type="button" className="secondary-action compact" onClick={() => onEditVariation(variation)}>Curar</button>
            </div>
          ))}
        </div>
      </section>

      <section className="catalog-components-grid">
        {model.variants.slice(0, 4).map((variation) => (
          <JsonBlock key={variation.id} title={`Componentes · ${variation.name}`} value={variation.components} />
        ))}
      </section>
    </section>
  );
}

function CatalogLink({ icon: Icon, label, url }: { icon: LucideIcon; label: string; url: string | null }) {
  if (!url) {
    return <span className="catalog-link disabled"><Icon size={15} />{label}</span>;
  }
  return (
    <a className="catalog-link" href={url} target="_blank" rel="noreferrer">
      <Icon size={15} />
      {label}
    </a>
  );
}

function VariationForm({ mode, variation, modelOptions, busy, onSubmit }: { mode: "create-variation" | "edit-variation"; variation?: CatalogVariant; modelOptions: Array<{ id: number; label: string }>; busy: boolean; onSubmit: (event: React.FormEvent<HTMLFormElement>) => void }) {
  return (
    <form className="catalog-detail-panel catalog-form" onSubmit={onSubmit}>
      <header>
        <Save size={18} />
        <h3>{mode === "create-variation" ? "Criar variação" : "Editar variação"}</h3>
      </header>
      {mode === "create-variation" ? (
        <>
          <label>Modelo<select name="model_id" required>{modelOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>
          <label>Slug técnico<input name="slug" maxLength={120} /></label>
        </>
      ) : null}
      <label>Nome<input name="name" defaultValue={variation?.name ?? ""} required maxLength={160} /></label>
      <label>Firmware<input name="firmware_family" defaultValue={variation?.firmware_family ?? "klipper"} maxLength={80} /></label>
      <label>Estado<select name="trust_state" defaultValue={variation?.trust_state ?? "draft"}>{trustStates.map((state) => <option key={state} value={state}>{state}</option>)}</select></label>
      <label>Volume útil JSON<textarea name="build_volume" defaultValue={JSON.stringify(variation?.build_volume ?? {}, null, 2)} /></label>
      <label>Componentes JSON<textarea name="components" defaultValue={JSON.stringify(variation?.components ?? {}, null, 2)} /></label>
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

function formatVolume(value: Record<string, unknown>) {
  const x = value.x ?? "-";
  const y = value.y ?? "-";
  const z = value.z ?? "-";
  return `${x} x ${y} x ${z} mm`;
}

function parseJsonObject(value: string, label: string): Record<string, unknown> {
  const parsed = JSON.parse(value || "{}") as unknown;
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} deve ser um objeto JSON`);
  }
  return parsed as Record<string, unknown>;
}
