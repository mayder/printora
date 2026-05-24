import React from "react";
import { Activity, AlertTriangle, Crosshair, Database, Gauge, Radio, RefreshCw, ShieldCheck, SlidersHorizontal, Thermometer, Wind, Zap } from "lucide-react";
import { OperationActionParameterFields } from "./components/common/OperationActionParameterFields";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationCapability,
  OperationFan,
  OperationMetric,
  OperationStatusResponse,
  OperationTemperature,
  OperationTemperatureHistoryRow,
} from "./types";

type HealthResponse = {
  decision: "ok_para_imprimir" | "monitorar" | "nao_imprimir";
  counts: Record<string, number>;
};

type CanBusSummary = {
  data_state: "manual_records" | "no_data";
  overall_alert: "ok" | "monitorar" | "problema";
  counts: Record<string, number>;
};

type CanBusRecord = {
  id: number;
  interface_name: string;
  recorded_at: string;
  rx_error: number;
  tx_error: number;
  tx_retries: number;
  alert_level: "ok" | "monitorar" | "problema";
  diagnosis: string;
};

type CanBusRecordComparison = {
  before_record_id: number;
  after_record_id: number;
  interface_name: string;
  delta_rx_error: number | null;
  delta_tx_error: number | null;
  delta_tx_retries: number | null;
  alert_level: "ok" | "monitorar" | "problema";
  diagnosis: string;
};

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
  onLoadOfflineFixture,
  onCompareCan,
  onPreviewAction,
  onPreflightAction,
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
  onLoadOfflineFixture: () => void | Promise<void>;
  onCompareCan: () => void;
  onPreviewAction: (action: OperationAction) => void | Promise<void>;
  onPreflightAction: (action: OperationAction) => void | Promise<void>;
  onActionParameterChange: (actionId: string, parameterName: string, value: string) => void;
  onExecutionPhraseChange: (value: string) => void;
  onValidateExecutionGate: () => void | Promise<void>;
}) {
  const temperatureSeries = buildTemperatureSeries(operationStatus?.temperature_history ?? [], operationStatus?.temperatures ?? []);
  const fans = operationStatus?.miscellaneous.fans ?? [];
  const latestCanRecords = canRecords.slice(0, 4);
  const hotend = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bed = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const actions = operationStatus?.actions ?? [];
  const capabilities = operationStatus?.capabilities ?? [];
  const toolheadFacts = buildToolheadFacts(operationStatus);
  const extruderFacts = buildExtruderFacts(operationStatus);

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
            <RefreshCw size={15} />
            Atualizar agora
          </button>
          <button type="button" className="secondary-button" onClick={() => void onLoadOfflineFixture()} disabled={loading}>
            <Database size={15} />
            Exemplo offline
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

      {operationStatus?.data_state === "offline" ? (
        <div className="monitor-warning">
          <AlertTriangle size={17} />
          <span>{operationStatus.error ?? "Sem leitura ao vivo. Verifique se a impressora está ligada e na rede."}</span>
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
            Último estado conhecido: snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
          </span>
        </div>
      ) : null}

      <div className="monitor-grid">
        <section className="monitor-card monitor-card-wide">
          <div className="monitor-card-title">
            <Thermometer size={18} />
            <h3>Temperaturas</h3>
          </div>
          <TemperatureMonitor temperatures={operationStatus?.temperatures ?? []} series={temperatureSeries} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Crosshair size={18} />
            <h3>Toolhead</h3>
          </div>
          <FactGrid items={toolheadFacts} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <SlidersHorizontal size={18} />
            <h3>Extrusor</h3>
          </div>
          <FactGrid items={extruderFacts} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Gauge size={18} />
            <h3>Impressão</h3>
          </div>
          <RadialProgress value={operationStatus?.miscellaneous.progress ?? 0} />
          <div className="monitor-facts">
            <span>Arquivo</span>
            <strong>{operationStatus?.miscellaneous.filename || "-"}</strong>
            <span>Mensagem</span>
            <strong>{operationStatus?.miscellaneous.message || "-"}</strong>
          </div>
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

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Wind size={18} />
            <h3>Fans</h3>
          </div>
          <div className="fan-monitor-list">
            {fans.length === 0 ? <p className="muted">Nenhum fan retornado pelo Moonraker.</p> : null}
            {fans.map((fan) => (
              <LoadMeter
                key={fan.name}
                metric={{
                  label: fan.name,
                  value: typeof fan.speed === "number" ? fan.speed * 100 : null,
                  unit: "%",
                }}
                detail={`RPM ${fan.rpm ?? "-"}`}
              />
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

        <section className="monitor-card monitor-card-wide operation-command-center">
          <div className="monitor-card-title">
            <ShieldCheck size={18} />
            <h3>Ações protegidas</h3>
          </div>
          <OperationActions
            actions={actions}
            capabilities={capabilities}
            values={operationActionParameters}
            preview={operationActionPreview}
            executionAttempt={operationExecutionAttempt}
            executionHistory={operationExecutionHistory}
            actionHistory={operationActionHistory}
            confirmationPhrase={operationExecutionPhrase}
            loading={loading}
            canSendCommands={Boolean(operationStatus?.can_send_commands)}
            onPreview={onPreviewAction}
            onPreflight={onPreflightAction}
            onParameterChange={onActionParameterChange}
            onPhraseChange={onExecutionPhraseChange}
            onValidateExecutionGate={onValidateExecutionGate}
          />
        </section>
      </div>
    </article>
  );
}

function MonitorBadge({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon?: React.ElementType;
  label: string;
  value: string;
  tone?: "ok" | "warning" | "danger";
}) {
  return (
    <div className={`monitor-badge ${tone ?? ""}`}>
      {Icon ? <Icon size={17} /> : null}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function FactGrid({ items }: { items: Array<{ label: string; value: string }> }) {
  return (
    <div className="operation-fact-grid">
      {items.map((item) => (
        <div key={item.label} className="operation-fact">
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </div>
  );
}

function OperationActions({
  actions,
  capabilities,
  values,
  preview,
  executionAttempt,
  executionHistory,
  actionHistory,
  confirmationPhrase,
  loading,
  canSendCommands,
  onPreview,
  onPreflight,
  onParameterChange,
  onPhraseChange,
  onValidateExecutionGate,
}: {
  actions: OperationAction[];
  capabilities: OperationCapability[];
  values: Record<string, Record<string, string>>;
  preview: OperationActionPreview | null;
  executionAttempt: OperationActionExecutionAttempt | null;
  executionHistory: OperationActionExecutionAttempt[];
  actionHistory: OperationActionPreviewRecord[];
  confirmationPhrase: string;
  loading: boolean;
  canSendCommands: boolean;
  onPreview: (action: OperationAction) => void | Promise<void>;
  onPreflight: (action: OperationAction) => void | Promise<void>;
  onParameterChange: (actionId: string, parameterName: string, value: string) => void;
  onPhraseChange: (value: string) => void;
  onValidateExecutionGate: () => void | Promise<void>;
}) {
  const recentExecutions = executionHistory.slice(0, 3);
  const recentPreviews = actionHistory.slice(0, 3);

  return (
    <div className="operation-actions-layout">
      <div className="operation-capabilities">
        {capabilities.length === 0 ? <p className="muted">Sem capabilities retornadas para esta impressora.</p> : null}
        {capabilities.map((capability) => (
          <div key={capability.action_id} className={`operation-capability ${capability.status}`}>
            <strong>{capability.action_id}</strong>
            <span>{formatCapabilityStatus(capability.status)}</span>
            <small>{capability.reason}</small>
          </div>
        ))}
      </div>

      <div className="operation-actions">
        {actions.length === 0 ? <p className="muted">Nenhuma ação operacional retornada pelo backend.</p> : null}
        {actions.map((action) => (
          <div key={action.id} className="operation-action-card">
            <span>
              <strong>{action.label}</strong>
              <code>{action.id}</code>
            </span>
            <small>
              {action.group} · risco {action.risk}
              {action.block_reason ? ` · ${action.block_reason}` : ""}
            </small>
            <OperationActionParameterFields action={action} values={values[action.id] ?? {}} onChange={onParameterChange} />
            <div className="operation-action-buttons">
              <button type="button" className="secondary-button compact" onClick={() => void onPreflight(action)} disabled={loading}>
                Validar
              </button>
              <button type="button" className="secondary-button compact" onClick={() => void onPreview(action)} disabled={loading}>
                Prévia
              </button>
            </div>
          </div>
        ))}
      </div>

      {preview ? (
        <div className="operation-preview">
          <div>
            <strong>{preview.action.label}</strong>
            <span>{preview.executable ? "Executável após confirmação" : "Bloqueada"}</span>
          </div>
          {preview.blockers.length > 0 ? (
            <ul>
              {preview.blockers.map((blocker) => (
                <li key={blocker}>{blocker}</li>
              ))}
            </ul>
          ) : null}
          <pre>{preview.command_preview.length ? preview.command_preview.join("\n") : "Sem comandos planejados."}</pre>
          <div className="operation-execution-gate">
            <label>
              <span>Confirmação</span>
              <input
                value={confirmationPhrase}
                onChange={(event) => onPhraseChange(event.target.value)}
                placeholder={preview.confirmation_phrase}
                disabled={!preview.executable || !canSendCommands}
              />
            </label>
            <button type="button" className="primary-button" onClick={() => void onValidateExecutionGate()} disabled={loading || !preview.executable || !canSendCommands}>
              Executar
            </button>
          </div>
        </div>
      ) : null}

      {executionAttempt ? (
        <div className="operation-execution-result">
          <strong>Última tentativa: {executionAttempt.status}</strong>
          <span>{executionAttempt.block_reason || (executionAttempt.confirmation_matched ? "Confirmação validada." : "Confirmação não validada.")}</span>
          <small>{executionAttempt.created_at}</small>
        </div>
      ) : null}

      <div className="operation-history">
        <div className="operation-history-heading">
          <strong>Histórico recente</strong>
          <span>Prévia</span>
          <span>Execução</span>
        </div>
        {(recentPreviews.length || recentExecutions.length) ? (
          Array.from({ length: Math.max(recentPreviews.length, recentExecutions.length) }).map((_, index) => {
            const previewRow = recentPreviews[index];
            const executionRow = recentExecutions[index];
            return (
              <div key={`${previewRow?.id ?? "p"}-${executionRow?.id ?? "e"}-${index}`} className="operation-history-row">
                <div>
                  <strong>{previewRow?.action_label ?? executionRow?.action_id ?? "-"}</strong>
                  <small>{previewRow?.created_at ?? executionRow?.created_at ?? "-"}</small>
                </div>
                <span>{previewRow ? (previewRow.executable ? "executável" : "bloqueada") : "-"}</span>
                <span>{executionRow?.status ?? "-"}</span>
              </div>
            );
          })
        ) : (
          <p className="muted">Sem histórico operacional recente.</p>
        )}
      </div>
    </div>
  );
}

function TemperatureMonitor({ temperatures, series }: { temperatures: OperationTemperature[]; series: TemperatureSeries[] }) {
  const maxTemperature = Math.max(
    60,
    ...series.flatMap((item) => item.points.map((point) => point.temperature)),
    ...temperatures.flatMap((item) => [numericValue(item.temperature), numericValue(item.target)].filter((value): value is number => value !== null)),
  );
  const yMax = Math.max(300, Math.ceil(maxTemperature / 50) * 50);
  const gridLines = [yMax, yMax * 0.75, yMax * 0.5, yMax * 0.25, 0].map((value) => Math.round(value));

  return (
    <div className="temperature-monitor">
      <div className="temperature-table" role="table" aria-label="Temperaturas atuais">
        <div className="temperature-table-row temperature-table-head" role="row">
          <span role="columnheader">Nome</span>
          <span role="columnheader">Estado</span>
          <span role="columnheader">Atual</span>
          <span role="columnheader">Alvo</span>
          <span role="columnheader">Potência</span>
        </div>
        {temperatures.length === 0 ? <p className="muted">Nenhum heater ou sensor retornado pelo Moonraker.</p> : null}
        {temperatures.map((item, index) => (
          <div key={item.name} className="temperature-table-row" role="row">
            <span className="temperature-name" role="cell">
              <i style={{ "--series-color": temperatureColor(index) } as React.CSSProperties} />
              <strong>{item.name}</strong>
            </span>
            <strong role="cell">{temperatureState(item)}</strong>
            <strong role="cell">{formatTemperature(item.temperature)}</strong>
            <span className="temperature-target" role="cell">{formatTemperature(item.target)}</span>
            <span role="cell">{formatPercent(item.power)}</span>
          </div>
        ))}
      </div>
      {series.length === 0 ? <p className="muted">Sem histórico suficiente para desenhar gráfico.</p> : null}
      {series.length > 0 ? <CombinedTemperatureChart series={series} gridLines={gridLines} yMax={yMax} /> : null}
    </div>
  );
}

function CombinedTemperatureChart({
  series,
  gridLines,
  yMax,
}: {
  series: TemperatureSeries[];
  gridLines: number[];
  yMax: number;
}) {
  return (
    <div className="combined-temperature-chart">
      <span className="combined-temperature-label">Temperatura [°C]</span>
      <div className="combined-temperature-plot">
        <div className="combined-temperature-axis" aria-hidden="true">
          {gridLines.map((value) => (
            <span key={value}>{value}</span>
          ))}
        </div>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Evolução conjunta de temperaturas">
          {gridLines.map((value) => {
            const y = temperatureChartY(value, yMax);
            return <line key={value} className="temperature-grid-line horizontal" x1="0" y1={y} x2="100" y2={y} />;
          })}
          {[0, 20, 40, 60, 80, 100].map((x) => (
            <line key={x} className="temperature-grid-line vertical" x1={x} y1="0" x2={x} y2="100" />
          ))}
          {series.map((item, index) => (
            <polyline
              key={item.name}
              style={{ "--series-color": temperatureColor(index) } as React.CSSProperties}
              points={temperatureChartPoints(item.points, yMax)}
            />
          ))}
        </svg>
      </div>
      <div className="temperature-legend">
        {series.map((item, index) => (
          <span key={item.name}>
            <i style={{ "--series-color": temperatureColor(index) } as React.CSSProperties} />
            {item.name}
          </span>
        ))}
      </div>
    </div>
  );
}

function RadialProgress({ value }: { value: number }) {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="radial-progress" style={{ "--progress": `${percent}%` } as React.CSSProperties}>
      <strong>{percent}%</strong>
      <span>progresso</span>
    </div>
  );
}

function LoadMeter({ metric, detail }: { metric: OperationMetric; detail?: string }) {
  const numericValue = typeof metric.value === "number" ? metric.value : null;
  const percent = normalizeMeterPercent(numericValue, metric.unit);
  return (
    <div className="load-meter">
      <div>
        <span>{metric.label}</span>
        <strong>{formatOperationValue(metric.value, metric.unit)}</strong>
      </div>
      <div className="load-meter-track">
        <span style={{ width: `${percent}%` }} />
      </div>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

type TemperatureSeries = {
  name: string;
  points: Array<{ snapshotId: number | null; createdAt: string; temperature: number }>;
  min: number;
  max: number;
};

function buildTemperatureSeries(history: OperationTemperatureHistoryRow[], current: OperationTemperature[]): TemperatureSeries[] {
  const series = new Map<string, TemperatureSeries["points"]>();
  history.forEach((row) => {
    row.readings.forEach((reading) => {
      if (typeof reading.temperature !== "number") return;
      const points = series.get(reading.name) ?? [];
      points.push({ snapshotId: row.snapshot_id, createdAt: row.created_at, temperature: reading.temperature });
      series.set(reading.name, points);
    });
  });
  current.forEach((reading) => {
    if (typeof reading.temperature !== "number") return;
    const points = series.get(reading.name) ?? [];
    points.push({ snapshotId: null, createdAt: "agora", temperature: reading.temperature });
    series.set(reading.name, points);
  });
  return Array.from(series.entries()).map(([name, points]) => {
    const temperatures = points.map((point) => point.temperature);
    return { name, points: points.slice(-20), min: Math.min(...temperatures), max: Math.max(...temperatures) };
  });
}

function temperatureChartPoints(points: TemperatureSeries["points"], yMax: number) {
  return points
    .map((point, index) => {
      const x = points.length === 1 ? 100 : (index / (points.length - 1)) * 100;
      const y = temperatureChartY(point.temperature, yMax);
      return `${x},${y}`;
    })
    .join(" ");
}

function temperatureChartY(value: number, yMax: number) {
  return 100 - (Math.max(0, Math.min(yMax, value)) / yMax) * 100;
}

function temperatureColor(index: number) {
  const colors = ["#ef4444", "#3b82f6", "#a855f7", "#22c55e", "#f59e0b", "#22d3ee", "#f97316", "#e879f9"];
  return colors[index % colors.length];
}

function temperatureState(item: OperationTemperature) {
  const current = numericValue(item.temperature);
  const target = numericValue(item.target);
  const power = numericValue(item.power);
  if (power !== null && power > 0) return `${Math.round(power * 100)} %`;
  if (target !== null && target > 0 && current !== null && current < target - 1) return "aquecendo";
  if (target !== null && target > 0) return "alvo";
  return "off";
}

function numericValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function normalizeMeterPercent(value: number | null, unit?: string | null) {
  if (value === null || Number.isNaN(value)) return 0;
  if (unit === "%" || value <= 1) return Math.max(0, Math.min(100, value <= 1 ? value * 100 : value));
  return Math.max(0, Math.min(100, value));
}

function buildToolheadFacts(operationStatus: OperationStatusResponse | null) {
  const toolhead = operationStatus?.toolhead ?? {};
  return [
    { label: "Posição", value: formatPosition(toolhead.position) },
    { label: "Home", value: formatUnknown(toolhead.homed_axes) },
    { label: "Velocidade máx.", value: formatOperationValue(toolhead.max_velocity, "mm/s") },
    { label: "Aceleração máx.", value: formatOperationValue(toolhead.max_accel, "mm/s²") },
    { label: "Speed factor", value: formatPercent(toolhead.speed_factor) },
  ];
}

function buildExtruderFacts(operationStatus: OperationStatusResponse | null) {
  const extruder = operationStatus?.extruder ?? {};
  return [
    { label: "Pressure advance", value: formatUnknown(extruder.pressure_advance) },
    { label: "Smooth time", value: formatOperationValue(extruder.smooth_time, "s") },
    { label: "Extrusion factor", value: formatPercent(extruder.extrusion_factor) },
    { label: "Filamento usado", value: formatOperationValue(extruder.filament_used, "mm") },
  ];
}

function formatPosition(value: unknown) {
  if (Array.isArray(value)) {
    return value.map((item) => formatOperationValue(item)).join(" / ");
  }
  return formatUnknown(value);
}

function formatPercent(value: unknown) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return `${Number((value * 100).toFixed(1))} %`;
}

function formatUnknown(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function formatCapabilityStatus(status: OperationCapability["status"]) {
  if (status === "supported") return "Suportada";
  if (status === "blocked") return "Bloqueada";
  return "Indefinida";
}

function formatDecision(decision?: HealthResponse["decision"]) {
  if (decision === "ok_para_imprimir") return "OK";
  if (decision === "monitorar") return "Monitorar";
  if (decision === "nao_imprimir") return "Não imprimir";
  return "-";
}

function healthTone(decision?: HealthResponse["decision"]) {
  if (decision === "ok_para_imprimir") return "ok";
  if (decision === "nao_imprimir") return "danger";
  if (decision === "monitorar") return "warning";
  return undefined;
}

function canTone(alert?: CanBusSummary["overall_alert"] | CanBusRecord["alert_level"]) {
  if (alert === "problema") return "danger";
  if (alert === "monitorar") return "warning";
  if (alert === "ok") return "ok";
  return undefined;
}

function formatCanAlert(alert: CanBusSummary["overall_alert"]) {
  if (alert === "problema") return "Problema";
  if (alert === "monitorar") return "Monitorar";
  return "OK";
}

function formatDataState(dataState?: OperationStatusResponse["data_state"]) {
  if (dataState === "live") return "ao vivo";
  if (dataState === "last_snapshot") return "snapshot";
  if (dataState === "fixture") return "exemplo";
  if (dataState === "offline") return "offline";
  return "-";
}

function formatOperationValue(value: unknown, unit?: string | null) {
  if (value === null || value === undefined || value === "") return "-";
  const normalized = typeof value === "number" ? Number(value.toFixed(2)).toString() : String(value);
  return unit && unit !== "bytes" ? `${normalized} ${unit}` : normalized;
}

function formatTemperature(value: unknown) {
  if (typeof value !== "number") return "-";
  return `${Number(value.toFixed(1))} °C`;
}

function formatOptional(value: number | null) {
  return value === null ? "-" : String(value);
}
