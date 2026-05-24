import type { AuditFinding, HealthItem } from "../../alertCenter";
import type { SnapshotDiffItem } from "../../types";

export function formatClassification(classification: AuditFinding["classification"]) {
  return classification.replace("_", " ");
}

export function formatMetricLabel(label: string) {
  const labels: Record<string, string> = {
    klipper_state: "Klipper",
    klipper_version: "Versão Klipper",
    moonraker_version: "Moonraker",
    cpu_temp: "CPU temp.",
    disk_available_bytes: "Disco livre",
    memory_available_bytes: "Memória livre",
    api_latency_ms: "Latência API",
    data_state: "Origem",
    snapshot_count: "Snapshots",
    latest_snapshot_id: "Último snapshot",
    latest_diff_severity: "Último diff",
  };
  return labels[label] ?? label.replaceAll("_", " ");
}
export function formatSeverity(severity: SnapshotDiffItem["severity"]) {
  const labels: Record<SnapshotDiffItem["severity"], string> = {
    info: "informativo",
    monitorar: "monitorar",
    risco: "risco",
    bloqueio: "bloqueio",
  };
  return labels[severity];
}

export function formatHealthSeverity(severity: HealthItem["severity"]) {
  const labels: Record<HealthItem["severity"], string> = {
    ok: "ok",
    info: "informativo",
    warning: "atenção",
    blocker: "bloqueio",
  };
  return labels[severity];
}

export function formatRedaction(redaction: string) {
  const labels: Record<string, string> = {
    urls: "URLs",
    ip_addresses: "IPs",
    home_paths: "caminhos locais",
    secret_values: "valores sensíveis",
  };
  return labels[redaction] ?? redaction;
}
