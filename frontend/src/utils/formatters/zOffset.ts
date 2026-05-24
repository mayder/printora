import type { ZOffsetRecord } from "../../types";

export function formatLatestZOffset(record: ZOffsetRecord | undefined) {
  if (!record) {
    return "Sem histórico";
  }
  return `${record.offset_value.toFixed(3)} · ${formatZOffsetAlert(record.alert_level)}`;
}

export function formatZOffsetAlert(alertLevel: ZOffsetRecord["alert_level"]) {
  const labels: Record<ZOffsetRecord["alert_level"], string> = {
    ok: "ok",
    monitorar: "monitorar",
    revisar: "revisar antes de imprimir",
  };
  return labels[alertLevel];
}
