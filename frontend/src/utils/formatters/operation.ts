import type { OperationActionParameterSpec, OperationCapability, OperationStatusResponse, OperationTemperatureHistoryRow } from "../../types";

export function buildTemperatureSeries(history: OperationTemperatureHistoryRow[]) {
  const series = new Map<
    string,
    Array<{ snapshotId: number | null; createdAt: string; temperature: number }>
  >();
  history.forEach((row) => {
    row.readings.forEach((reading) => {
      if (typeof reading.temperature !== "number") {
        return;
      }
      const points = series.get(reading.name) ?? [];
      points.push({ snapshotId: row.snapshot_id, createdAt: row.created_at, temperature: reading.temperature });
      series.set(reading.name, points);
    });
  });
  return Array.from(series.entries()).map(([name, points]) => {
    const temperatures = points.map((point) => point.temperature);
    return {
      name,
      points,
      min: Math.min(...temperatures),
      max: Math.max(...temperatures),
    };
  });
}

export function temperatureBarHeight(value: number, min: number, max: number) {
  if (max === min) {
    return 55;
  }
  return Math.max(18, Math.round(((value - min) / (max - min)) * 82) + 18);
}

export function operationActionParameterSpecs(actionId: string): OperationActionParameterSpec[] {
  const specs: Record<string, OperationActionParameterSpec[]> = {
    move_xy: [
      { name: "axis", type: "enum", values: ["X", "Y"], default: "X" },
      { name: "distance_mm", type: "number", default: 10, min: -50, max: 50 },
      { name: "feedrate", type: "number", default: 6000, min: 600, max: 12000 },
    ],
    move_z: [
      { name: "distance_mm", type: "number", default: 5, min: -10, max: 10 },
      { name: "feedrate", type: "number", default: 1200, min: 120, max: 3000 },
    ],
    extrude: [
      { name: "length_mm", type: "number", default: 5, min: -10, max: 50 },
      { name: "feedrate", type: "number", default: 300, min: 60, max: 1200 },
    ],
    set_hotend_temp: [{ name: "temperature", type: "number", default: 0, min: 0, max: 300 }],
    set_bed_temp: [{ name: "temperature", type: "number", default: 0, min: 0, max: 130 }],
    set_fan: [
      { name: "fan_name", type: "text", default: "" },
      { name: "speed_percent", type: "number", default: 0, min: 0, max: 100 },
    ],
    set_led: [
      { name: "led_name", type: "text", default: "" },
      { name: "brightness_percent", type: "number", default: 0, min: 0, max: 100 },
    ],
  };
  return specs[actionId] ?? [];
}

export function buildOperationActionPayload(values: Record<string, string | number>) {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => {
      const numericValue = Number(value);
      const textValue = String(value);
      return [key, textValue.trim() !== "" && Number.isFinite(numericValue) ? numericValue : value];
    }),
  );
}

export function formatOperationParameterLabel(name: string) {
  const labels: Record<string, string> = {
    axis: "Eixo",
    distance_mm: "Distância mm",
    feedrate: "Feedrate",
    length_mm: "Comprimento mm",
    temperature: "Temperatura",
    fan_name: "Fan",
    speed_percent: "Velocidade %",
    led_name: "Nome do LED",
    brightness_percent: "Brilho %",
  };
  return labels[name] ?? name;
}

export function formatOperationActionId(actionId: string) {
  return actionId.replaceAll("_", " ");
}

export function formatOperationCapabilityStatus(status: OperationCapability["status"]) {
  if (status === "supported") {
    return "suportado";
  }
  if (status === "blocked") {
    return "bloqueado";
  }
  return "desconhecido";
}

export function formatRollbackPlan(plan: string | string[]) {
  return Array.isArray(plan) ? plan.join(" · ") : plan;
}

export function formatOperationDataState(dataState: OperationStatusResponse["data_state"] | undefined) {
  if (dataState === "live") {
    return "ao vivo";
  }
  if (dataState === "offline") {
    return "offline";
  }
  if (dataState === "fixture") {
    return "fixture";
  }
  if (dataState === "last_snapshot") {
    return "snapshot";
  }
  return "-";
}

export function formatOperationValue(value: unknown, unit?: string | null) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const normalized = typeof value === "number" ? Number(value.toFixed(2)).toString() : formatUnknown(value);
  return unit && unit !== "bytes" ? `${normalized} ${unit}` : normalized;
}

export function formatTemperature(value: unknown) {
  if (typeof value !== "number") {
    return "-";
  }
  return `${Number(value.toFixed(1))} °C`;
}

export function formatPercent(value: unknown) {
  if (typeof value !== "number") {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

export function formatPosition(value: unknown) {
  if (!Array.isArray(value)) {
    return "-";
  }
  return value
    .slice(0, 3)
    .map((axis) => (typeof axis === "number" ? Number(axis.toFixed(2)) : axis))
    .join(" / ");
}

export function formatUnknown(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "string") {
    return value || "-";
  }
  return JSON.stringify(value) ?? "-";
}
