import type { CanBusRecord } from "../../types";

export function formatLatestCan(record: CanBusRecord | undefined) {
  if (!record) {
    return "Sem histórico";
  }
  return `${formatCanAlert(record.alert_level)} · retries ${record.tx_retries}`;
}

export function formatCanAlert(alertLevel: CanBusRecord["alert_level"]) {
  const labels: Record<CanBusRecord["alert_level"], string> = {
    ok: "ok",
    monitorar: "monitorar",
    problema: "problema físico/elétrico possível",
  };
  return labels[alertLevel];
}
