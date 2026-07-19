import React from "react";
import { Activity, AlertTriangle, Database, Gauge, Radio, RefreshCw, ShieldCheck, Thermometer, Zap } from "lucide-react";
import { LoadMeter, MonitorBadge, RadialProgress } from "./common";
import { MachinePanel, OperationActions } from "./OperationActions";
import { PrintVisual } from "./PrintPreview";
import { TemperatureMonitor, buildTemperatureSeries } from "./temperature";
import { canTone, formatCanAlert, formatDataState, formatDecision, formatOperationValue, formatOptional, formatPercent, formatTemperature, healthTone } from "./formatters";
import { formatDateTime } from "../../utils/formatters";
import type { CanBusRecord, CanBusRecordComparison, CanBusSummary, HealthResponse } from "./types";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationCapability,
  OperationStatusResponse,
} from "../../types";

type CapabilityStatus = OperationCapability["status"];

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
}) {
  const [capabilityModalStatus, setCapabilityModalStatus] = React.useState<CapabilityStatus | null>(null);
  const temperatureSeries = buildTemperatureSeries(operationStatus?.temperature_history ?? [], operationStatus?.temperatures ?? []);
  const latestCanRecords = canRecords.slice(0, 4);
  const hotend = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bed = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const actions = operationStatus?.actions ?? [];
  const capabilities = operationStatus?.capabilities ?? [];
  const progressLabel = progressSourceLabel(operationStatus?.miscellaneous.progress_source);
  const printFacts = buildPrintFacts(operationStatus);
  const thumbnail = operationStatus?.miscellaneous.thumbnail ?? null;
  const layerPreview = operationStatus?.miscellaneous.layer_preview ?? null;
  const hasThumbnail = hasPrintVisualData(thumbnail);
  const hasLayerPreview = hasPrintVisualData(layerPreview);
  const primaryPrintVisual = hasLayerPreview
    ? { key: "layer", title: "Camada", visual: layerPreview, emptyText: "Sem prévia de camada nesta leitura." }
    : hasThumbnail
      ? { key: "thumbnail", title: "Peça", visual: thumbnail, emptyText: "Sem thumbnail do G-code." }
      : null;
  const sideThumbnail = hasLayerPreview && hasThumbnail ? { title: "Peça", visual: thumbnail, emptyText: "Sem thumbnail do G-code." } : null;
  const hasPrintVisuals = Boolean(primaryPrintVisual);
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
          <div className={`print-monitor-body${hasPrintVisuals ? "" : " is-compact"}`}>
            {primaryPrintVisual ? (
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
              {sideThumbnail ? (
                <div className="print-side-thumbnail">
                  <PrintVisual title={sideThumbnail.title} visual={sideThumbnail.visual} emptyText={sideThumbnail.emptyText} />
                </div>
              ) : null}
              <div className="print-monitor-layout">
                <RadialProgress value={operationStatus?.miscellaneous.progress ?? 0} label={progressLabel} />
                <div className="monitor-facts print-monitor-facts">
                  {printFacts.map((item) => (
                    <React.Fragment key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </React.Fragment>
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

function buildPrintFacts(operationStatus: OperationStatusResponse | null) {
  const miscellaneous = operationStatus?.miscellaneous;
  return [
    { label: "Estado", value: miscellaneous?.print_state || "-" },
    { label: "Camada", value: formatLayer(miscellaneous?.current_layer, miscellaneous?.total_layers) },
    { label: "Tempo", value: formatDuration(miscellaneous?.print_duration) },
    { label: "Restante", value: formatDuration(miscellaneous?.remaining_time) },
    { label: "Conclusão", value: formatEta(miscellaneous?.remaining_time) },
    { label: "Estimativa", value: formatDuration(miscellaneous?.estimated_time) },
    { label: "Arquivo", value: formatPercent(miscellaneous?.file_progress) },
    { label: "Filamento", value: formatFilament(operationStatus) },
    { label: "Slicer", value: formatSlicer(miscellaneous?.slicer, miscellaneous?.slicer_version) },
    { label: "Material", value: miscellaneous?.filament_type || miscellaneous?.filament_name || "-" },
    { label: "G-code", value: miscellaneous?.filename || "-" },
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

function formatFilament(operationStatus: OperationStatusResponse | null) {
  const used = operationStatus?.extruder?.filament_used;
  const total = operationStatus?.miscellaneous.filament_total;
  if (typeof used === "number" && typeof total === "number") return `${formatOperationValue(used, "mm")} / ${formatOperationValue(total, "mm")}`;
  if (typeof used === "number") return formatOperationValue(used, "mm");
  if (typeof total === "number") return formatOperationValue(total, "mm");
  const weight = operationStatus?.miscellaneous.filament_weight_total;
  return typeof weight === "number" ? formatOperationValue(weight, "g") : "-";
}

function formatSlicer(slicer?: string | null, version?: string | null) {
  if (!slicer && !version) return "-";
  return [slicer, version].filter(Boolean).join(" ");
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
