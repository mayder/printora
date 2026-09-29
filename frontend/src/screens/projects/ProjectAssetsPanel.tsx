import React from "react";
import { Box, Download, Ruler, Save, TriangleAlert } from "lucide-react";
import { printProjectsApi } from "../../services/printProjectsApi";
import type { PrintProjectDetail, PrintProjectFile, PrintProjectFileStructurePayload } from "../../types/printProjects";
import { ProjectMeshPreview } from "./ProjectMeshPreview";

type CommonProps = {
  project: PrintProjectDetail;
  setError: (message: string | null) => void;
};

export function ProjectAssetsSummary({ project, setError, canDownload }: CommonProps & { canDownload: boolean }) {
  const inspected = project.files.filter((file) => file.inspection_status !== "not_applicable");
  const [bundleBusy, setBundleBusy] = React.useState(false);

  function downloadManifest() {
    const body = JSON.stringify(project.current_manifest, null, 2);
    downloadBlob(new Blob([body], { type: "application/json" }), `${project.slug}-manifest.json`);
  }

  async function downloadBundle() {
    setBundleBusy(true);
    try {
      downloadBlob(await printProjectsApi.bundleBlob(project.id), `${project.slug}.zip`);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível preparar o pacote");
    } finally {
      setBundleBusy(false);
    }
  }

  return (
    <section className="print-project-detail-section project-assets" aria-labelledby="project-assets-title">
      <div className="project-assets-heading">
        <div>
          <h4 id="project-assets-title">Peças e inspeção</h4>
          <span className="muted">Confira medidas e avisos antes de fatiar.</span>
        </div>
        {project.current_manifest_sha256 && canDownload ? <div className="project-asset-actions">
          <button type="button" className="secondary-button" onClick={downloadManifest}><Download size={16} /> Manifesto</button>
          <button type="button" className="secondary-button" onClick={() => void downloadBundle()} disabled={bundleBusy}><Download size={16} /> {bundleBusy ? "Preparando" : "Baixar pacote"}</button>
        </div> : null}
      </div>
      {inspected.map((file) => <AssetCard key={file.id} file={file} setError={setError} canDownload={canDownload} />)}
      {inspected.length === 0 ? <span className="muted">Envie um STL ou 3MF para conferir a peça.</span> : null}
      {project.current_manifest_sha256 ? (
        <small className="project-asset-checksum">Identificador desta versão: {project.current_manifest_sha256.slice(0, 12)}</small>
      ) : null}
    </section>
  );
}

export function ProjectAssetsEditor({ project, setError, onChanged }: CommonProps & { onChanged: (detail: PrintProjectDetail) => void }) {
  return (
    <section className="print-project-detail-section project-assets-editor" aria-labelledby="project-structure-title">
      <div>
        <h4 id="project-structure-title">Organizar peças</h4>
        <p className="muted">Dê nomes simples para encontrar cada peça e variação depois.</p>
      </div>
      {project.files.filter((file) => file.file_role !== "external_reference").map((file) => (
        <AssetStructureForm key={file.id} project={project} file={file} setError={setError} onChanged={onChanged} />
      ))}
    </section>
  );
}

function AssetCard({ file, setError, canDownload }: { file: PrintProjectFile; setError: (message: string | null) => void; canDownload: boolean }) {
  const [busy, setBusy] = React.useState(false);
  const inspection = file.inspection ?? {};
  const dimensions = inspection.dimensions_mm;
  const warnings = inspection.warnings ?? [];

  async function download() {
    setBusy(true);
    try {
      downloadBlob(await printProjectsApi.fileBlob(file.id), file.file_name);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível baixar o arquivo");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="project-asset-card">
      <div className="project-asset-preview" role="img" aria-label={dimensions ? `Prévia dimensional: ${dimensions.x} por ${dimensions.y} por ${dimensions.z} milímetros` : "Prévia 3D indisponível; dados do arquivo exibidos ao lado"}>
        <Box size={54} aria-hidden="true" />
        <span>{file.file_kind.toUpperCase()}</span>
      </div>
      <div className="project-asset-facts">
        <strong>{file.piece_name || file.file_name}</strong>
        <span>{[file.assembly_name, file.variant_name].filter(Boolean).join(" · ") || "Peça sem grupo ou variação"}</span>
        {dimensions ? (
          <span><Ruler size={14} /> {dimensions.x} × {dimensions.y} × {dimensions.z} mm</span>
        ) : (
          <span>Medidas ainda não disponíveis.</span>
        )}
        {inspection.triangle_count !== undefined ? <span>{inspection.triangle_count.toLocaleString("pt-BR")} triângulo(s)</span> : null}
        {warnings.map((warning) => <span className="project-asset-warning" key={warning}><TriangleAlert size={14} /> {warning}</span>)}
        <ProjectMeshPreview file={file} />
      </div>
      {file.validation_status === "validated" && canDownload ? (
        <button type="button" className="secondary-button" onClick={() => void download()} disabled={busy}>
          <Download size={16} /> {busy ? "Preparando" : "Baixar"}
        </button>
      ) : null}
    </article>
  );
}

function AssetStructureForm({ project, file, setError, onChanged }: CommonProps & { file: PrintProjectFile; onChanged: (detail: PrintProjectDetail) => void }) {
  const [draft, setDraft] = React.useState<PrintProjectFileStructurePayload>({
    piece_name: file.piece_name || file.file_name.replace(/\.[^.]+$/, ""),
    variant_name: file.variant_name,
    assembly_name: file.assembly_name,
    display_order: file.display_order,
    unit: file.unit,
  });
  const [busy, setBusy] = React.useState(false);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      onChanged(await printProjectsApi.updateFileStructure(project.id, file.id, draft));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível organizar a peça");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="project-asset-structure-form" onSubmit={(event) => void save(event)}>
      <strong>{file.file_name}</strong>
      <label>Nome para a peça<input value={draft.piece_name} onChange={(event) => setDraft({ ...draft, piece_name: event.target.value })} maxLength={160} /></label>
      <label>Grupo ou montagem<input value={draft.assembly_name} onChange={(event) => setDraft({ ...draft, assembly_name: event.target.value })} placeholder="Ex.: Corpo principal" maxLength={160} /></label>
      <label>Variação<input value={draft.variant_name} onChange={(event) => setDraft({ ...draft, variant_name: event.target.value })} placeholder="Ex.: Grande" maxLength={160} /></label>
      <button type="submit" className="secondary-button" disabled={busy || !draft.piece_name.trim()}><Save size={16} /> {busy ? "Salvando" : "Salvar organização"}</button>
    </form>
  );
}

function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}
