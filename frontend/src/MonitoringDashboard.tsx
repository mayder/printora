import React from "react";
import { Activity, AlertTriangle, Database, Gauge, Radio, RefreshCw, Thermometer, Wind } from "lucide-react";

type OperationMetric = {
  label: string;
  value: unknown;
  unit?: string | null;
};

type OperationTemperature = {
  name: string;
  temperature?: number | null;
  target?: number | null;
  power?: number | null;
};

type OperationFan = {
  name: string;
  speed?: number | null;
  rpm?: number | null;
};

type OperationTemperatureHistoryRow = {
  snapshot_id: number | null;
  created_at: string;
  readings: Array<{
    name: string;
    temperature?: number | null;
  }>;
};

type OperationStatusResponse = {
  connected: boolean;
  data_state: "live" | "offline" | "fixture" | "last_snapshot";
  summary: string;
  error?: string;
  system_loads: OperationMetric[];
  temperatures: OperationTemperature[];
  temperature_history: OperationTemperatureHistoryRow[];
  miscellaneous: {
    fans?: OperationFan[];
    progress?: number | null;
    message?: string | null;
    print_state?: string | null;
    filename?: string | null;
    total_print_hours?: number | null;
  };
};

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
  health,
  canSummary,
  canRecords,
  canComparison,
  loading,
  onRefresh,
  onCompareCan,
}: {
  selectedPrinterName: string;
  operationStatus: OperationStatusResponse | null;
  health: HealthResponse | null;
  canSummary: CanBusSummary | null;
  canRecords: CanBusRecord[];
  canComparison: CanBusRecordComparison | null;
  loading: boolean;
  onRefresh: () => void;
  onCompareCan: () => void;
}) {
  const temperatureSeries = buildTemperatureSeries(operationStatus?.temperature_history ?? [], operationStatus?.temperatures ?? []);
  const fans = operationStatus?.miscellaneous.fans ?? [];
  const latestCanRecords = canRecords.slice(0, 4);
  const hotend = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bed = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));

  return (
    <article className="panel wide panel-section panel-monitoring monitoring-dashboard">
      <div className="panel-heading monitoring-heading">
        <div>
          <h2>Monitoramento em tempo real</h2>
          <p className="muted">{operationStatus?.summary ?? "Aguardando leitura da impressora selecionada."}</p>
        </div>
        <div className="panel-actions">
          <span className="live-pill">Atualiza sozinho</span>
          <button type="button" className="secondary-button" onClick={onRefresh} disabled={loading}>
            <RefreshCw size={15} />
            Atualizar agora
          </button>
        </div>
      </div>

      <div className="monitor-status-strip">
        <MonitorBadge icon={Radio} label="Impressora" value={selectedPrinterName} tone={operationStatus?.connected ? "ok" : "danger"} />
        <MonitorBadge icon={Gauge} label="Estado" value={operationStatus?.miscellaneous.print_state ?? "-"} tone={operationStatus?.connected ? "ok" : "warning"} />
        <MonitorBadge icon={AlertTriangle} label="Risco" value={formatDecision(health?.decision)} tone={healthTone(health?.decision)} />
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
