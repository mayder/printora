import type { MaintenanceEventRecord, MaintenanceTaskRecord } from "../../types";

export function formatMaintenanceEventType(eventType: MaintenanceEventRecord["event_type"]) {
  const labels: Record<MaintenanceEventRecord["event_type"], string> = {
    maintenance: "manutenção",
    failure: "falha",
    adjustment: "ajuste",
    note: "nota",
  };
  return labels[eventType];
}

export function formatDueStatus(task: MaintenanceTaskRecord) {
  if (!task.is_active) {
    return "sem lembrete";
  }
  if (task.interval_kind === "print_hours") {
    if (task.due_status === "due") {
      return "pendente";
    }
    if (task.due_status === "soon") {
      return `${formatHours(task.print_hours_until_due ?? 0)} restantes · atenção`;
    }
    if (task.due_status === "not_validated") {
      return "aguardando horas";
    }
    if (task.due_status === "needs_review") {
      return "base precisa revisão";
    }
    if (task.due_status === "unknown") {
      return "status inválido";
    }
    return `${formatHours(task.print_hours_until_due ?? 0)} restantes`;
  }
  if (task.due_status === "due") {
    return "pendente";
  }
  if (task.due_status === "soon") {
    return `${task.days_until_due ?? "-"} dias restantes · atenção`;
  }
  if (task.due_status === "unknown") {
    return "data inválida";
  }
  return `${task.days_until_due ?? "-"} dias restantes`;
}

export function formatMaintenanceInterval(task: MaintenanceTaskRecord) {
  if (task.interval_kind === "print_hours") {
    return `A cada ${formatHours(task.interval_value)} de impressão`;
  }
  return `A cada ${Math.round(task.interval_value || task.interval_days)} dias`;
}

export function formatMaintenanceIntervalValue(task: MaintenanceTaskRecord) {
  const value = task.interval_kind === "print_hours" ? task.interval_value : task.interval_value || task.interval_days;
  return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(1)));
}

export function formatPrintHoursDueLine(task: MaintenanceTaskRecord) {
  if (task.due_status === "due" && (task.last_done_print_hours === null || task.last_done_print_hours === undefined)) {
    return task.due_detail ?? "Primeira execução pendente";
  }
  if (task.due_status === "not_validated") {
    return task.due_detail ?? "Aguardando leitura de horas";
  }
  if (task.due_status === "needs_review") {
    return task.due_detail ?? "Base precisa revisão";
  }
  if (task.print_hours_until_due === null || task.print_hours_until_due === undefined) {
    return task.due_detail ?? "Sem leitura de horas";
  }
  if (task.due_status === "due") {
    const overdue = Math.max(0, (task.print_hours_delta ?? 0) - task.interval_value);
    return `Vencida há ${formatHours(overdue)}`;
  }
  return `Faltam ${formatHours(task.print_hours_until_due)}`;
}

export function formatOptionalHours(value?: number | null) {
  return value === null || value === undefined ? "pendente" : formatHours(value);
}

export function formatHours(value: number) {
  return `${Number(value.toFixed(1))}h`;
}
