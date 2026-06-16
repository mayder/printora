import React from "react";
import { Archive, ArrowLeft, Box, ChevronLeft, ChevronRight, ExternalLink, FileText, Filter, FolderOpen, Lock, MessageSquare, Pin, Printer, SlidersHorizontal, UserRound, Users, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { Community, CommunityDetail, CommunityFeedItem, CommunityFeedSummary, FeedContentType, FeedOrder } from "../types";

interface PublicCommunityScreenProps {
  slug: string;
}

type CommunityTab = "feed" | "files" | "mods" | "profiles" | "members" | "printers";

const feedTypeOptions: Array<{ value: FeedContentType | ""; label: string }> = [
  { value: "", label: "Todos" },
  { value: "technical_post", label: "Técnico" },
  { value: "question", label: "Dúvidas" },
  { value: "mod", label: "Mods" },
  { value: "print_result", label: "Resultados" },
  { value: "file_announcement", label: "Arquivos" },
  { value: "curation_notice", label: "Curadoria" },
];

const feedOrderOptions: Array<{ value: FeedOrder; label: string }> = [
  { value: "recommended", label: "Recomendado" },
  { value: "recent", label: "Recentes" },
  { value: "pinned", label: "Fixados" },
];

const tabs: Array<{ key: CommunityTab; label: string; icon: LucideIcon }> = [
  { key: "feed", label: "Feed", icon: MessageSquare },
  { key: "files", label: "Arquivos", icon: FolderOpen },
  { key: "mods", label: "Mods", icon: Wrench },
  { key: "profiles", label: "Perfis", icon: UserRound },
  { key: "members", label: "Membros", icon: Users },
  { key: "printers", label: "Impressoras públicas", icon: Printer },
];

export function PublicCommunityScreen({ slug }: PublicCommunityScreenProps) {
  const [community, setCommunity] = React.useState<CommunityDetail | null>(null);
  const [activeTab, setActiveTab] = React.useState<CommunityTab>("feed");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let active = true;
    async function loadCommunity() {
      setLoading(true);
      setError(null);
      try {
        const payload = await socialApi.community(slug);
        if (active) setCommunity(payload);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Comunidade indisponível");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadCommunity();
    return () => {
      active = false;
    };
  }, [slug]);

  return (
    <main className="public-profile-shell">
      <section className="public-profile-topbar">
        <img src="/brand/printora-logo-horizontal-color.png" alt="Printora" />
        <a href="/?section=social" className="secondary-button"><ArrowLeft size={16} />Social</a>
      </section>

      {loading ? (
        <section className="public-profile-empty">Carregando comunidade...</section>
      ) : error ? (
        <section className="public-profile-empty">
          <Lock size={22} />
          <h1>Comunidade indisponível</h1>
          <p>{error}</p>
        </section>
      ) : community ? (
        <section className="public-profile-page">
          <header className="public-profile-hero public-community-hero">
            <div className="public-avatar">
              <Users size={36} />
            </div>
            <div>
              <span className="account-eyebrow">{scopeLabel(community.scope)} / {statusLabel(community.status)}</span>
              <h1>{community.name}</h1>
              <p>{statusDescription(community)}</p>
              <div className="public-profile-meta">
                <span><Box size={15} />{communityContext(community)}</span>
                {community.merged_into_slug ? <a href={`/c/${community.merged_into_slug}`}><ExternalLink size={15} />Abrir destino</a> : null}
              </div>
            </div>
          </header>

          <section className="community-metrics">
            <CommunityMetric icon={Users} label="Membros" value={community.member_count} />
            <CommunityMetric icon={Printer} label="Impressoras públicas" value={community.printer_count} />
            <CommunityMetric icon={FileText} label="Arquivos" value={community.file_count} />
            <CommunityMetric icon={Wrench} label="Mods" value={community.mod_count} />
          </section>

          <nav className="community-tabs" aria-label="Abas da comunidade">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
              <button key={tab.key} type="button" className={activeTab === tab.key ? "active" : ""} onClick={() => setActiveTab(tab.key)}>
                <Icon size={16} />
                {tab.label}
              </button>
              );
            })}
          </nav>

          <section className="public-profile-grid community-tab-grid">
            <article className="panel public-profile-panel">
              <h2>Contexto técnico</h2>
              <div className="public-spec-list">
                <span><Archive size={15} />Catálogo mestre</span>
                <span><SlidersHorizontal size={15} />{communityContext(community)}</span>
                <span><Lock size={15} />Sem acesso operacional, agente, Moonraker, SSH, token ou organização</span>
              </div>
            </article>
            <article className="panel public-profile-panel">
              <CommunityTabContent community={community} tab={activeTab} />
            </article>
          </section>
        </section>
      ) : null}
    </main>
  );
}

function CommunityMetric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: number }) {
  return (
    <div className="social-metric">
      <Icon size={17} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CommunityTabContent({ community, tab }: { community: CommunityDetail; tab: CommunityTab }) {
  if (community.status === "obsolete") {
    return <Placeholder title="Comunidade obsoleta" text="A comunidade fica visível para histórico, mas não recebe novas associações públicas." />;
  }
  if (community.status === "merged") {
    return <Placeholder title="Comunidade mesclada" text="Use a comunidade de destino indicada no cabeçalho. Nenhum vínculo novo é criado nesta origem." />;
  }
  if (tab === "printers") {
    return (
      <>
        <h2>Impressoras públicas</h2>
        <div className="public-printer-list">
          {community.printers.map((printer) => (
            <section key={printer.id} className="public-printer-card">
              <div>
                <Printer size={17} />
                <strong>{printer.public_name}</strong>
              </div>
              <span>{printer.manufacturer_name} / {printer.model_name} / {printer.variant_name}</span>
              {printer.public_description ? <p>{printer.public_description}</p> : null}
              <a href={`/p/${printer.id}`}><ExternalLink size={15} />Abrir impressora pública</a>
            </section>
          ))}
          {community.printers.length === 0 ? <p>Nenhuma impressora pública nesta comunidade.</p> : null}
        </div>
      </>
    );
  }
  if (tab === "members" || tab === "profiles") {
    return (
      <>
        <h2>{tab === "profiles" ? "Perfis" : "Membros"}</h2>
        <div className="public-printer-list">
          {community.members.map((member) => (
            <section key={member.user_id} className="public-printer-card">
              <div>
                <UserRound size={17} />
                <strong>{member.display_name}</strong>
              </div>
              <span>@{member.slug}</span>
              {member.bio ? <p>{member.bio}</p> : null}
              <a href={`/u/${member.slug}`}><ExternalLink size={15} />Abrir perfil público</a>
            </section>
          ))}
          {community.members.length === 0 ? <p>Nenhum perfil público nesta comunidade.</p> : null}
        </div>
      </>
    );
  }
  if (tab === "mods") {
    const mods = [...new Set(community.printers.flatMap((printer) => printer.public_mods))];
    return mods.length ? (
      <>
        <h2>Mods públicos</h2>
        <div className="community-chip-list">{mods.map((mod) => <span key={mod}>{mod}</span>)}</div>
      </>
    ) : <Placeholder title="Mods" text="A estrutura inicial usa mods declarados na publicação da impressora. Biblioteca dedicada será ligada ao pacote de arquivos/modelos." />;
  }
  if (tab === "files") {
    return <Placeholder title="Arquivos" text="A aba está reservada para arquivos públicos vinculados à comunidade; contagem preparada e sem expor arquivos privados." />;
  }
  return <CommunityFeed community={community} />;
}

function CommunityFeed({ community }: { community: CommunityDetail }) {
  const [feed, setFeed] = React.useState<CommunityFeedSummary | null>(null);
  const [contentType, setContentType] = React.useState<FeedContentType | "">("");
  const [component, setComponent] = React.useState("");
  const [material, setMaterial] = React.useState("");
  const [firmware, setFirmware] = React.useState("");
  const [problem, setProblem] = React.useState("");
  const [order, setOrder] = React.useState<FeedOrder>("recommended");
  const [page, setPage] = React.useState(1);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    async function loadFeed() {
      setLoading(true);
      setError(null);
      try {
        const payload = await socialApi.communityFeed(community.slug, {
          content_type: contentType,
          component,
          material,
          firmware_family: firmware,
          problem,
          order,
          page,
          page_size: 10,
        });
        if (active) setFeed(payload);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Feed indisponível");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadFeed();
    return () => {
      active = false;
    };
  }, [community.slug, contentType, component, material, firmware, problem, order, page]);

  const resetPage = (action: () => void) => {
    setPage(1);
    action();
  };

  return (
    <div className="community-feed">
      <div className="community-feed-header">
        <div>
          <h2>Feed técnico</h2>
          <p>Conteúdo público da comunidade, organizado por contexto técnico.</p>
        </div>
        <div className="community-feed-order">
          <Filter size={15} />
          <select value={order} onChange={(event) => resetPage(() => setOrder(event.target.value as FeedOrder))}>
            {feedOrderOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
      </div>

      <div className="community-feed-filters">
        <select value={contentType} onChange={(event) => resetPage(() => setContentType(event.target.value as FeedContentType | ""))}>
          {feedTypeOptions.map((option) => <option key={option.value || "all"} value={option.value}>{option.label}</option>)}
        </select>
        <FilterSelect label="Componente" value={component} options={feed?.filters.components ?? []} onChange={(value) => resetPage(() => setComponent(value))} />
        <FilterSelect label="Material" value={material} options={feed?.filters.materials ?? []} onChange={(value) => resetPage(() => setMaterial(value))} />
        <FilterSelect label="Firmware" value={firmware} options={feed?.filters.firmware ?? []} onChange={(value) => resetPage(() => setFirmware(value))} />
        <FilterSelect label="Problema" value={problem} options={feed?.filters.problems ?? []} onChange={(value) => resetPage(() => setProblem(value))} />
      </div>

      {loading ? <p>Carregando feed...</p> : error ? <p>{error}</p> : feed && feed.items.length ? (
        <>
          <div className="community-feed-list">
            {feed.items.map((item) => <FeedItemCard key={item.id} item={item} />)}
          </div>
          <div className="community-feed-pagination">
            <button type="button" className="secondary-button" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}><ChevronLeft size={15} />Anterior</button>
            <span>Página {feed.page}</span>
            <button type="button" className="secondary-button" disabled={!feed.has_more} onClick={() => setPage((current) => current + 1)}>Próxima<ChevronRight size={15} /></button>
          </div>
        </>
      ) : <Placeholder title="Sem itens no feed" text="Nenhum conteúdo público corresponde aos filtros selecionados." />}
    </div>
  );
}

function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="">{label}</option>
      {options.map((option) => <option key={option} value={option}>{option}</option>)}
    </select>
  );
}

function FeedItemCard({ item }: { item: CommunityFeedItem }) {
  return (
    <article className="community-feed-card">
      <header>
        <span>{feedTypeLabel(item.content_type)}</span>
        {item.pinned ? <strong><Pin size={14} />Fixado</strong> : null}
      </header>
      <h3>{item.title}</h3>
      <p>{item.body}</p>
      <div className="community-feed-tags">
        {item.component ? <span>{item.component}</span> : null}
        {item.material ? <span>{item.material}</span> : null}
        {item.firmware_family ? <span>{item.firmware_family}</span> : null}
        {item.problem_tag ? <span>{item.problem_tag}</span> : null}
      </div>
      <footer>{item.author_display_name ? `Por ${item.author_display_name}` : "Curadoria da comunidade"}</footer>
    </article>
  );
}

function feedTypeLabel(type: FeedContentType) {
  return {
    technical_post: "Post técnico",
    question: "Dúvida",
    mod: "Mod",
    print_result: "Resultado",
    file_announcement: "Arquivo",
    curation_notice: "Curadoria",
  }[type];
}

function Placeholder({ title, text }: { title: string; text: string }) {
  return (
    <div className="community-placeholder">
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
  );
}

function scopeLabel(scope: Community["scope"]) {
  return { manufacturer: "Fabricante", model: "Modelo", variant: "Variante" }[scope];
}

function statusLabel(status: Community["status"]) {
  return { active: "ativa", uncurated: "sem curadoria", obsolete: "obsoleta", merged: "mesclada" }[status];
}

function statusDescription(community: CommunityDetail) {
  if (community.status === "obsolete") return "Comunidade preservada para histórico. Novas impressoras não entram neste estado.";
  if (community.status === "merged") return "Comunidade redirecionada para outra comunidade canônica.";
  if (community.status === "uncurated") return "Comunidade criada automaticamente a partir de item do catálogo ainda sem curadoria final.";
  return "Comunidade automática derivada do catálogo e de impressoras públicas autorizadas.";
}

function communityContext(community: Community) {
  return [community.manufacturer_name, community.model_name, community.variant_name].filter(Boolean).join(" / ") || "Catálogo mestre";
}
