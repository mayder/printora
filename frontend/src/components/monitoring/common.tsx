import React from "react";
import { formatOperationValue, normalizeMeterPercent } from "./formatters";
import type { OperationMetric } from "../../types";

export function MonitorBadge({
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

export function FactGrid({ items }: { items: Array<{ label: string; value: string }> }) {
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

export function RadialProgress({ value }: { value: number }) {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="radial-progress" style={{ "--progress": `${percent}%` } as React.CSSProperties}>
      <div>
        <strong>{percent}%</strong>
        <span>progresso</span>
      </div>
    </div>
  );
}

export function LoadMeter({ metric, detail }: { metric: OperationMetric; detail?: string }) {
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
