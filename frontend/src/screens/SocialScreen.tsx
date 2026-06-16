import React from "react";
import { ChevronLeft, ChevronRight, ExternalLink, Filter, Globe2, RefreshCw, Search, Shield, UserRound, Users } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogSummary, Community, PublicPrinter, PublicProfile, RelationshipRecord, RelationshipSummary } from "../types";

type SocialScreenProps = ScreenPropsFor<"setError">;
type SocialTab = "communities" | "printers" | "makers" | "relationships";
type SocialFilters = { manufacturer: string; model: string; variant: string; component: string; mod: string };
const pageSize = 12;

const socialTabs: Array<{ key: SocialTab; label: string; icon: typeof Users }> = [
  { key: "communities", label: "Comunidades", icon: Users },
  { key: "printers", label: "Impressoras", icon: Globe2 },
  { key: "makers", label: "Makers", icon: UserRound },
  { key: "relationships", label: "Relações", icon: Shield },
];

export function SocialScreen({ setError }: SocialScreenProps) {
  const [activeTab, setActiveTab] = React.useState<SocialTab>("communities");
  const [catalog, setCatalog] = React.useState<CatalogSummary | null>(null);
  const [communities, setCommunities] = React.useState<Community[]>([]);
  const [publicPrinters, setPublicPrinters] = React.useState<PublicPrinter[]>([]);
  const [makers, setMakers] = React.useState<PublicProfile[]>([]);
  const [relationships, setRelationships] = React.useState<RelationshipSummary | null>(null);
  const [makerSearch, setMakerSearch] = React.useState("");
  const [filters, setFilters] = React.useState<SocialFilters>({ manufacturer: "", model: "", variant: "", component: "", mod: "" });
  const [pages, setPages] = React.useState<Record<SocialTab, number>>({ communities: 1, printers: 1, makers: 1, relationships: 1 });
  const [busy, setBusy] = React.useState(false);

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

  async function searchMakers() {
    try {
      setMakers(await socialApi.searchProfiles(makerSearch.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao buscar makers");
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

        {activeTab === "communities" || activeTab === "printers" ? (
          <CatalogFilters
            catalog={catalog}
            filters={filters}
            setFilters={setFilters}
            showComponent={activeTab === "communities"}
            showMod={activeTab === "printers"}
          />
        ) : null}

        {activeTab === "communities" ? <CommunitiesTab communities={communities} page={pages.communities} setPage={(page) => setPages((current) => ({ ...current, communities: page }))} /> : null}
        {activeTab === "printers" ? <PrintersTab printers={publicPrinters} page={pages.printers} setPage={(page) => setPages((current) => ({ ...current, printers: page }))} /> : null}
        {activeTab === "makers" ? (
          <MakersTab makers={makers} makerSearch={makerSearch} setMakerSearch={setMakerSearch} searchMakers={searchMakers} busy={busy} page={pages.makers} setPage={(page) => setPages((current) => ({ ...current, makers: page }))} />
        ) : null}
        {activeTab === "relationships" ? <RelationshipsTab relationships={relationships} /> : null}
      </section>
    </div>
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

  return (
    <div className="community-filter-grid">
      <label>
        Fabricante
        <select value={filters.manufacturer} onChange={(event) => setFilters((current) => ({ ...current, manufacturer: event.target.value, model: "", variant: "" }))}>
          <option value="">Todos</option>
          {catalog?.manufacturers.map((manufacturer) => (
            <option key={manufacturer.slug} value={manufacturer.slug}>{manufacturer.name}</option>
          ))}
        </select>
      </label>
      <label>
        Modelo
        <select value={filters.model} onChange={(event) => setFilters((current) => ({ ...current, model: event.target.value, variant: "" }))}>
          <option value="">Todos</option>
          {visibleModels.map((model) => (
            <option key={model.slug} value={model.slug}>{model.name}</option>
          ))}
        </select>
      </label>
      <label>
        Variante
        <select value={filters.variant} onChange={(event) => setFilters((current) => ({ ...current, variant: event.target.value }))}>
          <option value="">Todas</option>
          {visibleVariants.map((variant) => (
            <option key={variant.slug} value={variant.slug}>{variant.name}</option>
          ))}
        </select>
      </label>
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
              <span>{scopeLabel(community.scope)} · {statusLabel(community.status)}</span>
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
      <div className="maker-list social-card-grid">
        {visible.map((maker) => (
          <article key={maker.user_id} className="social-discovery-card">
            <div className="social-card-heading">
              <div className="maker-avatar">
                {maker.avatar_url ? <img src={maker.avatar_url} alt="" /> : <UserRound size={20} />}
              </div>
              <div className="social-card-copy">
                <strong>{maker.display_name}</strong>
                <span>@{maker.slug}</span>
                <small>{maker.bio || "Perfil público sem bio."}</small>
              </div>
            </div>
            <div className="social-card-stats">
              <span className="social-card-stat">
                <b>{maker.public_printer_count ?? 0}</b>
                <small>Impressoras</small>
              </span>
            </div>
            <a className="social-card-action" href={`/u/${maker.slug}`} aria-label={`Abrir perfil público de ${maker.display_name}`}>
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

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="social-empty-state">
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}
