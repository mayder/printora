import React from "react";
import { ExternalLink, Filter, Globe2, RefreshCw, Search, Shield, Users } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogSummary, Community, PublicPrinter, PublicProfile, RelationshipSummary } from "../types";

type SocialScreenProps = ScreenPropsFor<"authUser" | "setError">;

export function SocialScreen({ authUser, setError }: SocialScreenProps) {
  const [profile, setProfile] = React.useState<PublicProfile | null>(null);
  const [catalog, setCatalog] = React.useState<CatalogSummary | null>(null);
  const [publicPrinters, setPublicPrinters] = React.useState<PublicPrinter[]>([]);
  const [communities, setCommunities] = React.useState<Community[]>([]);
  const [relationships, setRelationships] = React.useState<RelationshipSummary | null>(null);
  const [profileSearch, setProfileSearch] = React.useState("");
  const [profileResults, setProfileResults] = React.useState<PublicProfile[]>([]);
  const [filters, setFilters] = React.useState({ manufacturer: "", model: "", variant: "", component: "" });
  const [busy, setBusy] = React.useState(false);

  async function loadSocial() {
    setBusy(true);
    try {
      const [catalogPayload, profilePayload, communitiesPayload] = await Promise.all([
        socialApi.catalog(),
        socialApi.myProfile(),
        socialApi.communities(filters),
      ]);
      setCatalog(catalogPayload);
      setProfile(profilePayload);
      setCommunities(communitiesPayload);
      try {
        setPublicPrinters(await socialApi.profilePrinters(profilePayload.slug));
      } catch {
        setPublicPrinters([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar área social");
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
    void loadSocial();
  }, [filters.manufacturer, filters.model, filters.variant, filters.component]);

  async function searchProfiles() {
    if (!profileSearch.trim()) {
      setProfileResults([]);
      return;
    }
    try {
      setProfileResults(await socialApi.searchProfiles(profileSearch));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao buscar perfis");
    }
  }

  return (
    <div className="social-screen">
      <section className="social-band">
        <div>
          <span className="eyebrow">Perfil público</span>
          <h2>{profile?.display_name ?? authUser?.display_name ?? authUser?.email}</h2>
          <p>{profile?.bio || "Identidade social separada da conta operacional, sem expor permissões, endpoint Moonraker, agente ou credenciais."}</p>
        </div>
        <div className="social-status-grid">
          <Metric icon={Globe2} label="Impressoras públicas" value={String(publicPrinters.length)} />
          <Metric icon={Users} label="Comunidades" value={String(communities.filter((item) => item.member_count > 0).length)} />
          <Metric icon={Shield} label="Bloqueios" value={String(relationships?.blocked.length ?? 0)} />
        </div>
      </section>

      <section className="social-layout">
        <section className="social-panel">
          <header>
            <Users size={18} />
            <h3>Comunidades automáticas</h3>
            <button type="button" className="icon-button" onClick={() => void loadSocial()} disabled={busy} aria-label="Recarregar social">
              <RefreshCw size={15} />
            </button>
          </header>
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
                {catalog?.manufacturers
                  .filter((manufacturer) => !filters.manufacturer || manufacturer.slug === filters.manufacturer)
                  .flatMap((manufacturer) => manufacturer.models)
                  .map((model) => (
                    <option key={model.slug} value={model.slug}>{model.name}</option>
                  ))}
              </select>
            </label>
            <label>
              Variante
              <select value={filters.variant} onChange={(event) => setFilters((current) => ({ ...current, variant: event.target.value }))}>
                <option value="">Todas</option>
                {catalog?.manufacturers
                  .filter((manufacturer) => !filters.manufacturer || manufacturer.slug === filters.manufacturer)
                  .flatMap((manufacturer) => manufacturer.models)
                  .filter((model) => !filters.model || model.slug === filters.model)
                  .flatMap((model) => model.variants)
                  .map((variant) => (
                    <option key={variant.slug} value={variant.slug}>{variant.name}</option>
                  ))}
              </select>
            </label>
            <label>
              Componente
              <span className="input-with-icon">
                <Filter size={15} />
                <input value={filters.component} onChange={(event) => setFilters((current) => ({ ...current, component: event.target.value }))} placeholder="Tap, ERCF, CAN..." />
              </span>
            </label>
          </div>
          <div className="community-list">
            {communities.map((community) => (
              <article key={community.id} className={`community-row ${community.member_count > 0 ? "active" : ""}`}>
                <div>
                  <strong>{community.name}</strong>
                  <span>{scopeLabel(community.scope)} · {statusLabel(community.status)}</span>
                  <small>{communityContext(community)}</small>
                </div>
                <div>
                  <b>{community.member_count}</b>
                  <small>membros</small>
                </div>
                <div>
                  <b>{community.printer_count}</b>
                  <small>impressoras</small>
                </div>
                <a className="icon-button" href={`/c/${community.slug}`} aria-label={`Abrir comunidade ${community.name}`}>
                  <ExternalLink size={15} />
                </a>
              </article>
            ))}
            {communities.length === 0 ? <p className="muted">Nenhuma comunidade encontrada para os filtros selecionados.</p> : null}
          </div>
        </section>

        <section className="social-panel">
          <header>
            <Shield size={18} />
            <h3>Relações</h3>
          </header>
          <div className="social-profile-search">
            <label>
              Buscar perfil
              <span className="input-with-icon">
                <Search size={15} />
                <input value={profileSearch} onChange={(event) => setProfileSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void searchProfiles(); }} placeholder="slug ou nome público" />
              </span>
            </label>
            <button type="button" className="secondary-button" onClick={() => void searchProfiles()} disabled={busy || !profileSearch.trim()}>
              <Search size={15} />
              Buscar
            </button>
          </div>
          {profileResults.length ? (
            <div className="relationship-block">
              <strong>Perfis encontrados</strong>
              {profileResults.map((item) => (
                <a key={item.user_id} href={`/u/${item.slug}`}>
                  {item.display_name} · @{item.slug}
                </a>
              ))}
            </div>
          ) : null}
          <RelationshipBlock title="Seguindo" items={relationships?.following ?? []} />
          <RelationshipBlock title="Seguidores" items={relationships?.followers ?? []} />
          <RelationshipBlock title="Amigos" items={relationships?.friends ?? []} />
          <RelationshipBlock title="Solicitações pendentes" items={relationships?.pending_friend_requests ?? []} />
          <RelationshipBlock title="Solicitações enviadas" items={relationships?.sent_friend_requests ?? []} />
          <RelationshipBlock title="Bloqueados" items={relationships?.blocked ?? []} />
        </section>
      </section>
    </div>
  );
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

function RelationshipBlock({ title, items }: { title: string; items: Array<{ target_display_name: string | null; target_slug: string | null; status: string }> }) {
  return (
    <div className="relationship-block">
      <strong>{title}</strong>
      {items.length === 0 ? <span className="muted">Sem registros.</span> : null}
      {items.map((item) => (
        <a key={`${title}-${item.target_slug ?? item.target_display_name}-${item.status}`} href={item.target_slug ? `/u/${item.target_slug}` : undefined}>
          {item.target_display_name ?? item.target_slug ?? "Usuário"} · {item.status}
        </a>
      ))}
    </div>
  );
}
