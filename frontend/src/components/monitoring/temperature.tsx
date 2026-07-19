import React from "react";
import { formatPercent, formatTemperature, numericValue } from "./formatters";
import type { OperationAction, OperationTemperature, OperationTemperatureHistoryRow } from "../../types";

export function TemperatureMonitor({
  temperatures,
  series,
  actions = [],
  loading = false,
  onParameterChange,
  onExecute,
}: {
  temperatures: OperationTemperature[];
  series: TemperatureSeries[];
  actions?: OperationAction[];
  loading?: boolean;
  onParameterChange?: (actionId: string, parameterName: string, value: string) => void;
  onExecute?: (action: OperationAction, parameters?: Record<string, string | number>) => void | Promise<void>;
}) {
  const [targetValues, setTargetValues] = React.useState<Record<string, string>>({});
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
            <span className="temperature-target" role="cell">
              <TemperatureTargetInput
                item={item}
                actions={actions}
                loading={loading}
                value={targetValues[item.name] ?? String(numericValue(item.target) ?? 0)}
                onChange={(value) => {
                  setTargetValues((current) => ({ ...current, [item.name]: value }));
                  const action = temperatureActionFor(item, actions);
                  if (action) onParameterChange?.(action.id, "temperature", value);
                }}
                onSubmit={(value) => {
                  const action = temperatureActionFor(item, actions);
                  if (!action || !onExecute) return;
                  const boundedValue = clampTemperatureTarget(value, temperatureMaximumFor(item));
                  setTargetValues((current) => ({ ...current, [item.name]: String(boundedValue) }));
                  onParameterChange?.(action.id, "temperature", String(boundedValue));
                  void onExecute(action, { temperature: boundedValue });
                }}
              />
            </span>
            <span role="cell">{formatPercent(item.power)}</span>
          </div>
        ))}
      </div>
      {series.length === 0 ? <p className="muted">Sem histórico suficiente para desenhar gráfico.</p> : null}
      {series.length > 0 ? <CombinedTemperatureChart series={series} gridLines={gridLines} yMax={yMax} /> : null}
    </div>
  );
}

function TemperatureTargetInput({
  item,
  actions,
  loading,
  value,
  onChange,
  onSubmit,
}: {
  item: OperationTemperature;
  actions: OperationAction[];
  loading: boolean;
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
}) {
  const action = temperatureActionFor(item, actions);
  if (!action) {
    return <span className="temperature-target-readonly">{formatTemperature(item.target)}</span>;
  }
  const maximum = temperatureMaximumFor(item);
  return (
    <label className="temperature-target-control" title={`Enter envia alvo de 0 a ${maximum} °C`}>
      <input
        aria-label={`Alvo ${item.name}`}
        inputMode="decimal"
        value={value}
        disabled={loading}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") onSubmit(event.currentTarget.value);
        }}
      />
      <span>°C</span>
    </label>
  );
}

function temperatureActionFor(item: OperationTemperature, actions: OperationAction[]) {
  const name = item.name.toLowerCase();
  const actionId = name.includes("extruder") ? "set_hotend_temp" : name.includes("bed") ? "set_bed_temp" : "";
  return actionId ? actions.find((action) => action.id === actionId) ?? null : null;
}

function temperatureMaximumFor(item: OperationTemperature) {
  return item.name.toLowerCase().includes("bed") ? 130 : 300;
}

function clampTemperatureTarget(value: string, maximum: number) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) return 0;
  return Math.max(0, Math.min(maximum, Math.round(numberValue * 10) / 10));
}

export function CombinedTemperatureChart({
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

export type TemperatureSeries = {
  name: string;
  points: Array<{ snapshotId: number | null; createdAt: string; temperature: number }>;
  min: number;
  max: number;
};

export function buildTemperatureSeries(history: OperationTemperatureHistoryRow[], current: OperationTemperature[]): TemperatureSeries[] {
  const series = new Map<string, TemperatureSeries["points"]>();
  history.forEach((row) => {
    row.readings.forEach((reading) => {
      if (typeof reading.temperature !== "number") return;
      const points = series.get(reading.name) ?? [];
      points.push({ snapshotId: row.snapshot_id, createdAt: row.created_at, temperature: reading.temperature });
      series.set(reading.name, points);
    });
  });
  if (!historyHasCurrentReadings(history, current)) {
    current.forEach((reading) => {
      if (typeof reading.temperature !== "number") return;
      const points = series.get(reading.name) ?? [];
      points.push({ snapshotId: null, createdAt: "agora", temperature: reading.temperature });
      series.set(reading.name, points);
    });
  }
  return Array.from(series.entries()).map(([name, points]) => {
    const temperatures = points.map((point) => point.temperature);
    return { name, points, min: Math.min(...temperatures), max: Math.max(...temperatures) };
  });
}

export function temperatureChartPoints(points: TemperatureSeries["points"], yMax: number) {
  if (points.length === 1) {
    const y = temperatureChartY(points[0].temperature, yMax);
    return `0,${y} 100,${y}`;
  }
  return points
    .map((point, index) => {
      const x = points.length === 1 ? 100 : (index / (points.length - 1)) * 100;
      const y = temperatureChartY(point.temperature, yMax);
      return `${x},${y}`;
    })
    .join(" ");
}

function historyHasCurrentReadings(history: OperationTemperatureHistoryRow[], current: OperationTemperature[]) {
  const latest = history.at(-1);
  if (!latest || latest.snapshot_id !== null) {
    return false;
  }
  return current
    .filter((reading) => typeof reading.temperature === "number")
    .every((reading) =>
      latest.readings.some(
        (historyReading) =>
          historyReading.name === reading.name &&
          historyReading.temperature === reading.temperature &&
          (historyReading.target ?? null) === (reading.target ?? null),
      ),
    );
}

export function temperatureChartY(value: number, yMax: number) {
  return 100 - (Math.max(0, Math.min(yMax, value)) / yMax) * 100;
}

export function temperatureColor(index: number) {
  const colors = ["#ef4444", "#3b82f6", "#a855f7", "#22c55e", "#f59e0b", "#22d3ee", "#f97316", "#e879f9"];
  return colors[index % colors.length];
}

export function temperatureState(item: OperationTemperature) {
  const current = numericValue(item.temperature);
  const target = numericValue(item.target);
  const power = numericValue(item.power);
  if (power !== null && power > 0) return `${Math.round(power * 100)} %`;
  if (target !== null && target > 0 && current !== null && current < target - 1) return "aquecendo";
  if (target !== null && target > 0) return "alvo";
  return "off";
}
