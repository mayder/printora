import type { HealthItem, HealthResponse } from "../../alertCenter";

export function formatReportValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return Number(value.toFixed(2)).toLocaleString("pt-BR");
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

export function formatReportBytes(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "-";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${Number(size.toFixed(size >= 10 || index === 0 ? 0 : 1)).toLocaleString("pt-BR")} ${units[index]}`;
}

export function formatReportLatency(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "-";
  }
  if (value >= 1000) {
    return `${Number((value / 1000).toFixed(1)).toLocaleString("pt-BR")} s`;
  }
  return `${Math.round(value).toLocaleString("pt-BR")} ms`;
}

export function reportMetricLabel(key: string): string {
  const labels: Record<string, string> = {
    klipper_state: "Estado do Klipper",
    klipper_version: "Versão do Klipper",
    moonraker_version: "Versão do Moonraker",
    cpu_temp: "Temperatura da Raspberry",
    disk_free: "Espaço livre",
    disk_total_bytes: "Disco total",
    memory_free: "Memória livre",
    memory_total_bytes: "Memória total",
    api_latency_ms: "Comunicação Printora ↔ Moonraker",
    snapshot_count: "Snapshots salvos",
    latest_snapshot_id: "Último snapshot",
    latest_diff_severity: "Última comparação",
    data_state: "Origem da leitura",
    disk_available_bytes: "Disco livre",
    memory_available_bytes: "Memória livre",
  };
  return labels[key] ?? key.replaceAll("_", " ");
}

export function reportMetricHelp(key: string): string {
  const helps: Record<string, string> = {
    klipper_state: "Estado operacional do Klipper lido pelo Moonraker.",
    cpu_temp: "Temperatura do host onde o Klipper/Moonraker roda, normalmente a Raspberry Pi.",
    disk_free: "Espaço disponível no host da impressora quando o Moonraker informa esse dado.",
    disk_total_bytes: "Tamanho total do disco informado pelo host da impressora.",
    memory_free: "Memória disponível no host da impressora.",
    memory_total_bytes: "Memória total do host da impressora.",
    api_latency_ms:
      "Tempo de ida e volta entre o Printora e o Moonraker pela rede local. Como o Printora pode rodar no Android e o Moonraker na Raspberry, alguma latência é normal.",
    snapshot_count: "Quantidade de leituras salvas para comparar mudanças ao longo do tempo.",
    latest_snapshot_id: "Identificador da leitura mais recente usada como evidência.",
    latest_diff_severity: "Gravidade da comparação mais recente entre snapshots.",
    data_state: "Indica se os dados vieram da leitura ao vivo, de snapshot salvo ou de estado offline.",
    disk_available_bytes: "Espaço livre no host da impressora informado pelo Moonraker.",
    memory_available_bytes: "Memória disponível no host da impressora.",
  };
  return helps[key] ?? "Dado técnico retornado pelo diagnóstico da impressora.";
}

export function reportHealthTitle(item: HealthItem): string {
  if (item.key === "api_latency") {
    return "Comunicação Printora ↔ Moonraker lenta";
  }
  return item.title;
}

export function reportHealthDetail(item: HealthItem): string {
  if (item.key === "api_latency") {
    return `A resposta levou ${item.detail}. Isso mede a ida e volta entre o Printora e o Moonraker pela rede local. Como eles podem estar em dispositivos diferentes, alguma latência é esperada.`;
  }
  return item.detail;
}

export function reportHealthAction(item: HealthItem): string {
  if (item.key === "api_latency") {
    return "Monitore antes de uma operação longa. Só trate como problema se a demora for frequente, crescer muito ou vier junto de perda de conexão.";
  }
  return item.action;
}

export function formatReportMetricValue(key: string, value: unknown): string {
  if (key.includes("bytes") || key === "memory_free" || key === "disk_free") {
    return formatReportBytes(value);
  }
  if (key === "api_latency_ms") {
    return formatReportLatency(value);
  }
  return formatReportValue(value);
}

export function primaryHealthReason(health: HealthResponse | null): HealthItem | null {
  if (!health) {
    return null;
  }
  return (
    health.items.find((item) => item.severity === "blocker") ??
    health.items.find((item) => item.severity === "warning") ??
    health.items.find((item) => item.severity === "info") ??
    null
  );
}

export function explainPrintDecision(health: HealthResponse | null): string {
  const reason = primaryHealthReason(health);
  if (!health) {
    return "O Printora ainda não recebeu dados suficientes para orientar a decisão.";
  }
  if (health.decision === "ok_para_imprimir") {
    return "Nenhum bloqueio crítico foi encontrado na leitura atual.";
  }
  if (!reason) {
    return health.summary;
  }
  if (health.decision === "nao_imprimir") {
    return `${reportHealthTitle(reason)}: ${reportHealthDetail(reason)}`;
  }
  return `${reportHealthTitle(reason)}: ${reportHealthDetail(reason)}`;
}
