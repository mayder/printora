import React from "react";
import { Activity, AlertTriangle, Database, FileText, FolderOpen, Gauge, History, Radio, RefreshCw, ShieldCheck, Thermometer, Zap } from "lucide-react";
import { LoadMeter, MonitorBadge, RadialProgress } from "./common";
import { MachinePanel, OperationActions } from "./OperationActions";
import { GcodePrintViewer } from "./GcodePrintViewer";
import { PrintVisual } from "./PrintPreview";
import { TemperatureMonitor, buildTemperatureSeries } from "./temperature";
import { canTone, formatCanAlert, formatDataState, formatDecision, formatOperationValue, formatOptional, formatPercent, formatTemperature, healthTone } from "./formatters";
import { formatDateTime } from "../../utils/formatters";
import { apiResponse } from "../../services/http";
import type { CanBusRecord, CanBusRecordComparison, CanBusSummary, HealthResponse } from "./types";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationCapability,
  OperationGcodeFile,
  OperationStatusResponse,
} from "../../types";

type CapabilityStatus = OperationCapability["status"];
type DatabaseTransitionStatus = {
  backend: "sqlite" | "postgresql";
  state: string;
  watermark?: number;
  events?: number;
  changed_tables?: number;
  updated_at?: string | null;
};

const PRIMARY_PRINT_FACT_LABELS = new Set(["Estado", "Camada", "Tempo", "Restante"]);
const MIN_GCODE_VIEWER_AGENT_VERSION = "0.1.30";
const MIN_GCODE_FILES_AGENT_VERSION = "0.1.31";

export function MonitoringDashboard({
  selectedPrinterName,
  operationStatus,
  operationActionHistory,
  operationActionParameters,
  operationActionPreview,
  operationExecutionAttempt,
  operationExecutionHistory,
  operationExecutionPhrase,
  health,
  canSummary,
  canRecords,
  canComparison,
  loading,
  onRefresh,
  onCompareCan,
  onPreviewAction,
  onPreflightAction,
  onExecuteAction,
  onActionParameterChange,
  onExecutionPhraseChange,
  onValidateExecutionGate,
  onOpenGcodeFiles,
}: {
  selectedPrinterName: string;
  operationStatus: OperationStatusResponse | null;
  operationActionHistory: OperationActionPreviewRecord[];
  operationActionParameters: Record<string, Record<string, string>>;
  operationActionPreview: OperationActionPreview | null;
  operationExecutionAttempt: OperationActionExecutionAttempt | null;
  operationExecutionHistory: OperationActionExecutionAttempt[];
  operationExecutionPhrase: string;
  health: HealthResponse | null;
  canSummary: CanBusSummary | null;
  canRecords: CanBusRecord[];
  canComparison: CanBusRecordComparison | null;
  loading: boolean;
  onRefresh: () => void;
  onCompareCan: () => void;
  onPreviewAction: (action: OperationAction, parameters?: Record<string, string | number>) => void | Promise<void>;
  onPreflightAction: (action: OperationAction, parameters?: Record<string, string | number>) => void | Promise<void>;
  onExecuteAction: (action: OperationAction, parameters?: Record<string, string | number>) => void | Promise<void>;
  onActionParameterChange: (actionId: string, parameterName: string, value: string) => void;
  onExecutionPhraseChange: (value: string) => void;
  onValidateExecutionGate: () => void | Promise<void>;
  onOpenGcodeFiles: () => void;
}) {
  const [capabilityModalStatus, setCapabilityModalStatus] = React.useState<CapabilityStatus | null>(null);
  const [databaseTransition, setDatabaseTransition] = React.useState<DatabaseTransitionStatus | null>(null);
  const printBodyRef = React.useRef<HTMLDivElement | null>(null);
  const temperatureSeries = buildTemperatureSeries(operationStatus?.temperature_history ?? [], operationStatus?.temperatures ?? []);
  const latestCanRecords = canRecords.slice(0, 4);
  const hotend = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bed = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const actions = operationStatus?.actions ?? [];
  const capabilities = operationStatus?.capabilities ?? [];
  const printState = operationStatus?.miscellaneous.print_state;
  const progressLabel = progressSourceLabel(operationStatus?.miscellaneous.progress_source);
  const printActive = isActivePrintState(printState);
  const hasMaterialProgress = hasPrintMaterialProgress(operationStatus);
  const idleGcodeFiles = operationStatus?.miscellaneous.gcode_files ?? [];
  const completedPrintFile = completedPrintPreviewFile(operationStatus, idleGcodeFiles);
  const completedPreview = Boolean(!printActive && completedPrintFile);

  React.useEffect(() => {
    let cancelled = false;
    let refreshTimer: number | undefined;
    async function loadDatabaseTransition() {
      try {
        const response = await apiResponse("/api/system/version/internal");
        if (!response.ok || cancelled) return;
        const payload = (await response.json()) as { database_transition?: DatabaseTransitionStatus };
        if (!cancelled && payload.database_transition) {
          setDatabaseTransition(payload.database_transition);
        }
      } catch {
        // This support-only status must not affect the operational dashboard.
      } finally {
        if (!cancelled) {
          refreshTimer = window.setTimeout(() => void loadDatabaseTransition(), 15_000);
        }
      }
    }
    void loadDatabaseTransition();
    return () => {
      cancelled = true;
      if (refreshTimer !== undefined) window.clearTimeout(refreshTimer);
    };
  }, []);
  const gcodeFilename = printActive
    ? (operationStatus?.miscellaneous.filename ?? "").trim()
    : ((operationStatus?.miscellaneous.filename ?? "").trim() || operationGcodeFilePath(completedPrintFile));
  const canUseGcodeViewer = Boolean(
    operationStatus?.printer_id &&
      gcodeFilename &&
      supportsGcodeCache(operationStatus?.agent?.version),
  );
  const showPrintPreview = printActive || (completedPreview && canUseGcodeViewer);
  const viewerTotalLayers = operationStatus?.miscellaneous.total_layers ?? completedPrintFile?.layer_count ?? null;
  const viewerCurrentLayer = completedPreview ? viewerTotalLayers : hasMaterialProgress ? operationStatus?.miscellaneous.current_layer : null;
  const viewerProgress = completedPreview ? 1 : hasMaterialProgress ? operationStatus?.miscellaneous.progress ?? 0 : 0;
  const viewerFilePosition = completedPreview ? null : hasMaterialProgress ? operationStatus?.miscellaneous.file_position : null;
  const printFacts = buildPrintFacts(operationStatus, hasMaterialProgress, completedPrintFile, gcodeFilename, completedPreview);
  const primaryPrintFacts = printFacts.filter((item) => PRIMARY_PRINT_FACT_LABELS.has(item.label));
  const secondaryPrintFacts = printFacts.filter((item) => !PRIMARY_PRINT_FACT_LABELS.has(item.label));
  const thumbnail = operationStatus?.miscellaneous.thumbnail ?? null;
  const layerPreview = operationStatus?.miscellaneous.layer_preview ?? null;
  const hasThumbnail = hasPrintVisualData(thumbnail);
  const hasLayerPreview = hasPrintVisualData(layerPreview);
  const primaryPrintVisual = hasLayerPreview
    ? { key: "layer", title: "Camada", visual: layerPreview, emptyText: "Sem prévia de camada nesta leitura." }
    : hasThumbnail
      ? { key: "thumbnail", title: "Peça", visual: thumbnail, emptyText: "Sem thumbnail do G-code." }
      : null;
  const sideThumbnail = hasThumbnail && (canUseGcodeViewer || hasLayerPreview) ? { title: "Peça", visual: thumbnail, emptyText: "Sem thumbnail do G-code." } : null;
  const hasPrintVisuals = Boolean(canUseGcodeViewer || primaryPrintVisual);
  const canUseIdleGcodeFiles = supportsGcodeFiles(operationStatus?.agent?.version);
  const liveUnavailable = operationStatus?.data_state === "offline";
  const operationNotice = liveUnavailable ? formatOperationNotice(operationStatus) : "";
  const selectedCapabilities = capabilityModalStatus ? capabilities.filter((capability) => capability.status === capabilityModalStatus) : [];
  const findAction = (actionId: string) => actions.find((action) => action.id === actionId) ?? null;
  const currentOperationValue = (actionId: string, parameterName: string, fallback: string | number) => operationActionParameters[actionId]?.[parameterName] ?? String(fallback);
  const executeActionById = (actionId: string, parameters: Record<string, string | number> = {}) => {
    const action = findAction(actionId);
    if (!action) return;
    Object.entries(parameters).forEach(([name, value]) => onActionParameterChange(actionId, name, String(value)));
    void onExecuteAction(action, parameters);
  };

  React.useEffect(() => {
    const printBody = printBodyRef.current;
    if (!showPrintPreview) {
      printBody?.style.removeProperty("--print-viewer-target-height");
      return undefined;
    }
    if (!printBody || typeof ResizeObserver === "undefined") return undefined;
    const sideStack = printBody.querySelector<HTMLElement>(".print-side-stack");
    if (!sideStack) return undefined;
    const sideBySideQuery = window.matchMedia("(min-width: 1321px)");
    const syncViewerHeight = () => {
      if (!sideBySideQuery.matches) {
        printBody.style.removeProperty("--print-viewer-target-height");
        return;
      }
      const measuredHeight = Math.ceil(sideStack.getBoundingClientRect().height);
      if (measuredHeight > 0) {
        printBody.style.setProperty("--print-viewer-target-height", `${measuredHeight}px`);
      }
    };
    const observer = new ResizeObserver(syncViewerHeight);
    observer.observe(sideStack);
    observer.observe(printBody);
    sideBySideQuery.addEventListener("change", syncViewerHeight);
    window.requestAnimationFrame(syncViewerHeight);
    return () => {
      observer.disconnect();
      sideBySideQuery.removeEventListener("change", syncViewerHeight);
      printBody.style.removeProperty("--print-viewer-target-height");
    };
  }, [showPrintPreview]);

  return (
    <article className="panel wide panel-section panel-monitoring monitoring-dashboard">
      <div className="panel-heading monitoring-heading">
        <div>
          <h2>Operação em tempo real</h2>
          <p className="muted">{operationStatus?.summary ?? "Aguardando leitura da impressora selecionada."}</p>
        </div>
        <div className="panel-actions">
          <span className="live-pill">Atualiza sozinho</span>
          <button type="button" className="secondary-button" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
            Atualizar agora
          </button>
        </div>
      </div>

      <div className="monitor-status-strip">
        <MonitorBadge icon={Radio} label="Impressora" value={selectedPrinterName} tone={operationStatus?.connected ? "ok" : "danger"} />
        <MonitorBadge icon={Radio} label="Moonraker" value={operationStatus?.connected ? "online" : "offline"} tone={operationStatus?.connected ? "ok" : "danger"} />
        <MonitorBadge icon={Gauge} label="Estado" value={operationStatus?.miscellaneous.print_state ?? "-"} tone={operationStatus?.connected ? "ok" : "warning"} />
        <MonitorBadge icon={AlertTriangle} label="Risco" value={formatDecision(health?.decision)} tone={healthTone(health?.decision)} />
        <MonitorBadge icon={ShieldCheck} label="Modo" value={operationStatus?.safe_mode ?? "read only"} />
        <MonitorBadge icon={Zap} label="Comandos" value={operationStatus?.can_send_commands ? "habilitados" : "bloqueados"} tone={operationStatus?.can_send_commands ? "warning" : "ok"} />
        <MonitorBadge icon={Thermometer} label="Hotend" value={formatTemperature(hotend?.temperature)} />
        <MonitorBadge icon={Thermometer} label="Mesa" value={formatTemperature(bed?.temperature)} />
        <MonitorBadge icon={Database} label="Origem" value={formatDataState(operationStatus?.data_state)} />
      </div>

      {databaseTransition ? (
        <section className="monitor-card database-transition-card" aria-label="Progresso da transição de banco">
          <div className="monitor-card-title">
            <Database size={18} />
            <h3>Transição de banco</h3>
          </div>
          <div className="monitor-status-strip">
            <MonitorBadge icon={Database} label="Backend" value={databaseTransition.backend} tone="ok" />
            <MonitorBadge icon={Activity} label="Estado" value={databaseTransition.state} />
            <MonitorBadge icon={Gauge} label="Watermark" value={String(databaseTransition.watermark ?? 0)} />
            <MonitorBadge
              icon={FileText}
              label="Eventos"
              value={String(databaseTransition.events ?? databaseTransition.changed_tables ?? 0)}
            />
          </div>
        </section>
      ) : null}

      {liveUnavailable ? (
        <div className="monitor-note monitor-live-unavailable">
          <AlertTriangle size={17} />
          <span>{operationNotice}</span>
        </div>
      ) : null}
      {operationStatus?.data_state === "fixture" ? (
        <div className="monitor-note">
          <Database size={17} />
          <span>Dados simulados para validar layout com a impressora desligada. Nenhum endpoint da impressora foi chamado.</span>
        </div>
      ) : null}
      {operationStatus?.data_state === "last_snapshot" ? (
        <div className="monitor-note">
          <Database size={17} />
          <span>
            Último estado conhecido: snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {formatDateTime(operationStatus.last_snapshot?.created_at)}.
          </span>
        </div>
      ) : null}

      <div className="monitor-operation-layout">
        <section className="monitor-card print-monitor-card operation-print-card">
          <div className="monitor-card-title">
            <Gauge size={18} />
            <h3>Impressão</h3>
          </div>
          <div ref={printBodyRef} className={showPrintPreview ? `print-monitor-body${hasPrintVisuals ? "" : " is-compact"}` : "print-monitor-body is-idle-files"}>
            {showPrintPreview ? (
              <>
                {canUseGcodeViewer ? (
                  <div className="print-primary-visual">
                    <GcodePrintViewer
                      printerId={operationStatus!.printer_id}
                      filename={gcodeFilename}
                      filePosition={viewerFilePosition}
                      currentLayer={viewerCurrentLayer}
                      totalLayers={viewerTotalLayers}
                      printState={completedPreview ? "complete" : printState}
                      progress={viewerProgress}
                      buildVolume={operationStatus?.toolhead}
                      nozzleDiameter={operationStatus?.miscellaneous.nozzle_diameter}
                    />
                  </div>
                ) : primaryPrintVisual ? (
                  <div className={`print-primary-visual ${primaryPrintVisual.key === "thumbnail" ? "is-thumbnail-only" : ""}`}>
                    <PrintVisual title={primaryPrintVisual.title} visual={primaryPrintVisual.visual} emptyText={primaryPrintVisual.emptyText} />
                  </div>
                ) : (
                  <div className="print-compact-state">
                    <Database size={18} />
                    <div>
                      <strong>{liveUnavailable ? "Sem leitura ao vivo" : "Sem prévia carregada"}</strong>
                      <span>{liveUnavailable ? operationNotice : "A prévia aparece quando o agente entrega thumbnail, camada ou cena do G-code."}</span>
                    </div>
                  </div>
                )}
                <div className="print-side-stack">
                  <div className={`print-side-overview${sideThumbnail ? "" : " no-thumbnail"}`}>
                    {sideThumbnail ? (
                      <div className="print-side-thumbnail">
                        <PrintVisual title={sideThumbnail.title} visual={sideThumbnail.visual} emptyText={sideThumbnail.emptyText} />
                      </div>
                    ) : null}
                    <div className="print-side-progress">
                      <RadialProgress value={viewerProgress} label={completedPreview ? "display" : progressLabel} />
                    </div>
                  </div>
                  <div className="print-side-facts-card">
                    <div className="print-side-core-facts">
                      {primaryPrintFacts.map((item) => (
                        <div key={item.label} className="print-side-core-fact">
                          <span>{item.label}</span>
                          <strong title={item.value}>{item.value}</strong>
                        </div>
                      ))}
                    </div>
                    <div className="print-side-meta-list">
                      {secondaryPrintFacts.map((item) => (
                        <div key={item.label} className="print-side-meta-row">
                          <span>{item.label}</span>
                          <strong title={item.value}>{item.value}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                  <MachinePanel
                    disabled={loading}
                    status={operationStatus}
                    setVelocityLimit={findAction("set_velocity_limit")}
                    currentValue={currentOperationValue}
                    onChange={onActionParameterChange}
                    onExecute={executeActionById}
                  />
                </div>
              </>
            ) : (
              <>
                <IdleGcodeFilesPanel
                  files={idleGcodeFiles}
                  operationStatus={operationStatus}
                  liveUnavailable={liveUnavailable}
                  agentSupportsFiles={canUseIdleGcodeFiles}
                  onOpenGcodeFiles={onOpenGcodeFiles}
                />
                <div className="print-idle-side">
                  <MachinePanel
                    disabled={loading}
                    status={operationStatus}
                    setVelocityLimit={findAction("set_velocity_limit")}
                    currentValue={currentOperationValue}
                    onChange={onActionParameterChange}
                    onExecute={executeActionById}
                  />
                </div>
              </>
            )}
          </div>
        </section>

        <section className="monitor-card temperature-monitor-card">
          <div className="monitor-card-title">
            <Thermometer size={18} />
            <h3>Temperaturas</h3>
          </div>
          <TemperatureMonitor
            temperatures={operationStatus?.temperatures ?? []}
            series={temperatureSeries}
            actions={actions}
            loading={loading}
            onParameterChange={onActionParameterChange}
            onExecute={onExecuteAction}
          />
        </section>
      </div>

      <div className="monitor-grid">
        <section className="monitor-card monitor-card-wide operation-command-center">
          <div className="monitor-card-title">
            <ShieldCheck size={18} />
            <h3>Ações protegidas</h3>
          </div>
          <OperationActions
            actions={actions}
            capabilities={capabilities}
            operationStatus={operationStatus}
            values={operationActionParameters}
            preview={operationActionPreview}
            executionAttempt={operationExecutionAttempt}
            confirmationPhrase={operationExecutionPhrase}
            loading={loading}
            canSendCommands={Boolean(operationStatus?.can_send_commands)}
            onPreview={onPreviewAction}
            onPreflight={onPreflightAction}
            onExecute={onExecuteAction}
            onParameterChange={onActionParameterChange}
            onPhraseChange={onExecutionPhraseChange}
            onValidateExecutionGate={onValidateExecutionGate}
          />
        </section>

        <section className="monitor-card operation-capability-summary-card">
          <CapabilitySummary capabilities={capabilities} actions={actions} canSendCommands={Boolean(operationStatus?.can_send_commands)} onOpen={setCapabilityModalStatus} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Activity size={18} />
            <h3>Sistema</h3>
          </div>
          <div className="load-list">
            {operationStatus?.system_loads.length ? null : <p className="muted">Sem métricas do host nesta leitura.</p>}
            {operationStatus?.system_loads.map((metric) => (
              <LoadMeter key={metric.label} metric={metric} />
            ))}
          </div>
        </section>

        <section className="monitor-card monitor-card-wide">
          <div className="monitor-card-title">
            <Radio size={18} />
            <h3>CAN</h3>
          </div>
          <div className="can-monitor-header">
            <MonitorBadge label="Estado" value={formatCanAlert(canSummary?.overall_alert ?? latestCanRecords[0]?.alert_level ?? "ok")} tone={canTone(canSummary?.overall_alert ?? latestCanRecords[0]?.alert_level)} />
            <MonitorBadge label="OK" value={String(canSummary?.counts.ok ?? 0)} />
            <MonitorBadge label="Atenção" value={String(canSummary?.counts.monitorar ?? 0)} tone="warning" />
            <MonitorBadge label="Problemas" value={String(canSummary?.counts.problema ?? 0)} tone="danger" />
            <button type="button" className="secondary-button compact" onClick={onCompareCan} disabled={loading || canRecords.length < 2}>
              Comparar leituras
            </button>
          </div>
          {canSummary?.data_state === "no_data" || latestCanRecords.length === 0 ? (
            <p className="muted">Sem leituras CAN registradas para exibir evolução.</p>
          ) : null}
          {canComparison ? (
            <div className={`monitor-can-comparison ${canComparison.alert_level}`}>
              <strong>Última comparação</strong>
              <span>
                {canComparison.interface_name}: rx {formatOptional(canComparison.delta_rx_error)} · tx {formatOptional(canComparison.delta_tx_error)} · retries {formatOptional(canComparison.delta_tx_retries)}
              </span>
              <small>{canComparison.diagnosis}</small>
            </div>
          ) : null}
          <div className="can-monitor-list">
            {latestCanRecords.map((record) => (
              <div key={record.id} className={`can-monitor-row ${record.alert_level}`}>
                <strong>{record.interface_name}</strong>
                <span>rx {record.rx_error} · tx {record.tx_error} · retries {record.tx_retries}</span>
                <small>{record.recorded_at}</small>
                <small>{record.diagnosis}</small>
              </div>
            ))}
          </div>
        </section>
      </div>
      {capabilityModalStatus ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Detalhes dos comandos ${capabilityStatusLabel(capabilityModalStatus)}`}>
          <div className="modal-card operation-capability-modal-card">
            <div className="modal-header">
              <div>
                <h2>Comandos {capabilityStatusLabel(capabilityModalStatus)}</h2>
                <p>{selectedCapabilities.length} item(ns) nesta classificação.</p>
              </div>
              <button type="button" className="secondary-button compact" onClick={() => setCapabilityModalStatus(null)}>
                Fechar
              </button>
            </div>
            <div className="operation-capability-modal-list">
              {selectedCapabilities.map((capability) => (
                <div key={capability.action_id} className={`operation-capability-modal-row ${capability.status}`}>
                  <strong>{formatCapabilityActionLabel(capability, actions)}</strong>
                  <code>{capability.action_id}</code>
                  <span>{capability.reason}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </article>
  );
}

function CapabilitySummary({
  capabilities,
  actions,
  canSendCommands,
  onOpen,
}: {
  capabilities: OperationCapability[];
  actions: OperationAction[];
  canSendCommands: boolean;
  onOpen: (status: CapabilityStatus) => void;
}) {
  const supportedCount = capabilities.filter((capability) => capability.status === "supported").length;
  const blockedCount = capabilities.filter((capability) => capability.status === "blocked").length;
  const unknownCount = capabilities.filter((capability) => capability.status === "unknown").length;

  return (
    <div className="operation-actions-summary">
      <div>
        <strong>Comandos em modo protegido</strong>
        <span>{canSendCommands ? "Execução depende de confirmação." : "Prévia e validação disponíveis. Execução real bloqueada."}</span>
      </div>
      <div className="operation-capability-chips" aria-label="Resumo de compatibilidade">
        <CapabilityChip status="supported" count={supportedCount} label="suportadas" onOpen={onOpen} />
        <CapabilityChip status="blocked" count={blockedCount} label="bloqueadas" onOpen={onOpen} />
        <CapabilityChip status="unknown" count={unknownCount} label="indefinidas" onOpen={onOpen} />
      </div>
    </div>
  );
}

function CapabilityChip({
  status,
  count,
  label,
  onOpen,
}: {
  status: CapabilityStatus;
  count: number;
  label: string;
  onOpen: (status: CapabilityStatus) => void;
}) {
  const disabled = count === 0;
  return (
    <button
      type="button"
      className={`operation-capability-chip ${status}`}
      disabled={disabled}
      onClick={() => onOpen(status)}
      aria-label={disabled ? `${count} ${label}` : `Ver ${count} comandos ${label}`}
    >
      {count} {label}
    </button>
  );
}

function IdleGcodeFilesPanel({
  files,
  operationStatus,
  liveUnavailable,
  agentSupportsFiles,
  onOpenGcodeFiles,
}: {
  files: OperationGcodeFile[];
  operationStatus: OperationStatusResponse | null;
  liveUnavailable: boolean;
  agentSupportsFiles: boolean;
  onOpenGcodeFiles: () => void;
}) {
  const visibleFiles = recentGcodeFiles(files).slice(0, 4);
  const reliableLastJob = lastReliablePrintFile(files);
  const lastJob = reliableLastJob ?? (isCompletedPrintState(operationStatus?.miscellaneous.print_state) ? recentGcodeFiles(files)[0] ?? null : null);
  const state = idleOperationState(operationStatus, liveUnavailable);
  return (
    <div className="print-idle-panel">
      <div className="print-idle-header">
        <div>
          <strong>
            <state.icon size={17} />
            {state.title}
          </strong>
          <span>{state.detail}</span>
        </div>
        <button type="button" className="secondary-button compact" onClick={onOpenGcodeFiles}>
          <FolderOpen size={15} />
          Abrir arquivos
        </button>
      </div>

      {lastJob ? (
        <div className="print-idle-last-job">
          <div>
            <History size={16} />
            <span>{reliableLastJob ? "Último trabalho confiável" : "Última impressão detectada"}</span>
          </div>
          <strong title={lastJob.path ?? lastJob.filename}>{displayGcodeFileName(lastJob.filename)}</strong>
          <dl>
            <div>
              <dt>Final</dt>
              <dd>{formatUnixDate(lastJob.print_end_time ?? lastJob.modified)}</dd>
            </div>
            <div>
              <dt>Duração</dt>
              <dd>{formatDuration(lastJob.last_print_duration ?? lastJob.estimated_time)}</dd>
            </div>
            <div>
              <dt>Slicer</dt>
              <dd>{formatSlicer(lastJob.slicer, lastJob.slicer_version)}</dd>
            </div>
          </dl>
        </div>
      ) : (
        <div className="print-idle-empty">
          <Database size={18} />
          <div>
            <strong>{liveUnavailable ? "Sem leitura ao vivo" : agentSupportsFiles ? "Sem histórico confiável" : "Agente precisa atualizar"}</strong>
            <span>
              {liveUnavailable
                ? "A lista aparece quando o agente reconectar ao Moonraker."
                : agentSupportsFiles
                  ? "A Operação não encontrou um trabalho recente com fim ou duração confiável."
                  : "A lista de arquivos na Operação depende do agente 0.1.31 ou superior."}
            </span>
          </div>
        </div>
      )}

      {visibleFiles.length ? (
        <div className="print-idle-file-strip" aria-label="Arquivos G-code recentes">
          {visibleFiles.map((file) => (
            <button key={`${file.path ?? file.filename}-${file.modified ?? ""}`} type="button" className="print-idle-file-card" title={file.path ?? file.filename} onClick={onOpenGcodeFiles}>
              <FileText size={16} />
              <strong>{displayGcodeFileName(file.filename)}</strong>
              <span>{[formatUnixDate(file.modified), formatBytes(file.size), formatDuration(file.estimated_time)].filter((item) => item !== "-").join(" · ") || "Metadados pendentes"}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function recentGcodeFiles(files: OperationGcodeFile[]) {
  return [...files].sort((left, right) => gcodeFileSortTimestamp(right) - gcodeFileSortTimestamp(left));
}

function lastReliablePrintFile(files: OperationGcodeFile[]) {
  return recentGcodeFiles(files).find((file) => Boolean(file.print_end_time || file.print_start_time || file.last_print_duration)) ?? null;
}

function completedPrintPreviewFile(operationStatus: OperationStatusResponse | null, files: OperationGcodeFile[]): OperationGcodeFile | null {
  if (!isCompletedPrintState(operationStatus?.miscellaneous.print_state)) return null;
  const filename = (operationStatus?.miscellaneous.filename ?? "").trim();
  if (filename) {
    return files.find((file) => sameGcodeFile(file, filename)) ?? { filename, path: filename };
  }
  return lastReliablePrintFile(files) ?? recentGcodeFiles(files)[0] ?? null;
}

function operationGcodeFilePath(file?: OperationGcodeFile | null) {
  return (file?.path ?? file?.filename ?? "").trim();
}

function sameGcodeFile(file: OperationGcodeFile, requested: string) {
  const candidates = [file.path, file.filename].filter((value): value is string => Boolean(value));
  return candidates.some((candidate) => sameGcodePath(candidate, requested));
}

function sameGcodePath(left: string, right: string) {
  const normalizedLeft = normalizeGcodePath(left);
  const normalizedRight = normalizeGcodePath(right);
  return normalizedLeft === normalizedRight || gcodeBasename(normalizedLeft) === gcodeBasename(normalizedRight);
}

function normalizeGcodePath(value: string) {
  return value.trim().replace(/^\/+/, "").toLowerCase();
}

function gcodeBasename(value: string) {
  return value.split("/").filter(Boolean).at(-1) ?? value;
}

function gcodeFileSortTimestamp(file: OperationGcodeFile) {
  return numericValue(file.print_end_time) ?? numericValue(file.print_start_time) ?? numericValue(file.modified) ?? 0;
}

function idleOperationState(operationStatus: OperationStatusResponse | null, liveUnavailable: boolean) {
  const state = (operationStatus?.miscellaneous.print_state ?? "").trim().toLowerCase();
  if (!operationStatus) {
    return { icon: Database, title: "Sem leitura", detail: "Aguardando a primeira leitura operacional da impressora." };
  }
  if (liveUnavailable) {
    return { icon: AlertTriangle, title: "Sem leitura ao vivo", detail: "A tela mantém apenas atalhos seguros até o agente reconectar." };
  }
  if (state === "error") {
    return { icon: AlertTriangle, title: "Impressão com erro", detail: operationStatus.miscellaneous.message || "Verifique Moonraker/Klipper antes de iniciar outro trabalho." };
  }
  if (state === "complete") {
    return { icon: ShieldCheck, title: "Impressão concluída", detail: "Operação em espera, mantendo a última impressão quando disponível." };
  }
  if (state === "cancelled" || state === "canceled") {
    return { icon: AlertTriangle, title: "Impressão cancelada", detail: "Operação em espera; confira o arquivo antes de repetir a impressão." };
  }
  return { icon: ShieldCheck, title: "Impressora em espera", detail: "Sem impressão ativa. Gerenciamento completo fica em Arquivos G-code." };
}

function capabilityStatusLabel(status: CapabilityStatus) {
  if (status === "supported") return "suportados";
  if (status === "blocked") return "bloqueados";
  return "indefinidos";
}

function formatCapabilityActionLabel(capability: OperationCapability, actions: OperationAction[]) {
  return actions.find((action) => action.id === capability.action_id)?.label ?? capability.action_id.replaceAll("_", " ");
}

function formatLayer(current?: number | null, total?: number | null) {
  if (typeof current === "number" && typeof total === "number") return `${current} / ${total}`;
  if (typeof current === "number") return `${current} / -`;
  if (typeof total === "number") return `- / ${total}`;
  return "-";
}

function hasPrintVisualData(visual: OperationStatusResponse["miscellaneous"]["thumbnail"]) {
  return Boolean(visual?.data_uri || visual?.scene?.kind === "gcode_layer_scene");
}

function isActivePrintState(state?: string | null) {
  const normalized = (state ?? "").trim().toLowerCase();
  return Boolean(normalized && !["standby", "complete", "cancelled", "canceled", "error"].includes(normalized));
}

function isCompletedPrintState(state?: string | null) {
  return (state ?? "").trim().toLowerCase() === "complete";
}

function hasPrintMaterialProgress(operationStatus: OperationStatusResponse | null) {
  if (!isActivePrintState(operationStatus?.miscellaneous.print_state)) return true;
  const filamentUsed = numericValue(operationStatus?.extruder?.filament_used);
  const displayProgress = normalizedProgressValue(operationStatus?.miscellaneous.progress);
  const fileProgress = normalizedProgressValue(operationStatus?.miscellaneous.file_progress);
  if (filamentUsed !== null) {
    if (filamentUsed > 0.01) return true;
    return Boolean(displayProgress !== null && displayProgress > 0.001);
  }
  if (displayProgress !== null && displayProgress > 0.001) return true;
  if (fileProgress !== null && fileProgress > 0.02) return !looksLikePreprintMessage(operationStatus?.miscellaneous.message);
  return false;
}

function numericValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function normalizedProgressValue(value: unknown) {
  const number = numericValue(value);
  if (number === null) return null;
  if (number < 0) return 0;
  if (number <= 1) return number;
  if (number <= 100) return number / 100;
  return 1;
}

function looksLikePreprintMessage(value?: string | null) {
  const normalized = (value ?? "").trim().toLowerCase().replaceAll("-", "_").replaceAll(" ", "_");
  return ["qgl", "quad_gantry_level", "bed_mesh", "homing", "g28", "z_tilt", "calibrate_z"].some((token) => normalized.includes(token));
}

function buildPrintFacts(
  operationStatus: OperationStatusResponse | null,
  hasMaterialProgress = true,
  completedFile: OperationGcodeFile | null = null,
  filenameOverride = "",
  completedPreview = false,
) {
  const miscellaneous = operationStatus?.miscellaneous;
  const totalLayers = miscellaneous?.total_layers ?? completedFile?.layer_count;
  const currentLayer = completedPreview ? totalLayers ?? null : hasMaterialProgress ? miscellaneous?.current_layer : null;
  const printDuration = miscellaneous?.print_duration ?? completedFile?.last_print_duration;
  const estimatedTime = miscellaneous?.estimated_time ?? completedFile?.estimated_time;
  const remainingTime = completedPreview ? null : miscellaneous?.remaining_time;
  return [
    { label: "Estado", value: miscellaneous?.print_state || "-" },
    { label: "Camada", value: formatLayer(currentLayer, totalLayers) },
    { label: "Tempo", value: formatDuration(printDuration) },
    { label: "Restante", value: formatDuration(remainingTime) },
    { label: "Conclusão", value: completedPreview ? formatUnixDate(completedFile?.print_end_time) : formatEta(remainingTime) },
    { label: "Estimativa", value: formatDuration(estimatedTime) },
    { label: "Arquivo", value: completedPreview ? "100%" : formatPercent(miscellaneous?.file_progress) },
    { label: "Filamento", value: formatFilament(operationStatus, completedFile, completedPreview) },
    { label: "Slicer", value: formatSlicer(miscellaneous?.slicer ?? completedFile?.slicer, miscellaneous?.slicer_version ?? completedFile?.slicer_version) },
    { label: "Material", value: miscellaneous?.filament_type || miscellaneous?.filament_name || completedFile?.filament_type || completedFile?.filament_name || "-" },
    { label: "G-code", value: filenameOverride || miscellaneous?.filename || completedFile?.path || completedFile?.filename || "-" },
    { label: "Mensagem", value: miscellaneous?.message || "-" },
  ];
}

function formatOperationNotice(operationStatus: OperationStatusResponse | null) {
  const error = (operationStatus?.error ?? "").toLowerCase();
  if (error.includes("timeout") || error.includes("sem resposta")) {
    return "Agente sem resposta nesta leitura. A tela fica compacta até a próxima leitura ao vivo.";
  }
  return "Sem leitura ao vivo do agente ou Moonraker no momento. As ações reais permanecem bloqueadas até reconectar.";
}

function progressSourceLabel(source?: string | null) {
  if (source === "display_status") return "display";
  if (source === "virtual_sdcard") return "arquivo";
  return "progresso";
}

function supportsGcodeCache(version?: string | null) {
  return compareVersion(version, MIN_GCODE_VIEWER_AGENT_VERSION) >= 0;
}

function supportsGcodeFiles(version?: string | null) {
  return compareVersion(version, MIN_GCODE_FILES_AGENT_VERSION) >= 0;
}

function compareVersion(current?: string | null, minimum?: string | null) {
  const left = parseVersion(current);
  const right = parseVersion(minimum);
  if (!left || !right) return -1;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    const diff = (left[index] ?? 0) - (right[index] ?? 0);
    if (diff !== 0) return diff > 0 ? 1 : -1;
  }
  return 0;
}

function parseVersion(value?: string | null) {
  const cleaned = (value ?? "").trim().replace(/^v/i, "");
  if (!cleaned) return null;
  const parts = cleaned.split(".").map((part) => Number.parseInt(part, 10));
  return parts.every((part) => Number.isFinite(part)) ? parts : null;
}

function formatFilament(operationStatus: OperationStatusResponse | null, completedFile: OperationGcodeFile | null = null, completedPreview = false) {
  const used = completedPreview ? null : operationStatus?.extruder?.filament_used;
  const total = operationStatus?.miscellaneous.filament_total ?? completedFile?.filament_total;
  if (typeof used === "number" && typeof total === "number") return `${formatOperationValue(used, "mm")} / ${formatOperationValue(total, "mm")}`;
  if (typeof used === "number") return formatOperationValue(used, "mm");
  if (typeof total === "number") return formatOperationValue(total, "mm");
  const weight = operationStatus?.miscellaneous.filament_weight_total ?? completedFile?.filament_weight_total;
  return typeof weight === "number" ? formatOperationValue(weight, "g") : "-";
}

function formatSlicer(slicer?: string | null, version?: string | null) {
  if (!slicer && !version) return "-";
  return [slicer, version].filter(Boolean).join(" ");
}

function displayGcodeFileName(filename?: string | null) {
  const clean = (filename ?? "").trim();
  if (!clean) return "-";
  return clean.split("/").filter(Boolean).pop() ?? clean;
}

function formatUnixDate(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "-";
  const timestamp = value > 1000000000000 ? value : value * 1000;
  return new Date(timestamp).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatBytes(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) return "-";
  if (value < 1024) return `${Math.round(value)} B`;
  const units = ["KB", "MB", "GB"];
  let size = value / 1024;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size >= 10 ? size.toFixed(1) : size.toFixed(2)} ${units[unitIndex]}`;
}

function formatMillimeters(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "-";
  return `${value >= 10 ? value.toFixed(1) : value.toFixed(2)} mm`;
}

function formatGcodeFileFilament(file: OperationGcodeFile) {
  const material = file.filament_type || file.filament_name || "";
  const weight = typeof file.filament_weight_total === "number" ? formatOperationValue(file.filament_weight_total, "g") : "";
  const length = typeof file.filament_total === "number" ? formatOperationValue(file.filament_total, "mm") : "";
  return [material, weight || length].filter(Boolean).join(" · ") || "-";
}

function formatEta(seconds?: number | null) {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) return "-";
  return new Date(Date.now() + seconds * 1000).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(seconds?: number | null) {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) return "-";
  const totalSeconds = Math.round(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  return `${minutes}m ${String(remainingSeconds).padStart(2, "0")}s`;
}
