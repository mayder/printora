import React from "react";
import { ExternalLink, FileArchive, FileText, Link2, RefreshCw, Search, ShieldCheck, Tags } from "lucide-react";
import { printProjectsApi } from "../services/printProjectsApi";
import type { PrintProjectContract, PrintProjectSummary } from "../types/printProjects";
import type { ScreenPropsFor } from "./ScreenProps";

type PrintProjectsScreenProps = ScreenPropsFor<"setError">;

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

export function PrintProjectsScreen({ setError }: PrintProjectsScreenProps) {
  const [query, setQuery] = React.useState("");
  const [contract, setContract] = React.useState<PrintProjectContract | null>(null);
  const [projects, setProjects] = React.useState<PrintProjectSummary[]>([]);
  const [busy, setBusy] = React.useState(false);

  async function loadProjects(nextQuery = query) {
    setBusy(true);
    try {
      const [contractPayload, projectsPayload] = await Promise.all([
        printProjectsApi.contract(),
        printProjectsApi.explore({ q: nextQuery.trim(), limit: 24 }),
      ]);
      setContract(contractPayload);
      setProjects(projectsPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar projetos de impressão");
    } finally {
      setBusy(false);
    }
  }

  React.useEffect(() => {
    void loadProjects("");
  }, []);

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
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </div>

        <aside className="print-projects-panel print-projects-rules">
          <h3>Contrato operacional</h3>
          <Rule icon={ShieldCheck} label="Snapshot" text="Fatiamento, G-code e histórico exigem versão imutável." />
          <Rule icon={Link2} label="Links externos" text="Referência sem arquivo validado não pode ser fatiada ou enviada." />
          <Rule icon={Tags} label="Dimensões separadas" text="Visibilidade, publicação, venda e comunidade não se misturam." />
          <Rule icon={FileText} label="Legado" text="Comunidade e Administração ficam como vitrine, diagnóstico ou fallback." />
        </aside>
      </section>
    </div>
  );
}

function ProjectCard({ project }: { project: PrintProjectSummary }) {
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
    </article>
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
