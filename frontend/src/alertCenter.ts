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
  repo_url?: string | null;
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
  rollback_version?: string | null;
  can_rollback: boolean;
  risk_level: "normal" | "caution" | "high";
  risk_reason?: string | null;
  requires_confirmation: boolean;
  alert_silenced: boolean;
  alert_silence_id?: number | null;
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

export type MaintenanceTaskAlert = {
  id: number;
  name: string;
  component: string;
  interval_kind: "days" | "print_hours";
  interval_value: number;
  due_status: "due" | "soon" | "ok" | "unknown" | "not_validated" | "needs_review";
  days_until_due?: number | null;
  print_hours_until_due?: number | null;
  due_detail?: string | null;
  is_active: boolean;
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
  actionKind: "revalidate" | "open_updates" | "refresh_update" | "run_update" | "open_monitoring" | "open_maintenance";
  target?: string;
};

export function buildAlertCenterItems({
  health,
  updateStatus,
  checklist,
  audit,
  maintenanceTasks,
}: {
  health: HealthResponse | null;
  updateStatus: UpdateStatusResponse | null;
  checklist: ChecklistResponse | null;
  audit: AuditResponse | null;
  maintenanceTasks?: MaintenanceTaskAlert[];
}): AlertCenterItem[] {
  const items: AlertCenterItem[] = [];
  const printerOffline = Boolean(health && !health.connected);

  health?.items
    .filter((item) => item.severity === "blocker" || item.severity === "warning")
    .filter((item) => !printerOffline || isPrinterReadProblem(item.key))
    .forEach((item) => {
      const printoraReadProblem = isPrinterReadProblem(item.key);
      items.push({
        id: `health-${item.key}`,
        source: "Health Check",
        title: printerOffline && printoraReadProblem ? "Impressora offline" : healthAlertTitle(item),
        detail: item.detail,
        action: printerOffline && printoraReadProblem ? "Ligue a impressora e revalide a conexão." : healthAlertAction(item),
        severity: item.severity === "blocker" && !printoraReadProblem ? "blocker" : "warning",
        reason: printerOffline && printoraReadProblem ? "A impressora não está acessível agora; alertas que dependem dela ligada ficam ocultos." : healthAlertReason(item),
        actionLabel: printoraReadProblem ? "Revalidar conexão" : "Revalidar agora",
        actionKind: "revalidate",
      });
    });

  if (printerOffline) {
    return dedupeAlertCenterItems(items);
  }

  updateStatus?.components
    .filter((component) => !component.alert_silenced)
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
          ? component.requires_confirmation
            ? "Atualização de risco alto. Revise compatibilidade e tenha rollback antes de continuar."
            : "Atualização disponível. Revise o plano e execute pelo Update Manager quando a impressora estiver parada."
          : "Reanalise o componente. Se continuar com aviso, revisar o repositório antes de imprimir ou atualizar.",
        severity: component.status === "warning" || component.anomalies.length > 0 ? "warning" : "info",
        reason: updateAlertReason(component),
        actionLabel: component.can_update ? (component.requires_confirmation ? "Revisar update" : "Atualizar componente") : "Reanalisar",
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

  maintenanceTasks
    ?.filter((task) => task.is_active)
    .filter((task) => ["due", "soon", "not_validated", "needs_review"].includes(task.due_status))
    .forEach((task) => {
      items.push({
        id: `maintenance-${task.id}`,
        source: `Manutenção · ${task.component}`,
        title: task.name,
        detail: maintenanceAlertDetail(task),
        action: maintenanceAlertAction(task),
        severity: task.due_status === "due" ? "warning" : "info",
        reason: maintenanceAlertReason(task),
        actionLabel: "Abrir manutenção",
        actionKind: "open_maintenance",
      });
    });

  return dedupeAlertCenterItems(items);
}

function isPrinterReadProblem(key: string): boolean {
  return key === "data_state" || key === "moonraker_unreachable";
}

function dedupeAlertCenterItems(items: AlertCenterItem[]): AlertCenterItem[] {
  return items.filter((item, index, allItems) => allItems.findIndex((candidate) => candidate.id === item.id) === index);
}

function healthAlertTitle(item: HealthItem): string {
  if (item.key === "api_latency") {
    return "Comunicação Printora ↔ Moonraker lenta";
  }
  return item.title;
}

function healthAlertAction(item: HealthItem): string {
  if (item.key === "api_latency") {
    return "Monitore antes de uma operação longa. Trate como problema se a demora for frequente, crescer muito ou vier junto de perda de conexão.";
  }
  return item.action;
}

function healthAlertReason(item: HealthItem): string {
  if (item.key === "api_latency") {
    return `A resposta levou ${item.detail}. Isso mede a ida e volta entre o Printora e o Moonraker pela rede local; como eles podem estar em dispositivos diferentes, alguma latência é esperada.`;
  }
  if (item.severity === "blocker") {
    return "Este item impede a liberação segura da impressora no health check.";
  }
  return "Este item não bloqueia sozinho, mas exige revisão antes de uma operação longa.";
}

function updateAlertReason(component: UpdateComponent): string {
  if (component.requires_confirmation) {
    return component.risk_reason ?? "Este componente exige confirmação porque pode quebrar compatibilidade operacional.";
  }
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

function maintenanceAlertDetail(task: MaintenanceTaskAlert): string {
  if (task.interval_kind === "print_hours") {
    if (task.due_status === "soon") {
      return `A cada ${formatHours(task.interval_value)} de impressão · faltam ${formatHours(task.print_hours_until_due ?? 0)}.`;
    }
    return `A cada ${formatHours(task.interval_value)} de impressão · ${task.due_detail ?? "pendência ativa"}.`;
  }
  if (task.due_status === "soon") {
    return `A cada ${Math.round(task.interval_value)} dias · faltam ${task.days_until_due ?? "-"} dia(s).`;
  }
  return `A cada ${Math.round(task.interval_value)} dias · pendência ativa.`;
}

function maintenanceAlertReason(task: MaintenanceTaskAlert): string {
  if (task.due_status === "not_validated" || task.due_status === "needs_review") {
    return "A rotina usa horas de impressão, mas a base salva precisa ser registrada ou revisada.";
  }
  if (task.interval_kind === "print_hours") {
    return "A rotina preventiva venceu ou está próxima pelo total de horas de impressão.";
  }
  return "A rotina preventiva venceu ou está próxima pelo prazo em dias.";
}

function maintenanceAlertAction(task: MaintenanceTaskAlert): string {
  if (task.due_status === "not_validated" || task.due_status === "needs_review") {
    return "Abra Manutenção, marque a rotina como feita quando executar e salve a leitura atual de horas como nova base.";
  }
  return "Abra Manutenção, execute a conferência indicada e registre a conclusão.";
}

function formatHours(value: number): string {
  return `${Number(value.toFixed(1))}h`;
}
