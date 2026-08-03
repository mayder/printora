import { AlertTriangle, CheckCircle2, Gauge, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { UpdateComponent, UpdateStatusResponse } from "../../alertCenter";
import type { SystemReleasesResponse, UpdateDialogState } from "../../types";

export function formatUpdateStatus(status: UpdateComponent["status"]) {
  const labels: Record<UpdateComponent["status"], string> = {
    up_to_date: "atualizado",
    update_available: "update disponível",
    warning: "atenção",
    busy: "ocupado",
    unknown: "desconhecido",
  };
  return labels[status];
}

export function formatReleaseUpdateStatus(
  releases: SystemReleasesResponse | null,
  loading: boolean,
  fetchError: string | null,
) {
  if (loading) {
    return "carregando";
  }
  if (fetchError) {
    return "erro de rede";
  }
  if (!releases) {
    return "não carregado";
  }
  if (releases.status !== "ok") {
    return formatReleaseSourceStatus(releases.status);
  }
  const labels: Record<SystemReleasesResponse["update_status"], string> = {
    up_to_date: "já atualizado",
    outdated: "update disponível",
    unknown: releases.releases.length === 0 ? "sem release publicada" : "desconhecido",
  };
  return labels[releases.update_status];
}

export function formatReleaseSourceStatus(status: SystemReleasesResponse["status"]) {
  const labels: Record<SystemReleasesResponse["status"], string> = {
    ok: "online",
    offline: "GitHub offline",
    rate_limited: "limite do GitHub",
    disabled: "desabilitado",
    error: "erro de rede",
  };
  return labels[status];
}

export function releaseStatusPillClass(releases: SystemReleasesResponse | null) {
  if (!releases || releases.status !== "ok") {
    return "warning";
  }
  if (releases.update_status === "up_to_date") {
    return "up_to_date";
  }
  if (releases.update_status === "outdated") {
    return "update_available";
  }
  return "warning";
}

export function releasePanelClass(releases: SystemReleasesResponse | null) {
  if (!releases) {
    return "";
  }
  if (releases.status !== "ok") {
    return "warn";
  }
  return releases.update_status === "up_to_date" ? "ok" : "warn";
}

export function countPendingUpdates(status: UpdateStatusResponse | null) {
  if (!status) {
    return "-";
  }
  return status.components.filter((component) => !component.alert_silenced && (component.can_update || component.status === "update_available")).length;
}

export function isUpdateTargetConfirmedUpdated(status: UpdateStatusResponse | null, target: string) {
  if (!status) {
    return false;
  }
  if (target === "all") {
    return status.components.every((component) => !component.can_update && component.status !== "update_available" && component.status !== "busy");
  }
  const component = status.components.find((item) => item.name === target);
  return Boolean(component && !component.can_update && component.status === "up_to_date");
}
export function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function formatUpdatePhase(phase: UpdateDialogState["phase"]) {
  const labels: Record<UpdateDialogState["phase"], string> = {
    confirm: "Aguardando confirmação",
    running: "Operação em andamento",
    done: "Operação concluída",
    failed: "Operação com erro",
  };
  return labels[phase];
}

export function updatePhaseIcon(phase: UpdateDialogState["phase"]): LucideIcon {
  const icons: Record<UpdateDialogState["phase"], LucideIcon> = {
    confirm: AlertTriangle,
    running: RefreshCw,
    done: CheckCircle2,
    failed: AlertTriangle,
  };
  return icons[phase];
}

export function updateStatusIcon(status: UpdateComponent["status"]): LucideIcon {
  const icons: Record<UpdateComponent["status"], LucideIcon> = {
    up_to_date: CheckCircle2,
    update_available: RefreshCw,
    warning: AlertTriangle,
    busy: Gauge,
    unknown: Gauge,
  };
  return icons[status];
}
