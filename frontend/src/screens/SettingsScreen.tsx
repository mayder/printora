import React from "react";
import { Metric } from "../components/common";
import { printerApi } from "../services/printerApi";
import { slicingApi, type PrintPreflight, type SlicingEngineInfo, type SlicingJob } from "../services/slicingApi";
import { formatDateTime } from "../utils/formatters";
import type { ScreenPropsFor } from "./ScreenProps";
import type { PrinterRecord } from "../types/printers";

type SettingsScreenProps = ScreenPropsFor<
  | "authUser"
  | "FileText"
  | "History"
  | "RefreshCw"
  | "Settings"
  | "displayedReleaseRows"
  | "formatReleaseSourceStatus"
  | "formatReleaseUpdateStatus"
  | "formatSelfUpdateStatus"
  | "loadSelfUpdateHistory"
  | "loadSystemReleases"
  | "releaseError"
  | "releaseLoading"
  | "releasePanelClass"
  | "releaseStatusPillClass"
  | "selfUpdateHistory"
  | "selfUpdateRunClass"
  | "systemReleases"
>;

export function SettingsScreen(props: SettingsScreenProps) {
  const {
    authUser,
    FileText,
    History,
    RefreshCw,
    Settings,
    displayedReleaseRows,
    formatReleaseSourceStatus,
    formatReleaseUpdateStatus,
    formatSelfUpdateStatus,
    loadSelfUpdateHistory,
    loadSystemReleases,
    releaseError,
    releaseLoading,
    releasePanelClass,
    releaseStatusPillClass,
    selfUpdateHistory,
    selfUpdateRunClass,
    systemReleases,
  } = props;
  const isPlatformAdmin = authUser?.email?.toLowerCase() === "breno@mayder.com.br";
  const [slicingEngine, setSlicingEngine] = React.useState<SlicingEngineInfo | null>(null);
  const [slicingLoading, setSlicingLoading] = React.useState(false);
  const [slicingError, setSlicingError] = React.useState<string | null>(null);
  const [slicingJobs, setSlicingJobs] = React.useState<SlicingJob[]>([]);
  const [printPreflights, setPrintPreflights] = React.useState<PrintPreflight[]>([]);
  const [slicingPrinters, setSlicingPrinters] = React.useState<PrinterRecord[]>([]);
  const [slicingJobBusy, setSlicingJobBusy] = React.useState(false);
  const [slicingDraft, setSlicingDraft] = React.useState({
    printerId: "",
    modelReference: "library://modelo.stl",
    qualityReference: "0.20 qualidade",
    x: "",
    y: "",
    z: "",
  });

  React.useEffect(() => {
    void loadSlicingPipeline();
  }, []);

  async function loadSlicingEngine() {
    setSlicingLoading(true);
    setSlicingError(null);
    try {
      setSlicingEngine(await slicingApi.engine());
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao verificar engine de fatiamento");
    } finally {
      setSlicingLoading(false);
    }
  }

  async function loadSlicingPipeline() {
    try {
      const [printersResponse, jobs, preflights] = await Promise.all([printerApi.list(), slicingApi.jobs(), slicingApi.preflights()]);
      const printersPayload = await printersResponse.json() as PrinterRecord[] | { printers?: PrinterRecord[] };
      const printers = Array.isArray(printersPayload) ? printersPayload : printersPayload.printers ?? [];
      setSlicingPrinters(printers.filter((printer) => printer.is_active));
      setSlicingJobs(jobs);
      setPrintPreflights(preflights);
      setSlicingDraft((current) => current.printerId || printers.length === 0 ? current : { ...current, printerId: String(printers[0].id) });
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao carregar pipeline de fatiamento");
    }
  }

  async function createSlicingJob() {
    const printerId = Number(slicingDraft.printerId);
    if (!printerId) {
      setSlicingError("Selecione uma impressora para criar o job.");
      return;
    }
    setSlicingJobBusy(true);
    setSlicingError(null);
    try {
      const job = await slicingApi.createJob({
        printer_id: printerId,
        engine: "orcaslicer",
        model_reference: slicingDraft.modelReference,
        model_dimensions: {
          x_mm: numberOrNull(slicingDraft.x),
          y_mm: numberOrNull(slicingDraft.y),
          z_mm: numberOrNull(slicingDraft.z),
        },
        quality_reference: slicingDraft.qualityReference,
      });
      setSlicingJobs((current) => [job, ...current.filter((item) => item.id !== job.id)].slice(0, 20));
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao criar job de fatiamento");
    } finally {
      setSlicingJobBusy(false);
    }
  }

  async function runSlicingJob(jobId: number) {
    setSlicingJobBusy(true);
    setSlicingError(null);
    try {
      const job = await slicingApi.runJob(jobId);
      setSlicingJobs((current) => current.map((item) => item.id === job.id ? job : item));
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao executar job de fatiamento");
    } finally {
      setSlicingJobBusy(false);
    }
  }

  async function cancelSlicingJob(jobId: number) {
    setSlicingJobBusy(true);
    setSlicingError(null);
    try {
      const job = await slicingApi.cancelJob(jobId);
      setSlicingJobs((current) => current.map((item) => item.id === job.id ? job : item));
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao cancelar job de fatiamento");
    } finally {
      setSlicingJobBusy(false);
    }
  }

  async function createPrintPreflight(jobId: number) {
    setSlicingJobBusy(true);
    setSlicingError(null);
    try {
      const preflight = await slicingApi.createPreflight(jobId);
      setPrintPreflights((current) => [preflight, ...current.filter((item) => item.id !== preflight.id)].slice(0, 30));
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao criar preflight de impressão");
    } finally {
      setSlicingJobBusy(false);
    }
  }

  async function refreshPrintPreflight(preflightId: number) {
    setSlicingJobBusy(true);
    setSlicingError(null);
    try {
      const preflight = await slicingApi.refreshPreflight(preflightId);
      setPrintPreflights((current) => current.map((item) => item.id === preflight.id ? preflight : item));
    } catch (err) {
      setSlicingError(err instanceof Error ? err.message : "Falha ao atualizar preflight de impressão");
    } finally {
      setSlicingJobBusy(false);
    }
  }

  return (
    <>
      <article className="panel wide panel-section panel-settings">
        <div className="panel-header-row">
          <div>
            <h2>Administração</h2>
            <p>Configurações globais do Printora Cloud. Releases da plataforma não fazem parte da operação do cliente.</p>
          </div>
          <Settings size={20} />
        </div>
        <div className="release-summary-grid">
          <Metric label="Plataforma" value="Printora Cloud" />
          <Metric label="Impressoras" value="por registro" />
          <Metric label="Agentes" value="com releases próprias" />
          <Metric label="Atualizações" value="por agente" />
        </div>
      </article>

      <article className="panel wide panel-section panel-settings">
        <div className="panel-header-row">
          <div>
            <h2>Escopo global</h2>
            <p>Itens técnicos específicos saíram desta tela para evitar misturar plataforma, impressora e host do agente.</p>
          </div>
          <Settings size={20} />
        </div>
        <div className="release-summary-grid">
          <Metric label="Plataforma" value="Printora Cloud" />
          <Metric label="Operação" value="por impressora" />
          <Metric label="Diagnóstico host" value="por agente" />
          <Metric label="CAN técnico" value="por impressora" />
        </div>
      </article>

      <article className="panel wide panel-section panel-settings">
        <div className="panel-header-row">
          <div>
            <h2>Fatiamento controlado</h2>
            <p>Verificação somente leitura da engine CLI. O Printora não embute a interface do fatiador.</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void loadSlicingEngine()} disabled={slicingLoading}>
            <RefreshCw className={slicingLoading ? "button-busy-icon" : undefined} size={16} />
            {slicingLoading ? "Verificando" : "Verificar engine"}
          </button>
        </div>
        <div className="release-summary-grid">
          <Metric label="Engine" value={slicingEngine?.engine ?? "OrcaSlicer"} />
          <Metric label="Status" value={slicingEngine?.status === "ready" ? "pronta" : "bloqueada"} />
          <Metric label="Versão" value={slicingEngine?.version_text ?? "-"} />
          <Metric label="Modo" value="dry-run" />
        </div>
        {slicingError ? (
          <div className="action-result warning">
            <strong>Falha na verificação</strong>
            <span>{slicingError}</span>
          </div>
        ) : null}
        {slicingEngine ? (
          <div className={`action-result ${slicingEngine.status === "ready" ? "success" : "warning"}`}>
            <strong>{slicingEngine.status === "ready" ? "Engine detectada" : "Engine não configurada"}</strong>
            <span>{slicingEngine.detected_path ?? slicingEngine.installation_hint}</span>
            {slicingEngine.warnings.length ? <small>{slicingEngine.warnings.join(" ")}</small> : null}
          </div>
        ) : null}
      </article>

      <article className="panel wide panel-section panel-settings">
        <div className="panel-header-row">
          <div>
            <h2>Pipeline de fatiamento</h2>
            <p>Jobs rastreáveis por modelo, impressora, perfil e artefatos. Execução real depende da engine configurada.</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void loadSlicingPipeline()} disabled={slicingJobBusy}>
            <RefreshCw className={slicingJobBusy ? "button-busy-icon" : undefined} size={16} />
            Recarregar
          </button>
        </div>
        <div className="settings-inline-form">
          <label>
            Impressora
            <select value={slicingDraft.printerId} onChange={(event) => setSlicingDraft((current) => ({ ...current, printerId: event.target.value }))}>
              <option value="">Selecione</option>
              {slicingPrinters.map((printer) => <option key={printer.id} value={printer.id}>{printer.name}</option>)}
            </select>
          </label>
          <label>
            Modelo
            <input value={slicingDraft.modelReference} onChange={(event) => setSlicingDraft((current) => ({ ...current, modelReference: event.target.value }))} />
          </label>
          <label>
            Qualidade
            <input value={slicingDraft.qualityReference} onChange={(event) => setSlicingDraft((current) => ({ ...current, qualityReference: event.target.value }))} />
          </label>
          <label>
            X mm
            <input inputMode="decimal" value={slicingDraft.x} onChange={(event) => setSlicingDraft((current) => ({ ...current, x: event.target.value }))} />
          </label>
          <label>
            Y mm
            <input inputMode="decimal" value={slicingDraft.y} onChange={(event) => setSlicingDraft((current) => ({ ...current, y: event.target.value }))} />
          </label>
          <label>
            Z mm
            <input inputMode="decimal" value={slicingDraft.z} onChange={(event) => setSlicingDraft((current) => ({ ...current, z: event.target.value }))} />
          </label>
          <button type="button" className="primary-button" onClick={() => void createSlicingJob()} disabled={slicingJobBusy || !slicingDraft.printerId}>
            Criar job
          </button>
        </div>
        <div className="settings-job-list">
          {slicingJobs.length === 0 ? <p className="muted">Nenhum job de fatiamento registrado.</p> : null}
          {slicingJobs.slice(0, 6).map((job) => (
            <div key={job.id} className={`update-row ${job.status === "failed" ? "failed" : job.status === "completed" ? "success" : ""}`}>
              <div className="update-main">
                <div>
                  <strong>#{job.id} · {job.model_reference}</strong>
                  <span>{slicingJobStatus(job.status)} · {job.quality_reference} · {formatDateTime(job.created_at)}</span>
                  {job.error_message ? <small>{job.error_message}</small> : null}
                  {job.artifacts.length ? <small>{job.artifacts.length} artefato(s) rastreado(s)</small> : null}
                  <PreflightSummary preflight={latestPreflightForJob(printPreflights, job.id)} />
                </div>
                <div className="inline-actions">
                  {job.status === "planned" || job.status === "failed" ? (
                    <button type="button" className="secondary-button" onClick={() => void runSlicingJob(job.id)} disabled={slicingJobBusy}>
                      Executar
                    </button>
                  ) : null}
                  {job.status === "planned" || job.status === "running" ? (
                    <button type="button" className="secondary-button" onClick={() => void cancelSlicingJob(job.id)} disabled={slicingJobBusy}>
                      Cancelar
                    </button>
                  ) : null}
                  {job.status === "completed" ? (
                    <button type="button" className="secondary-button" onClick={() => void createPrintPreflight(job.id)} disabled={slicingJobBusy}>
                      Preflight
                    </button>
                  ) : null}
                  {latestPreflightForJob(printPreflights, job.id)?.status === "pending_remote" ? (
                    <button type="button" className="secondary-button" onClick={() => void refreshPrintPreflight(latestPreflightForJob(printPreflights, job.id)!.id)} disabled={slicingJobBusy}>
                      Atualizar preflight
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      </article>

      {isPlatformAdmin ? (
        <>
          <article className={`panel wide panel-section panel-settings releases-panel ${releasePanelClass(systemReleases)}`}>
            <div className="panel-header-row">
              <div>
                <h2>Plataforma Printora (interno)</h2>
                <p>Visível somente para suporte. Clientes operam releases de agente dentro dos registros de agente.</p>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => void loadSystemReleases()}
                disabled={releaseLoading}
              >
                <RefreshCw className={releaseLoading ? "button-busy-icon" : undefined} size={16} />
                {releaseLoading ? "Verificando" : "Verificar plataforma"}
              </button>
            </div>
            <div className="release-summary-grid">
              <Metric label="Versão publicada" value={systemReleases?.installed_version ?? "-"} />
              <Metric label="Última release" value={systemReleases?.latest_release?.tag ?? "-"} />
              <Metric label="Canal" value={systemReleases?.channel ?? "-"} />
              <Metric label="Status" value={formatReleaseUpdateStatus(systemReleases, releaseLoading, releaseError)} />
            </div>
            {releaseError ? (
              <div className="action-result warning">
                <strong>Erro de rede</strong>
                <span>{releaseError}</span>
              </div>
            ) : null}
            {systemReleases?.error ? (
              <div className="action-result warning">
                <strong>{formatReleaseSourceStatus(systemReleases.status)}</strong>
                <span>{systemReleases.error}</span>
              </div>
            ) : null}
            {systemReleases?.latest_release ? (
              <div className="release-latest-card">
                <div>
                  <span className={`status-pill ${releaseStatusPillClass(systemReleases)}`}>
                    {formatReleaseUpdateStatus(systemReleases, false, null)}
                  </span>
                  <strong>{systemReleases.latest_release.name}</strong>
                  <small>
                    {systemReleases.latest_release.tag} · {systemReleases.latest_release.published_at ?? "sem data"} ·{" "}
                    {systemReleases.latest_release.channel}
                  </small>
                </div>
                <p>{systemReleases.latest_release.changelog_summary || "Sem changelog informado."}</p>
              </div>
            ) : (
              <div className="release-latest-card">
                <div>
                  <span className="status-pill">interno</span>
                  <strong>Status da plataforma ainda não carregado</strong>
                  <small>Use verificar plataforma para consultar o estado publicado.</small>
                </div>
                <p>Em cloud, update da plataforma é rotina administrativa fora da operação do cliente.</p>
              </div>
            )}
          </article>

          <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel release-history-panel">
            <summary className="settings-advanced-summary">
              <span>Releases anteriores</span>
            </summary>
            <div className="release-list">
              {releaseLoading ? <p className="muted">Carregando releases de produção...</p> : null}
              {!releaseLoading && displayedReleaseRows.length === 0 ? (
                <p className="muted">Nenhuma release anterior para listar.</p>
              ) : null}
              {displayedReleaseRows.map((release: any) => (
                <div key={release.tag} className={`release-row ${release.installed ? "installed" : ""}`}>
                  <div>
                    <strong>{release.name}</strong>
                    <span>
                      {release.tag} · {release.published_at ?? "sem data"} ·{" "}
                      {release.installed ? "publicada" : release.channel}
                    </span>
                  </div>
                  <p>{release.changelog_summary || "Sem changelog informado."}</p>
                </div>
              ))}
            </div>
          </details>

          <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel self-update-history">
            <summary className="settings-advanced-summary">
              <span>Histórico da plataforma</span>
              <button
                type="button"
                className="secondary-button compact-summary-action"
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  void loadSelfUpdateHistory();
                }}
              >
                <History size={15} />
                Recarregar
              </button>
            </summary>
            <p className="muted">
              Histórico administrativo do Printora. Update e rollback da plataforma não são operação do usuário final.
            </p>
            {selfUpdateHistory.length === 0 ? <p className="muted">Nenhum update do Printora registrado.</p> : null}
            {selfUpdateHistory.slice(0, 5).map((run: any) => (
              <div key={run.id} className={`update-row ${selfUpdateRunClass(run.status)}`}>
                <div className="update-main">
                  <div>
                    <strong>#{run.id} · {run.target_tag}</strong>
                    <span>
                      {formatSelfUpdateStatus(run.status)} · {formatDateTime(run.created_at)}
                    </span>
                  </div>
                  <FileText size={16} />
                </div>
              </div>
            ))}
          </details>
        </>
      ) : null}
    </>
  );
}

function numberOrNull(value: string): number | null {
  const parsed = Number(value.replace(",", "."));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
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

function latestPreflightForJob(preflights: PrintPreflight[], jobId: number): PrintPreflight | null {
  return preflights.find((item) => item.slicing_job_id === jobId) ?? null;
}

function PreflightSummary({ preflight }: { preflight: PrintPreflight | null }) {
  if (!preflight) return null;
  const labels: Record<PrintPreflight["status"], string> = {
    approved: "preflight aprovado",
    blocked: "preflight bloqueado",
    pending_remote: "preflight remoto pendente",
    failed: "preflight falhou",
  };
  return (
    <div className={`settings-preflight-summary ${preflight.status}`}>
      <small>{labels[preflight.status]} · {preflight.local_metadata.command_count ?? 0} comando(s)</small>
      {preflight.blockers.slice(0, 2).map((blocker) => <small key={blocker}>{blocker}</small>)}
      {preflight.warnings.slice(0, 2).map((warning) => <small key={warning}>{warning}</small>)}
      {preflight.status === "approved" ? <small>{preflight.checklist.slice(0, 3).join(" · ")}</small> : null}
    </div>
  );
}
