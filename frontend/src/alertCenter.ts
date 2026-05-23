export type ChecklistItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: string;
  detail: string;
  status: string;
  source: string;
};

export type ChecklistResponse = {
  can_print: boolean;
  data_state: string;
  source: string;
  error?: string | null;
  summary: string;
  items: ChecklistItem[];
};

export type HealthItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: "ok" | "info" | "warning" | "blocker";
  detail: string;
  action: string;
};

export type HealthResponse = {
  connected: boolean;
  safe_mode: string;
  data_state: string;
  source: string;
  error?: string | null;
  printer_id: number;
  moonraker_url: string;
  decision: "ok_para_imprimir" | "monitorar" | "nao_imprimir";
  summary: string;
  metrics: Record<string, unknown>;
  counts: Record<string, number>;
  items: HealthItem[];
};

export type AuditFinding = {
  id: string;
  title: string;
  category: string;
  classification: "corrigir_agora" | "monitorar" | "ignorar" | "precisa_confirmacao";
  severity: "blocker" | "warning" | "info";
  detail: string;
  safe_action: string;
};

export type AuditResponse = {
  connected: boolean;
  safe_mode: string;
  data_state?: "live" | "last_snapshot" | "offline";
  source?: string;
  error?: string | null;
  mode?: string;
  executed?: boolean;
  summary: string;
  counts: Record<string, number>;
  findings: AuditFinding[];
  section_summary?: Record<string, unknown>;
};

export type UpdateComponent = {
  name: string;
  title: string;
  configured_type: string;
  status: "up_to_date" | "update_available" | "warning" | "busy" | "unknown";
  current_version?: string | null;
  remote_version?: string | null;
  full_version?: string | null;
  is_dirty?: boolean | null;
  is_valid?: boolean | null;
  commits_behind_count: number;
  package_count: number;
  warnings: string[];
  anomalies: string[];
  can_update: boolean;
};

export type UpdateStatusResponse = {
  safe_mode: string;
  busy: boolean;
  github_requests_remaining?: number | null;
  github_rate_limit?: number | null;
  summary: string;
  counts: Record<string, number>;
  components: UpdateComponent[];
};

export type AlertCenterItem = {
  id: string;
  source: string;
  title: string;
  detail: string;
  action: string;
  severity: "blocker" | "warning" | "info";
  reason: string;
  actionLabel: string;
  actionKind: "revalidate" | "open_updates" | "refresh_update" | "run_update" | "open_monitoring";
  target?: string;
};

export function buildAlertCenterItems({
  health,
  updateStatus,
  checklist,
  audit,
}: {
  health: HealthResponse | null;
  updateStatus: UpdateStatusResponse | null;
  checklist: ChecklistResponse | null;
  audit: AuditResponse | null;
}): AlertCenterItem[] {
  const items: AlertCenterItem[] = [];

  health?.items
    .filter((item) => item.severity === "blocker" || item.severity === "warning")
    .forEach((item) => {
      const printoraReadProblem = item.key === "data_state" || item.key === "moonraker_unreachable";
      items.push({
        id: `health-${item.key}`,
        source: "Health Check",
        title: item.title,
        detail: item.detail,
        action: item.action,
        severity: item.severity === "blocker" && !printoraReadProblem ? "blocker" : "warning",
        reason: healthAlertReason(item),
        actionLabel: printoraReadProblem ? "Revalidar conexão" : "Revalidar agora",
        actionKind: "revalidate",
      });
    });

  updateStatus?.components
    .filter((component) => component.can_update || component.status === "warning" || component.warnings.length > 0 || component.anomalies.length > 0)
    .forEach((component) => {
      items.push({
        id: `update-${component.name}`,
        source: "Update Manager",
        title: component.title,
        detail:
          component.status === "warning"
            ? [...component.warnings, ...component.anomalies].filter(Boolean).join(" · ") || "Componente com aviso no Update Manager."
            : `${component.current_version ?? "-"} → ${component.remote_version ?? component.full_version ?? "-"}`,
        action: component.can_update
          ? "Atualização disponível. Revise o plano e execute pelo Update Manager quando a impressora estiver parada."
          : "Reanalise o componente. Se continuar com aviso, revisar o repositório antes de imprimir ou atualizar.",
        severity: component.status === "warning" || component.anomalies.length > 0 ? "warning" : "info",
        reason: updateAlertReason(component),
        actionLabel: component.can_update ? "Atualizar componente" : "Reanalisar",
        actionKind: component.can_update ? "run_update" : "refresh_update",
        target: component.name,
      });
    });

  checklist?.items
    .filter((item) => !item.ok)
    .forEach((item) => {
      items.push({
        id: `checklist-${item.key}`,
        source: "Checklist pós-update",
        title: item.title,
        detail: item.detail,
        action: "Corrija este item antes de considerar a impressora pronta.",
        severity: item.severity === "blocker" ? "blocker" : "warning",
        reason: checklistAlertReason(item),
        actionLabel: item.status === "manual" || item.severity === "manual" ? "Abrir checklist" : "Revalidar agora",
        actionKind: item.status === "manual" || item.severity === "manual" ? "open_monitoring" : "revalidate",
      });
    });

  audit?.findings
    .filter((finding) => finding.severity === "blocker" || finding.severity === "warning")
    .forEach((finding) => {
      items.push({
        id: `audit-${finding.id}`,
        source: `Auditoria · ${finding.category}`,
        title: finding.title,
        detail: finding.detail,
        action: finding.safe_action,
        severity: finding.severity,
        reason: auditAlertReason(finding),
        actionLabel: "Abrir diagnóstico",
        actionKind: "open_monitoring",
      });
    });

  return items;
}

function healthAlertReason(item: HealthItem): string {
  if (item.severity === "blocker") {
    return "Este item impede a liberação segura da impressora no health check.";
  }
  return "Este item não bloqueia sozinho, mas exige revisão antes de uma operação longa.";
}

function updateAlertReason(component: UpdateComponent): string {
  if (component.can_update) {
    return "Há versão nova disponível no Update Manager para este componente.";
  }
  if (component.status === "warning") {
    return "O Update Manager retornou o componente em estado de aviso.";
  }
  if (component.anomalies.length > 0) {
    return "O Update Manager encontrou anomalia no repositório.";
  }
  return "O Update Manager encontrou warnings ou sinais que precisam de reanálise.";
}

function checklistAlertReason(item: ChecklistItem): string {
  if (item.status === "manual" || item.severity === "manual") {
    return "Este item depende de conferência presencial do operador depois de update ou manutenção.";
  }
  if (item.severity === "blocker") {
    return "O checklist pós-update marcou uma condição que bloqueia considerar a impressora pronta.";
  }
  return "O checklist pós-update marcou uma pendência de revisão.";
}

function auditAlertReason(finding: AuditFinding): string {
  if (finding.severity === "blocker") {
    return "A auditoria somente leitura encontrou um achado que pode afetar a operação.";
  }
  return "A auditoria encontrou um achado que precisa de revisão técnica.";
}
