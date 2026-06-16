import React from "react";
import { Archive, ArrowLeft, Box, CheckCircle2, ChevronLeft, ChevronRight, ExternalLink, FileText, Filter, FolderOpen, Lock, MessageSquare, Pencil, Pin, Printer, Reply, Send, SlidersHorizontal, ThumbsUp, Trash2, UserRound, Users, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { Community, CommunityDetail, CommunityFeedItem, CommunityFeedSummary, DiscussionComment, DiscussionDetail, FeedContentType, FeedOrder } from "../types";

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
  const [selectedPostId, setSelectedPostId] = React.useState<number | null>(null);
  const [newPost, setNewPost] = React.useState({ content_type: "question" as FeedContentType, title: "", body: "", component: "", material: "", firmware_family: "", problem_tag: "" });
  const [posting, setPosting] = React.useState(false);
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

      <form className="community-discussion-form" onSubmit={submitPost}>
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
      </form>

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
