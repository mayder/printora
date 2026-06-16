import React from "react";
import { Archive, ArrowLeft, Box, CheckCircle2, ChevronLeft, ChevronRight, Download, ExternalLink, FileText, Filter, FolderOpen, GitBranch, Heart, ListChecks, Lock, MessageSquare, Pencil, Pin, Printer, Reply, RotateCcw, Send, SlidersHorizontal, ThumbsUp, Trash2, UserRound, Users, Wrench, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { Community, CommunityDetail, CommunityFeedItem, CommunityFeedSummary, DiscussionComment, DiscussionDetail, FeedContentType, FeedOrder, LibraryCollectionVisibility, LibraryFileKind, LibraryItem, LibraryLicense, LibraryOrganizerSummary, LibraryVisibility } from "../types";

interface PublicCommunityScreenProps {
  slug: string;
  embedded?: boolean;
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

export function PublicCommunityScreen({ slug, embedded = false }: PublicCommunityScreenProps) {
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

  const content = (
    <>
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
            <CommunityBrandMark community={community} />
            <div>
              <span className="account-eyebrow">{communityEyebrow(community)}</span>
              <h1>{community.name}</h1>
              <p>{statusDescription(community)}</p>
              <div className="public-profile-meta">
                <span><Box size={15} />{communityContext(community)}</span>
                {community.merged_into_slug ? <a href={`/c/${community.merged_into_slug}`}><ExternalLink size={15} />Abrir destino</a> : null}
              </div>
            </div>
            <a href="/?section=social" className="secondary-button public-community-back"><ArrowLeft size={16} />Voltar ao Social</a>
          </header>

          <section className="community-metrics">
            <CommunityMetric icon={Users} label="Membros" value={community.member_count} />
            <CommunityMetric icon={Printer} label="Impressoras públicas" value={community.printer_count} />
            <CommunityMetric icon={FileText} label="Arquivos" value={community.file_count} />
            <CommunityMetric icon={Wrench} label="Mods" value={community.mod_count} />
          </section>

          <article className="panel public-profile-panel community-technical-context">
            <h2>Contexto técnico</h2>
            <div className="public-spec-list">
              <span><Archive size={15} />Catálogo mestre</span>
              <span><SlidersHorizontal size={15} />{communityContext(community)}</span>
              <span><Lock size={15} />Sem acesso operacional, agente, Moonraker, SSH, token ou organização</span>
            </div>
          </article>

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

          <article className="panel public-profile-panel community-tab-panel">
            <CommunityTabContent community={community} tab={activeTab} />
          </article>
        </section>
      ) : null}
    </>
  );

  if (embedded) {
    return (
      <section className="public-profile-shell public-community-shell public-community-embedded">
        {content}
      </section>
    );
  }

  return (
    <main className="public-profile-shell public-community-shell">
      <section className="public-profile-topbar">
        <img src="/brand/printora-logo-horizontal-color.png" alt="Printora" />
        <a href="/?section=social" className="secondary-button"><ArrowLeft size={16} />Voltar ao Social</a>
      </section>
      {content}
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

function CommunityBrandMark({ community }: { community: CommunityDetail }) {
  return (
    <div className="public-avatar community-brand-avatar">
      {community.manufacturer_logo_url ? <img src={community.manufacturer_logo_url} alt="" /> : <span>{brandInitials(community.manufacturer_name ?? community.name)}</span>}
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
    return <CommunityLibrary community={community} />;
  }
  return <CommunityFeed community={community} />;
}

const visibilityOptions: Array<{ value: LibraryVisibility; label: string }> = [
  { value: "community", label: "Comunidade" },
  { value: "public", label: "Público" },
  { value: "friends", label: "Amigos" },
  { value: "private", label: "Privado" },
];

const licenseOptions: Array<{ value: LibraryLicense; label: string }> = [
  { value: "cc-by", label: "CC BY" },
  { value: "cc-by-sa", label: "CC BY-SA" },
  { value: "cc0", label: "CC0" },
  { value: "mit", label: "MIT" },
  { value: "custom", label: "Personalizada" },
  { value: "all-rights-reserved", label: "Todos os direitos" },
];

function CommunityLibrary({ community }: { community: CommunityDetail }) {
  const [items, setItems] = React.useState<LibraryItem[]>([]);
  const [organizer, setOrganizer] = React.useState<LibraryOrganizerSummary | null>(null);
  const [draft, setDraft] = React.useState({
    title: "",
    description: "",
    visibility: "community" as LibraryVisibility,
    component: "",
    version_label: "v1",
    material_suggestion: "",
    supports_required: false,
    orientation_notes: "",
    license: "cc-by" as LibraryLicense,
    original_author_name: "",
    source_url: "",
    attribution_text: "",
    publication_terms_accepted: false,
    file_kind: "stl" as LibraryFileKind,
    file_name: "",
    original_url: "",
  });
  const [collectionDraft, setCollectionDraft] = React.useState({ name: "", visibility: "private" as LibraryCollectionVisibility });
  const [printListDraft, setPrintListDraft] = React.useState({ name: "", printer_id: "" });
  const [uploadFile, setUploadFile] = React.useState<File | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [createOpen, setCreateOpen] = React.useState(false);

  const loadLibrary = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await socialApi.communityLibrary(community.slug));
      try {
        setOrganizer(await socialApi.libraryOrganizer());
      } catch {
        setOrganizer(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Biblioteca indisponível");
    } finally {
      setLoading(false);
    }
  }, [community.slug]);

  React.useEffect(() => {
    void loadLibrary();
  }, [loadLibrary]);

  async function submitItem(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      let created = await socialApi.createLibraryItem({
        title: draft.title,
        description: draft.description,
        visibility: draft.visibility,
        community_slug: community.slug,
        catalog_variant_id: community.variant_id,
        component: draft.component || null,
        version_label: draft.version_label || "v1",
        material_suggestion: draft.material_suggestion || null,
        supports_required: draft.supports_required,
        orientation_notes: draft.orientation_notes || null,
        license: draft.license,
        original_author_name: draft.original_author_name || null,
        source_url: draft.source_url || null,
        attribution_text: draft.attribution_text || null,
        publication_terms_accepted: draft.publication_terms_accepted,
        files: [{
          file_kind: draft.file_kind,
          file_name: draft.file_name,
          original_url: draft.original_url || null,
        }],
      });
      if (uploadFile) {
        created = await socialApi.uploadLibraryFile(created.id, uploadFile);
      }
      setItems((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setDraft((current) => ({ ...current, title: "", description: "", file_name: "", original_url: "", component: "", material_suggestion: "", orientation_notes: "", original_author_name: "", source_url: "", attribution_text: "", publication_terms_accepted: false }));
      setUploadFile(null);
      setCreateOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível cadastrar arquivo");
    }
  }

  async function registerDownload(itemId: number) {
    try {
      const updated = await socialApi.registerLibraryDownload(itemId);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      try {
        setOrganizer(await socialApi.libraryOrganizer());
      } catch {
        setOrganizer(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download não registrado");
    }
  }

  async function registerVersionDownload(itemId: number, versionId: number) {
    try {
      const updated = await socialApi.registerLibraryVersionDownload(itemId, versionId);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      try {
        setOrganizer(await socialApi.libraryOrganizer());
      } catch {
        setOrganizer(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download da versão não registrado");
    }
  }

  async function createVersion(item: LibraryItem, versionLabel: string, changelog: string) {
    try {
      const updated = await socialApi.createLibraryVersion(item.id, {
        version_label: versionLabel,
        changelog,
        files: item.files.map((file) => ({
          file_kind: file.file_kind,
          file_name: file.file_name,
          original_url: file.original_url,
          size_bytes: file.size_bytes,
          sha256: file.sha256,
        })),
      });
      setItems((current) => current.map((currentItem) => currentItem.id === updated.id ? updated : currentItem));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Versão não criada");
    }
  }

  async function promoteVersion(itemId: number, versionId: number) {
    try {
      const updated = await socialApi.promoteLibraryVersion(itemId, versionId);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Versão não promovida");
    }
  }

  async function createCollection(event: React.FormEvent) {
    event.preventDefault();
    try {
      setOrganizer(await socialApi.createLibraryCollection({
        name: collectionDraft.name,
        visibility: collectionDraft.visibility,
        community_slug: collectionDraft.visibility === "community" ? community.slug : null,
      }));
      setCollectionDraft({ name: "", visibility: "private" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Coleção não criada");
    }
  }

  async function createPrintList(event: React.FormEvent) {
    event.preventDefault();
    try {
      setOrganizer(await socialApi.createPrintList({
        name: printListDraft.name,
        printer_id: printListDraft.printer_id ? Number(printListDraft.printer_id) : null,
      }));
      setPrintListDraft({ name: "", printer_id: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lista não criada");
    }
  }

  async function favoriteItem(itemId: number) {
    try {
      const updated = await socialApi.favoriteLibraryItem(itemId);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      setOrganizer(await socialApi.libraryOrganizer());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Favorito não registrado");
    }
  }

  async function addToCollection(item: LibraryItem) {
    const collection = organizer?.collections[0];
    if (!collection) {
      setError("Crie uma coleção antes de adicionar arquivos");
      return;
    }
    try {
      setOrganizer(await socialApi.addLibraryCollectionItem(collection.id, { item_id: item.id, version_id: item.current_version_id }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Arquivo não adicionado à coleção");
    }
  }

  async function addToPrintList(item: LibraryItem) {
    const printList = organizer?.print_lists[0];
    if (!printList || !item.current_version_id) {
      setError("Crie uma lista de impressão e mantenha uma versão atual antes de adicionar");
      return;
    }
    try {
      setOrganizer(await socialApi.addPrintListItem(printList.id, { item_id: item.id, version_id: item.current_version_id, status: "want_to_print" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Arquivo não adicionado à lista");
    }
  }

  async function archiveItem(itemId: number) {
    try {
      await socialApi.archiveLibraryItem(itemId);
      setItems((current) => current.filter((item) => item.id !== itemId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível arquivar");
    }
  }

  async function analyzeFile(fileId: number) {
    try {
      const updated = await socialApi.analyzeLibraryFile(fileId);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Análise não concluída");
    }
  }

  return (
    <div className="community-library">
      <div className="community-feed-header">
        <div>
          <h2>Biblioteca de arquivos</h2>
          <p>Modelos STL/3MF e pacotes declarados por metadados, com dono, licença e visibilidade explícitos.</p>
        </div>
        <button type="button" className="primary-button" onClick={() => setCreateOpen(true)}><FileText size={15} />Cadastrar arquivo</button>
      </div>
      {createOpen ? (
        <div className="modal-backdrop" role="presentation">
          <section className="modal-card community-library-modal" role="dialog" aria-modal="true" aria-label="Cadastrar arquivo">
            <header className="modal-header">
              <div>
                <h2>Cadastrar arquivo</h2>
                <p>Informe autoria, licença e arquivo antes de publicar na biblioteca da comunidade.</p>
              </div>
              <button type="button" className="icon-button" onClick={() => setCreateOpen(false)} aria-label="Fechar cadastro"><X size={17} /></button>
            </header>
            <form className="community-library-form community-library-form-redesign" onSubmit={submitItem}>
              <section className="community-library-form-section">
                <header>
                  <strong>Modelo</strong>
                  <span>Identificação pública e visibilidade do item.</span>
                </header>
                <div className="community-library-form-grid">
                  <label className="community-library-field span-2">
                    <span>Nome do modelo</span>
                    <input value={draft.title} maxLength={160} placeholder="Ex.: Suporte de sensor TAP" onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} required />
                  </label>
                  <label className="community-library-field">
                    <span>Visibilidade</span>
                    <select value={draft.visibility} onChange={(event) => setDraft((current) => ({ ...current, visibility: event.target.value as LibraryVisibility }))}>
                      {visibilityOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                  </label>
                  <label className="community-library-field span-full">
                    <span>Descrição técnica</span>
                    <textarea value={draft.description} maxLength={1200} placeholder="Compatibilidade, contexto de uso e observações relevantes para impressão." onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} />
                  </label>
                </div>
              </section>

              <section className="community-library-form-section">
                <header>
                  <strong>Arquivo</strong>
                  <span>STL, 3MF ou pacote enviado para validação/quarentena.</span>
                </header>
                <div className="community-library-form-grid">
                  <label className="community-library-field">
                    <span>Tipo</span>
                    <select value={draft.file_kind} onChange={(event) => setDraft((current) => ({ ...current, file_kind: event.target.value as LibraryFileKind }))}>
                      <option value="stl">STL</option>
                      <option value="3mf">3MF</option>
                      <option value="bundle">Pacote</option>
                    </select>
                  </label>
                  <label className="community-library-field">
                    <span>Nome do arquivo</span>
                    <input value={draft.file_name} placeholder="arquivo.stl" onChange={(event) => setDraft((current) => ({ ...current, file_name: event.target.value }))} required />
                  </label>
                  <label className="community-library-field span-2">
                    <span>URL pública opcional</span>
                    <input value={draft.original_url} placeholder="https://..." onChange={(event) => setDraft((current) => ({ ...current, original_url: event.target.value }))} />
                  </label>
                  <label className="community-library-field span-full">
                    <span>Upload local</span>
                    <input className="community-file-input" type="file" accept=".stl,.3mf,.zip" onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      setUploadFile(file);
                      if (file) setDraft((current) => ({ ...current, file_name: file.name }));
                    }} />
                  </label>
                </div>
              </section>

              <section className="community-library-form-section">
                <header>
                  <strong>Autoria e licença</strong>
                  <span>Dados necessários para atribuição e uso público do modelo.</span>
                </header>
                <div className="community-library-form-grid">
                  <label className="community-library-field">
                    <span>Licença</span>
                    <select value={draft.license} onChange={(event) => setDraft((current) => ({ ...current, license: event.target.value as LibraryLicense }))}>
                      {licenseOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                  </label>
                  <label className="community-library-field">
                    <span>Autor original</span>
                    <input value={draft.original_author_name} placeholder="Nome ou usuário" onChange={(event) => setDraft((current) => ({ ...current, original_author_name: event.target.value }))} />
                  </label>
                  <label className="community-library-field span-2">
                    <span>Fonte pública</span>
                    <input value={draft.source_url} placeholder="https://..." onChange={(event) => setDraft((current) => ({ ...current, source_url: event.target.value }))} />
                  </label>
                  <label className="community-library-field span-full">
                    <span>Crédito e atribuição</span>
                    <input value={draft.attribution_text} placeholder="Texto de atribuição exibido junto do item." onChange={(event) => setDraft((current) => ({ ...current, attribution_text: event.target.value }))} />
                  </label>
                  <label className="community-checkbox-card span-full">
                    <input type="checkbox" checked={draft.publication_terms_accepted} onChange={(event) => setDraft((current) => ({ ...current, publication_terms_accepted: event.target.checked }))} />
                    <span>
                      <strong>Termos de publicação aceitos</strong>
                      <small>Confirmo que tenho autorização para publicar este arquivo e sua licença.</small>
                    </span>
                  </label>
                </div>
              </section>

              <section className="community-library-form-section">
                <header>
                  <strong>Impressão</strong>
                  <span>Metadados técnicos usados em busca, análise e listas de impressão.</span>
                </header>
                <div className="community-library-form-grid">
                  <label className="community-library-field">
                    <span>Componente</span>
                    <input value={draft.component} placeholder="Ex.: hotend, TAP, painel" onChange={(event) => setDraft((current) => ({ ...current, component: event.target.value }))} />
                  </label>
                  <label className="community-library-field">
                    <span>Versão inicial</span>
                    <input value={draft.version_label} placeholder="v1" onChange={(event) => setDraft((current) => ({ ...current, version_label: event.target.value }))} required />
                  </label>
                  <label className="community-library-field span-2">
                    <span>Material sugerido</span>
                    <input value={draft.material_suggestion} placeholder="Ex.: ABS, ASA, PETG" onChange={(event) => setDraft((current) => ({ ...current, material_suggestion: event.target.value }))} />
                  </label>
                  <label className="community-checkbox-card span-full">
                    <input type="checkbox" checked={draft.supports_required} onChange={(event) => setDraft((current) => ({ ...current, supports_required: event.target.checked }))} />
                    <span>
                      <strong>Exige suporte</strong>
                      <small>Marque quando a orientação recomendada precisar de suporte.</small>
                    </span>
                  </label>
                  <label className="community-library-field span-full">
                    <span>Orientação de impressão</span>
                    <textarea value={draft.orientation_notes} maxLength={500} placeholder="Posição na mesa, orientação, brim, suportes e observações de fatiamento." onChange={(event) => setDraft((current) => ({ ...current, orientation_notes: event.target.value }))} />
                  </label>
                </div>
              </section>
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancelar</button>
                <button type="submit" className="primary-button"><FileText size={15} />Cadastrar arquivo</button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
      {organizer ? (
        <section className="community-organizer-panel">
          <header>
            <strong><ListChecks size={15} />Coleções e listas</strong>
            <span>{organizer.favorites.length} favoritos / {organizer.collections.length} coleções / {organizer.print_lists.length} listas</span>
          </header>
          <div className="community-organizer-grid">
            <form onSubmit={createCollection}>
              <input value={collectionDraft.name} placeholder="Nova coleção" onChange={(event) => setCollectionDraft((current) => ({ ...current, name: event.target.value }))} required />
              <select value={collectionDraft.visibility} onChange={(event) => setCollectionDraft((current) => ({ ...current, visibility: event.target.value as LibraryCollectionVisibility }))}>
                <option value="private">Privada</option>
                <option value="community">Comunidade</option>
                <option value="public">Pública</option>
              </select>
              <button type="submit" className="secondary-button"><FolderOpen size={15} />Criar</button>
            </form>
            <form onSubmit={createPrintList}>
              <input value={printListDraft.name} placeholder="Nova lista de impressão" onChange={(event) => setPrintListDraft((current) => ({ ...current, name: event.target.value }))} required />
              <input value={printListDraft.printer_id} inputMode="numeric" placeholder="ID da impressora" onChange={(event) => setPrintListDraft((current) => ({ ...current, printer_id: event.target.value }))} />
              <button type="submit" className="secondary-button"><Printer size={15} />Criar</button>
            </form>
          </div>
          <div className="community-organizer-summary">
            {organizer.collections.slice(0, 4).map((collection) => <span key={collection.id}>{collection.name} / {collection.item_count} itens</span>)}
            {organizer.print_lists.slice(0, 4).map((list) => <span key={list.id}>{list.name} / {list.items.length} itens</span>)}
            {organizer.downloads.slice(0, 3).map((download) => <span key={download.id}>{download.title} / {download.version_label || "atual"}</span>)}
          </div>
        </section>
      ) : null}
      {error ? <p className="public-action-error">{error}</p> : null}
      {loading ? <p>Carregando biblioteca...</p> : items.length ? (
        <div className="community-library-list">
          {items.map((item) => (
            <LibraryItemCard
              key={item.id}
              item={item}
              onDownload={() => registerDownload(item.id)}
              onVersionDownload={(versionId) => registerVersionDownload(item.id, versionId)}
              onCreateVersion={(versionLabel, changelog) => createVersion(item, versionLabel, changelog)}
              onPromoteVersion={(versionId) => promoteVersion(item.id, versionId)}
              onFavorite={() => favoriteItem(item.id)}
              onAddToCollection={() => addToCollection(item)}
              onAddToPrintList={() => addToPrintList(item)}
              onArchive={() => archiveItem(item.id)}
              onAnalyze={analyzeFile}
            />
          ))}
        </div>
      ) : <Placeholder title="Biblioteca vazia" text="Nenhum arquivo visível para esta comunidade." />}
    </div>
  );
}

function LibraryItemCard({
  item,
  onDownload,
  onVersionDownload,
  onCreateVersion,
  onPromoteVersion,
  onFavorite,
  onAddToCollection,
  onAddToPrintList,
  onArchive,
  onAnalyze,
}: {
  item: LibraryItem;
  onDownload: () => void;
  onVersionDownload: (versionId: number) => void;
  onCreateVersion: (versionLabel: string, changelog: string) => void;
  onPromoteVersion: (versionId: number) => void;
  onFavorite: () => void;
  onAddToCollection: () => void;
  onAddToPrintList: () => void;
  onArchive: () => void;
  onAnalyze: (fileId: number) => void;
}) {
  const analyzedFile = item.files.find((file) => file.thumbnail_svg || file.analysis?.dimensions_mm);
  const [versionDraft, setVersionDraft] = React.useState({ label: nextVersionLabel(item.version_label), changelog: "" });
  return (
    <article className="community-library-card">
      <header>
        <div>
          <span>{libraryVisibilityLabel(item.visibility)}</span>
          <h3>{item.title}</h3>
        </div>
        <strong>{item.version_label}</strong>
      </header>
      {item.description ? <p>{item.description}</p> : null}
      <div className="community-license-strip">
        <span>{licenseLabel(item.license)}</span>
        <span>{item.original_author_name ? `Autor: ${item.original_author_name}` : "Autoria não declarada"}</span>
        {item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer"><ExternalLink size={14} />Fonte</a> : null}
        {item.remix_source_title ? <span>Derivado de {item.remix_source_title}</span> : null}
      </div>
      {item.attribution_text ? <small>{item.attribution_text}</small> : null}
      {analyzedFile?.thumbnail_svg ? <div className="community-model-preview" dangerouslySetInnerHTML={{ __html: analyzedFile.thumbnail_svg }} /> : null}
      {analyzedFile ? <ModelAnalysisSummary file={analyzedFile} /> : null}
      <div className="community-feed-tags">
        {item.component ? <span>{item.component}</span> : null}
        {item.material_suggestion ? <span>{item.material_suggestion}</span> : null}
        {item.supports_required ? <span>Suporte necessário</span> : null}
        <span>{licenseLabel(item.license)}</span>
      </div>
      <div className="community-file-list">
        {item.files.map((file) => (
          <span key={file.id ?? file.file_name}><FileText size={14} />{file.file_name} / {file.file_kind.toUpperCase()} / {uploadStatusLabel(file.validation_status)}</span>
        ))}
      </div>
      {item.files.some((file) => file.rejection_reason) ? <small>{item.files.find((file) => file.rejection_reason)?.rejection_reason}</small> : null}
      {item.orientation_notes ? <small>{item.orientation_notes}</small> : null}
      <section className="community-version-panel">
        <header>
          <strong><GitBranch size={15} />Histórico de versões</strong>
          <span>{item.current_version_id ? `Atual: ${item.version_label}` : item.version_label}</span>
        </header>
        <form onSubmit={(event) => {
          event.preventDefault();
          onCreateVersion(versionDraft.label, versionDraft.changelog);
          setVersionDraft((current) => ({ label: nextVersionLabel(current.label), changelog: "" }));
        }}>
          <input value={versionDraft.label} maxLength={40} placeholder="Nova versão" onChange={(event) => setVersionDraft((current) => ({ ...current, label: event.target.value }))} required />
          <input value={versionDraft.changelog} maxLength={1000} placeholder="Changelog da versão" onChange={(event) => setVersionDraft((current) => ({ ...current, changelog: event.target.value }))} />
          <button type="submit" className="secondary-button"><GitBranch size={15} />Criar versão</button>
        </form>
        <div className="community-version-list">
          {item.versions.map((version) => (
            <div key={version.id} className={version.is_current ? "active" : ""}>
              <div>
                <strong>{version.version_label}</strong>
                <small>{version.changelog || "Sem changelog"} / {version.files.length} arquivo(s) / {version.download_count} downloads</small>
              </div>
              <button type="button" className="secondary-button" onClick={() => onVersionDownload(version.id)}><Download size={15} />Versão</button>
              {!version.is_current ? <button type="button" className="secondary-button" onClick={() => onPromoteVersion(version.id)}><RotateCcw size={15} />Usar</button> : null}
            </div>
          ))}
        </div>
      </section>
      <footer>
        <span>{item.owner_display_name ? `Por ${item.owner_display_name}` : "Autor"}</span>
        <span>{item.manufacturer_name && item.model_name ? `${item.manufacturer_name} / ${item.model_name}` : "Sem vínculo de catálogo"}</span>
        <span>{item.download_count} downloads</span>
        <span>{item.favorite_count} favoritos</span>
        <span>{item.collection_count} coleções</span>
        <span>{item.print_list_count} listas</span>
      </footer>
      <div className="community-feed-actions">
        {item.files.filter((file) => file.id && ["quarantined", "analysis_failed", "analyzed"].includes(file.validation_status)).map((file) => (
          <button key={file.id} type="button" className="secondary-button" onClick={() => onAnalyze(file.id ?? 0)}><Box size={15} />Analisar</button>
        ))}
        <button type="button" className="secondary-button" onClick={onFavorite}><Heart size={15} />Favoritar</button>
        <button type="button" className="secondary-button" onClick={onAddToCollection}><FolderOpen size={15} />Coleção</button>
        <button type="button" className="secondary-button" onClick={onAddToPrintList}><ListChecks size={15} />Lista</button>
        <button type="button" className="secondary-button" onClick={onDownload}><Download size={15} />Download</button>
        <button type="button" className="secondary-button danger" onClick={onArchive}><Trash2 size={15} />Arquivar</button>
      </div>
    </article>
  );
}

function ModelAnalysisSummary({ file }: { file: LibraryItem["files"][number] }) {
  const dimensions = file.analysis?.dimensions_mm as { x?: number; y?: number; z?: number } | undefined;
  const problems = Array.isArray(file.analysis?.problems) ? file.analysis.problems as Array<{ code?: string; message?: string; severity?: string }> : [];
  return (
    <div className="community-model-analysis">
      {dimensions ? <span>{Number(dimensions.x ?? 0).toFixed(1)} x {Number(dimensions.y ?? 0).toFixed(1)} x {Number(dimensions.z ?? 0).toFixed(1)} mm</span> : null}
      {typeof file.analysis?.approx_volume_mm3 === "number" ? <span>{Number(file.analysis.approx_volume_mm3).toFixed(0)} mm3</span> : null}
      {typeof file.analysis?.triangle_count === "number" ? <span>{Number(file.analysis.triangle_count)} triângulos</span> : null}
      {problems.map((problem) => <small key={`${problem.code}-${problem.message}`}>{problem.message}</small>)}
    </div>
  );
}

function nextVersionLabel(current: string) {
  const match = current.match(/^v(\d+)$/i);
  if (!match) return "";
  return `v${Number(match[1]) + 1}`;
}

function CommunityFeed({ community }: { community: CommunityDetail }) {
  const [feed, setFeed] = React.useState<CommunityFeedSummary | null>(null);
  const [selectedPostId, setSelectedPostId] = React.useState<number | null>(null);
  const [newPost, setNewPost] = React.useState({ content_type: "question" as FeedContentType, title: "", body: "", component: "", material: "", firmware_family: "", problem_tag: "" });
  const [posting, setPosting] = React.useState(false);
  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [postFormOpen, setPostFormOpen] = React.useState(false);
  const [contentType, setContentType] = React.useState<FeedContentType | "">("");
  const [component, setComponent] = React.useState("");
  const [material, setMaterial] = React.useState("");
  const [firmware, setFirmware] = React.useState("");
  const [problem, setProblem] = React.useState("");
  const [order, setOrder] = React.useState<FeedOrder>("recommended");
  const [page, setPage] = React.useState(1);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const loadFeed = React.useCallback(async () => {
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
      setFeed(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feed indisponível");
    } finally {
      setLoading(false);
    }
  }, [community.slug, contentType, component, material, firmware, problem, order, page]);

  React.useEffect(() => {
    let active = true;
    void loadFeed().then(() => {
      if (!active) return;
    });
    return () => {
      active = false;
    };
  }, [loadFeed]);

  const resetPage = (action: () => void) => {
    setPage(1);
    action();
  };

  async function submitPost(event: React.FormEvent) {
    event.preventDefault();
    setPosting(true);
    setError(null);
    try {
      const payload = await socialApi.createCommunityPost(community.slug, {
        content_type: newPost.content_type,
        title: newPost.title,
        body: newPost.body,
        component: newPost.component || null,
        material: newPost.material || null,
        firmware_family: newPost.firmware_family || null,
        problem_tag: newPost.problem_tag || null,
      });
      setFeed(payload);
      setSelectedPostId(payload.items.find((item) => item.title === newPost.title)?.id ?? null);
      setNewPost({ content_type: "question", title: "", body: "", component: "", material: "", firmware_family: "", problem_tag: "" });
      setPostFormOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível publicar");
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="community-feed">
      <div className="community-feed-header">
        <div>
          <h2>Feed técnico</h2>
          <p>Conteúdo público da comunidade, organizado por contexto técnico.</p>
        </div>
        <div className="community-feed-controls">
          <button type="button" className={`secondary-button ${filtersOpen ? "active" : ""}`} onClick={() => setFiltersOpen((current) => !current)}><Filter size={15} />Filtros</button>
          <select aria-label="Ordenar feed" value={order} onChange={(event) => resetPage(() => setOrder(event.target.value as FeedOrder))}>
            {feedOrderOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <button type="button" className="primary-button" onClick={() => setPostFormOpen((current) => !current)}><MessageSquare size={15} />Nova discussão</button>
        </div>
      </div>

      {filtersOpen ? <div className="community-feed-filters">
        <select value={contentType} onChange={(event) => resetPage(() => setContentType(event.target.value as FeedContentType | ""))}>
          {feedTypeOptions.map((option) => <option key={option.value || "all"} value={option.value}>{option.label}</option>)}
        </select>
        <FilterSelect label="Componente" value={component} options={feed?.filters.components ?? []} onChange={(value) => resetPage(() => setComponent(value))} />
        <FilterSelect label="Material" value={material} options={feed?.filters.materials ?? []} onChange={(value) => resetPage(() => setMaterial(value))} />
        <FilterSelect label="Firmware" value={firmware} options={feed?.filters.firmware ?? []} onChange={(value) => resetPage(() => setFirmware(value))} />
        <FilterSelect label="Problema" value={problem} options={feed?.filters.problems ?? []} onChange={(value) => resetPage(() => setProblem(value))} />
      </div> : null}

      {postFormOpen ? <form className="community-discussion-form" onSubmit={submitPost}>
        <div className="community-discussion-form-row">
          <select value={newPost.content_type} onChange={(event) => setNewPost((current) => ({ ...current, content_type: event.target.value as FeedContentType }))}>
            {feedTypeOptions.filter((option) => option.value && option.value !== "curation_notice").map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <input value={newPost.title} maxLength={160} placeholder="Título da discussão" onChange={(event) => setNewPost((current) => ({ ...current, title: event.target.value }))} required />
        </div>
        <textarea value={newPost.body} maxLength={1200} placeholder="Descreva dúvida, ajuste, mod ou resultado técnico" onChange={(event) => setNewPost((current) => ({ ...current, body: event.target.value }))} required />
        <div className="community-discussion-form-row">
          <input value={newPost.component} placeholder="Componente" onChange={(event) => setNewPost((current) => ({ ...current, component: event.target.value }))} />
          <input value={newPost.material} placeholder="Material" onChange={(event) => setNewPost((current) => ({ ...current, material: event.target.value }))} />
          <input value={newPost.firmware_family} placeholder="Firmware" onChange={(event) => setNewPost((current) => ({ ...current, firmware_family: event.target.value }))} />
          <input value={newPost.problem_tag} placeholder="Problema" onChange={(event) => setNewPost((current) => ({ ...current, problem_tag: event.target.value }))} />
          <button type="submit" className="primary-button" disabled={posting}><Send size={15} />Publicar</button>
        </div>
      </form> : null}

      {loading ? <p>Carregando feed...</p> : error ? <p>{error}</p> : feed && feed.items.length ? (
        <>
          <div className="community-feed-list">
            {feed.items.map((item) => (
              <FeedItemCard
                key={item.id}
                item={item}
                selected={selectedPostId === item.id}
                onOpen={() => setSelectedPostId((current) => current === item.id ? null : item.id)}
                onReact={async () => {
                  await socialApi.reactToPost(item.id, "useful");
                  await loadFeed();
                }}
              />
            ))}
          </div>
          {selectedPostId ? <DiscussionPanel postId={selectedPostId} onChanged={loadFeed} /> : null}
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

function FeedItemCard({ item, selected, onOpen, onReact }: { item: CommunityFeedItem; selected: boolean; onOpen: () => void; onReact: () => void }) {
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
      <footer>
        <span>{item.author_display_name ? `Por ${item.author_display_name}` : "Curadoria da comunidade"}</span>
        <span>{item.comment_count} comentários</span>
        <span>{item.reaction_count} reações</span>
        {item.solution_comment_id ? <span><CheckCircle2 size={14} />Solução marcada</span> : null}
      </footer>
      <div className="community-feed-actions">
        <button type="button" className="secondary-button" onClick={onOpen}><MessageSquare size={15} />{selected ? "Fechar" : "Discussão"}</button>
        <button type="button" className="secondary-button" onClick={onReact}><ThumbsUp size={15} />Útil</button>
      </div>
    </article>
  );
}

function DiscussionPanel({ postId, onChanged }: { postId: number; onChanged: () => void }) {
  const [detail, setDetail] = React.useState<DiscussionDetail | null>(null);
  const [commentBody, setCommentBody] = React.useState("");
  const [replyTo, setReplyTo] = React.useState<number | null>(null);
  const [editPost, setEditPost] = React.useState(false);
  const [postDraft, setPostDraft] = React.useState({ title: "", body: "" });
  const [error, setError] = React.useState<string | null>(null);

  const loadDiscussion = React.useCallback(async () => {
    try {
      const payload = await socialApi.discussion(postId);
      setDetail(payload);
      setPostDraft({ title: payload.post.title, body: payload.post.body });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Discussão indisponível");
    }
  }, [postId]);

  React.useEffect(() => {
    void loadDiscussion();
  }, [loadDiscussion]);

  async function submitComment(event: React.FormEvent) {
    event.preventDefault();
    try {
      await socialApi.createComment(postId, { body: commentBody, parent_comment_id: replyTo });
      setCommentBody("");
      setReplyTo(null);
      await loadDiscussion();
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível comentar");
    }
  }

  async function savePost(event: React.FormEvent) {
    event.preventDefault();
    try {
      const payload = await socialApi.updatePost(postId, postDraft);
      setDetail(payload);
      setEditPost(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível editar");
    }
  }

  async function deletePost() {
    try {
      await socialApi.deletePost(postId);
      await loadDiscussion();
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível remover");
    }
  }

  if (!detail) return <div className="community-discussion-panel">{error || "Carregando discussão..."}</div>;

  return (
    <section className="community-discussion-panel">
      <header>
        <div>
          <h3>Discussão técnica</h3>
          <p>{detail.post.deleted_at ? "Conteúdo removido logicamente; comentários permanecem para contexto." : detail.post.title}</p>
        </div>
        <div className="community-feed-actions">
          <button type="button" className="secondary-button" onClick={() => setEditPost((current) => !current)}><Pencil size={15} />Editar</button>
          <button type="button" className="secondary-button danger" onClick={deletePost}><Trash2 size={15} />Remover</button>
        </div>
      </header>
      {error ? <p className="public-action-error">{error}</p> : null}
      {editPost ? (
        <form className="community-discussion-form" onSubmit={savePost}>
          <input value={postDraft.title} onChange={(event) => setPostDraft((current) => ({ ...current, title: event.target.value }))} required />
          <textarea value={postDraft.body} onChange={(event) => setPostDraft((current) => ({ ...current, body: event.target.value }))} required />
          <button type="submit" className="primary-button"><Pencil size={15} />Salvar edição</button>
        </form>
      ) : null}
      <div className="community-comment-list">
        {detail.comments.map((comment) => (
          <CommentCard key={comment.id} postId={postId} comment={comment} solved={detail.post.solution_comment_id === comment.id} onReply={setReplyTo} onChanged={async () => { await loadDiscussion(); await onChanged(); }} />
        ))}
        {detail.comments.length === 0 ? <p>Nenhum comentário ainda.</p> : null}
      </div>
      <form className="community-discussion-form" onSubmit={submitComment}>
        <textarea value={commentBody} maxLength={1200} placeholder={replyTo ? "Responder comentário" : "Adicionar comentário técnico"} onChange={(event) => setCommentBody(event.target.value)} required />
        <div className="community-feed-actions">
          {replyTo ? <button type="button" className="secondary-button" onClick={() => setReplyTo(null)}>Cancelar resposta</button> : null}
          <button type="submit" className="primary-button"><Send size={15} />Comentar</button>
        </div>
      </form>
    </section>
  );
}

function CommentCard({ postId, comment, solved, onReply, onChanged }: { postId: number; comment: DiscussionComment; solved: boolean; onReply: (id: number) => void; onChanged: () => Promise<void> }) {
  const [editing, setEditing] = React.useState(false);
  const [body, setBody] = React.useState(comment.body);

  async function saveComment(event: React.FormEvent) {
    event.preventDefault();
    await socialApi.updateComment(comment.id, { body });
    setEditing(false);
    await onChanged();
  }

  return (
    <article className={`community-comment-card${solved ? " solved" : ""}`}>
      <header>
        <strong>{comment.author_display_name || "Maker"}</strong>
        {solved ? <span><CheckCircle2 size={14} />Solução</span> : null}
      </header>
      {editing ? (
        <form className="community-discussion-form" onSubmit={saveComment}>
          <textarea value={body} onChange={(event) => setBody(event.target.value)} required />
          <button type="submit" className="primary-button"><Pencil size={15} />Salvar</button>
        </form>
      ) : <p>{comment.deleted_at ? "Comentário removido" : comment.body}</p>}
      <div className="community-feed-actions">
        <button type="button" className="secondary-button" onClick={() => onReply(comment.id)}><Reply size={15} />Responder</button>
        <button type="button" className="secondary-button" onClick={() => setEditing((current) => !current)}><Pencil size={15} />Editar</button>
        <button type="button" className="secondary-button" onClick={async () => { await socialApi.markSolution(postId, comment.id); await onChanged(); }}><CheckCircle2 size={15} />Solução</button>
        <button type="button" className="secondary-button danger" onClick={async () => { await socialApi.deleteComment(comment.id); await onChanged(); }}><Trash2 size={15} />Remover</button>
      </div>
      {comment.replies.length ? <div className="community-reply-list">{comment.replies.map((reply) => <CommentCard key={reply.id} postId={postId} comment={reply} solved={false} onReply={onReply} onChanged={onChanged} />)}</div> : null}
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

function libraryVisibilityLabel(visibility: LibraryVisibility) {
  return {
    private: "Privado",
    friends: "Amigos",
    community: "Comunidade",
    public: "Público",
  }[visibility];
}

function licenseLabel(license: LibraryLicense) {
  return {
    "cc-by": "CC BY",
    "cc-by-sa": "CC BY-SA",
    cc0: "CC0",
    mit: "MIT",
    custom: "Licença personalizada",
    "all-rights-reserved": "Todos os direitos",
  }[license];
}

function uploadStatusLabel(status: string) {
  return {
    metadata_only: "Metadados",
    quarantined: "Quarentena",
    validated: "Validado",
    rejected: "Rejeitado",
  }[status] ?? status;
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

function communityEyebrow(community: Community) {
  if (community.status === "obsolete" || community.status === "merged") {
    return `${scopeLabel(community.scope)} / ${statusLabel(community.status)}`;
  }
  return "Comunidade técnica";
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

function brandInitials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "P";
}
