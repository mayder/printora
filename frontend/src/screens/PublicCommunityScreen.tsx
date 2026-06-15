import React from "react";
import { Archive, Box, FileText, Lock, Printer, SlidersHorizontal, UserRound, Users, Wrench } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { Community, CommunityDetail } from "../types";

interface PublicCommunityScreenProps {
  slug: string;
}

type CommunityTab = "feed" | "files" | "mods" | "profiles" | "members" | "printers";

const tabs: Array<{ key: CommunityTab; label: string }> = [
  { key: "feed", label: "Feed" },
  { key: "files", label: "Arquivos" },
  { key: "mods", label: "Mods" },
  { key: "profiles", label: "Perfis" },
  { key: "members", label: "Membros" },
  { key: "printers", label: "Impressoras públicas" },
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
        <a href="/?section=social" className="secondary-button">Social</a>
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
                {community.merged_into_slug ? <a href={`/c/${community.merged_into_slug}`}>Abrir destino</a> : null}
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
            {tabs.map((tab) => (
              <button key={tab.key} type="button" className={activeTab === tab.key ? "active" : ""} onClick={() => setActiveTab(tab.key)}>
                {tab.label}
              </button>
            ))}
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

function CommunityMetric({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: number }) {
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
              <a href={`/p/${printer.id}`}>Abrir impressora pública</a>
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
              <a href={`/u/${member.slug}`}>Abrir perfil público</a>
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
  return <Placeholder title="Feed" text="Feed técnico reservado para conteúdo público da comunidade, sem misturar organização operacional ou dados privados." />;
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
