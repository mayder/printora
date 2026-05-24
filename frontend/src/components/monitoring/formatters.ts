import type { CanBusRecord, CanBusSummary, HealthResponse } from "./types";
import type { OperationCapability, OperationStatusResponse } from "../../types";

export function numericValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function normalizeMeterPercent(value: number | null, unit?: string | null) {
  if (value === null || Number.isNaN(value)) return 0;
  if (unit === "%" || value <= 1) return Math.max(0, Math.min(100, value <= 1 ? value * 100 : value));
  return Math.max(0, Math.min(100, value));
}

export function buildToolheadFacts(operationStatus: OperationStatusResponse | null) {
  const toolhead = operationStatus?.toolhead ?? {};
  return [
    { label: "Posição", value: formatPosition(toolhead.position) },
    { label: "Home", value: formatUnknown(toolhead.homed_axes) },
    { label: "Velocidade máx.", value: formatOperationValue(toolhead.max_velocity, "mm/s") },
    { label: "Aceleração máx.", value: formatOperationValue(toolhead.max_accel, "mm/s²") },
    { label: "Speed factor", value: formatPercent(toolhead.speed_factor) },
  ];
}

export function buildExtruderFacts(operationStatus: OperationStatusResponse | null) {
  const extruder = operationStatus?.extruder ?? {};
  return [
    { label: "Pressure advance", value: formatUnknown(extruder.pressure_advance) },
    { label: "Smooth time", value: formatOperationValue(extruder.smooth_time, "s") },
    { label: "Extrusion factor", value: formatPercent(extruder.extrusion_factor) },
    { label: "Filamento usado", value: formatOperationValue(extruder.filament_used, "mm") },
  ];
}

export function formatPosition(value: unknown) {
  if (Array.isArray(value)) {
    return value.map((item) => formatOperationValue(item)).join(" / ");
  }
  return formatUnknown(value);
}

export function formatPercent(value: unknown) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return `${Number((value * 100).toFixed(1))} %`;
}

export function formatUnknown(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

export function formatCapabilityStatus(status: OperationCapability["status"]) {
  if (status === "supported") return "Suportada";
  if (status === "blocked") return "Bloqueada";
  return "Indefinida";
}

export function formatDecision(decision?: HealthResponse["decision"]) {
  if (decision === "ok_para_imprimir") return "OK";
  if (decision === "monitorar") return "Monitorar";
  if (decision === "nao_imprimir") return "Não imprimir";
  return "-";
}

export function healthTone(decision?: HealthResponse["decision"]) {
  if (decision === "ok_para_imprimir") return "ok";
  if (decision === "nao_imprimir") return "danger";
  if (decision === "monitorar") return "warning";
  return undefined;
}

export function canTone(alert?: CanBusSummary["overall_alert"] | CanBusRecord["alert_level"]) {
  if (alert === "problema") return "danger";
  if (alert === "monitorar") return "warning";
  if (alert === "ok") return "ok";
  return undefined;
}

export function formatCanAlert(alert: CanBusSummary["overall_alert"]) {
  if (alert === "problema") return "Problema";
  if (alert === "monitorar") return "Monitorar";
  return "OK";
}

export function formatDataState(dataState?: OperationStatusResponse["data_state"]) {
  if (dataState === "live") return "ao vivo";
  if (dataState === "last_snapshot") return "snapshot";
  if (dataState === "fixture") return "exemplo";
  if (dataState === "offline") return "offline";
  return "-";
}

export function formatOperationValue(value: unknown, unit?: string | null) {
  if (value === null || value === undefined || value === "") return "-";
  const normalized = typeof value === "number" ? Number(value.toFixed(2)).toString() : String(value);
  return unit && unit !== "bytes" ? `${normalized} ${unit}` : normalized;
}

export function formatTemperature(value: unknown) {
  if (typeof value !== "number") return "-";
  return `${Number(value.toFixed(1))} °C`;
}

export function formatOptional(value: number | null) {
  return value === null ? "-" : String(value);
}
