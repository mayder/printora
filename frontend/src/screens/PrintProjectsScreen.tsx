import React from "react";
import { CheckCircle2, ExternalLink, FileArchive, FileText, Link2, RefreshCw, Search, ShieldCheck, Tags } from "lucide-react";
import { printProjectsApi } from "../services/printProjectsApi";
import type { PrintProjectContract, PrintProjectDetail, PrintProjectFile, PrintProjectSummary } from "../types/printProjects";
import type { ScreenPropsFor } from "./ScreenProps";

type PrintProjectsScreenProps = ScreenPropsFor<"authUser" | "setError">;
type ProjectFilters = { file_kind: string; license: string; origin: "" | "hosted" | "external" };

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

const fileRoleLabels: Record<PrintProjectFile["file_role"], string> = {
  primary: "Principal",
  printable: "Imprimível",
  optional_part: "Peça opcional",
  documentation: "Documentação",
  preview: "Preview",
  external_reference: "Referência externa",
  artifact: "Artefato",
};

export function PrintProjectsScreen({ authUser, setError }: PrintProjectsScreenProps) {
  const [query, setQuery] = React.useState("");
  const [filters, setFilters] = React.useState<ProjectFilters>({ file_kind: "", license: "", origin: "" });
  const [contract, setContract] = React.useState<PrintProjectContract | null>(null);
  const [projects, setProjects] = React.useState<PrintProjectSummary[]>([]);
  const [selectedProject, setSelectedProject] = React.useState<PrintProjectDetail | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [savingId, setSavingId] = React.useState<number | null>(null);

  async function loadProjects(nextQuery = query) {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar projeto");
    } finally {
      setSavingId(null);
    }
  }

  React.useEffect(() => {
    void loadProjects("");
  }, [filters.file_kind, filters.license, filters.origin]);

  return (
    <div className="print-projects-screen">
      <section className="print-projects-band">
        <div>
          <span className="eyebrow">Projetos de impressão</span>
          <h2>Biblioteca central de STL, 3MF, ZIP e referências externas</h2>
          <p>Busque projetos sem entrar em uma comunidade e abra o detalhe central antes de fatiar, salvar G-code ou enviar para impressora.</p>
        </div>
        <div className="print-projects-contract">
          <span>Raiz do domínio</span>
          <strong>{contract?.root_entity ?? "Projeto de impressão"}</strong>
          <small>{contract?.community_ownership_rule ?? "Comunidades compartilham projetos; não são donas."}</small>
        </div>
      </section>

      <section className="print-projects-toolbar" aria-label="Busca de projetos">
        <label>
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void loadProjects();
            }}
            placeholder="Buscar por nome, tag, licença, arquivo ou comunidade"
          />
        </label>
        <button type="button" className="secondary-button" onClick={() => void loadProjects()} disabled={busy}>
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

      <section className="print-projects-layout">
        <div className="print-projects-panel">
          <header>
            <h3>Explorar</h3>
            <span>{projects.length} projeto(s)</span>
          </header>
          {projects.length === 0 ? (
            <div className="empty-state">
              <FileArchive size={22} />
              <strong>Nenhum projeto público encontrado</strong>
              <p>O contrato e a navegação já estão preparados. Upload, salvos e migração legada entram nas próximas etapas.</p>
            </div>
          ) : (
            <div className="print-project-grid">
              {projects.map((project) => (
                <ProjectCard key={project.id} project={project} onOpen={openProject} />
              ))}
            </div>
          )}
        </div>

        <aside className="print-projects-panel print-projects-rules">
          {selectedProject ? (
            <ProjectDetail project={selectedProject} authUserPresent={!!authUser} saving={savingId === selectedProject.id} onSave={saveProject} />
          ) : (
            <>
              <h3>Contrato operacional</h3>
              <Rule icon={ShieldCheck} label="Snapshot" text="Fatiamento, G-code e histórico exigem versão imutável." />
              <Rule icon={Link2} label="Links externos" text="Referência sem arquivo validado não pode ser fatiada ou enviada." />
              <Rule icon={Tags} label="Dimensões separadas" text="Visibilidade, publicação, venda e comunidade não se misturam." />
              <Rule icon={FileText} label="Legado" text="Comunidade e Administração ficam como vitrine, diagnóstico ou fallback." />
            </>
          )}
        </aside>
      </section>
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
        <span>{commercialLabels[project.commercial_class]}</span>
        <span>{publicationLabels[project.publication_status]}</span>
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
        <span>{commercialLabels[project.commercial_class]}</span>
        <span>{publicationLabels[project.publication_status]}</span>
        <span>{project.immutable_snapshot_ready ? "Snapshot pronto" : "Snapshot pendente"}</span>
      </div>
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
        {project.versions.length === 0 ? <span className="muted">Snapshot será exigido antes de fatiar, gerar G-code ou registrar histórico.</span> : null}
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
        <span>{file.file_kind.toUpperCase()} · {fileRoleLabels[file.file_role]}</span>
      </div>
      <span>{file.can_slice ? "Fatiável" : "Bloqueado"}</span>
    </div>
  );
}

function Rule({ icon: Icon, label, text }: { icon: typeof ShieldCheck; label: string; text: string }) {
  return (
    <div className="print-project-rule">
      <Icon size={17} />
      <div>
        <strong>{label}</strong>
        <span>{text}</span>
      </div>
    </div>
  );
}
