import React from "react";
import { Globe2, Lock, RadioTower, RefreshCw, Shield, UserRound, Users } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { ScreenPropsFor } from "./ScreenProps";
import type { CatalogSummary, CatalogVariant, Community, ProfileVisibility, PublicPrinter, PublicProfile, RelationshipSummary } from "../types";

type SocialScreenProps = ScreenPropsFor<"authUser" | "printers" | "loadPrinters" | "setError" | "showToast">;

export function SocialScreen({ authUser, printers, loadPrinters, setError, showToast }: SocialScreenProps) {
  const [catalog, setCatalog] = React.useState<CatalogSummary | null>(null);
  const [profile, setProfile] = React.useState<PublicProfile | null>(null);
  const [publicPrinters, setPublicPrinters] = React.useState<PublicPrinter[]>([]);
  const [communities, setCommunities] = React.useState<Community[]>([]);
  const [relationships, setRelationships] = React.useState<RelationshipSummary | null>(null);
  const [selectedPrinterId, setSelectedPrinterId] = React.useState<number | "">("");
  const [selectedVariantId, setSelectedVariantId] = React.useState<number | "">("");
  const [publicDescription, setPublicDescription] = React.useState("");
  const [publicMods, setPublicMods] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const variants = React.useMemo(() => flattenVariants(catalog), [catalog]);
  const selectedPrinter = printers.find((printer) => printer.id === selectedPrinterId);
  const selectedVariant = variants.find((variant) => variant.id === selectedVariantId);

  async function loadSocial() {
    setBusy(true);
    try {
      const [catalogPayload, profilePayload, communitiesPayload, relationshipsPayload] = await Promise.all([
        socialApi.catalog(),
        socialApi.myProfile(),
        socialApi.communities(),
        socialApi.relationships(),
      ]);
      setCatalog(catalogPayload);
      setProfile(profilePayload);
      setCommunities(communitiesPayload);
      setRelationships(relationshipsPayload);
      setPublicPrinters(await socialApi.profilePrinters(profilePayload.slug));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar área social");
    } finally {
      setBusy(false);
    }
  }

  React.useEffect(() => {
    void loadSocial();
  }, []);

  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) {
      return;
    }
    const form = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const visibility = String(form.get("visibility") || "public") as ProfileVisibility;
      const updated = await socialApi.updateProfile({
        slug: String(form.get("slug") || ""),
        display_name: String(form.get("display_name") || authUser?.display_name || authUser?.email || "Maker"),
        bio: String(form.get("bio") || "") || null,
        location: String(form.get("location") || "") || null,
        avatar_url: String(form.get("avatar_url") || "") || null,
        social_links: {
          website: String(form.get("website") || "") || null,
          github: String(form.get("github") || "") || null,
          instagram: String(form.get("instagram") || "") || null,
        },
        visibility,
      });
      setProfile(updated);
      showToast({ tone: "success", title: "Perfil social salvo" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar perfil social");
    } finally {
      setBusy(false);
    }
  }

  async function publishPrinter(publicEnabled: boolean) {
    if (!selectedPrinterId || !selectedPrinter || (!selectedVariantId && publicEnabled)) {
      setError("Selecione uma impressora e uma variante do catálogo.");
      return;
    }
    setBusy(true);
    try {
      await socialApi.updatePrinterPublic(Number(selectedPrinterId), {
        public_profile_enabled: publicEnabled,
        catalog_variant_id: publicEnabled ? Number(selectedVariantId) : null,
        public_name: selectedPrinter.name,
        public_description: publicDescription || null,
        public_mods: publicMods.split(",").map((item) => item.trim()).filter(Boolean),
      });
      await loadPrinters();
      await loadSocial();
      showToast({ tone: "success", title: publicEnabled ? "Impressora publicada" : "Impressora privada" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar visibilidade da impressora");
    } finally {
      setBusy(false);
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
        <form className="social-panel" onSubmit={saveProfile}>
          <header>
            <UserRound size={18} />
            <h3>Perfil</h3>
          </header>
          <label>
            Nome público
            <input name="display_name" defaultValue={profile?.display_name ?? authUser?.display_name ?? ""} maxLength={120} />
          </label>
          <label>
            Slug
            <input name="slug" defaultValue={profile?.slug ?? ""} maxLength={80} />
          </label>
          <label>
            Bio
            <textarea name="bio" defaultValue={profile?.bio ?? ""} maxLength={280} />
          </label>
          <div className="social-form-grid">
            <label>
              Localização
              <input name="location" defaultValue={profile?.location ?? ""} maxLength={120} />
            </label>
            <label>
              Visibilidade
              <select name="visibility" defaultValue={profile?.visibility ?? "public"}>
                <option value="public">Público</option>
                <option value="unlisted">Não listado</option>
                <option value="private">Privado</option>
              </select>
            </label>
          </div>
          <div className="social-form-grid">
            <label>
              Site
              <input name="website" defaultValue={profile?.social_links.website ?? ""} />
            </label>
            <label>
              GitHub
              <input name="github" defaultValue={profile?.social_links.github ?? ""} />
            </label>
            <label>
              Instagram
              <input name="instagram" defaultValue={profile?.social_links.instagram ?? ""} />
            </label>
            <label>
              Avatar URL
              <input name="avatar_url" defaultValue={profile?.avatar_url ?? ""} />
            </label>
          </div>
          <button type="submit" className="primary-action" disabled={busy}>Salvar perfil</button>
        </form>

        <section className="social-panel">
          <header>
            <RadioTower size={18} />
            <h3>Impressora pública</h3>
          </header>
          <label>
            Inventário real
            <select value={selectedPrinterId} onChange={(event) => setSelectedPrinterId(event.target.value ? Number(event.target.value) : "")}>
              <option value="">Selecione</option>
              {printers.map((printer) => (
                <option key={printer.id} value={printer.id}>{printer.name}</option>
              ))}
            </select>
          </label>
          <label>
            Variante canônica
            <select value={selectedVariantId} onChange={(event) => setSelectedVariantId(event.target.value ? Number(event.target.value) : "")}>
              <option value="">Selecione</option>
              {variants.map((variant) => (
                <option key={variant.id} value={variant.id}>{variant.label}</option>
              ))}
            </select>
          </label>
          <label>
            Descrição pública
            <textarea value={publicDescription} onChange={(event) => setPublicDescription(event.target.value)} maxLength={500} />
          </label>
          <label>
            Mods públicos
            <input value={publicMods} onChange={(event) => setPublicMods(event.target.value)} placeholder="Tap, Nevermore, ERCF" />
          </label>
          <div className="social-actions">
            <button type="button" className="primary-action" disabled={busy || !selectedVariant} onClick={() => void publishPrinter(true)}>
              <Globe2 size={16} />
              Publicar
            </button>
            <button type="button" className="secondary-action" disabled={busy || !selectedPrinterId} onClick={() => void publishPrinter(false)}>
              <Lock size={16} />
              Tornar privada
            </button>
          </div>
          <PublicPrinterList printers={publicPrinters} />
        </section>
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
          <div className="community-list">
            {communities.map((community) => (
              <article key={community.id} className={`community-row ${community.member_count > 0 ? "active" : ""}`}>
                <div>
                  <strong>{community.name}</strong>
                  <span>{community.scope} · {community.status}</span>
                </div>
                <div>
                  <b>{community.member_count}</b>
                  <small>membros</small>
                </div>
                <div>
                  <b>{community.printer_count}</b>
                  <small>impressoras</small>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="social-panel">
          <header>
            <Shield size={18} />
            <h3>Relações</h3>
          </header>
          <RelationshipBlock title="Seguindo" items={relationships?.following ?? []} />
          <RelationshipBlock title="Seguidores" items={relationships?.followers ?? []} />
          <RelationshipBlock title="Amigos" items={relationships?.friends ?? []} />
          <RelationshipBlock title="Bloqueados" items={relationships?.blocked ?? []} />
        </section>
      </section>
    </div>
  );
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

function PublicPrinterList({ printers }: { printers: PublicPrinter[] }) {
  if (printers.length === 0) {
    return <p className="muted">Nenhuma impressora pública.</p>;
  }
  return (
    <div className="public-printer-list">
      {printers.map((printer) => (
        <article key={printer.id}>
          <strong>{printer.public_name}</strong>
          <span>{printer.manufacturer_name} · {printer.model_name} · {printer.variant_name}</span>
        </article>
      ))}
    </div>
  );
}

function RelationshipBlock({ title, items }: { title: string; items: Array<{ target_display_name: string | null; target_slug: string | null; status: string }> }) {
  return (
    <div className="relationship-block">
      <strong>{title}</strong>
      {items.length === 0 ? <span className="muted">Sem registros.</span> : null}
      {items.map((item) => (
        <span key={`${title}-${item.target_slug ?? item.target_display_name}-${item.status}`}>
          {item.target_display_name ?? item.target_slug ?? "Usuário"} · {item.status}
        </span>
      ))}
    </div>
  );
}

function flattenVariants(catalog: CatalogSummary | null): Array<CatalogVariant & { label: string }> {
  if (!catalog) {
    return [];
  }
  return catalog.manufacturers.flatMap((manufacturer) =>
    manufacturer.models.flatMap((model) =>
      model.variants.map((variant) => ({
        ...variant,
        label: `${manufacturer.name} · ${model.name} · ${variant.name}`,
      })),
    ),
  );
}
