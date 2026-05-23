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
          {temperatureSeries.length === 0 ? <p className="muted">Sem histórico suficiente para desenhar gráfico.</p> : null}
          <div className="live-chart-list">
            {temperatureSeries.map((series) => (
              <LiveSeriesChart key={series.name} series={series} unit="°C" />
            ))}
          </div>
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

function LiveSeriesChart({ series, unit }: { series: TemperatureSeries; unit: string }) {
  const points = series.points.map((point, index) => {
    const x = series.points.length === 1 ? 100 : (index / (series.points.length - 1)) * 100;
    const range = series.max - series.min || 1;
    const y = 88 - ((point.temperature - series.min) / range) * 70;
    return `${x},${y}`;
  });
  const latest = series.points[series.points.length - 1]?.temperature;

  return (
    <div className="live-series">
      <div className="live-series-label">
        <strong>{series.name}</strong>
        <span>
          {formatTemperature(latest)} · {formatTemperature(series.min)} a {formatTemperature(series.max)}
        </span>
      </div>
      <svg className="live-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={`Evolução ${series.name}`}>
        <polyline points={points.join(" ")} />
      </svg>
      <span className="live-series-unit">{unit}</span>
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
