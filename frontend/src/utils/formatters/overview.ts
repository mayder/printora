import { AlertTriangle, Bell } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { AlertCenterItem, ChecklistItem, HealthResponse, HealthItem } from "../../alertCenter";

export function alertCenterIcon(severity: AlertCenterItem["severity"]): LucideIcon {
  const icons: Record<AlertCenterItem["severity"], LucideIcon> = {
    blocker: AlertTriangle,
    warning: AlertTriangle,
    info: Bell,
  };
  return icons[severity];
}

export function confirmedWizardSteps(checks: Record<string, boolean>) {
  return Object.values(checks).filter(Boolean).length;
}

export function formatDecision(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "OK";
  }
  if (decision === "monitorar") {
    return "Monitorar";
  }
  if (decision === "nao_imprimir") {
    return "Não imprimir";
  }
  return "-";
}

export function displayHealthDecision(health: HealthResponse | null): HealthResponse["decision"] | undefined {
  if (!health) {
    return undefined;
  }
  const blockerItems = health.items.filter((item) => item.severity === "blocker");
  const onlyPrintoraReadBlocked =
    blockerItems.length > 0 && blockerItems.every((item) => item.key === "data_state" || item.key === "moonraker_unreachable");
  return onlyPrintoraReadBlocked ? "monitorar" : health.decision;
}

export function healthPanelClass(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "ok";
  }
  if (decision === "nao_imprimir") {
    return "danger";
  }
  return "warn";
}

export function overviewRiskClass(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "ok";
  }
  if (decision === "nao_imprimir") {
    return "danger";
  }
  if (decision === "monitorar") {
    return "warn";
  }
  return "unknown";
}

export function healthFindingClass(severity: HealthItem["severity"]) {
  if (severity === "blocker") {
    return "blocker";
  }
  if (severity === "warning") {
    return "warning";
  }
  return "info";
}

export function checklistDotClass(item: ChecklistItem) {
  if (item.ok) {
    return "dot good";
  }
  if (item.severity === "manual" || item.status === "manual") {
    return "dot manual";
  }
  return "dot bad";
}

export function formatChecklistDataState(dataState: string) {
  if (dataState === "live") {
    return "ao vivo";
  }
  if (dataState === "last_snapshot") {
    return "último snapshot";
  }
  if (dataState === "offline") {
    return "offline";
  }
  if (dataState === "no_data") {
    return "sem dados";
  }
  return dataState;
}
