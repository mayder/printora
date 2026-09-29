import React from "react";
import { Bell, Check, ChevronDown, ChevronLeft, ChevronRight, ExternalLink, FileText, Filter, Globe2, RefreshCw, Search, Shield, Tags, UserRound, Users, Wrench } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogSummary, Community, NotificationCenter, NotificationPreference, PublicPrinter, PublicProfile, RecommendationResponse, RelationshipRecord, RelationshipSummary, SearchEntityType, SearchOrder, SearchResponse, SocialNotificationStatus } from "../types";

type SocialScreenProps = ScreenPropsFor<"setError">;
type SocialTab = "discovery" | "communities" | "printers" | "makers" | "relationships" | "notifications";
type SocialFilters = { manufacturer: string; model: string; variant: string; component: string; mod: string };
type DiscoveryFilters = { entity_type: SearchEntityType | ""; tag: string; material: string; component: string; license: string; file_kind: string; order: SearchOrder };
type FilterOption = { value: string; label: string };
const pageSize = 12;

const socialTabs: Array<{ key: SocialTab; label: string; icon: typeof Users }> = [
  { key: "discovery", label: "Descoberta", icon: Search },
  { key: "communities", label: "Comunidades", icon: Users },
  { key: "printers", label: "Impressoras", icon: Globe2 },
  { key: "makers", label: "Makers", icon: UserRound },
  { key: "relationships", label: "Relações", icon: Shield },
  { key: "notifications", label: "Notificações", icon: Bell },
];

export function SocialScreen({ setError }: SocialScreenProps) {
  const [activeTab, setActiveTab] = React.useState<SocialTab>("communities");
  const [catalog, setCatalog] = React.useState<CatalogSummary | null>(null);
  const [communities, setCommunities] = React.useState<Community[]>([]);
  const [publicPrinters, setPublicPrinters] = React.useState<PublicPrinter[]>([]);
  const [makers, setMakers] = React.useState<PublicProfile[]>([]);
  const [relationships, setRelationships] = React.useState<RelationshipSummary | null>(null);
  const [makerSearch, setMakerSearch] = React.useState("");
  const [discoveryQuery, setDiscoveryQuery] = React.useState("");
  const [discoveryFilters, setDiscoveryFilters] = React.useState<DiscoveryFilters>({ entity_type: "", tag: "", material: "", component: "", license: "", file_kind: "", order: "relevance" });
  const [discovery, setDiscovery] = React.useState<SearchResponse | null>(null);
  const [recommendations, setRecommendations] = React.useState<RecommendationResponse | null>(null);
  const [notificationCenter, setNotificationCenter] = React.useState<NotificationCenter | null>(null);
  const [notificationStatus, setNotificationStatus] = React.useState<SocialNotificationStatus | "">("");
  const [filters, setFilters] = React.useState<SocialFilters>({ manufacturer: "", model: "", variant: "", component: "", mod: "" });
  const [pages, setPages] = React.useState<Record<SocialTab, number>>({ discovery: 1, communities: 1, printers: 1, makers: 1, relationships: 1, notifications: 1 });
  const [busy, setBusy] = React.useState(false);
  const [discoveryBusy, setDiscoveryBusy] = React.useState(false);

  async function loadDiscovery() {
    setBusy(true);
    try {
      const communityFilters = {
        manufacturer: filters.manufacturer,
        model: filters.model,
        variant: filters.variant,
        component: filters.component,
      };
      const printerFilters = {
        manufacturer: filters.manufacturer,
        model: filters.model,
        variant: filters.variant,
        mod: filters.mod,
      };
      const [catalogPayload, communitiesPayload, printersPayload, makersPayload] = await Promise.all([
        socialApi.catalog(),
        socialApi.communities(communityFilters),
        socialApi.publicPrinters(printerFilters),
        socialApi.searchProfiles(makerSearch.trim()),
      ]);
      setCatalog(catalogPayload);
      setCommunities(communitiesPayload);
      setPublicPrinters(printersPayload);
      setMakers(makersPayload);
      setPages((current) => ({ ...current, communities: 1, printers: 1, makers: 1 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar descoberta social");
    }
    try {
      setRelationships(await socialApi.relationships());
    } catch {
      setRelationships(null);
    } finally {
      setBusy(false);
    }
  }

  React.useEffect(() => {
    void loadDiscovery();
  }, [filters.manufacturer, filters.model, filters.variant, filters.component, filters.mod]);

  React.useEffect(() => {
    void loadSearchContent(pages.discovery);
  }, [discoveryFilters.entity_type, discoveryFilters.tag, discoveryFilters.material, discoveryFilters.component, discoveryFilters.license, discoveryFilters.file_kind, discoveryFilters.order, pages.discovery]);

  React.useEffect(() => {
    if (activeTab === "notifications") {
      void loadNotifications();
    }
  }, [activeTab, notificationStatus]);

  async function loadSearchContent(page = 1) {
    setDiscoveryBusy(true);
    try {
      const searchFilters = { ...discoveryFilters, q: discoveryQuery.trim(), page, page_size: pageSize };
      const [searchPayload, recommendationPayload] = await Promise.all([
        socialApi.searchContent(searchFilters),
        socialApi.recommendations({
          q: discoveryQuery.trim(),
          material: discoveryFilters.material,
          component: discoveryFilters.component,
          entity_type: discoveryFilters.entity_type,
          page_size: 4,
        }),
      ]);
      setDiscovery(searchPayload);
      setRecommendations(recommendationPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao buscar conteúdo social");
    } finally {
      setDiscoveryBusy(false);
    }
  }

  async function searchMakers() {
    try {
      setMakers(await socialApi.searchProfiles(makerSearch.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao buscar makers");
    }
  }

  async function loadNotifications() {
    try {
      setNotificationCenter(await socialApi.notificationCenter(notificationStatus));
    } catch {
      setNotificationCenter(null);
    }
  }

  async function markAllNotificationsRead() {
    try {
      await socialApi.markAllNotificationsRead();
      await loadNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao marcar notificações");
    }
  }

  async function updateNotificationPreference(preference: NotificationPreference, patch: Partial<NotificationPreference>) {
    try {
      await socialApi.updateNotificationPreference({ ...preference, ...patch });
      await loadNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar preferência");
    }
  }

  const relationshipCount =
    relationItems(relationships?.following).length +
    relationItems(relationships?.followers).length +
    relationItems(relationships?.friends).length +
    relationItems(relationships?.pending_friend_requests).length +
    relationItems(relationships?.sent_friend_requests).length;

  return (
    <div className="social-screen">
      <section className="social-band">
        <div>
          <span className="eyebrow">Descoberta pública</span>
          <h2>Makers, impressoras públicas e comunidades técnicas</h2>
          <p>Social reúne conteúdo publicado no Printora. Gestão de perfil fica em Conta, publicação fica no detalhe da impressora e curadoria fica no Catálogo.</p>
        </div>
        <div className="social-status-grid">
          <Metric icon={Users} label="Comunidades" value={String(communities.length)} />
          <Metric icon={Globe2} label="Impressoras públicas" value={String(publicPrinters.length)} />
          <Metric icon={Shield} label="Relações" value={String(relationshipCount)} />
          <Metric icon={Bell} label="Não lidas" value={String(notificationCenter?.unread_count ?? 0)} />
        </div>
      </section>

      <section className="social-panel social-discovery-panel">
        <header>
          <Users size={18} />
          <h3>Social</h3>
          <button type="button" className="icon-button" onClick={() => void loadDiscovery()} disabled={busy} aria-label="Recarregar social">
            <RefreshCw size={15} />
          </button>
        </header>

        <nav className="social-tabs" aria-label="Áreas sociais">
          {socialTabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button key={tab.key} type="button" className={activeTab === tab.key ? "active" : ""} onClick={() => setActiveTab(tab.key)}>
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        <div className="social-tab-panel">
          {activeTab === "communities" || activeTab === "printers" ? (
            <CatalogFilters
              catalog={catalog}
              filters={filters}
              setFilters={setFilters}
              showComponent={activeTab === "communities"}
              showMod={activeTab === "printers"}
            />
          ) : null}

          {activeTab === "discovery" ? (
            <DiscoveryTab
              discovery={discovery}
              recommendations={recommendations}
              query={discoveryQuery}
              setQuery={setDiscoveryQuery}
              filters={discoveryFilters}
              setFilters={setDiscoveryFilters}
              busy={discoveryBusy}
              page={pages.discovery}
              setPage={(page) => setPages((current) => ({ ...current, discovery: page }))}
              search={() => {
                setPages((current) => ({ ...current, discovery: 1 }));
                void loadSearchContent(1);
              }}
            />
          ) : null}
          {activeTab === "communities" ? <CommunitiesTab communities={communities} page={pages.communities} setPage={(page) => setPages((current) => ({ ...current, communities: page }))} /> : null}
          {activeTab === "printers" ? <PrintersTab printers={publicPrinters} page={pages.printers} setPage={(page) => setPages((current) => ({ ...current, printers: page }))} /> : null}
          {activeTab === "makers" ? (
            <MakersTab makers={makers} makerSearch={makerSearch} setMakerSearch={setMakerSearch} searchMakers={searchMakers} busy={busy} page={pages.makers} setPage={(page) => setPages((current) => ({ ...current, makers: page }))} />
          ) : null}
          {activeTab === "relationships" ? <RelationshipsTab relationships={relationships} /> : null}
          {activeTab === "notifications" ? (
            <NotificationsTab
              center={notificationCenter}
              status={notificationStatus}
              setStatus={setNotificationStatus}
              reload={loadNotifications}
              markAllRead={markAllNotificationsRead}
              updatePreference={updateNotificationPreference}
            />
          ) : null}
        </div>
      </section>
    </div>
  );
}

function NotificationsTab({
  center,
  status,
  setStatus,
  reload,
  markAllRead,
  updatePreference,
}: {
  center: NotificationCenter | null;
  status: SocialNotificationStatus | "";
  setStatus: (status: SocialNotificationStatus | "") => void;
  reload: () => void;
  markAllRead: () => void;
  updatePreference: (preference: NotificationPreference, patch: Partial<NotificationPreference>) => void;
}) {
  return (
    <section className="social-notifications-panel">
      <header className="social-section-heading">
        <div>
          <span className="eyebrow">Central social</span>
          <h4>Notificações de comunidade e conteúdo</h4>
        </div>
        <div className="social-notification-tools">
          <select value={status} onChange={(event) => setStatus(event.target.value as SocialNotificationStatus | "")} aria-label="Filtrar notificações sociais">
            <option value="">Todas</option>
            <option value="unread">Não lidas</option>
            <option value="read">Lidas</option>
            <option value="archived">Arquivadas</option>
          </select>
          <button type="button" className="secondary-button" onClick={reload}>
            <RefreshCw size={15} />
            Atualizar
          </button>
          <button type="button" className="primary-button" onClick={markAllRead} disabled={!center?.unread_count}>
            <Check size={15} />
            Marcar lidas
          </button>
        </div>
      </header>

      <div className="social-notification-grid">
        <div className="social-notification-list">
          {center?.notifications.length ? null : <EmptyState title="Sem notificações sociais" text="Interações de comunidade, respostas, relações e conteúdo acompanhado aparecerão aqui." />}
          {center?.notifications.map((notification) => (
            <article className={`social-notification-card ${notification.status === "unread" ? "unread" : ""}`} key={notification.id}>
              <header>
                <Bell size={16} />
                <div>
                  <strong>{notification.title}</strong>
                  <span>{notificationLabel(notification.notification_type)} · {notification.actor_display_name ?? "Sistema social"}</span>
                </div>
              </header>
              <p>{notification.body}</p>
              {notification.action_url ? <a href={notification.action_url}>Abrir contexto</a> : null}
            </article>
          ))}
        </div>

        <aside className="social-notification-side">
          <section>
            <strong>Digest</strong>
            {center?.digest.length ? center.digest.slice(0, 5).map((item) => <span key={item.id}>{item.title}</span>) : <span>Nenhum item pendente para digest.</span>}
          </section>
          <section>
            <strong>Acompanhando</strong>
            {center?.follows.length ? center.follows.slice(0, 6).map((follow) => <span key={follow.id}>{follow.title}{follow.muted ? " · silenciado" : ""}</span>) : <span>Nenhum conteúdo acompanhado.</span>}
          </section>
          <section>
            <strong>Preferências</strong>
            {center?.preferences.map((preference) => (
              <label className="social-preference-row" key={preference.notification_type}>
                <span>{notificationLabel(preference.notification_type)}</span>
                <input type="checkbox" checked={preference.in_app_enabled} onChange={(event) => updatePreference(preference, { in_app_enabled: event.target.checked })} />
              </label>
            ))}
          </section>
        </aside>
      </div>
    </section>
  );
}

function CatalogFilters({
  catalog,
  filters,
  setFilters,
  showComponent,
  showMod,
}: {
  catalog: CatalogSummary | null;
  filters: SocialFilters;
  setFilters: React.Dispatch<React.SetStateAction<SocialFilters>>;
  showComponent: boolean;
  showMod: boolean;
}) {
  const visibleModels = catalog?.manufacturers
    .filter((manufacturer) => !filters.manufacturer || manufacturer.slug === filters.manufacturer)
    .flatMap((manufacturer) => manufacturer.models) ?? [];
  const visibleVariants = visibleModels
    .filter((model) => !filters.model || model.slug === filters.model)
    .flatMap((model) => model.variants);
  const manufacturerOptions = catalog?.manufacturers.map((manufacturer) => ({ value: manufacturer.slug, label: manufacturer.name })) ?? [];
  const modelOptions = visibleModels.map((model) => ({ value: model.slug, label: model.name }));
  const variantOptions = visibleVariants.map((variant) => ({ value: variant.slug, label: variant.name }));

  return (
    <div className="community-filter-grid">
      <SearchableFilter
        label="Fabricante"
        value={filters.manufacturer}
        emptyLabel="Todos"
        options={manufacturerOptions}
        onChange={(value) => setFilters((current) => ({ ...current, manufacturer: value, model: "", variant: "" }))}
      />
      <SearchableFilter
        label="Modelo"
        value={filters.model}
        emptyLabel="Todos"
        options={modelOptions}
        onChange={(value) => setFilters((current) => ({ ...current, model: value, variant: "" }))}
      />
      <SearchableFilter
        label="Variante"
        value={filters.variant}
        emptyLabel="Todas"
        options={variantOptions}
        onChange={(value) => setFilters((current) => ({ ...current, variant: value }))}
      />
      {showComponent ? (
        <label>
          Componente
          <span className="input-with-icon">
            <Filter size={15} />
            <input value={filters.component} onChange={(event) => setFilters((current) => ({ ...current, component: event.target.value }))} placeholder="Tap, ERCF, CAN..." />
          </span>
        </label>
      ) : null}
      {showMod ? (
        <label>
          Mod
          <span className="input-with-icon">
            <Filter size={15} />
            <input value={filters.mod} onChange={(event) => setFilters((current) => ({ ...current, mod: event.target.value }))} placeholder="Tap, ERCF, enclosure..." />
          </span>
        </label>
      ) : null}
    </div>
  );
}

function DiscoveryTab({
  discovery,
  recommendations,
  query,
  setQuery,
  filters,
  setFilters,
  busy,
  page,
  setPage,
  search,
}: {
  discovery: SearchResponse | null;
  recommendations: RecommendationResponse | null;
  query: string;
  setQuery: React.Dispatch<React.SetStateAction<string>>;
  filters: DiscoveryFilters;
  setFilters: React.Dispatch<React.SetStateAction<DiscoveryFilters>>;
  busy: boolean;
  page: number;
  setPage: (page: number) => void;
  search: () => void;
}) {
  const results = discovery?.results ?? [];
  const total = discovery ? results.length + (discovery.has_more ? 1 : 0) + (page - 1) * pageSize : 0;
  return (
    <div className="discovery-workspace">
      <section className="discovery-control-panel">
        <div className="discovery-searchbar">
          <label>
            Buscar conteúdo
            <span className="input-with-icon">
              <Search size={15} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") search(); }} placeholder="material, peça, perfil, comunidade..." />
            </span>
          </label>
          <button type="button" className="secondary-button" onClick={search} disabled={busy}>
            <Search size={15} />
            Buscar
          </button>
        </div>
        <div className="discovery-filter-grid">
          <label>
            Tipo
            <select value={filters.entity_type} onChange={(event) => setFilters((current) => ({ ...current, entity_type: event.target.value as SearchEntityType | "" }))}>
              <option value="">Todos</option>
              <option value="community">Comunidades</option>
              <option value="post">Discussões</option>
              <option value="library_item">Projetos</option>
              <option value="technical_config">Configurações</option>
              <option value="material_profile">Materiais</option>
              <option value="catalog_variant">Catálogo</option>
            </select>
          </label>
          <label>
            Ordenação
            <select value={filters.order} onChange={(event) => setFilters((current) => ({ ...current, order: event.target.value as SearchOrder }))}>
              <option value="relevance">Relevância</option>
              <option value="recent">Mais recentes</option>
              <option value="popular">Populares</option>
            </select>
          </label>
          <DiscoveryInput label="Tag" icon={Tags} value={filters.tag} onChange={(value) => setFilters((current) => ({ ...current, tag: value }))} placeholder="material-abs" />
          <DiscoveryInput label="Material" icon={Filter} value={filters.material} onChange={(value) => setFilters((current) => ({ ...current, material: value }))} placeholder="ABS, PETG..." />
          <DiscoveryInput label="Componente" icon={Wrench} value={filters.component} onChange={(value) => setFilters((current) => ({ ...current, component: value }))} placeholder="hotend, extrusor..." />
          <DiscoveryInput label="Licença" icon={Shield} value={filters.license} onChange={(value) => setFilters((current) => ({ ...current, license: value }))} placeholder="cc-by, mit..." />
          <DiscoveryInput label="Arquivo" icon={FileText} value={filters.file_kind} onChange={(value) => setFilters((current) => ({ ...current, file_kind: value }))} placeholder="stl, 3mf..." />
        </div>
      </section>

      <div className="discovery-content-grid">
        <FacetRail discovery={discovery} filters={filters} setFilters={setFilters} />
        <div className="discovery-main-column">
          <div className="social-result-toolbar">
            <div className="social-result-summary">
              <strong>Resultados públicos</strong>
              <span>{results.length} resultados nesta página, {discovery?.indexed_count ?? 0} itens indexados</span>
            </div>
            <Pagination total={total} page={page} setPage={setPage} />
          </div>
          <div className="discovery-result-list">
            {results.map((result) => (
              <article key={`${result.entity_type}-${result.entity_id}`} className="social-discovery-card discovery-result-card">
                <div className="discovery-result-topline">
                  <span className="discovery-type-pill">{entityTypeLabel(result.entity_type)}</span>
                  <span>{formatDate(result.updated_at)}</span>
                </div>
                <div className="social-card-copy">
                  <strong>{result.title}</strong>
                  <span>{result.summary || "Sem resumo público."}</span>
                  <small>{resultContext(result)}</small>
                </div>
                <TagList tags={result.tags} />
                <div className="social-card-stats">
                  <span className="social-card-stat">
                    <b>{result.popularity_score}</b>
                    <small>Popularidade</small>
                  </span>
                  <span className="social-card-stat">
                    <b>{result.owner_display_name ?? result.community_name ?? "Público"}</b>
                    <small>Origem</small>
                  </span>
                </div>
                <a className="social-card-action" href={result.url} aria-label={`Abrir ${result.title}`}>
                  Abrir resultado <ExternalLink size={15} />
                </a>
              </article>
            ))}
            {results.length === 0 ? <EmptyState title="Nenhum conteúdo encontrado" text="Ajuste os filtros ou busque por comunidade, material, componente, arquivo ou perfil técnico publicado." /> : null}
          </div>
          <RecommendationStrip recommendations={recommendations} />
        </div>
      </div>
    </div>
  );
}

function RecommendationStrip({ recommendations }: { recommendations: RecommendationResponse | null }) {
  const items = recommendations?.items ?? [];
  if (items.length === 0) return null;
  return (
    <section className="recommendation-strip" aria-label="Recomendações técnicas">
      <div className="social-result-summary">
        <strong>Recomendações técnicas</strong>
        <span>{items.length} sugestões com score determinístico e motivo visível</span>
      </div>
      <div className="recommendation-grid">
        {items.map((item) => (
          <article key={`${item.result.entity_type}-${item.result.entity_id}`} className="recommendation-card">
            <div>
              <span className="discovery-type-pill">{entityTypeLabel(item.result.entity_type)}</span>
              <strong>{item.result.title}</strong>
            </div>
            <p>{item.reasons.join(" · ")}</p>
            <div className="recommendation-meta">
              <span>Score {item.score}</span>
              <span>Reputação {item.contributor_reputation}</span>
            </div>
            <a href={item.result.url} aria-label={`Abrir recomendação ${item.result.title}`}>
              Abrir <ExternalLink size={14} />
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}

function DiscoveryInput({ label, icon: Icon, value, onChange, placeholder }: { label: string; icon: typeof Search; value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <label>
      {label}
      <span className="input-with-icon">
        <Icon size={15} />
        <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
      </span>
    </label>
  );
}

function FacetRail({ discovery, filters, setFilters }: { discovery: SearchResponse | null; filters: DiscoveryFilters; setFilters: React.Dispatch<React.SetStateAction<DiscoveryFilters>> }) {
  if (!discovery) return null;
  const facets = [
    { title: "Tags", items: discovery.facets.tags.slice(0, 8), field: "tag" as const },
    { title: "Materiais", items: discovery.facets.materials.slice(0, 6), field: "material" as const },
    { title: "Componentes", items: discovery.facets.components.slice(0, 6), field: "component" as const },
    { title: "Tipos de projeto", items: discovery.facets.file_kinds.slice(0, 6), field: "file_kind" as const },
  ];
  return (
    <div className="discovery-facet-rail">
      {facets.map((facet) => (
        <div key={facet.title} className="discovery-facet-group">
          <strong>{facet.title}</strong>
          <div>
            {facet.items.map((item) => (
              <button key={item.value} type="button" className={filters[facet.field] === item.value ? "active" : ""} onClick={() => setFilters((current) => ({ ...current, [facet.field]: current[facet.field] === item.value ? "" : item.value }))}>
                {item.label} <span>{item.count}</span>
              </button>
            ))}
            {facet.items.length === 0 ? <span className="muted">Sem opções.</span> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function SearchableFilter({
  label,
  value,
  emptyLabel,
  options,
  onChange,
}: {
  label: string;
  value: string;
  emptyLabel: string;
  options: FilterOption[];
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const ref = React.useRef<HTMLDivElement | null>(null);
  const selected = options.find((option) => option.value === value);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredOptions = normalizedQuery
    ? options.filter((option) => option.label.toLowerCase().includes(normalizedQuery))
    : options;

  React.useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: PointerEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [open]);

  function selectValue(nextValue: string) {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  }

  return (
    <div className={`social-combobox-field${open ? " open" : ""}`} ref={ref}>
      <span className="social-filter-label">{label}</span>
      <button type="button" className="social-combobox-trigger" aria-expanded={open} aria-haspopup="listbox" onClick={() => setOpen((current) => !current)}>
        <span>{selected?.label ?? emptyLabel}</span>
        <ChevronDown size={15} />
      </button>
      {open ? (
        <div className="social-combobox-popover">
          <span className="social-combobox-search">
            <Search size={14} />
            <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Buscar ${label.toLowerCase()}`} />
          </span>
          <div className="social-combobox-options" role="listbox" aria-label={label}>
            <button type="button" className={!value ? "active" : ""} role="option" aria-selected={!value} onClick={() => selectValue("")}>
              <Check size={14} />
              {emptyLabel}
            </button>
            {filteredOptions.map((option) => (
              <button key={option.value} type="button" className={value === option.value ? "active" : ""} role="option" aria-selected={value === option.value} onClick={() => selectValue(option.value)}>
                <Check size={14} />
                {option.label}
              </button>
            ))}
            {filteredOptions.length === 0 ? <span className="social-combobox-empty">Nenhum resultado.</span> : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function CommunitiesTab({ communities, page, setPage }: { communities: Community[]; page: number; setPage: (page: number) => void }) {
  const visible = pageItems(communities, page);
  return (
    <>
    <div className="social-result-toolbar">
      <div className="social-result-summary">
        <strong>Comunidades técnicas</strong>
        <span>{communities.length} comunidades encontradas, {visible.length} nesta página</span>
      </div>
      <Pagination total={communities.length} page={page} setPage={setPage} />
    </div>
    <div className="community-list social-card-grid">
      {visible.map((community) => (
        <article key={community.id} className={`social-discovery-card ${community.member_count > 0 ? "active" : ""}`}>
          <div className="social-card-heading">
            <BrandMark name={community.manufacturer_name ?? community.name} logoUrl={community.manufacturer_logo_url} />
            <div className="social-card-copy">
              <strong>{community.name}</strong>
              <small>{communityContext(community)}</small>
            </div>
          </div>
          <div className="social-card-stats">
            <span className="social-card-stat">
              <b>{community.member_count}</b>
              <small>Membros</small>
            </span>
            <span className="social-card-stat">
              <b>{community.printer_count}</b>
              <small>Impressoras</small>
            </span>
          </div>
          <a className="social-card-action" href={`/?section=social&community=${community.slug}`} aria-label={`Abrir comunidade ${community.name}`}>
            Abrir comunidade <ExternalLink size={15} />
          </a>
        </article>
      ))}
      {communities.length === 0 ? <EmptyState title="Nenhuma comunidade encontrada" text="Ajuste os filtros do catálogo ou publique uma impressora com variante canônica para criar vínculos públicos." /> : null}
    </div>
    </>
  );
}

function PrintersTab({ printers, page, setPage }: { printers: PublicPrinter[]; page: number; setPage: (page: number) => void }) {
  const visible = pageItems(printers, page);
  return (
    <>
    <div className="social-result-toolbar">
      <div className="social-result-summary">
        <strong>Impressoras públicas</strong>
        <span>{printers.length} impressoras encontradas, {visible.length} nesta página</span>
      </div>
      <Pagination total={printers.length} page={page} setPage={setPage} />
    </div>
    <div className="public-printer-list social-card-grid">
      {visible.map((printer) => (
        <article key={printer.id} className="social-discovery-card">
          <div className="social-card-heading">
            <BrandMark name={printer.manufacturer_name} />
            <div className="social-card-copy">
              <strong>{printer.public_name}</strong>
              <span>{printer.manufacturer_name} / {printer.model_name} / {printer.variant_name}</span>
              <small>{publicMods(printer).length ? publicMods(printer).join(", ") : "Sem mods públicos"}</small>
            </div>
          </div>
          <div className="social-card-stats">
            <span className="social-card-stat">
              <b>{printer.owner_display_name ?? "Maker"}</b>
              <small>Autor</small>
            </span>
          </div>
          <a className="social-card-action" href={`/p/${printer.id}`} aria-label={`Abrir impressora pública ${printer.public_name}`}>
            Abrir impressora <ExternalLink size={15} />
          </a>
        </article>
      ))}
      {printers.length === 0 ? <EmptyState title="Nenhuma impressora pública encontrada" text="Social lista somente impressoras publicadas por perfis públicos. Publicação é feita no detalhe da impressora." /> : null}
    </div>
    </>
  );
}

function MakersTab({
  makers,
  makerSearch,
  setMakerSearch,
  searchMakers,
  busy,
  page,
  setPage,
}: {
  makers: PublicProfile[];
  makerSearch: string;
  setMakerSearch: React.Dispatch<React.SetStateAction<string>>;
  searchMakers: () => Promise<void>;
  busy: boolean;
  page: number;
  setPage: (page: number) => void;
}) {
  const visible = pageItems(makers, page);
  return (
    <div className="makers-tab">
      <div className="social-profile-search">
        <label>
          Buscar maker
          <span className="input-with-icon">
            <Search size={15} />
            <input value={makerSearch} onChange={(event) => setMakerSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void searchMakers(); }} placeholder="slug ou nome público" />
          </span>
        </label>
        <button type="button" className="secondary-button" onClick={() => void searchMakers()} disabled={busy}>
          <Search size={15} />
          Buscar
        </button>
      </div>
      <div className="social-result-toolbar">
        <div className="social-result-summary">
          <strong>Makers públicos</strong>
          <span>{makers.length} makers encontrados, {visible.length} nesta página</span>
        </div>
        <Pagination total={makers.length} page={page} setPage={setPage} />
      </div>
      <div className="maker-list social-card-grid maker-card-grid">
        {visible.map((maker) => (
          <article key={maker.user_id} className="social-discovery-card maker-discovery-card">
            <div className="social-card-heading maker-card-heading">
              <div className="maker-avatar">
                {maker.avatar_url ? <img src={maker.avatar_url} alt="" /> : <UserRound size={20} />}
              </div>
              <div className="social-card-copy">
                <strong>{maker.display_name}</strong>
                <span>@{maker.slug}</span>
              </div>
            </div>
            <p className="maker-card-bio">{maker.bio || "Perfil público sem bio."}</p>
            <div className="social-card-stats">
              <span className="social-card-stat">
                <b>{maker.public_printer_count ?? 0}</b>
                <small>Impressoras</small>
              </span>
              <span className="social-card-stat">
                <b>{maker.location || "Não informada"}</b>
                <small>Localização</small>
              </span>
            </div>
            <a className="social-card-action" href={`/?section=social&profile=${maker.slug}`} aria-label={`Abrir perfil público de ${maker.display_name}`}>
              Abrir perfil <ExternalLink size={15} />
            </a>
          </article>
        ))}
        {makers.length === 0 ? <EmptyState title="Nenhum maker encontrado" text="Perfis privados não entram na descoberta. A gestão do seu perfil público fica em Conta > Perfil." /> : null}
      </div>
    </div>
  );
}

function Pagination({ total, page, setPage }: { total: number; page: number; setPage: (page: number) => void }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="social-pagination">
      <button type="button" className="icon-button" onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} aria-label="Página anterior">
        <ChevronLeft size={15} />
      </button>
      <span>{page} / {totalPages}</span>
      <button type="button" className="icon-button" onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages} aria-label="Próxima página">
        <ChevronRight size={15} />
      </button>
    </div>
  );
}

function BrandMark({ name, logoUrl }: { name: string; logoUrl?: string | null }) {
  return (
    <div className="social-brand-mark" aria-hidden="true">
      {logoUrl ? <img src={logoUrl} alt="" loading="lazy" /> : <span>{brandInitials(name)}</span>}
    </div>
  );
}

function pageItems<T>(items: T[], page: number) {
  return items.slice((page - 1) * pageSize, page * pageSize);
}

function brandInitials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "P";
}

function RelationshipsTab({ relationships }: { relationships: RelationshipSummary | null }) {
  if (!relationships) {
    return <EmptyState title="Relações indisponíveis" text="Entre com uma conta para ver seguidores, amigos e solicitações. Ações completas ficam nos perfis públicos." />;
  }
  const pendingRequests = relationItems(relationships.pending_friend_requests);
  const sentRequests = relationItems(relationships.sent_friend_requests);
  return (
    <div className="relationships-grid">
      <RelationshipBlock title="Seguindo" items={relationItems(relationships.following)} />
      <RelationshipBlock title="Seguidores" items={relationItems(relationships.followers)} />
      <RelationshipBlock title="Amigos" items={relationItems(relationships.friends)} />
      <RelationshipBlock title="Solicitações" items={[...pendingRequests, ...sentRequests]} />
    </div>
  );
}

function relationItems(items: RelationshipRecord[] | undefined) {
  return Array.isArray(items) ? items : [];
}

function publicMods(printer: PublicPrinter) {
  return Array.isArray(printer.public_mods) ? printer.public_mods : [];
}

function entityTypeLabel(type: SearchEntityType) {
  const labels: Record<SearchEntityType, string> = {
    community: "Comunidade",
    post: "Discussão",
    library_item: "Projeto",
    technical_config: "Configuração",
    material_profile: "Material",
    catalog_variant: "Catálogo",
  };
  return labels[type] ?? type;
}

function resultContext(result: { community_name: string | null; manufacturer_name: string | null; model_name: string | null; variant_name: string | null; material_type: string | null; component: string | null; file_kind: string | null; license: string | null }) {
  return [
    result.community_name,
    [result.manufacturer_name, result.model_name, result.variant_name].filter(Boolean).join(" / "),
    result.material_type ? `material: ${result.material_type}` : "",
    result.component ? `componente: ${result.component}` : "",
    result.file_kind ? `arquivo: ${result.file_kind}` : "",
    result.license ? `licença: ${result.license}` : "",
  ].filter(Boolean).join(" · ") || "Conteúdo público";
}

function TagList({ tags }: { tags: string[] }) {
  const visibleTags = tags.slice(0, 8);
  return (
    <div className="discovery-tag-list">
      {visibleTags.map((tag) => <span key={tag}>{tagLabel(tag)}</span>)}
    </div>
  );
}

function tagLabel(tag: string) {
  return tag.replace(/-/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("pt-BR");
}

function scopeLabel(scope: Community["scope"]) {
  return { manufacturer: "fabricante", model: "modelo", variant: "variante" }[scope];
}

function statusLabel(status: Community["status"]) {
  const labels = { active: "ativa", uncurated: "sem curadoria", obsolete: "obsoleta", merged: "mesclada" };
  return labels[status] ?? status;
}

function communityContext(community: Community) {
  const parts = [community.manufacturer_name, community.model_name, community.variant_name].filter(Boolean);
  if (community.status === "merged" && community.merged_into_slug) {
    parts.push(`destino: ${community.merged_into_name ?? community.merged_into_slug}`);
  }
  return parts.length ? parts.join(" / ") : "Derivada do catálogo mestre";
}

function Metric({ icon: Icon, label, value }: { icon: typeof Globe2; label: string; value: string }) {
  return (
    <div className="social-metric">
      <Icon size={17} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RelationshipBlock({ title, items }: { title: string; items: RelationshipRecord[] }) {
  return (
    <article className="relationship-block">
      <strong>{title}</strong>
      <b>{items.length}</b>
      {items.length === 0 ? <span className="muted">Sem registros.</span> : null}
      {items.slice(0, 6).map((item) => (
        <a key={`${title}-${item.target_slug ?? item.target_user_id}-${item.status}`} href={item.target_slug ? `/u/${item.target_slug}` : undefined}>
          {item.target_display_name ?? item.target_slug ?? "Usuário"} · {relationStatusLabel(item.status)}
        </a>
      ))}
    </article>
  );
}

function relationStatusLabel(status: string) {
  return { active: "ativo", pending: "pendente", accepted: "aceito", ended: "encerrado" }[status] ?? status;
}

function notificationLabel(type: string) {
  const labels: Record<string, string> = {
    comment: "Resposta",
    reaction: "Reação",
    solution: "Solução",
    follow: "Seguidor",
    friend_request: "Amizade",
    friend_accept: "Amizade aceita",
    content_update: "Atualização",
    community_post: "Comunidade",
    digest: "Digest",
  };
  return labels[type] ?? type;
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="social-empty-state">
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}
