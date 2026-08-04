import React from "react";
import {
  ArrowLeft,
  Archive,
  Camera,
  CheckCircle2,
  ExternalLink,
  FileArchive,
  FilePlus2,
  HardDrive,
  Link2,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  Send,
  ShieldCheck,
  Upload,
} from "lucide-react";
import { GcodePrintViewer } from "../components/monitoring/GcodePrintViewer";
import { printProjectsApi } from "../services/printProjectsApi";
import { printerApi } from "../services/printerApi";
import { materialsApi } from "../services/materialsApi";
import {
  slicingApi,
  type PrintDelivery,
  type PrintJobFeedback,
  type PrintJobHistory,
  type MeshPhysicalValidation,
  type PrintPreflight,
  type SlicingEngineInfo,
  type SlicingJob,
  type SlicingProfileBundle,
} from "../services/slicingApi";
import type { PrinterRecord } from "../types/printers";
import type { MaterialSpool } from "../types";
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
import { ProjectAssetsEditor, ProjectAssetsSummary } from "./projects/ProjectAssetsPanel";
import { SlicingProfilesPanel } from "./projects/SlicingProfilesPanel";

const PhotoCapturePanel = React.lazy(async () => {
  const module = await import("./projects/PhotoCapturePanel");
  return { default: module.PhotoCapturePanel };
});

type PrintProjectsScreenProps = ScreenPropsFor<"authUser" | "setError">;
type ProjectFilters = { file_kind: string; license: string; origin: "" | "hosted" | "external" };
type ProjectTab = "explore" | "mine";
type ProjectView = "list" | "create" | "detail";
type ProjectDetailTab = "overview" | "files" | "capture" | "slicing" | "publication";

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
  const [view, setView] = React.useState<ProjectView>("list");
  const [detailTab, setDetailTab] = React.useState<ProjectDetailTab>("overview");
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
      setDetailTab("overview");
      setView("detail");
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
    if (detail) {
      setSelectedProject(detail);
      setDetailTab("overview");
      setView("detail");
    }
    await Promise.all([loadExplore(), loadMine()]);
  }

  async function refreshApprovedModel() {
    if (!selectedProject) return;
    setSelectedProject(await printProjectsApi.detail(selectedProject.slug));
  }

  React.useEffect(() => {
    void loadExplore("");
  }, [filters.file_kind, filters.license, filters.origin]);

  React.useEffect(() => {
    if (activeTab === "mine") void loadMine();
  }, [activeTab, authUser?.id]);

  function changeArea(tab: ProjectTab) {
    setActiveTab(tab);
    setSelectedProject(null);
    setView("list");
  }

  const ownsSelectedProject = !!selectedProject
    && myProjects.some((project) => project.id === selectedProject.id)
    && !selectedProject.saved_by_viewer;

  if (view === "create") {
    return (
      <div className="print-projects-screen">
        <ProjectPageHeader
          eyebrow="Meus projetos"
          title="Criar projeto"
          description="Comece com um nome. Depois você poderá enviar arquivos ou fotografar um objeto real."
          onBack={() => setView("list")}
        />
        <section className="print-projects-panel print-project-create-page">
          <div className="print-project-create-intro">
            <FilePlus2 size={28} aria-hidden="true" />
            <div>
              <h3>Informações básicas</h3>
              <p>Seu projeto começa privado. Você decide se quer publicar somente quando ele estiver pronto.</p>
            </div>
          </div>
          <ProjectCreateForm disabled={!authUser || busy} onCreated={(detail) => void afterProjectMutation(detail)} setError={setError} />
        </section>
      </div>
    );
  }

  if (view === "detail" && selectedProject) {
    return (
      <div className="print-projects-screen">
        <ProjectPageHeader
          eyebrow={activeTab === "mine" ? "Meus projetos" : "Explorar"}
          title={selectedProject.title}
          description={selectedProject.description || "Organize os arquivos e escolha o próximo passo deste projeto."}
          onBack={() => {
            setSelectedProject(null);
            setView("list");
          }}
        />
        <nav className="print-project-detail-tabs" aria-label="Seções do projeto">
          <DetailTabButton active={detailTab === "overview"} onClick={() => setDetailTab("overview")}>Visão geral</DetailTabButton>
          {ownsSelectedProject ? <DetailTabButton active={detailTab === "files"} onClick={() => setDetailTab("files")}>Arquivos</DetailTabButton> : null}
          {ownsSelectedProject ? <DetailTabButton active={detailTab === "capture"} onClick={() => setDetailTab("capture")}><Camera size={16} /> Digitalizar objeto</DetailTabButton> : null}
          {ownsSelectedProject ? <DetailTabButton active={detailTab === "slicing"} onClick={() => setDetailTab("slicing")}>Fatiar e imprimir</DetailTabButton> : null}
          {ownsSelectedProject ? <DetailTabButton active={detailTab === "publication"} onClick={() => setDetailTab("publication")}>Publicação</DetailTabButton> : null}
        </nav>
        <section className="print-projects-panel print-project-detail-page">
          {detailTab === "overview" ? <ProjectDetail project={selectedProject} authUserPresent={!!authUser} saving={savingId === selectedProject.id} onSave={saveProject} setError={setError} /> : null}
          {detailTab === "files" && ownsSelectedProject ? <ProjectFileActions project={selectedProject} setError={setError} onChanged={(detail) => void afterProjectMutation(detail)} /> : null}
          {detailTab === "capture" && ownsSelectedProject ? <React.Suspense fallback={<div className="empty-state"><Camera size={22} /><strong>Preparando a digitalização...</strong></div>}><PhotoCapturePanel projectId={selectedProject.id} setError={setError} onModelApproved={refreshApprovedModel} /></React.Suspense> : null}
          {detailTab === "slicing" && ownsSelectedProject ? <ProjectSlicingPanel project={selectedProject} setError={setError} /> : null}
          {detailTab === "publication" && ownsSelectedProject ? <ProjectPublicationForm project={selectedProject} setError={setError} onChanged={(detail) => void afterProjectMutation(detail)} /> : null}
        </section>
      </div>
    );
  }

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
        <button type="button" className={activeTab === "explore" ? "active" : ""} onClick={() => changeArea("explore")}>
          <Search size={16} />
          Explorar
        </button>
        <button type="button" className={activeTab === "mine" ? "active" : ""} onClick={() => changeArea("mine")} disabled={!authUser}>
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
            onOpen={openProject}
          />
        </>
      ) : (
        <section className="print-projects-panel">
            <header>
              <div><h3>Meus projetos</h3><span className="muted">{myProjects.length} projeto(s)</span></div>
              <div className="print-project-list-actions">
                <button type="button" className="secondary-button" onClick={() => void loadMine()} disabled={busy || !authUser}><RefreshCw size={16} />Atualizar</button>
                <button type="button" className="primary-button" onClick={() => setView("create")} disabled={!authUser}><FilePlus2 size={16} />Novo projeto</button>
              </div>
            </header>
            <StoragePanel storage={storage} />
            <SlicingProfilesPanel setError={setError} />
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
        </section>
      )}
    </div>
  );
}

function ProjectLayout({
  title,
  projects,
  onOpen,
}: {
  title: string;
  projects: PrintProjectSummary[];
  onOpen: (project: PrintProjectSummary) => void;
}) {
  return (
    <section className="print-projects-panel">
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
    </section>
  );
}

function ProjectPageHeader({ eyebrow, title, description, onBack }: { eyebrow: string; title: string; description: string; onBack: () => void }) {
  return (
    <section className="print-project-page-header">
      <button type="button" className="secondary-button" onClick={onBack}><ArrowLeft size={17} />Voltar para projetos</button>
      <div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>
    </section>
  );
}

function DetailTabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" className={active ? "active" : ""} aria-current={active ? "page" : undefined} onClick={onClick}>{children}</button>;
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

function ProjectSlicingPanel({ project, setError }: { project: PrintProjectDetail; setError: (message: string | null) => void }) {
  const slicableFiles = project.files.filter((file) => file.can_slice && file.file_role !== "external_reference");
  const fileSignature = project.files.map((file) => `${file.id}:${file.can_slice}:${file.file_role}`).join("|");
  const [selectedFileIds, setSelectedFileIds] = React.useState<number[]>(slicableFiles.map((file) => file.id));
  const [fileQuantities, setFileQuantities] = React.useState<Record<number, number>>(
    Object.fromEntries(slicableFiles.map((file) => [file.id, 1])),
  );
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [spools, setSpools] = React.useState<MaterialSpool[]>([]);
  const [spoolId, setSpoolId] = React.useState("");
  const [printerId, setPrinterId] = React.useState("");
  const [engineInfo, setEngineInfo] = React.useState<SlicingEngineInfo | null>(null);
  const [profileBundles, setProfileBundles] = React.useState<SlicingProfileBundle[]>([]);
  const [profileRevisionId, setProfileRevisionId] = React.useState("");
  const [quality, setQuality] = React.useState("0.20 qualidade");
  const [profile, setProfile] = React.useState("");
  const [jobs, setJobs] = React.useState<SlicingJob[]>([]);
  const [preflights, setPreflights] = React.useState<PrintPreflight[]>([]);
  const [deliveries, setDeliveries] = React.useState<PrintDelivery[]>([]);
  const [history, setHistory] = React.useState<PrintJobHistory[]>([]);
  const [confirmationByPreflight, setConfirmationByPreflight] = React.useState<Record<number, string>>({});
  const [feedbackDrafts, setFeedbackDrafts] = React.useState<Record<number, { outcome: PrintJobFeedback["outcome"]; visibility: PrintJobFeedback["visibility"]; note: string; photo_url: string }>>({});
  const [measurementDrafts, setMeasurementDrafts] = React.useState<Record<number, { outcome: MeshPhysicalValidation["outcome"]; instrument: string; x: string; y: string; z: string; note: string }>>({});
  const [busy, setBusy] = React.useState(false);
  const [preflightMessage, setPreflightMessage] = React.useState("");
  const [previewJobId, setPreviewJobId] = React.useState<number | null>(null);
  const [previewText, setPreviewText] = React.useState("");

  React.useEffect(() => {
    setSelectedFileIds(slicableFiles.map((file) => file.id));
    setFileQuantities(Object.fromEntries(slicableFiles.map((file) => [file.id, 1])));
    setPreflightMessage("");
  }, [project.id, fileSignature]);

  React.useEffect(() => {
    void loadSlicingContext();
  }, [project.id]);

  async function loadSlicingContext() {
    try {
      const [printerResponse, spoolRows, projectJobs, engine, profileRows, preflightRows, deliveryRows, historyRows] = await Promise.all([
        printerApi.list(),
        materialsApi.spools(),
        slicingApi.projectJobs(project.id),
        slicingApi.engine(),
        slicingApi.profileBundles(),
        slicingApi.preflights(),
        slicingApi.deliveries(),
        slicingApi.history(),
      ]);
      if (!printerResponse.ok) {
        throw new Error("Falha ao carregar impressoras");
      }
      const printerPayload = (await printerResponse.json()) as { printers?: PrinterRecord[] } | PrinterRecord[];
      const printerRecords = Array.isArray(printerPayload) ? printerPayload : printerPayload.printers ?? [];
      const activePrinters = printerRecords.filter((printer) => printer.is_active);
      const jobIds = new Set(projectJobs.map((job) => job.id));
      setPrinters(activePrinters);
      setSpools(spoolRows);
      setSpoolId((current) => current || String(spoolRows[0]?.id ?? ""));
      setPrinterId((current) => current || String(activePrinters[0]?.id ?? ""));
      setJobs(projectJobs);
      setEngineInfo(engine);
      setProfileBundles(profileRows);
      setProfileRevisionId((current) => current || String(profileRows[0]?.current_revision_id ?? ""));
      setPreflights(preflightRows.filter((item) => jobIds.has(item.slicing_job_id)));
      setDeliveries(deliveryRows.filter((item) => jobIds.has(item.slicing_job_id)));
      setHistory(historyRows.filter((item) => item.slicing_job_id !== null && jobIds.has(item.slicing_job_id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar contexto de fatiamento");
    }
  }

  function toggleFile(fileId: number) {
    setSelectedFileIds((current) => (current.includes(fileId) ? current.filter((id) => id !== fileId) : [...current, fileId]));
  }

  async function createJob(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const job = await slicingApi.createProjectJob(project.id, {
        project_id: project.id,
        selected_file_ids: selectedFileIds,
        file_quantities: Object.fromEntries(selectedFileIds.map((fileId) => [fileId, fileQuantities[fileId] ?? 1])),
        printer_id: Number(printerId),
        spool_id: spoolId ? Number(spoolId) : null,
        material_profile_id: spools.find((item) => item.id === Number(spoolId))?.material_profile_id ?? null,
        slicing_profile_revision_id: profileRevisionId ? Number(profileRevisionId) : null,
        engine: "orcaslicer",
        model_dimensions: {},
        quality_reference: quality,
        profile_reference: profile || null,
      });
      setJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
      await loadSlicingContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar job de fatiamento");
    } finally {
      setBusy(false);
    }
  }

  async function openPreview(jobId: number) {
    setBusy(true);
    try {
      setPreviewText(await slicingApi.gcodeText(jobId));
      setPreviewJobId(jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar a prévia do G-code");
    } finally {
      setBusy(false);
    }
  }

  async function approvePreview(jobId: number) {
    setBusy(true);
    try {
      const job = await slicingApi.approvePreview(jobId);
      setJobs((current) => current.map((item) => (item.id === job.id ? job : item)));
      setPreflightMessage("Prévia aprovada. Agora faça a verificação de segurança.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao aprovar a prévia");
    } finally {
      setBusy(false);
    }
  }

  async function reprintJob(jobId: number) {
    setBusy(true);
    try {
      const job = await slicingApi.reprintJob(jobId);
      setJobs((current) => [job, ...current]);
      setPreflightMessage("Cópia reproduzível criada. Execute o fatiamento e revise a nova prévia.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao preparar a reimpressão");
    } finally {
      setBusy(false);
    }
  }

  async function runJob(jobId: number) {
    setBusy(true);
    try {
      const job = await slicingApi.runJob(jobId);
      setJobs((current) => current.map((item) => (item.id === job.id ? job : item)));
      await loadSlicingContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao executar fatiamento");
    } finally {
      setBusy(false);
    }
  }

  async function createPreflight(jobId: number) {
    setBusy(true);
    try {
      const preflight = await slicingApi.createPreflight(jobId);
      setPreflightMessage(preflight.status === "approved" ? "Verificação concluída. Você pode enviar." : "Verificação iniciada. Atualize quando a impressora responder.");
      setPreflights((current) => [preflight, ...current.filter((item) => item.id !== preflight.id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar preflight");
    } finally {
      setBusy(false);
    }
  }

  async function refreshPreflight(preflightId: number) {
    setBusy(true);
    try {
      const preflight = await slicingApi.refreshPreflight(preflightId);
      setPreflights((current) => current.map((item) => (item.id === preflight.id ? preflight : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar preflight");
    } finally {
      setBusy(false);
    }
  }

  async function createDelivery(preflight: PrintPreflight, mode: PrintDelivery["mode"]) {
    setBusy(true);
    try {
      const delivery = await slicingApi.createDelivery({
        preflight_id: preflight.id,
        mode,
        confirmation_phrase: mode === "save_and_print" ? confirmationByPreflight[preflight.id] ?? "" : "",
      });
      setDeliveries((current) => [delivery, ...current.filter((item) => item.id !== delivery.id)]);
      await loadSlicingContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar G-code");
    } finally {
      setBusy(false);
    }
  }

  async function rollbackDelivery(deliveryId: number) {
    setBusy(true);
    try {
      const delivery = await slicingApi.rollbackDelivery(deliveryId);
      setDeliveries((current) => current.map((item) => (item.id === delivery.id ? delivery : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover arquivo salvo");
    } finally {
      setBusy(false);
    }
  }

  async function recordHistory(historyId: number, status: PrintJobHistory["status"]) {
    setBusy(true);
    try {
      const updated = await slicingApi.recordHistoryEvent(historyId, { status, result: { status } });
      setHistory((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar histórico");
    } finally {
      setBusy(false);
    }
  }

  async function addFeedback(historyId: number) {
    const draft = feedbackDrafts[historyId] ?? { outcome: "worked", visibility: "private", note: "", photo_url: "" };
    setBusy(true);
    try {
      const updated = await slicingApi.addHistoryFeedback(historyId, {
        outcome: draft.outcome,
        visibility: draft.visibility,
        note: draft.note,
        photo_url: draft.photo_url || null,
      });
      setHistory((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setFeedbackDrafts((current) => ({ ...current, [historyId]: { outcome: "worked", visibility: "private", note: "", photo_url: "" } }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao registrar feedback");
    } finally {
      setBusy(false);
    }
  }

  async function addPhysicalValidation(historyId: number) {
    const draft = measurementDrafts[historyId] ?? { outcome: "passed", instrument: "Paquímetro", x: "", y: "", z: "", note: "" };
    setBusy(true);
    try {
      const validation = await slicingApi.createMeshPhysicalValidation(historyId, {
        outcome: draft.outcome,
        instrument_label: draft.instrument,
        ...(draft.x ? { measured_x_mm: Number(draft.x) } : {}),
        ...(draft.y ? { measured_y_mm: Number(draft.y) } : {}),
        ...(draft.z ? { measured_z_mm: Number(draft.z) } : {}),
        note: draft.note,
      });
      setHistory((current) => current.map((item) => item.id === historyId ? { ...item, mesh_physical_validation: validation } : item));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível registrar as medidas.");
    } finally {
      setBusy(false);
    }
  }

  const engineBlocked = engineInfo?.status === "blocked";

  return (
    <form id="project-slicing" className="print-project-detail-section print-project-slicing-form" onSubmit={(event) => void createJob(event)}>
      <h4>Fatiamento</h4>
      {engineBlocked ? (
        <div className="print-project-slicing-warning">
          Engine indisponível. Configure a engine em Administração antes de executar fatiamento.
        </div>
      ) : null}
      <ol className="print-project-journey-steps" aria-label="Etapas para imprimir">
        <li className={selectedFileIds.length ? "done" : "current"}>Escolha as peças</li>
        <li>Prepare o arquivo</li>
        <li>Revise a prévia</li>
        <li>Faça a verificação</li>
        <li>Envie e acompanhe</li>
      </ol>
      {slicableFiles.length ? (
        <div className="print-project-slice-files">
          {project.files.map((file) => (
            <label key={file.id} className={!file.can_slice || file.file_role === "external_reference" ? "disabled" : ""}>
              <input
                type="checkbox"
                checked={selectedFileIds.includes(file.id)}
                onChange={() => toggleFile(file.id)}
                disabled={!file.can_slice || file.file_role === "external_reference" || busy}
              />
              <span>{file.file_name}</span>
              <small>{sliceLabels[file.slice_status]}</small>
              {selectedFileIds.includes(file.id) ? (
                <span className="print-project-quantity">
                  Quantidade
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={fileQuantities[file.id] ?? 1}
                    onChange={(event) => setFileQuantities((current) => ({
                      ...current,
                      [file.id]: Math.max(1, Math.min(100, Number(event.target.value) || 1)),
                    }))}
                    onClick={(event) => event.stopPropagation()}
                    disabled={busy}
                    aria-label={`Quantidade de ${file.file_name}`}
                  />
                </span>
              ) : null}
            </label>
          ))}
        </div>
      ) : (
        <span className="muted">Adicione um arquivo local validado para fatiar.</span>
      )}
      <div className="print-project-slicing-grid">
        <label>
          Impressora
          <select value={printerId} onChange={(event) => setPrinterId(event.target.value)} disabled={busy || printers.length === 0}>
            <option value="">Selecione</option>
            {printers.map((printer) => (
              <option key={printer.id} value={printer.id}>{printer.name}</option>
            ))}
          </select>
        </label>
        <label>
          Qualidade
          <input value={quality} onChange={(event) => setQuality(event.target.value)} disabled={busy} />
        </label>
        <label>
          Material carregado
          <select value={spoolId} onChange={(event) => setSpoolId(event.target.value)} disabled={busy}>
            <option value="">Confirmar manualmente depois</option>
            {spools.map((spool) => (
              <option key={spool.id} value={spool.id}>
                {spool.name} · {spool.material_type}{spool.remaining_weight_g != null ? ` · ${Math.round(spool.remaining_weight_g)} g` : ""}
              </option>
            ))}
          </select>
        </label>
        <label>
          Perfil reproduzível
          <select value={profileRevisionId} onChange={(event) => setProfileRevisionId(event.target.value)} disabled={busy}>
            <option value="">Sem perfil executável</option>
            {profileBundles.map((bundle) => (
              <option key={bundle.id} value={bundle.current_revision_id ?? ""}>{bundle.title} · v{bundle.revisions[0]?.revision_number ?? 1}</option>
            ))}
          </select>
        </label>
        <label>
          Referência livre
          <input value={profile} onChange={(event) => setProfile(event.target.value)} placeholder="Opcional" disabled={busy} />
        </label>
      </div>
      <button type="submit" className="primary-button" disabled={busy || engineBlocked || !printerId || selectedFileIds.length === 0}>
        <FileArchive size={16} />
        Preparar para imprimir
      </button>
      {preflightMessage ? <span className="muted">{preflightMessage}</span> : null}
      {jobs.length ? (
        <div className="print-project-job-list">
          {jobs.map((job) => {
            const latestPreflight = preflights.find((item) => item.slicing_job_id === job.id) ?? null;
            const latestDelivery = deliveries.find((item) => item.slicing_job_id === job.id) ?? null;
            const expectedConfirmation = latestPreflight ? `IMPRIMIR ${latestPreflight.printer_id}-${latestPreflight.id}` : "";
            return (
              <div className="print-project-job-row" key={job.id}>
                <div>
                  <strong>Preparo #{job.id}</strong>
                  <span>{slicingJobStatus(job.status)} · versão preservada {job.print_project_version_id ?? "-"}</span>
                  <small>{job.selected_project_files?.map((file) => `${file.file_name} × ${file.quantity ?? 1}`).join(" · ")}</small>
                  {job.reprint_of_job_id ? <small>Reimpressão fiel do preparo #{job.reprint_of_job_id}</small> : null}
                  {job.slicing_profile_revision_id ? <small>Perfil reproduzível fixado · {job.slicing_profile_sha256?.slice(0, 12)}</small> : null}
                  {job.error_message ? <small>{job.error_message}</small> : null}
                  {latestPreflight ? <small>Verificação {preflightStatus(latestPreflight.status)}</small> : null}
                  {latestDelivery ? <small>{deliveryModeLabel(latestDelivery.mode)} · {deliveryStatus(latestDelivery.status)} · {latestDelivery.remote_filename}</small> : null}
                </div>
                <div className="print-project-job-actions">
                  {job.status === "planned" || job.status === "failed" ? (
                    <button type="button" className="secondary-button" onClick={() => void runJob(job.id)} disabled={busy || engineBlocked}>
                      <Play size={15} />
                      Executar
                    </button>
                  ) : null}
                  {job.status === "completed" ? (
                    <button type="button" className="secondary-button" onClick={() => void openPreview(job.id)} disabled={busy}>
                      <Search size={15} />
                      Ver prévia
                    </button>
                  ) : null}
                  {job.status === "completed" && previewJobId === job.id && !job.gcode_approved_at ? (
                    <button type="button" className="primary-button" onClick={() => void approvePreview(job.id)} disabled={busy || !previewText}>
                      <CheckCircle2 size={15} />
                      A prévia está correta
                    </button>
                  ) : null}
                  {job.status === "completed" && job.gcode_approved_at ? (
                    <button type="button" className="secondary-button" onClick={() => void createPreflight(job.id)} disabled={busy}>
                      <ShieldCheck size={15} />
                      Verificar segurança
                    </button>
                  ) : null}
                  {latestPreflight?.status === "pending_remote" ? (
                    <button type="button" className="secondary-button" onClick={() => void refreshPreflight(latestPreflight.id)} disabled={busy}>
                      <RefreshCw size={15} />
                      Atualizar
                    </button>
                  ) : null}
                  {latestPreflight?.status === "approved" ? (
                    <>
                      <button type="button" className="secondary-button" onClick={() => void createDelivery(latestPreflight, "save_only")} disabled={busy}>
                        <FileArchive size={15} />
                        Salvar G-code
                      </button>
                      <input
                        value={confirmationByPreflight[latestPreflight.id] ?? ""}
                        onChange={(event) => setConfirmationByPreflight((current) => ({ ...current, [latestPreflight.id]: event.target.value }))}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") event.preventDefault();
                        }}
                        placeholder={expectedConfirmation}
                        disabled={busy}
                      />
                      <button
                        type="button"
                        className="primary-button"
                        onClick={() => void createDelivery(latestPreflight, "save_and_print")}
                        disabled={busy || (confirmationByPreflight[latestPreflight.id] ?? "") !== expectedConfirmation}
                      >
                        <Send size={15} />
                        Enviar e imprimir
                      </button>
                    </>
                  ) : null}
                  {latestDelivery?.status === "saved" && latestDelivery.mode === "save_only" ? (
                    <button type="button" className="secondary-button" onClick={() => void rollbackDelivery(latestDelivery.id)} disabled={busy}>
                      <RotateCcw size={15} />
                      Remover salvo
                    </button>
                  ) : null}
                  {latestDelivery && ["printing", "saved"].includes(latestDelivery.status) ? (
                    <span className="muted">Acompanhe este trabalho na impressora selecionada: {latestDelivery.remote_filename}</span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
      {previewJobId && previewText ? (
        <section className="print-project-gcode-preview" aria-label="Prévia visual do G-code">
          <div>
            <strong>Confira antes de continuar</strong>
            <span>Veja se a peça está inteira, dentro da mesa e na posição esperada.</span>
          </div>
          <GcodePrintViewer
            printerId={Number(jobs.find((job) => job.id === previewJobId)?.printer_id ?? 0)}
            filename={`job-${previewJobId}.gcode`}
            mode="full"
            sourceText={previewText}
          />
        </section>
      ) : null}
      {history.length ? (
        <div className="print-project-history-list">
          <h4>Histórico do projeto</h4>
          {history.map((item) => {
            const draft = feedbackDrafts[item.id] ?? { outcome: "worked", visibility: "private", note: "", photo_url: "" };
            const measurement = measurementDrafts[item.id] ?? { outcome: "passed" as const, instrument: "Paquímetro", x: "", y: "", z: "", note: "" };
            const job = jobs.find((candidate) => candidate.id === item.slicing_job_id);
            const isPhotoModel = job?.selected_project_files?.some((file) => String(file.file_name).startsWith("modelo-revisado-")) ?? false;
            return (
              <div className="print-project-history-row" key={item.id}>
                <div>
                  <strong>{printHistoryStatus(item.status)}</strong>
                  <span>{item.quality_reference || "qualidade padrão"} · {item.visibility === "public" ? "público sanitizado" : "privado"}</span>
                  {item.feedback.slice(0, 2).map((feedback) => (
                    <small key={feedback.id}>{feedbackOutcomeText(feedback.outcome)} · {feedback.visibility === "public" ? "público" : "privado"}{feedback.note ? ` · ${feedback.note}` : ""}</small>
                  ))}
                </div>
                <div className="print-project-feedback-grid">
                  <select
                    value={draft.outcome}
                    onChange={(event) => setFeedbackDrafts((current) => ({ ...current, [item.id]: { ...draft, outcome: event.target.value as PrintJobFeedback["outcome"] } }))}
                    disabled={busy}
                  >
                    <option value="worked">Deu certo</option>
                    <option value="failed">Falhou</option>
                    <option value="needs_adjustment">Precisa ajuste</option>
                  </select>
                  <select
                    value={draft.visibility}
                    onChange={(event) => setFeedbackDrafts((current) => ({ ...current, [item.id]: { ...draft, visibility: event.target.value as PrintJobFeedback["visibility"] } }))}
                    disabled={busy}
                  >
                    <option value="private">Privado</option>
                    <option value="public">Público sanitizado</option>
                  </select>
                  <input
                    value={draft.note}
                    onChange={(event) => setFeedbackDrafts((current) => ({ ...current, [item.id]: { ...draft, note: event.target.value } }))}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") event.preventDefault();
                    }}
                    placeholder="Feedback"
                    disabled={busy}
                  />
                  <input
                    value={draft.photo_url}
                    onChange={(event) => setFeedbackDrafts((current) => ({ ...current, [item.id]: { ...draft, photo_url: event.target.value } }))}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") event.preventDefault();
                    }}
                    placeholder="Foto HTTPS opcional"
                    disabled={busy}
                  />
                  <button type="button" className="secondary-button" onClick={() => void addFeedback(item.id)} disabled={busy}>
                    Registrar feedback
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void recordHistory(item.id, "completed")} disabled={busy}>
                    Concluiu
                  </button>
                  {item.slicing_job_id ? (
                    <button type="button" className="secondary-button" onClick={() => void reprintJob(item.slicing_job_id!)} disabled={busy}>
                      <RotateCcw size={15} />
                      Reimprimir igual
                    </button>
                  ) : null}
                </div>
                {isPhotoModel && ["completed", "failed"].includes(item.status) ? <div className="print-project-feedback-grid">
                  {item.mesh_physical_validation ? <div className="success-text"><strong>Peça medida</strong><span>Maior diferença: {item.mesh_physical_validation.max_error_percent.toFixed(1)}%. Instrumento: {item.mesh_physical_validation.instrument_label}.</span></div> : <>
                    <strong>Medir a peça criada pelas fotos</strong>
                    <p className="muted">Depois que a peça esfriar, meça largura, profundidade ou altura. Basta informar pelo menos uma medida.</p>
                    <select value={measurement.outcome} onChange={(event) => setMeasurementDrafts((current) => ({ ...current, [item.id]: { ...measurement, outcome: event.target.value as MeshPhysicalValidation["outcome"] } }))} disabled={busy}><option value="passed">Ficou boa</option><option value="needs_adjustment">Precisa ajuste</option><option value="failed">A impressão falhou</option></select>
                    <input value={measurement.instrument} onChange={(event) => setMeasurementDrafts((current) => ({ ...current, [item.id]: { ...measurement, instrument: event.target.value } }))} placeholder="Instrumento usado" disabled={busy} />
                    <input type="number" inputMode="decimal" min="0.1" step="0.1" value={measurement.x} onChange={(event) => setMeasurementDrafts((current) => ({ ...current, [item.id]: { ...measurement, x: event.target.value } }))} placeholder="Largura X em mm" disabled={busy} />
                    <input type="number" inputMode="decimal" min="0.1" step="0.1" value={measurement.y} onChange={(event) => setMeasurementDrafts((current) => ({ ...current, [item.id]: { ...measurement, y: event.target.value } }))} placeholder="Profundidade Y em mm" disabled={busy} />
                    <input type="number" inputMode="decimal" min="0.1" step="0.1" value={measurement.z} onChange={(event) => setMeasurementDrafts((current) => ({ ...current, [item.id]: { ...measurement, z: event.target.value } }))} placeholder="Altura Z em mm" disabled={busy} />
                    <input value={measurement.note} onChange={(event) => setMeasurementDrafts((current) => ({ ...current, [item.id]: { ...measurement, note: event.target.value } }))} placeholder="Observação opcional" disabled={busy} />
                    <button type="button" className="primary-button" onClick={() => void addPhysicalValidation(item.id)} disabled={busy || !measurement.instrument.trim() || !(measurement.x || measurement.y || measurement.z)}>Salvar medidas</button>
                  </>}
                </div> : null}
              </div>
            );
          })}
        </div>
      ) : null}
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
      <ProjectAssetsEditor project={project} setError={setError} onChanged={onChanged} />
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

function ProjectDetail({ project, authUserPresent, saving, onSave, setError }: { project: PrintProjectDetail; authUserPresent: boolean; saving: boolean; onSave: (projectId: number) => void; setError: (message: string | null) => void }) {
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
      <ProjectAssetsSummary project={project} setError={setError} canDownload={authUserPresent} />
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

function slicingJobStatus(status: SlicingJob["status"]): string {
  const labels: Record<SlicingJob["status"], string> = {
    planned: "planejado",
    running: "executando",
    completed: "concluído",
    failed: "falhou",
    canceled: "cancelado",
  };
  return labels[status];
}

function preflightStatus(status: PrintPreflight["status"]): string {
  const labels: Record<PrintPreflight["status"], string> = {
    approved: "aprovado",
    blocked: "bloqueado",
    pending_remote: "aguardando agente",
    failed: "falhou",
  };
  return labels[status];
}

function deliveryStatus(status: PrintDelivery["status"]): string {
  const labels: Record<PrintDelivery["status"], string> = {
    pending_remote: "aguardando agente",
    saved: "salvo",
    printing: "imprimindo",
    blocked: "bloqueado",
    failed: "falhou",
    canceled: "cancelado",
    rollback_pending: "removendo",
    rolled_back: "removido",
    rollback_failed: "falha ao remover",
  };
  return labels[status];
}

function deliveryModeLabel(mode: PrintDelivery["mode"]): string {
  return mode === "save_and_print" ? "enviar e iniciar" : "salvar G-code";
}

function printHistoryStatus(status: PrintJobHistory["status"]): string {
  const labels: Record<PrintJobHistory["status"], string> = {
    sent: "enviado",
    started: "iniciado",
    completed: "concluído",
    failed: "falhou",
    canceled: "cancelado",
  };
  return labels[status];
}

function feedbackOutcomeText(outcome: PrintJobFeedback["outcome"]): string {
  const labels: Record<PrintJobFeedback["outcome"], string> = {
    worked: "deu certo",
    failed: "falhou",
    needs_adjustment: "precisa ajuste",
  };
  return labels[outcome];
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
