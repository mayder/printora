import React from "react";
import { Boxes, Database, ExternalLink, FileText, Filter, GitBranch, RefreshCw, ShieldCheck, SlidersHorizontal } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { socialApi, type CatalogAdminFilters } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogAdminSummary, CatalogModelAdmin, CatalogTrustState, CatalogVariant } from "../types";

type CatalogAdminScreenProps = ScreenPropsFor<"authUser" | "setError">;

const emptyCatalog: CatalogAdminSummary = { models: [], manufacturer_count: 0, model_count: 0, variant_count: 0 };
const trustStates: CatalogTrustState[] = ["official", "community", "draft", "obsolete", "blocked"];

export function CatalogAdminScreen({ authUser, setError }: CatalogAdminScreenProps) {
  const isAdmin = authUser?.email.toLowerCase() === "breno@mayder.com.br";
  const [catalog, setCatalog] = React.useState<CatalogAdminSummary>(emptyCatalog);
  const [referenceCatalog, setReferenceCatalog] = React.useState<CatalogAdminSummary>(emptyCatalog);
  const [filters, setFilters] = React.useState<CatalogAdminFilters>({});
  const [selectedModelId, setSelectedModelId] = React.useState<number | null>(null);
  const [busy, setBusy] = React.useState(false);

  const selectedModel = catalog.models.find((item) => item.id === selectedModelId) ?? catalog.models[0] ?? null;
  const filterOptions = React.useMemo(() => buildFilterOptions(referenceCatalog.models), [referenceCatalog.models]);
  const modelOptions = React.useMemo(
    () => filterOptions.models.filter((option) => !filters.manufacturer || option.manufacturer_slug === filters.manufacturer),
    [filterOptions.models, filters.manufacturer],
  );
  const variationOptions = React.useMemo(
    () => filterOptions.variations.filter((option) => {
      if (filters.manufacturer && option.manufacturer_slug !== filters.manufacturer) return false;
      if (filters.model && option.model_slug !== filters.model) return false;
      return true;
    }),
    [filterOptions.variations, filters.manufacturer, filters.model],
  );

  async function loadCatalog(nextFilters = filters) {
    if (!isAdmin) return;
    setBusy(true);
    try {
      const [referencePayload, filteredPayload] = await Promise.all([
        referenceCatalog.models.length ? Promise.resolve(referenceCatalog) : socialApi.adminCatalog(),
        socialApi.adminCatalog(nextFilters),
      ]);
      setReferenceCatalog(referencePayload);
      setCatalog(filteredPayload);
      setSelectedModelId((current) => current && filteredPayload.models.some((model) => model.id === current) ? current : filteredPayload.models[0]?.id ?? null);
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
    setFilters((current) => {
      const next = { ...current, [key]: value || undefined };
      if (key === "manufacturer") {
        next.model = undefined;
        next.variant = undefined;
      }
      if (key === "model") {
        next.variant = undefined;
      }
      return next;
    });
  }

  async function applyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadCatalog(filters);
  }

  async function clearFilters() {
    setFilters({});
    await loadCatalog({});
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
        </div>
      </section>

      <form className="catalog-filter-panel" onSubmit={applyFilters}>
        <div className="catalog-filter-title">
          <Filter size={17} />
          <strong>Filtros</strong>
        </div>
        <SelectField label="Fabricante" value={filters.manufacturer ?? ""} onChange={(value) => updateFilter("manufacturer", value)}>
          <option value="">Todos fabricantes</option>
          {filterOptions.manufacturers.map((manufacturer) => (
            <option key={manufacturer.slug} value={manufacturer.slug}>{manufacturer.name}</option>
          ))}
        </SelectField>
        <SelectField label="Modelo" value={filters.model ?? ""} onChange={(value) => updateFilter("model", value)}>
          <option value="">Todos modelos</option>
          {modelOptions.map((model) => (
            <option key={`${model.manufacturer_slug}:${model.slug}`} value={model.slug}>{model.name}</option>
          ))}
        </SelectField>
        <SelectField label="Tamanho / versão" value={filters.variant ?? ""} onChange={(value) => updateFilter("variant", value)}>
          <option value="">Todas variações</option>
          {variationOptions.map((variation) => (
            <option key={`${variation.model_slug}:${variation.slug}`} value={variation.slug}>{variation.name}</option>
          ))}
        </SelectField>
        <SelectField label="Componente" value={filters.component ?? ""} onChange={(value) => updateFilter("component", value)}>
          <option value="">Todos componentes</option>
          {filterOptions.components.map((component) => (
            <option key={component} value={component}>{componentLabel(component)}</option>
          ))}
        </SelectField>
        <SelectField label="Cinemática" value={filters.kinematics ?? ""} onChange={(value) => updateFilter("kinematics", value)}>
          <option value="">Todas cinemáticas</option>
          {filterOptions.kinematics.map((kinematics) => (
            <option key={kinematics} value={kinematics}>{kinematics}</option>
          ))}
        </SelectField>
        <SelectField label="Firmware" value={filters.firmware_family ?? ""} onChange={(value) => updateFilter("firmware_family", value)}>
          <option value="">Todos firmwares</option>
          {filterOptions.firmwareFamilies.map((firmware) => (
            <option key={firmware} value={firmware}>{firmware}</option>
          ))}
        </SelectField>
        <SelectField label="Estado" value={filters.trust_state ?? ""} onChange={(value) => updateFilter("trust_state", value)}>
          <option value="">Todos estados</option>
          {trustStates.map((state) => <option key={state} value={state}>{state}</option>)}
        </SelectField>
        <div className="catalog-filter-actions">
          <button type="button" className="secondary-action" onClick={() => void clearFilters()} disabled={busy}>
            Limpar
          </button>
          <button type="submit" className="primary-action" disabled={busy}>
            <SlidersHorizontal size={16} />
            Aplicar
          </button>
        </div>
      </form>

      <section className="catalog-results-panel">
        <header className="catalog-section-heading">
          <div>
            <span className="eyebrow">Listagem</span>
            <h3>Modelos cadastrados</h3>
          </div>
          <span>{catalog.models.length} itens</span>
        </header>
        <ModelTable models={catalog.models} selectedModelId={selectedModel?.id ?? null} onSelect={setSelectedModelId} />
      </section>

      <ModelDetail model={selectedModel} />
    </div>
  );
}

function SelectField({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <label className="catalog-select-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
    </label>
  );
}

function ModelTable({ models, selectedModelId, onSelect }: { models: CatalogModelAdmin[]; selectedModelId: number | null; onSelect: (modelId: number) => void }) {
  if (models.length === 0) {
    return <div className="catalog-empty-state">Nenhum modelo encontrado para os filtros selecionados.</div>;
  }
  return (
    <div className="catalog-table" role="table" aria-label="Modelos do catálogo">
      <div className="catalog-table-header" role="row">
        <span>Fabricante</span>
        <span>Modelo</span>
        <span>Cinemática</span>
        <span>Variações</span>
        <span>Firmware</span>
        <span>Estado</span>
        <span>Ações</span>
      </div>
      {models.map((model) => (
        <button
          type="button"
          key={model.id}
          className={`catalog-table-row ${selectedModelId === model.id ? "active" : ""}`}
          onClick={() => onSelect(model.id)}
          role="row"
        >
          <span>{model.manufacturer_name}</span>
          <strong>{model.name}</strong>
          <span>{model.kinematics}</span>
          <span>{model.variants.length}</span>
          <span>{formatFirmwareSummary(model.variants)}</span>
          <span><span className={`catalog-state state-${model.trust_state}`}>{model.trust_state}</span></span>
          <span className="catalog-row-actions">Detalhar</span>
        </button>
      ))}
    </div>
  );
}

function ModelDetail({ model }: { model: CatalogModelAdmin | null }) {
  if (!model) {
    return (
      <section className="catalog-detail-panel">
        <p className="muted">Selecione um modelo na listagem para ver o detalhe.</p>
      </section>
    );
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
          </div>
          {model.variants.map((variation) => (
            <div className="catalog-variation-row" key={variation.id}>
              <strong>{variation.name}</strong>
              <span>{formatVolume(variation.build_volume)}</span>
              <span>{variation.firmware_family ?? "-"}</span>
              <span className={`catalog-state state-${variation.trust_state}`}>{variation.trust_state}</span>
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

function JsonBlock({ title, value }: { title: string; value: Record<string, unknown> }) {
  return (
    <div className="catalog-json-block">
      <strong>{title}</strong>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </div>
  );
}

function buildFilterOptions(models: CatalogModelAdmin[]) {
  const manufacturers = new Map<string, string>();
  const modelOptions: Array<{ slug: string; name: string; manufacturer_slug: string }> = [];
  const variationOptions: Array<{ slug: string; name: string; model_slug: string; manufacturer_slug: string }> = [];
  const components = new Set<string>();
  const kinematics = new Set<string>();
  const firmwareFamilies = new Set<string>();

  models.forEach((model) => {
    manufacturers.set(model.manufacturer_slug, model.manufacturer_name);
    modelOptions.push({ slug: model.slug, name: model.name, manufacturer_slug: model.manufacturer_slug });
    kinematics.add(model.kinematics);
    model.variants.forEach((variation) => {
      variationOptions.push({ slug: variation.slug, name: variation.name, model_slug: model.slug, manufacturer_slug: model.manufacturer_slug });
      if (variation.firmware_family) firmwareFamilies.add(variation.firmware_family);
      Object.keys(variation.components).forEach((component) => components.add(component));
    });
  });

  return {
    manufacturers: Array.from(manufacturers.entries()).map(([slug, name]) => ({ slug, name })).sort(byName),
    models: modelOptions.sort(byName),
    variations: variationOptions.sort(byName),
    components: Array.from(components).sort(),
    kinematics: Array.from(kinematics).sort(),
    firmwareFamilies: Array.from(firmwareFamilies).sort(),
  };
}

function formatVolume(value: Record<string, unknown>) {
  const x = value.x ?? "-";
  const y = value.y ?? "-";
  const z = value.z ?? "-";
  return `${x} x ${y} x ${z} mm`;
}

function formatFirmwareSummary(variants: CatalogVariant[]) {
  const firmware = Array.from(new Set(variants.map((variation) => variation.firmware_family).filter(Boolean)));
  return firmware.length ? firmware.join(", ") : "-";
}

function componentLabel(value: string) {
  const labels: Record<string, string> = {
    bed: "Mesa",
    extruder: "Extrusor",
    hotend: "Hotend",
    kinematics: "Cinemática",
    mainboard: "Mainboard",
    mcu: "MCU",
    probe: "Probe",
    toolhead: "Toolhead",
  };
  return labels[value] ?? value;
}

function byName<T extends { name: string }>(left: T, right: T) {
  return left.name.localeCompare(right.name, "pt-BR");
}
