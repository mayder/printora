import * as React from "react";
import { Box, CircleAlert, Download, LoaderCircle, RotateCcw, XCircle } from "lucide-react";
import { photoReconstructionApi } from "../../services/photoReconstructionApi";
import type { ReconstructionEnginePolicy, ReconstructionJob } from "../../types/photoReconstruction";

const MeshRepairPanel = React.lazy(() => import("./MeshRepairPanel").then((module) => ({ default: module.MeshRepairPanel })));

interface Props {
  captureSessionId: number;
  setError: (message: string | null) => void;
  onModelApproved?: () => Promise<void>;
}

const stageLabels: Record<string, string> = {
  waiting: "Aguardando capacidade",
  preparing: "Preparando fotos privadas",
  camera_poses: "Encontrando os ângulos",
  dense_cloud: "Construindo a forma",
  surface: "Criando a superfície",
  packaging: "Conferindo o resultado",
  ready: "Malha bruta pronta",
  failed: "Processamento interrompido",
  cancelled: "Processamento cancelado",
};

const engineLabels: Record<string, string> = {
  "fixture-photogrammetry": "Demonstração local",
  "local-photogrammetry": "Processamento privado",
  "provider-multiview-gateway": "Serviço online homologado",
};

export function ReconstructionPanel({ captureSessionId, setError, onModelApproved }: Props) {
  const [job, setJob] = React.useState<ReconstructionJob | null>(null);
  const [policy, setPolicy] = React.useState<ReconstructionEnginePolicy>("auto");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    let active = true;
    void photoReconstructionApi.list(captureSessionId).then((rows) => {
      if (active) setJob(rows[0] ?? null);
    }).catch(() => undefined);
    return () => { active = false; };
  }, [captureSessionId]);

  React.useEffect(() => {
    if (!job || !["queued", "processing"].includes(job.status)) return;
    const timer = window.setInterval(() => {
      void photoReconstructionApi.get(job.id).then(setJob).catch(() => undefined);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [job?.id, job?.status]);

  async function run(action: () => Promise<ReconstructionJob>) {
    setBusy(true);
    setError(null);
    try {
      setJob(await action());
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível atualizar a reconstrução.");
    } finally {
      setBusy(false);
    }
  }

  async function download() {
    if (!job) return;
    const artifact = job.artifacts.find((item) => item.artifact_type === "raw_mesh");
    if (!artifact) return;
    setBusy(true);
    try {
      const blob = await photoReconstructionApi.download(job.id, artifact.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `reconstrucao-${job.id}.${artifact.file_format}`;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível baixar a malha.");
    } finally {
      setBusy(false);
    }
  }

  if (!job) {
    return <section className="reconstruction-panel" aria-labelledby="reconstruction-title">
      <div className="photo-capture-heading"><Box size={22} aria-hidden="true" /><div><h4 id="reconstruction-title">Criar o modelo 3D</h4><p>O processamento acontece fora da impressora. Você pode sair e voltar depois.</p></div></div>
      <label>Como processar<select value={policy} onChange={(event) => setPolicy(event.target.value as ReconstructionEnginePolicy)}><option value="auto">Escolher a melhor opção disponível</option><option value="local">Processamento privado do Printora</option><option value="provider">Serviço online homologado</option></select></label>
      <p className="photo-capture-note"><CircleAlert size={16} /> O primeiro resultado é uma malha bruta. Ela ainda será conferida antes de virar um arquivo para impressão.</p>
      <button type="button" className="primary-button" disabled={busy} onClick={() => void run(() => photoReconstructionApi.create(captureSessionId, policy))}>{busy ? "Agendando..." : "Criar modelo 3D"}</button>
    </section>;
  }

  const artifact = job.artifacts.find((item) => item.artifact_type === "raw_mesh");
  const qualification = job.qualification;
  const blockers = qualification?.report.blockers ?? [];
  const dimensions = qualification?.report.dimensions;
  return <section className="reconstruction-panel" aria-live="polite">
    <div className="photo-capture-heading">{job.status === "processing" ? <LoaderCircle className="reconstruction-spinner" size={22} /> : <Box size={22} />}<div><h4>{stageLabels[job.stage] ?? "Reconstrução 3D"}</h4><p>{job.next_action}</p></div></div>
    {job.progress_percent !== null ? <progress max={100} value={job.progress_percent}>{job.progress_percent}%</progress> : null}
    {job.error_message ? <p className="error-text">{job.error_message}</p> : null}
    {job.engine_key ? <p className="photo-capture-note">Modo: {engineLabels[job.engine_key] ?? "Processamento 3D"}. Tentativas: {job.attempts.length}.</p> : null}
    <div className="reconstruction-actions">
      {job.can_cancel ? <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(() => photoReconstructionApi.cancel(job.id))}><XCircle size={16} /> Cancelar</button> : null}
      {job.can_retry ? <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(() => photoReconstructionApi.retry(job.id))}><RotateCcw size={16} /> Tentar novamente</button> : null}
      {artifact ? <button type="button" className="secondary-button" disabled={busy} onClick={() => void download()}><Download size={16} /> Baixar malha bruta</button> : null}
    </div>
    {artifact && qualification ? <div className="photo-capture-note" role="status">
      <CircleAlert size={16} aria-hidden="true" />
      <div><strong>Conferência para impressão em andamento</strong>
        {dimensions ? <p>Tamanho encontrado: {dimensions.x} × {dimensions.y} × {dimensions.z} {artifact.unit === "mm" ? "mm" : "(unidade ainda não confirmada)"}.</p> : null}
        <p>A malha bruta foi preservada. Ela só poderá ser aprovada depois destas conferências:</p>
        <ul>{blockers.map((message) => <li key={message}>{message}</li>)}</ul>
      </div>
    </div> : artifact ? <p className="photo-capture-note"><CircleAlert size={16} /> Esta malha ainda não foi qualificada para impressão. Áreas inferidas ou desconhecidas precisam de revisão.</p> : null}
    {artifact && (artifact.observed_ratio !== null || artifact.inferred_ratio !== null) ? <div className="photo-capture-note"><CircleAlert size={16} aria-hidden="true" /><div><strong>Origem da forma</strong><p>Partes observadas nas fotos: {Math.round((artifact.observed_ratio ?? 0) * 100)}%. Partes estimadas pelo processamento: {Math.round((artifact.inferred_ratio ?? 0) * 100)}%. As correções posteriores aparecem no histórico abaixo.</p></div></div> : null}
    {artifact && qualification ? <React.Suspense fallback={<p className="photo-capture-note">Carregando preparação segura…</p>}><MeshRepairPanel jobId={job.id} rawUnit={artifact.unit} rawChecks={qualification.report.checks ?? {}} rawDimensions={qualification.report.dimensions} setError={setError} onModelApproved={onModelApproved} /></React.Suspense> : null}
  </section>;
}
