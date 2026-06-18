import React from "react";
import {
  Archive,
  CheckCircle2,
  ExternalLink,
  FileArchive,
  FilePlus2,
  FileText,
  HardDrive,
  Link2,
  RefreshCw,
  Search,
  ShieldCheck,
  Tags,
  Upload,
} from "lucide-react";
import { printProjectsApi } from "../services/printProjectsApi";
import type {
  PrintProjectContract,
  PrintProjectCommercialClass,
  PrintProjectDetail,
  PrintProjectFile,
  PrintProjectFileRole,
  PrintProjectStorageReport,
  PrintProjectSummary,
  PrintProjectVisibility,
} from "../types/printProjects";
import type { ScreenPropsFor } from "./ScreenProps";

type PrintProjectsScreenProps = ScreenPropsFor<"authUser" | "setError">;
type ProjectFilters = { file_kind: string; license: string; origin: "" | "hosted" | "external" };
type ProjectTab = "explore" | "mine";

const commercialLabels: Record<PrintProjectSummary["commercial_class"], string> = {
  free: "Gratuito",
  curated: "Curado",
  premium: "Premium",
  sponsored: "Patrocinado",
};

const publicationLabels: Record<PrintProjectSummary["publication_status"], string> = {
  draft: "Rascunho",
  in_review: "Em revisão",
  approved: "Aprovado",
  rejected: "Rejeitado",
  archived: "Arquivado",
};

const visibilityLabels: Record<PrintProjectVisibility, string> = {
  private: "Privado",
  unlisted: "Não listado",
  public: "Público",
};

const fileRoleLabels: Record<PrintProjectFile["file_role"], string> = {
  primary: "Principal",
  printable: "Imprimível",
  optional_part: "Peça opcional",
  documentation: "Documentação",
  preview: "Preview",
  external_reference: "Referência externa",
  artifact: "Artefato",
};

const sliceLabels: Record<PrintProjectFile["slice_status"], string> = {
  eligible: "Fatiável",
  blocked: "Bloqueado",
  external_no_local: "Sem arquivo local",
  pending: "Em validação",
  failure: "Falha no arquivo",
};

export function PrintProjectsScreen({ authUser, setError }: PrintProjectsScreenProps) {
  const [activeTab, setActiveTab] = React.useState<ProjectTab>("explore");
  const [query, setQuery] = React.useState("");
  const [filters, setFilters] = React.useState<ProjectFilters>({ file_kind: "", license: "", origin: "" });
  const [contract, setContract] = React.useState<PrintProjectContract | null>(null);
  const [projects, setProjects] = React.useState<PrintProjectSummary[]>([]);
  const [myProjects, setMyProjects] = React.useState<PrintProjectSummary[]>([]);
  const [storage, setStorage] = React.useState<PrintProjectStorageReport | null>(null);
  const [selectedProject, setSelectedProject] = React.useState<PrintProjectDetail | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [savingId, setSavingId] = React.useState<number | null>(null);

  async function loadExplore(nextQuery = query) {
    setBusy(true);
    try {
      const [contractPayload, projectsPayload] = await Promise.all([
        printProjectsApi.contract(),
        printProjectsApi.explore({ q: nextQuery.trim(), ...filters, limit: 24 }),
      ]);
      setContract(contractPayload);
      setProjects(projectsPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar projetos de impressão");
    } finally {
      setBusy(false);
    }
  }

  async function loadMine() {
    if (!authUser) return;
    setBusy(true);
    try {
      const [owned, storagePayload] = await Promise.all([printProjectsApi.myProjects(), printProjectsApi.storage()]);
      setMyProjects(owned);
      setStorage(storagePayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar meus projetos");
    } finally {
      setBusy(false);
    }
  }

  async function openProject(project: PrintProjectSummary) {
    setError(null);
    try {
      setSelectedProject(await printProjectsApi.detail(project.slug));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao abrir projeto");
    }
  }

  async function saveProject(projectId: number) {
    setSavingId(projectId);
    try {
      const detail = await printProjectsApi.saveReference(projectId);
      setSelectedProject(detail);
      await loadMine();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar projeto");
    } finally {
      setSavingId(null);
    }
  }

  async function afterProjectMutation(detail?: PrintProjectDetail) {
    if (detail) setSelectedProject(detail);
    await Promise.all([loadExplore(), loadMine()]);
  }

  React.useEffect(() => {
    void loadExplore("");
  }, [filters.file_kind, filters.license, filters.origin]);

  React.useEffect(() => {
    if (activeTab === "mine") void loadMine();
  }, [activeTab, authUser?.id]);

  return (
    <div className="print-projects-screen">
      <section className="print-projects-band">
        <div>
          <span className="eyebrow">Projetos de impressão</span>
          <h2>Biblioteca central de STL, 3MF, ZIP e referências externas</h2>
          <p>Organize projetos próprios, salve referências, valide arquivos e abra snapshots antes de fatiar ou enviar para impressora.</p>
        </div>
        <div className="print-projects-contract">
          <span>Raiz do domínio</span>
          <strong>{contract?.root_entity ?? "Projeto de impressão"}</strong>
          <small>{contract?.community_ownership_rule ?? "Comunidades compartilham projetos; não são donas."}</small>
        </div>
      </section>

      <section className="print-project-tabs" aria-label="Área de projetos">
        <button type="button" className={activeTab === "explore" ? "active" : ""} onClick={() => setActiveTab("explore")}>
          <Search size={16} />
          Explorar
        </button>
        <button type="button" className={activeTab === "mine" ? "active" : ""} onClick={() => setActiveTab("mine")} disabled={!authUser}>
          <FileArchive size={16} />
          Meus projetos
        </button>
      </section>

      {activeTab === "explore" ? (
        <>
          <section className="print-projects-toolbar" aria-label="Busca de projetos">
            <label>
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void loadExplore();
                }}
                placeholder="Buscar por nome, tag, licença, arquivo ou comunidade"
              />
            </label>
            <button type="button" className="secondary-button" onClick={() => void loadExplore()} disabled={busy}>
              <RefreshCw size={16} />
              {busy ? "Carregando" : "Atualizar"}
            </button>
            <select value={filters.file_kind} onChange={(event) => setFilters((current) => ({ ...current, file_kind: event.target.value }))} aria-label="Tipo de arquivo">
              <option value="">Todos os arquivos</option>
              <option value="stl">STL</option>
              <option value="3mf">3MF</option>
              <option value="zip">ZIP</option>
              <option value="link">Link externo</option>
            </select>
            <select value={filters.license} onChange={(event) => setFilters((current) => ({ ...current, license: event.target.value }))} aria-label="Licença">
              <option value="">Todas as licenças</option>
              <option value="cc-by">CC BY</option>
              <option value="cc-by-sa">CC BY-SA</option>
              <option value="cc0">CC0</option>
              <option value="mit">MIT</option>
            </select>
            <select value={filters.origin} onChange={(event) => setFilters((current) => ({ ...current, origin: event.target.value as ProjectFilters["origin"] }))} aria-label="Origem">
              <option value="">Todas as origens</option>
              <option value="hosted">Hospedado</option>
              <option value="external">Referência externa</option>
            </select>
          </section>
          <ProjectLayout
            title="Explorar"
            projects={projects}
            selectedProject={selectedProject}
            authUserPresent={!!authUser}
            savingId={savingId}
            onOpen={openProject}
            onSave={saveProject}
          />
        </>
      ) : (
        <section className="print-projects-layout mine-layout">
          <div className="print-projects-panel">
            <header>
              <h3>Meus projetos</h3>
              <button type="button" className="secondary-button" onClick={() => void loadMine()} disabled={busy || !authUser}>
                <RefreshCw size={16} />
                Atualizar
              </button>
            </header>
            <StoragePanel storage={storage} />
            <ProjectCreateForm disabled={!authUser || busy} onCreated={(detail) => void afterProjectMutation(detail)} setError={setError} />
            {myProjects.length === 0 ? (
              <div className="empty-state">
                <FilePlus2 size={22} />
                <strong>Nenhum projeto pessoal</strong>
                <p>Crie um projeto e adicione arquivos locais ou referências externas.</p>
              </div>
            ) : (
              <div className="print-project-grid">
                {myProjects.map((project) => (
                  <ProjectCard key={project.id} project={project} onOpen={openProject} />
                ))}
              </div>
            )}
          </div>
          <aside className="print-projects-panel print-projects-rules">
            {selectedProject ? (
              <>
                <ProjectDetail project={selectedProject} authUserPresent={!!authUser} saving={savingId === selectedProject.id} onSave={saveProject} />
                <ProjectPublicationForm project={selectedProject} setError={setError} onChanged={(detail) => void afterProjectMutation(detail)} />
                <ProjectFileActions project={selectedProject} setError={setError} onChanged={(detail) => void afterProjectMutation(detail)} />
              </>
            ) : (
              <ProjectRules contract={contract} />
            )}
          </aside>
        </section>
      )}
    </div>
  );
}

function ProjectLayout({
  title,
  projects,
  selectedProject,
  authUserPresent,
  savingId,
  onOpen,
  onSave,
}: {
  title: string;
  projects: PrintProjectSummary[];
  selectedProject: PrintProjectDetail | null;
  authUserPresent: boolean;
  savingId: number | null;
  onOpen: (project: PrintProjectSummary) => void;
  onSave: (projectId: number) => void;
}) {
  return (
    <section className="print-projects-layout">
      <div className="print-projects-panel">
        <header>
          <h3>{title}</h3>
          <span>{projects.length} projeto(s)</span>
        </header>
        {projects.length === 0 ? (
          <div className="empty-state">
            <FileArchive size={22} />
            <strong>Nenhum projeto público encontrado</strong>
            <p>Use filtros diferentes ou cadastre um projeto pessoal para publicar depois.</p>
          </div>
        ) : (
          <div className="print-project-grid">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} onOpen={onOpen} />
            ))}
          </div>
        )}
      </div>

      <aside className="print-projects-panel print-projects-rules">
        {selectedProject ? (
          <ProjectDetail project={selectedProject} authUserPresent={authUserPresent} saving={savingId === selectedProject.id} onSave={onSave} />
        ) : (
          <ProjectRules />
        )}
      </aside>
    </section>
  );
}

function ProjectCreateForm({ disabled, onCreated, setError }: { disabled: boolean; onCreated: (detail: PrintProjectDetail) => void; setError: (message: string | null) => void }) {
  const [title, setTitle] = React.useState("");
  const [visibility, setVisibility] = React.useState<PrintProjectVisibility>("private");
  const [license, setLicense] = React.useState("cc-by");
  const [tags, setTags] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  async function createProject(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const detail = await printProjectsApi.create({
        title,
        visibility,
        license,
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      });
      setTitle("");
      setTags("");
      onCreated(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar projeto");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="print-project-form" onSubmit={(event) => void createProject(event)}>
      <label>
        Nome do projeto
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Ex.: Suporte de mesa" required disabled={disabled || busy} />
      </label>
      <label>
        Visibilidade
        <select value={visibility} onChange={(event) => setVisibility(event.target.value as PrintProjectVisibility)} disabled={disabled || busy}>
          <option value="private">Privado</option>
          <option value="unlisted">Não listado</option>
          <option value="public">Público</option>
        </select>
      </label>
      <label>
        Licença
        <input value={license} onChange={(event) => setLicense(event.target.value)} disabled={disabled || busy} />
      </label>
      <label>
        Tags
        <input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="mesa, pla, suporte" disabled={disabled || busy} />
      </label>
      <button type="submit" className="primary-button" disabled={disabled || busy || !title.trim()}>
        <FilePlus2 size={16} />
        Criar projeto
      </button>
    </form>
  );
}

function ProjectFileActions({ project, setError, onChanged }: { project: PrintProjectDetail; setError: (message: string | null) => void; onChanged: (detail: PrintProjectDetail) => void }) {
  const [fileRole, setFileRole] = React.useState<PrintProjectFileRole>("primary");
  const [externalUrl, setExternalUrl] = React.useState("");
  const [externalLabel, setExternalLabel] = React.useState("Referência externa");
  const [busy, setBusy] = React.useState(false);

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      onChanged(await printProjectsApi.uploadFile(project.id, file, fileRole));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar arquivo");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function addLink(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const detail = await printProjectsApi.addExternalLink(project.id, { url: externalUrl, label: externalLabel });
      setExternalUrl("");
      onChanged(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao adicionar link");
    } finally {
      setBusy(false);
    }
  }

  async function archiveProject() {
    setBusy(true);
    try {
      await printProjectsApi.archive(project.id);
      onChanged({ ...project, lifecycle_status: "archived" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao arquivar projeto");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="print-project-detail-section">
      <h4>Gerenciar</h4>
      <div className="print-project-upload-row">
        <select value={fileRole} onChange={(event) => setFileRole(event.target.value as PrintProjectFileRole)} disabled={busy}>
          <option value="primary">Principal</option>
          <option value="printable">Imprimível</option>
          <option value="optional_part">Peça opcional</option>
          <option value="documentation">Documentação</option>
          <option value="preview">Preview</option>
        </select>
        <label className="secondary-button file-button">
          <Upload size={16} />
          Enviar arquivo
          <input type="file" accept=".stl,.3mf,.zip" onChange={(event) => void upload(event)} disabled={busy} />
        </label>
      </div>
      <form className="print-project-link-form" onSubmit={(event) => void addLink(event)}>
        <input value={externalUrl} onChange={(event) => setExternalUrl(event.target.value)} placeholder="https://..." disabled={busy} />
        <input value={externalLabel} onChange={(event) => setExternalLabel(event.target.value)} disabled={busy} />
        <button type="submit" className="secondary-button" disabled={busy || !externalUrl.trim()}>
          <Link2 size={16} />
          Adicionar link
        </button>
      </form>
      <button type="button" className="secondary-button danger-soft" onClick={() => void archiveProject()} disabled={busy}>
        <Archive size={16} />
        Arquivar projeto
      </button>
    </section>
  );
}

function ProjectPublicationForm({ project, setError, onChanged }: { project: PrintProjectDetail; setError: (message: string | null) => void; onChanged: (detail: PrintProjectDetail) => void }) {
  const [visibility, setVisibility] = React.useState<PrintProjectVisibility>(project.visibility);
  const [commercialClass, setCommercialClass] = React.useState<PrintProjectCommercialClass>(project.commercial_class);
  const [price, setPrice] = React.useState(project.price_cents ? String(Math.round(project.price_cents / 100)) : "");
  const [terms, setTerms] = React.useState(project.commercial_terms);
  const [disclosure, setDisclosure] = React.useState(project.promotion_disclosure);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    setVisibility(project.visibility);
    setCommercialClass(project.commercial_class);
    setPrice(project.price_cents ? String(Math.round(project.price_cents / 100)) : "");
    setTerms(project.commercial_terms);
    setDisclosure(project.promotion_disclosure);
  }, [project.id, project.visibility, project.commercial_class, project.price_cents, project.commercial_terms, project.promotion_disclosure]);

  async function submitPublication(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const price_cents = commercialClass === "premium" ? Math.max(0, Number(price || 0) * 100) : 0;
      onChanged(
        await printProjectsApi.updatePublication(project.id, {
          visibility,
          commercial_class: commercialClass,
          price_cents,
          currency: "BRL",
          commercial_terms: terms,
          promotion_disclosure: disclosure,
          submit_for_review: true,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar publicação");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="print-project-detail-section print-project-publication-form" onSubmit={(event) => void submitPublication(event)}>
      <h4>Publicação e vitrine</h4>
      <div className="print-project-publication-grid">
        <label>
          Visibilidade
          <select value={visibility} onChange={(event) => setVisibility(event.target.value as PrintProjectVisibility)} disabled={busy}>
            <option value="private">Privado</option>
            <option value="unlisted">Não listado</option>
            <option value="public">Público</option>
          </select>
        </label>
        <label>
          Classificação
          <select value={commercialClass} onChange={(event) => setCommercialClass(event.target.value as PrintProjectCommercialClass)} disabled={busy}>
            <option value="free">Gratuito</option>
            <option value="curated">Curado</option>
            <option value="premium">Premium</option>
            <option value="sponsored">Patrocinado</option>
          </select>
        </label>
        <label>
          Preço preparado
          <input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="numeric" disabled={busy || commercialClass !== "premium"} />
        </label>
      </div>
      <label>
        Condição comercial
        <input value={terms} onChange={(event) => setTerms(event.target.value)} placeholder="Pagamento real ainda não está ativo" disabled={busy} />
      </label>
      <label>
        Transparência
        <input value={disclosure} onChange={(event) => setDisclosure(event.target.value)} placeholder="Obrigatória para patrocinado" disabled={busy} />
      </label>
      <div className="print-project-badges">
        <span>{publicationLabels[project.publication_status]}</span>
        <span>{commercialLabels[project.commercial_class]}</span>
        {project.publication_reviews[0] ? <span>Última revisão: {project.publication_reviews[0].status}</span> : null}
      </div>
      <button type="submit" className="primary-button" disabled={busy}>
        <ShieldCheck size={16} />
        Atualizar publicação
      </button>
    </form>
  );
}

function StoragePanel({ storage }: { storage: PrintProjectStorageReport | null }) {
  const usedPercent = storage ? Math.min(100, Math.round((storage.used_bytes / Math.max(storage.quota_bytes, 1)) * 100)) : 0;
  return (
    <div className="print-project-storage">
      <HardDrive size={18} />
      <div>
        <strong>Armazenamento pessoal</strong>
        <span>{storage ? `${formatBytes(storage.used_bytes)} usados de ${formatBytes(storage.quota_bytes)} · ${storage.file_count} arquivo(s)` : "Entre para ver cota e uso."}</span>
        <div className="storage-meter" aria-label="Uso de armazenamento">
          <span style={{ width: `${usedPercent}%` }} />
        </div>
      </div>
    </div>
  );
}

function ProjectCard({ project, onOpen }: { project: PrintProjectSummary; onOpen: (project: PrintProjectSummary) => void }) {
  return (
    <article className="print-project-card">
      <header>
        <div>
          <strong>{project.title}</strong>
          <span>{project.license || "Licença não informada"}</span>
        </div>
        {project.external_reference_only ? <ExternalLink size={18} /> : <FileArchive size={18} />}
      </header>
      <p>{project.description || "Sem descrição."}</p>
      <div className="print-project-badges">
        <span>{visibilityLabels[project.visibility]}</span>
        <span>{commercialLabels[project.commercial_class]}</span>
        <span>{publicationLabels[project.publication_status]}</span>
        {project.commercial_class === "sponsored" ? <span>Promoção identificada</span> : null}
        {project.commercial_class === "premium" ? <span>Pagamento não ativo</span> : null}
        <span>{project.can_slice ? "Fatiável" : "Não fatiável"}</span>
      </div>
      <dl>
        <div>
          <dt>Arquivos</dt>
          <dd>{project.file_count}</dd>
        </div>
        <div>
          <dt>Comunidades</dt>
          <dd>{project.community_shares.length}</dd>
        </div>
      </dl>
      <button type="button" className="secondary-button" onClick={() => void onOpen(project)}>
        Abrir projeto
      </button>
    </article>
  );
}

function ProjectDetail({ project, authUserPresent, saving, onSave }: { project: PrintProjectDetail; authUserPresent: boolean; saving: boolean; onSave: (projectId: number) => void }) {
  return (
    <>
      <header>
        <h3>{project.title}</h3>
        {project.external_reference_only ? <ExternalLink size={18} /> : <FileArchive size={18} />}
      </header>
      <p>{project.description || "Sem descrição."}</p>
      <div className="print-project-badges">
        <span>{visibilityLabels[project.visibility]}</span>
        <span>{commercialLabels[project.commercial_class]}</span>
        <span>{publicationLabels[project.publication_status]}</span>
        {project.price_cents > 0 ? <span>{formatMoney(project.price_cents, project.currency)}</span> : null}
        <span>{project.immutable_snapshot_ready ? "Snapshot pronto" : "Snapshot pendente"}</span>
      </div>
      {project.promotion_disclosure ? <p className="muted">{project.promotion_disclosure}</p> : null}
      {project.commercial_terms ? <p className="muted">{project.commercial_terms}</p> : null}
      <section className="print-project-detail-section">
        <h4>Arquivos</h4>
        {project.files.map((file) => <ProjectFileRow key={file.id} file={file} />)}
        {project.files.length === 0 ? <span className="muted">Nenhum arquivo declarado.</span> : null}
      </section>
      <section className="print-project-detail-section">
        <h4>Comunidades</h4>
        {project.community_shares.length ? <div className="print-project-tags">{project.community_shares.map((community) => <span key={community}>{community}</span>)}</div> : <span className="muted">Ainda não compartilhado.</span>}
      </section>
      <section className="print-project-detail-section">
        <h4>Versões</h4>
        {project.versions.map((version) => (
          <div className="print-project-version" key={version.id}>
            <strong>{version.version_label}</strong>
            <span>{version.changelog || "Snapshot imutável do projeto."}</span>
          </div>
        ))}
      </section>
      <button type="button" className="primary-button" disabled={!authUserPresent || saving || project.saved_by_viewer} onClick={() => onSave(project.id)}>
        {project.saved_by_viewer ? <CheckCircle2 size={16} /> : null}
        {project.saved_by_viewer ? "Salvo" : saving ? "Salvando" : "Salvar nos meus projetos"}
      </button>
    </>
  );
}

function ProjectFileRow({ file }: { file: PrintProjectFile }) {
  return (
    <div className="print-project-file-row">
      <div>
        <strong>{file.file_name}</strong>
        <span>
          {file.file_kind.toUpperCase()} · {fileRoleLabels[file.file_role]}
          {file.rejection_reason ? ` · ${file.rejection_reason}` : ""}
        </span>
      </div>
      <span>{sliceLabels[file.slice_status]}</span>
    </div>
  );
}

function ProjectRules({ contract }: { contract?: PrintProjectContract | null }) {
  return (
    <>
      <h3>Contrato operacional</h3>
      <Rule icon={ShieldCheck} label="Snapshot" text="Fatiamento, G-code e histórico exigem versão imutável." />
      <Rule icon={Link2} label="Links externos" text={contract?.external_link_rule ?? "Referência sem arquivo validado não pode ser fatiada ou enviada."} />
      <Rule icon={Tags} label="Dimensões separadas" text="Visibilidade, publicação, venda e comunidade não se misturam." />
      <Rule icon={FileText} label="Privacidade pública" text={contract?.public_privacy_rule ?? "Histórico público usa dados sanitizados."} />
    </>
  );
}

function Rule({ icon: Icon, label, text }: { icon: React.ComponentType<{ size?: number }>; label: string; text: string }) {
  return (
    <div className="print-project-rule">
      <Icon size={18} />
      <div>
        <strong>{label}</strong>
        <span>{text}</span>
      </div>
    </div>
  );
}

function formatBytes(value: number): string {
  if (value >= 1024 * 1024 * 1024) return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  if (value >= 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${value} B`;
}

function formatMoney(value: number, currency: string): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: currency || "BRL" }).format(value / 100);
}
