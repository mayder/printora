import React from "react";
import { ArrowLeft, Boxes, Check, ChevronDown, ChevronLeft, ChevronRight, Database, ExternalLink, Eye, FileText, Filter, GitBranch, Info, MessageCircle, RefreshCw, Search, ShieldCheck, SlidersHorizontal, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { socialApi, type CatalogAdminFilters } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogAdminSummary, CatalogModelAdmin, CatalogTrustState, CatalogVariant } from "../types";

type CatalogAdminScreenProps = ScreenPropsFor<"authUser" | "setError">;

const emptyCatalog: CatalogAdminSummary = { models: [], manufacturer_count: 0, model_count: 0, variant_count: 0 };
const trustStates: CatalogTrustState[] = ["official", "community", "draft", "obsolete", "blocked"];
const catalogPageSize = 10;
const catalogFilterKeys: Array<keyof CatalogAdminFilters> = ["manufacturer", "model", "variant", "component", "kinematics", "firmware_family", "trust_state"];

export function CatalogAdminScreen({ authUser, setError }: CatalogAdminScreenProps) {
  const isAdmin = authUser?.email.toLowerCase() === "breno@mayder.com.br";
  const [catalog, setCatalog] = React.useState<CatalogAdminSummary>(emptyCatalog);
  const [referenceCatalog, setReferenceCatalog] = React.useState<CatalogAdminSummary>(emptyCatalog);
  const [filters, setFilters] = React.useState<CatalogAdminFilters>(() => readCatalogFiltersFromUrl());
  const [page, setPage] = React.useState(() => readCatalogPageFromUrl());
  const [selectedModelId, setSelectedModelId] = React.useState<number | null>(null);
  const [detailModelSlug, setDetailModelSlug] = React.useState<string | null>(() => readCatalogDetailSlugFromUrl());
  const [busy, setBusy] = React.useState(false);

  const selectedModel = catalog.models.find((item) => item.id === selectedModelId) ?? catalog.models[0] ?? null;
  const detailModel = detailModelSlug ? referenceCatalog.models.find((item) => item.slug === detailModelSlug) ?? catalog.models.find((item) => item.slug === detailModelSlug) ?? null : null;
  const totalPages = Math.max(1, Math.ceil(catalog.models.length / catalogPageSize));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * catalogPageSize;
  const pageModels = catalog.models.slice(pageStart, pageStart + catalogPageSize);
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

  React.useEffect(() => {
    if (page > totalPages) {
      changePage(totalPages, true);
    }
  }, [page, totalPages]);

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
    setPage(1);
    updateCatalogUrl(filters, 1, detailModelSlug, true);
    await loadCatalog(filters);
  }

  async function clearFilters() {
    setFilters({});
    setPage(1);
    updateCatalogUrl({}, 1, null, true);
    await loadCatalog({});
  }

  function openModelDetail(model: CatalogModelAdmin) {
    setSelectedModelId(model.id);
    setDetailModelSlug(model.slug);
    updateCatalogUrl(filters, safePage, model.slug);
  }

  function closeModelDetail() {
    setDetailModelSlug(null);
    updateCatalogUrl(filters, safePage);
  }

  function changePage(nextPage: number, replace = false) {
    const boundedPage = Math.min(Math.max(nextPage, 1), totalPages);
    setPage(boundedPage);
    updateCatalogUrl(filters, boundedPage, detailModelSlug, replace);
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
            <ModelTable models={pageModels} selectedModelId={selectedModel?.id ?? null} onSelect={openModelDetail} />
            <CatalogPagination page={safePage} pageSize={catalogPageSize} totalItems={catalog.models.length} onPageChange={changePage} />
          </section>
        </>
      )}
    </div>
  );
}

function CatalogPagination({ page, pageSize, totalItems, onPageChange }: { page: number; pageSize: number; totalItems: number; onPageChange: (page: number) => void }) {
  if (totalItems <= pageSize) {
    return null;
  }
  const totalPages = Math.ceil(totalItems / pageSize);
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(totalItems, page * pageSize);
  return (
    <footer className="catalog-pagination">
      <span>{start}-{end} de {totalItems}</span>
      <div className="catalog-pagination-actions">
        <button type="button" className="secondary-action catalog-page-button" onClick={() => onPageChange(page - 1)} disabled={page <= 1} aria-label="Página anterior">
          <ChevronLeft size={16} />
        </button>
        <span>Página {page} de {totalPages}</span>
        <button type="button" className="secondary-action catalog-page-button" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} aria-label="Próxima página">
          <ChevronRight size={16} />
        </button>
      </div>
    </footer>
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

      <section className="catalog-profile-grid">
        <section className="catalog-profile-card">
          <header>
            <CatalogLogo name={model.manufacturer_name} logoUrl={model.manufacturer_logo_url} />
            <div>
              <span className="eyebrow">Fabricante</span>
              <h4>{model.manufacturer_name}</h4>
            </div>
          </header>
          <p>{model.manufacturer_summary ?? "Fabricante ou projeto comunitário do catálogo DIY. Complete a curadoria com site, repositório e canais oficiais quando confirmados."}</p>
          <div className="catalog-link-list">
            <CatalogLink icon={ExternalLink} label="Site oficial" url={model.manufacturer_website_url} />
            <CatalogLink icon={GitBranch} label="GitHub" url={model.manufacturer_repository_url} />
            <CatalogLink icon={FileText} label="Documentação" url={model.manufacturer_documentation_url} />
            <CatalogLink icon={MessageCircle} label="Discord" url={model.manufacturer_discord_url} />
            <CatalogLink icon={Users} label="Reddit" url={model.manufacturer_reddit_url} />
          </div>
        </section>

        <section className="catalog-profile-card">
          <header>
            <CatalogLogo name={model.name} logoUrl={model.image_url ?? model.manufacturer_logo_url} />
            <div>
              <span className="eyebrow">Impressora</span>
              <h4>{model.name}</h4>
            </div>
          </header>
          <p>{model.description ?? "Modelo DIY com configuração dependente da curadoria e do build real."}</p>
          <div className="catalog-link-list">
            <CatalogLink icon={ExternalLink} label="Página do modelo" url={model.website_url} />
            <CatalogLink icon={GitBranch} label="Git do projeto" url={model.repository_url} />
            <CatalogLink icon={FileText} label="Documentação" url={model.documentation_url ?? model.manufacturer_documentation_url} />
            <CatalogLink icon={Boxes} label="BOM" url={model.bom_url} />
            <CatalogLink icon={MessageCircle} label="Discord" url={model.discord_url ?? model.manufacturer_discord_url} />
            <CatalogLink icon={Users} label="Reddit" url={model.reddit_url ?? model.manufacturer_reddit_url} />
          </div>
        </section>
      </section>

      <dl className="catalog-detail-grid">
        <div><dt>Fabricante</dt><dd>{model.manufacturer_name}</dd></div>
        <div><dt>Modelo</dt><dd>{model.name}</dd></div>
        <div><dt>Cinemática</dt><dd>{model.kinematics}</dd></div>
        <div><dt>Estado</dt><dd>{model.trust_state}</dd></div>
        <div><dt>Variações</dt><dd>{model.variants.length}</dd></div>
      </dl>

      <CurationStatusPanel model={model} />

      <section className="catalog-curation-grid">
        <CatalogSpecPanel title="Ficha de curadoria" icon={ShieldCheck} values={model.detail} />
        <CatalogSourcePanel values={model.source_links} />
      </section>

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
          <ComponentSummary key={variation.id} variation={variation} />
        ))}
      </section>
    </section>
  );
}

function CurationStatusPanel({ model }: { model: CatalogModelAdmin }) {
  if (!model.curation_notes && model.trust_state === "official") {
    return null;
  }
  return (
    <section className="catalog-curation-status">
      <div className="catalog-curation-status-icon">
        <Info size={17} />
      </div>
      <div className="catalog-curation-status-body">
        <header>
          <strong>Status de curadoria</strong>
          <span className={`catalog-state state-${model.trust_state}`}>{model.trust_state}</span>
        </header>
        <p>{curationStatusText(model)}</p>
        <dl>
          <div>
            <dt>Evidência</dt>
            <dd>{curationEvidenceText(model)}</dd>
          </div>
          <div>
            <dt>Próxima ação</dt>
            <dd>{curationNextAction(model)}</dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

function CatalogSpecPanel({ title, icon: Icon, values }: { title: string; icon: LucideIcon; values: Record<string, unknown> }) {
  const entries = objectEntries(values);
  if (entries.length === 0) {
    return null;
  }
  return (
    <section className="catalog-spec-panel">
      <header>
        <Icon size={17} />
        <strong>{title}</strong>
      </header>
      <dl className="catalog-spec-list">
        {entries.map(([key, value]) => (
          <div key={key}>
            <dt>{detailLabel(key)}</dt>
            <dd>{formatDetailValue(value)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function CatalogSourcePanel({ values }: { values: Record<string, unknown> }) {
  const links = objectEntries(values).filter((entry): entry is [string, string] => typeof entry[1] === "string" && entry[1].startsWith("http"));
  if (links.length === 0) {
    return null;
  }
  return (
    <section className="catalog-spec-panel catalog-source-panel">
      <header>
        <ExternalLink size={17} />
        <div>
          <strong>Fontes de curadoria</strong>
          <span>Referências usadas para validar os dados deste modelo.</span>
        </div>
      </header>
      <div className="catalog-source-list">
        {links.map(([key, url]) => (
          <a className="catalog-source-link" href={url} target="_blank" rel="noreferrer" key={key}>
            <span className="catalog-source-icon">{catalogLinkIcon(sourceIconFor(key, url), 15)}</span>
            <span>
              <strong>{detailLabel(key)}</strong>
              <small>{formatSourceUrl(url)}</small>
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}

function CatalogLogo({ name, logoUrl }: { name: string; logoUrl: string | null }) {
  const initials = name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  if (!logoUrl) {
    return <span className="catalog-logo-fallback">{initials}</span>;
  }
  return <img className="catalog-logo" src={logoUrl} alt="" loading="lazy" referrerPolicy="no-referrer" />;
}

function CatalogLink({ icon: Icon, label, url }: { icon: LucideIcon; label: string; url: string | null }) {
  if (!url) {
    return (
      <span className="catalog-link disabled">
        <span className="catalog-link-icon">{catalogLinkIcon(Icon, 16)}</span>
        <span>
          <strong>{label}</strong>
          <small>não informado</small>
        </span>
      </span>
    );
  }
  return (
    <a className="catalog-link" href={url} target="_blank" rel="noreferrer">
      <span className="catalog-link-icon">{catalogLinkIcon(Icon, 16)}</span>
      <span>
        <strong>{label}</strong>
        <small>{formatSourceUrl(url)}</small>
      </span>
    </a>
  );
}

function catalogLinkIcon(Icon: LucideIcon, size: number) {
  return <Icon size={size} />;
}

function ComponentSummary({ variation }: { variation: CatalogVariant }) {
  const entries = objectEntries(variation.components).filter(([key, value]) => key !== "kinematics" && !isPendingComponentValue(value));
  const pending = objectEntries(variation.components).filter(([key, value]) => key !== "kinematics" && isPendingComponentValue(value));
  return (
    <section className="catalog-components-panel">
      <header>
        <Boxes size={17} />
        <div>
          <strong>Componentes conhecidos</strong>
          <span>{variation.name}</span>
        </div>
      </header>
      {entries.length ? (
        <dl className="catalog-component-list">
          {entries.map(([key, value]) => (
            <div key={key}>
              <dt>{componentLabel(key)}</dt>
              <dd>{formatDetailValue(value)}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <div className="catalog-component-empty">
          <Info size={16} />
          <span>Componentes ainda não validados para esta variação.</span>
        </div>
      )}
      {pending.length ? (
        <p className="catalog-component-pending">
          {pending.length} {pending.length === 1 ? "campo pendente" : "campos pendentes"} de curadoria.
        </p>
      ) : null}
    </section>
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

function objectEntries(value: Record<string, unknown>) {
  return Object.entries(value).filter(([, item]) => item !== null && item !== undefined && String(item).trim() !== "");
}

function formatDetailValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}

function curationStatusText(model: CatalogModelAdmin) {
  if (model.curation_notes) {
    return model.curation_notes;
  }
  if (model.trust_state === "community") {
    return "Cadastro aceito como referência comunitária, ainda sem revisão completa para virar oficial.";
  }
  if (model.trust_state === "draft") {
    return "Cadastro em rascunho técnico, usado para mapear o modelo sem afirmar dados ainda não verificados.";
  }
  if (model.trust_state === "obsolete") {
    return "Cadastro mantido para preservar histórico e vínculos existentes, mas não recomendado para novos cadastros.";
  }
  if (model.trust_state === "blocked") {
    return "Cadastro bloqueado na curadoria e fora da consulta pública padrão.";
  }
  return "Cadastro revisado e aceito como referência oficial no catálogo.";
}

function curationEvidenceText(model: CatalogModelAdmin) {
  const confidence = typeof model.detail.confidence === "string" ? model.detail.confidence : "";
  const links = objectEntries(model.source_links).filter(([, value]) => typeof value === "string" && value.startsWith("http"));
  if (confidence && links.length) {
    return `${confidence}; ${links.length} ${links.length === 1 ? "fonte vinculada" : "fontes vinculadas"}.`;
  }
  if (confidence) {
    return confidence;
  }
  if (links.length) {
    return `${links.length} ${links.length === 1 ? "fonte vinculada" : "fontes vinculadas"} na ficha do modelo.`;
  }
  return "Sem fonte externa vinculada nesta ficha.";
}

function curationNextAction(model: CatalogModelAdmin) {
  if (model.trust_state === "official") return "Manter revisão periódica e atualizar se o projeto publicar nova versão.";
  if (model.trust_state === "community") return "Conferir BOM, documentação e variações antes de promover para official.";
  if (model.trust_state === "draft") return "Validar BOM, versão de release, componentes e volumes antes de promover.";
  if (model.trust_state === "obsolete") return "Manter vínculos existentes e orientar novos cadastros para o modelo substituto.";
  if (model.trust_state === "blocked") return "Revisar bloqueio antes de qualquer reativação.";
  return "Revisar metadados do modelo.";
}

function isPendingComponentValue(value: unknown) {
  if (typeof value !== "string") return false;
  const normalized = normalizeSearch(value);
  return normalized.includes("definir na curadoria");
}

function formatSourceUrl(value: string) {
  try {
    const url = new URL(value);
    return url.hostname.replace(/^www\./, "");
  } catch {
    return value;
  }
}

function sourceIconFor(key: string, url: string): LucideIcon {
  const lower = `${key} ${url}`.toLowerCase();
  if (lower.includes("github") || lower.includes("git")) return GitBranch;
  if (lower.includes("bom") || lower.includes("hardware") || lower.includes("parts")) return Boxes;
  if (lower.includes("doc") || lower.includes("manual") || lower.includes("wiki")) return FileText;
  if (lower.includes("discord")) return MessageCircle;
  if (lower.includes("reddit")) return Users;
  return ExternalLink;
}

function detailLabel(value: string) {
  const labels: Record<string, string> = {
    build_volume: "Volume útil",
    confidence: "Confiança",
    documentation: "Documentação",
    extrusion: "Extrusão",
    firmware: "Firmware",
    frame: "Estrutura",
    github: "GitHub",
    github_org: "GitHub",
    github_outdated: "GitHub histórico",
    github_vz235: "GitHub Vz-235",
    github_vz330: "GitHub Vz-330",
    hardware: "Hardware",
    known_sizes: "Tamanhos conhecidos",
    license: "Licença",
    lineage: "Origem técnica",
    manual: "Manual",
    manufacturer: "Fabricante",
    motion: "Movimento",
    origin: "Origem",
    parts: "Partes",
    printables: "Printables",
    probe: "Probe",
    release: "Release",
    site: "Site",
    source: "Fonte",
    standard: "Padrão",
    status: "Status",
    volume: "Volume útil",
    wiki: "Wiki",
  };
  return labels[value] ?? value.replace(/_/g, " ");
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

function readCatalogFiltersFromUrl(): CatalogAdminFilters {
  const params = new URLSearchParams(window.location.search);
  return catalogFilterKeys.reduce<CatalogAdminFilters>((next, key) => {
    const value = params.get(catalogFilterUrlKey(key));
    if (value) {
      next[key] = value as never;
    }
    return next;
  }, {});
}

function readCatalogPageFromUrl() {
  const page = Number(new URLSearchParams(window.location.search).get("page"));
  return Number.isInteger(page) && page > 0 ? page : 1;
}

function readCatalogDetailSlugFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("open_model") ?? params.get("model");
}

function updateCatalogUrl(filters: CatalogAdminFilters, page: number, detailModelSlug?: string | null, replace = false) {
  const params = new URLSearchParams(window.location.search);
  params.set("section", "catalog");
  params.delete("model");
  catalogFilterKeys.forEach((key) => {
    const paramKey = catalogFilterUrlKey(key);
    const value = filters[key];
    if (value) {
      params.set(paramKey, value);
    } else {
      params.delete(paramKey);
    }
  });
  if (page > 1) {
    params.set("page", String(page));
  } else {
    params.delete("page");
  }
  if (detailModelSlug) {
    params.set("open_model", detailModelSlug);
  } else {
    params.delete("open_model");
  }
  const nextUrl = `?${params.toString()}`;
  if (replace) {
    window.history.replaceState(null, "", nextUrl);
  } else {
    window.history.pushState(null, "", nextUrl);
  }
}

function catalogFilterUrlKey(key: keyof CatalogAdminFilters) {
  return key === "model" ? "catalog_model" : key;
}

function byName<T extends { name: string }>(left: T, right: T) {
  return left.name.localeCompare(right.name, "pt-BR");
}
