import React from "react";
import { ArrowLeft, Ban, Download, ExternalLink, FileText, Lock, MapPin, Printer, UserPlus, UserRound, Users } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { LibraryItem, PublicPrinter, PublicProfile, RelationshipSummary } from "../types";

interface PublicProfileScreenProps {
  slug: string;
  embedded?: boolean;
}

export function PublicProfileScreen({ slug, embedded = false }: PublicProfileScreenProps) {
  const [profile, setProfile] = React.useState<PublicProfile | null>(null);
  const [printers, setPrinters] = React.useState<PublicPrinter[]>([]);
  const [library, setLibrary] = React.useState<LibraryItem[]>([]);
  const [relationships, setRelationships] = React.useState<RelationshipSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [actionError, setActionError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [busyAction, setBusyAction] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    async function loadProfile() {
      setLoading(true);
      setError(null);
      try {
        const profilePayload = await socialApi.publicProfile(slug);
        const printerPayload = await socialApi.profilePrinters(profilePayload.slug);
        const libraryPayload = await socialApi.profileLibrary(profilePayload.slug);
        let relationshipPayload: RelationshipSummary | null = null;
        try {
          relationshipPayload = await socialApi.relationships();
        } catch {
          relationshipPayload = null;
        }
        if (!active) return;
        setProfile(profilePayload);
        setPrinters(printerPayload);
        setLibrary(libraryPayload);
        setRelationships(relationshipPayload);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Perfil público indisponível");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadProfile();
    return () => {
      active = false;
    };
  }, [slug]);

  async function refreshRelationships() {
    try {
      setRelationships(await socialApi.relationships());
    } catch {
      setRelationships(null);
    }
  }

  async function runAction(action: string, callback: () => Promise<unknown>) {
    setBusyAction(action);
    setActionError(null);
    try {
      await callback();
      await refreshRelationships();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Ação social não concluída");
    } finally {
      setBusyAction(null);
    }
  }

  const relationState = profile && relationships ? summarizeRelationship(profile.user_id, relationships) : null;

  const content = (
    <>
      {loading ? (
        <section className="public-profile-empty">Carregando perfil público...</section>
      ) : error ? (
        <section className="public-profile-empty">
          <Lock size={22} />
          <h1>Perfil indisponível</h1>
          <p>{error}</p>
        </section>
      ) : profile ? (
        <section className="public-profile-page">
          <header className="public-profile-hero">
            <div className="public-avatar">
              {profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : <UserRound size={34} />}
            </div>
            <div>
              {embedded ? <a href="/?section=social" className="ghost-button compact public-community-back"><ArrowLeft size={15} />Social</a> : null}
              <span className="account-eyebrow">Perfil público Printora</span>
              <h1>{profile.display_name}</h1>
              {profile.bio ? <p>{profile.bio}</p> : null}
              <div className="public-profile-meta">
                {profile.location ? (
                  <span><MapPin size={15} />{profile.location}</span>
                ) : null}
              </div>
              <div className="public-profile-actions">
                <button type="button" className="secondary-button" disabled={busyAction !== null || relationState?.blocked} onClick={() => void runAction("follow", () => socialApi.follow(profile.user_id))}>
                  <UserPlus size={15} />
                  {relationState?.following ? "Seguindo" : "Seguir"}
                </button>
                {relationState?.following ? (
                  <button type="button" className="secondary-button" disabled={busyAction !== null} onClick={() => void runAction("unfollow", () => socialApi.unfollow(profile.user_id))}>
                    Deixar de seguir
                  </button>
                ) : null}
                <button type="button" className="secondary-button" disabled={busyAction !== null || relationState?.blocked || relationState?.friend || relationState?.sentFriendRequest} onClick={() => void runAction("friend", () => socialApi.requestFriend(profile.user_id))}>
                  <Users size={15} />
                  {relationState?.friend ? "Amigos" : relationState?.sentFriendRequest ? "Solicitada" : "Solicitar amizade"}
                </button>
                {relationState?.sentFriendRequest ? (
                  <button type="button" className="secondary-button" disabled={busyAction !== null} onClick={() => void runAction("cancel", () => socialApi.cancelFriendRequest(profile.user_id))}>
                    Cancelar solicitação
                  </button>
                ) : null}
                {relationState?.pendingFriendRequest ? (
                  <>
                    <button type="button" className="primary-button" disabled={busyAction !== null} onClick={() => void runAction("accept", () => socialApi.acceptFriend(profile.user_id))}>
                      Aceitar
                    </button>
                    <button type="button" className="secondary-button" disabled={busyAction !== null} onClick={() => void runAction("reject", () => socialApi.rejectFriend(profile.user_id))}>
                      Recusar
                    </button>
                  </>
                ) : null}
                {relationState?.friend ? (
                  <button type="button" className="secondary-button" disabled={busyAction !== null} onClick={() => void runAction("unfriend", () => socialApi.unfriend(profile.user_id))}>
                    Desfazer amizade
                  </button>
                ) : null}
                <button type="button" className="secondary-button danger" disabled={busyAction !== null} onClick={() => void runAction(relationState?.blocked ? "unblock" : "block", () => relationState?.blocked ? socialApi.unblock(profile.user_id) : socialApi.block(profile.user_id))}>
                  <Ban size={15} />
                  {relationState?.blocked ? "Desbloquear" : "Bloquear"}
                </button>
              </div>
              {actionError ? <p className="public-action-error">{actionError}</p> : null}
            </div>
          </header>

          <section className="public-profile-grid">
            <article className="panel public-profile-panel">
              <h2>Links</h2>
              <div className="public-link-list">
                {Object.entries(profile.social_links).filter(([, value]) => Boolean(value)).map(([key, value]) => (
                  <a key={key} href={value ?? "#"} target="_blank" rel="noreferrer">
                    <ExternalLink size={15} />
                    <span>{linkLabel(key)}</span>
                  </a>
                ))}
                {Object.values(profile.social_links).some(Boolean) ? null : <p>Nenhum link público informado.</p>}
              </div>
            </article>

            <article className="panel public-profile-panel">
              <h2>Impressoras públicas</h2>
              <div className="public-printer-list">
                {printers.map((printer) => (
                  <section key={printer.id} className="public-printer-card">
                    <div>
                      <Printer size={17} />
                      <strong>{printer.public_name}</strong>
                    </div>
                    <span>{printer.manufacturer_name} / {printer.model_name} / {printer.variant_name}</span>
                    {printer.public_description ? <p>{printer.public_description}</p> : null}
                    {printer.public_mods.length ? <small>Mods: {printer.public_mods.join(", ")}</small> : null}
                  </section>
                ))}
                {printers.length === 0 ? <p>Nenhuma impressora pública vinculada a este perfil.</p> : null}
              </div>
            </article>

            <article className="panel public-profile-panel">
              <h2>Biblioteca</h2>
              <div className="public-printer-list">
                {library.map((item) => (
                  <section key={item.id} className="public-printer-card">
                    <div>
                      <FileText size={17} />
                      <strong>{item.title}</strong>
                    </div>
                    <span>{item.files.map((file) => file.file_name).join(", ")}</span>
                    {item.description ? <p>{item.description}</p> : null}
                    {item.content_class !== "community" ? <small>{commercialLabel(item.content_class, item.commercial_status)}{item.promotion_disclosure ? ` · ${item.promotion_disclosure}` : ""}</small> : null}
                    <small>{item.version_label} / {item.license} / {item.original_author_name || "autoria não declarada"} / {item.download_count} downloads</small>
                    <button type="button" className="secondary-button" onClick={() => void socialApi.registerLibraryDownload(item.id)}>
                      <Download size={15} />
                      Download
                    </button>
                  </section>
                ))}
                {library.length === 0 ? <p>Nenhum arquivo visível neste perfil.</p> : null}
              </div>
            </article>
          </section>
        </section>
      ) : null}
    </>
  );

  if (embedded) {
    return (
      <section className="public-profile-shell public-profile-embedded">
        {content}
      </section>
    );
  }

  return (
    <main className="public-profile-shell">
      <section className="public-profile-topbar">
        <img src="/brand/printora-logo-horizontal-color.png" alt="Printora" />
        <a href="/" className="secondary-button">Entrar</a>
      </section>
      {content}
    </main>
  );
}

function commercialLabel(contentClass: LibraryItem["content_class"], status: LibraryItem["commercial_status"]) {
  const labels: Record<LibraryItem["content_class"], string> = {
    community: "Comunidade",
    curated: "Curado",
    premium: "Premium",
    sponsored: "Patrocinado",
  };
  return `${labels[contentClass]} · ${status === "approved" ? "revisado" : "em revisão"}`;
}

function summarizeRelationship(targetUserId: number, relationships: RelationshipSummary) {
  return {
    following: relationships.following.some((item) => item.target_user_id === targetUserId),
    friend: relationships.friends.some((item) => item.target_user_id === targetUserId),
    blocked: relationships.blocked.some((item) => item.target_user_id === targetUserId),
    sentFriendRequest: relationships.sent_friend_requests.some((item) => item.target_user_id === targetUserId),
    pendingFriendRequest: relationships.pending_friend_requests.some((item) => item.target_user_id === targetUserId),
  };
}

function linkLabel(key: string) {
  const labels: Record<string, string> = {
    website: "Site",
    github: "GitHub",
    instagram: "Instagram",
    youtube: "YouTube",
    x: "X/Twitter",
    printables: "Printables",
    makerworld: "MakerWorld",
  };
  return labels[key] ?? key;
}
