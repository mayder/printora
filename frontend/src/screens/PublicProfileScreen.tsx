import React from "react";
import { ExternalLink, Lock, MapPin, Printer, UserRound } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { PublicPrinter, PublicProfile } from "../types";

interface PublicProfileScreenProps {
  slug: string;
}

export function PublicProfileScreen({ slug }: PublicProfileScreenProps) {
  const [profile, setProfile] = React.useState<PublicProfile | null>(null);
  const [printers, setPrinters] = React.useState<PublicPrinter[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let active = true;
    async function loadProfile() {
      setLoading(true);
      setError(null);
      try {
        const profilePayload = await socialApi.publicProfile(slug);
        const printerPayload = await socialApi.profilePrinters(profilePayload.slug);
        if (!active) return;
        setProfile(profilePayload);
        setPrinters(printerPayload);
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

  return (
    <main className="public-profile-shell">
      <section className="public-profile-topbar">
        <img src="/brand/printora-logo-horizontal-color.png" alt="Printora" />
        <a href="/" className="secondary-button">Entrar</a>
      </section>

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
              <span className="account-eyebrow">Perfil público Printora</span>
              <h1>{profile.display_name}</h1>
              {profile.bio ? <p>{profile.bio}</p> : null}
              <div className="public-profile-meta">
                {profile.location ? (
                  <span><MapPin size={15} />{profile.location}</span>
                ) : null}
              </div>
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
          </section>
        </section>
      ) : null}
    </main>
  );
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
