import React from "react";
import { ArrowLeft, Boxes, Check, ChevronDown, Database, ExternalLink, Eye, FileText, Filter, GitBranch, RefreshCw, Search, ShieldCheck, SlidersHorizontal } from "lucide-react";
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
  const [detailModelSlug, setDetailModelSlug] = React.useState<string | null>(() => new URLSearchParams(window.location.search).get("model"));
  const [busy, setBusy] = React.useState(false);

  const selectedModel = catalog.models.find((item) => item.id === selectedModelId) ?? catalog.models[0] ?? null;
  const detailModel = detailModelSlug ? referenceCatalog.models.find((item) => item.slug === detailModelSlug) ?? catalog.models.find((item) => item.slug === detailModelSlug) ?? null : null;
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

  function openModelDetail(model: CatalogModelAdmin) {
    setSelectedModelId(model.id);
    setDetailModelSlug(model.slug);
    window.history.pushState(null, "", `?section=catalog&model=${encodeURIComponent(model.slug)}`);
  }

  function closeModelDetail() {
    setDetailModelSlug(null);
    window.history.pushState(null, "", "?section=catalog");
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

      {detailModel ? (
        <CatalogDetailView model={detailModel} onBack={closeModelDetail} />
      ) : (
        <>

          <form className="catalog-filter-panel" onSubmit={applyFilters}>
            <div className="catalog-filter-title">
              <Filter size={17} />
              <strong>Filtros</strong>
            </div>
            <SearchSelectField label="Fabricante" placeholder="Todos fabricantes" value={filters.manufacturer ?? ""} options={filterOptions.manufacturers.map((item) => ({ value: item.slug, label: item.name }))} onChange={(value) => updateFilter("manufacturer", value)} />
            <SearchSelectField
              label="Modelo"
              placeholder="Todos modelos"
              value={filters.model ?? ""}
              options={modelOptions.map((item) => ({ value: item.slug, label: filters.manufacturer ? item.name : `${item.manufacturer_name} · ${item.name}` }))}
              onChange={(value) => updateFilter("model", value)}
              disabled={modelOptions.length === 0}
            />
            <SearchSelectField
              label="Tamanho / versão"
              placeholder="Todas variações"
              value={filters.variant ?? ""}
              options={variationOptions.map((item) => ({
                value: item.slug,
                label: filters.model ? item.name : `${filters.manufacturer ? item.model_name : `${item.manufacturer_name} · ${item.model_name}`} · ${item.name}`,
              }))}
              onChange={(value) => updateFilter("variant", value)}
              disabled={variationOptions.length === 0}
            />
            <SearchSelectField label="Componente" placeholder="Todos componentes" value={filters.component ?? ""} options={filterOptions.components.map((component) => ({ value: component, label: componentLabel(component) }))} onChange={(value) => updateFilter("component", value)} />
            <SearchSelectField label="Cinemática" placeholder="Todas cinemáticas" value={filters.kinematics ?? ""} options={filterOptions.kinematics.map((kinematics) => ({ value: kinematics, label: kinematics }))} onChange={(value) => updateFilter("kinematics", value)} />
            <SearchSelectField label="Firmware" placeholder="Todos firmwares" value={filters.firmware_family ?? ""} options={filterOptions.firmwareFamilies.map((firmware) => ({ value: firmware, label: firmware }))} onChange={(value) => updateFilter("firmware_family", value)} />
            <SearchSelectField label="Estado" placeholder="Todos estados" value={filters.trust_state ?? ""} options={trustStates.map((state) => ({ value: state, label: state }))} onChange={(value) => updateFilter("trust_state", value)} />
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
            <ModelTable models={catalog.models} selectedModelId={selectedModel?.id ?? null} onSelect={openModelDetail} />
          </section>
        </>
      )}
    </div>
  );
}

function SearchSelectField({ label, placeholder, value, options, onChange, disabled = false }: { label: string; placeholder: string; value: string; options: Array<{ value: string; label: string }>; onChange: (value: string) => void; disabled?: boolean }) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const fieldRef = React.useRef<HTMLDivElement | null>(null);
  const selected = options.find((option) => option.value === value);
  const normalizedQuery = normalizeSearch(query);
  const visibleOptions = normalizedQuery ? options.filter((option) => normalizeSearch(option.label).includes(normalizedQuery)) : options;

  React.useEffect(() => {
    function onDocumentPointerDown(event: PointerEvent) {
      if (fieldRef.current && !fieldRef.current.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("pointerdown", onDocumentPointerDown);
    return () => document.removeEventListener("pointerdown", onDocumentPointerDown);
  }, []);

  function selectValue(nextValue: string) {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  }

  return (
    <div className="catalog-select-field catalog-search-select" ref={fieldRef}>
      <span>{label}</span>
      <button type="button" className="catalog-search-select-button" onClick={() => !disabled && setOpen((current) => !current)} disabled={disabled}>
        <span>{selected?.label ?? placeholder}</span>
        <ChevronDown size={15} />
      </button>
      {open ? (
        <div className="catalog-search-select-menu">
          <div className="catalog-search-select-input">
            <Search size={14} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar..." autoFocus />
          </div>
          <button type="button" className={`catalog-search-option ${value ? "" : "active"}`} onClick={() => selectValue("")}>
            <span>{placeholder}</span>
            {!value ? <Check size={14} /> : null}
          </button>
          <div className="catalog-search-options">
            {visibleOptions.map((option) => (
              <button key={option.value} type="button" className={`catalog-search-option ${option.value === value ? "active" : ""}`} onClick={() => selectValue(option.value)}>
                <span>{option.label}</span>
                {option.value === value ? <Check size={14} /> : null}
              </button>
            ))}
            {visibleOptions.length === 0 ? <div className="catalog-search-empty">Nenhum resultado.</div> : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ModelTable({ models, selectedModelId, onSelect }: { models: CatalogModelAdmin[]; selectedModelId: number | null; onSelect: (model: CatalogModelAdmin) => void }) {
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
        <div
          key={model.id}
          className={`catalog-table-row ${selectedModelId === model.id ? "active" : ""}`}
          onClick={() => onSelect(model)}
          role="row"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onSelect(model);
            }
          }}
        >
          <span>{model.manufacturer_name}</span>
          <strong>{model.name}</strong>
          <span>{model.kinematics}</span>
          <span>{model.variants.length}</span>
          <span>{formatFirmwareSummary(model.variants)}</span>
          <span><span className={`catalog-state state-${model.trust_state}`}>{model.trust_state}</span></span>
          <span>
            <a
              className="catalog-row-action-button"
              href={`?section=catalog&model=${encodeURIComponent(model.slug)}`}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                onSelect(model);
              }}
            >
              <Eye size={15} />
              Abrir
            </a>
          </span>
        </div>
      ))}
    </div>
  );
}

function CatalogDetailView({ model, onBack }: { model: CatalogModelAdmin; onBack: () => void }) {
  return (
    <section className="catalog-detail-panel">
      <button type="button" className="catalog-back-button secondary-action" onClick={onBack}>
        <ArrowLeft size={16} />
        Voltar para listagem
      </button>
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
  const modelOptions: Array<{ slug: string; name: string; manufacturer_slug: string; manufacturer_name: string }> = [];
  const variationOptions: Array<{ slug: string; name: string; model_slug: string; model_name: string; manufacturer_slug: string; manufacturer_name: string }> = [];
  const components = new Set<string>();
  const kinematics = new Set<string>();
  const firmwareFamilies = new Set<string>();

  models.forEach((model) => {
    manufacturers.set(model.manufacturer_slug, model.manufacturer_name);
    modelOptions.push({ slug: model.slug, name: model.name, manufacturer_slug: model.manufacturer_slug, manufacturer_name: model.manufacturer_name });
    kinematics.add(model.kinematics);
    model.variants.forEach((variation) => {
      variationOptions.push({
        slug: variation.slug,
        name: variation.name,
        model_slug: model.slug,
        model_name: model.name,
        manufacturer_slug: model.manufacturer_slug,
        manufacturer_name: model.manufacturer_name,
      });
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

function normalizeSearch(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function byName<T extends { name: string }>(left: T, right: T) {
  return left.name.localeCompare(right.name, "pt-BR");
}
