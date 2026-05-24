import { AlertTriangle, Bell, CheckCircle2, Gauge, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { AlertCenterItem, AuditFinding, ChecklistItem, HealthItem, HealthResponse, UpdateComponent, UpdateStatusResponse } from "../alertCenter";
import type { BoardPreset, CalibrationExecutionRecord, CalibrationResultFormConfig, CalibrationRunRecord, CalibrationSequencePlan, CalibrationTestRecord, CanBusRecord, MaintenanceEventRecord, MaintenanceTaskRecord, OperationActionParameterSpec, OperationCapability, OperationStatusResponse, OperationTemperatureHistoryRow, PluginAuditItem, PrinterRecord, SnapshotDiffItem, SystemReleasesResponse, UpdateDialogState, ZOffsetRecord } from "../types";

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

export function validatePrinterConnectionInput(moonrakerUrl: string, sshHost: string) {
  try {
    const parsedUrl = new URL(moonrakerUrl.trim());
    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      return "A URL do Moonraker precisa começar com http:// ou https://.";
    }
    if (parsedUrl.hostname.endsWith(".loca")) {
      return `Host Moonraker inválido: use ${parsedUrl.hostname}l ou um IP.`;
    }
  } catch {
    return "URL Moonraker inválida. Exemplo: http://voron.local:7125.";
  }

  const cleanSshHost = sshHost.trim();
  if (cleanSshHost.endsWith(".loca")) {
    return `Host SSH inválido: use ${cleanSshHost}l ou um IP.`;
  }
  return null;
}

export function extractHost(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

export function formatSshStatus(printer: PrinterRecord) {
  if (!printer.ssh_host || !printer.ssh_username) {
    return "pendente";
  }
  return printer.ssh_credential_configured ? "configurado" : "sem credencial";
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

export function formatMaintenanceEventType(eventType: MaintenanceEventRecord["event_type"]) {
  const labels: Record<MaintenanceEventRecord["event_type"], string> = {
    maintenance: "manutenção",
    failure: "falha",
    adjustment: "ajuste",
    note: "nota",
  };
  return labels[eventType];
}

export function formatOptionalLocalDateTime(value?: string | null) {
  return value ? formatLocalDateTime(value) : "nunca";
}

export function formatLocalDateTime(value: string | Date) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return typeof value === "string" ? value : "-";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
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

export function formatOptionalNumber(value: number | null | undefined) {
  return typeof value === "number" ? value.toFixed(3) : "-";
}

export function formatOptionalInt(value: number | null | undefined) {
  return typeof value === "number" ? String(value) : "-";
}

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

export function formatPluginClassification(classification: PluginAuditItem["classification"]) {
  const labels: Record<PluginAuditItem["classification"], string> = {
    necessario: "necessário",
    opcional: "opcional",
    legado_lixo_tecnico: "legado/lixo técnico",
    perigoso_remover_agora: "perigoso remover agora",
    seguro_remover_depois_backup: "seguro remover depois de backup",
    precisa_confirmacao: "precisa confirmação",
  };
  return labels[classification];
}

export function formatPluginAction(action: PluginAuditItem["action"]) {
  const labels: Record<PluginAuditItem["action"], string> = {
    manter: "manter",
    investigar: "investigar",
    remover_depois_backup: "remover depois de backup",
    nao_remover_agora: "não remover agora",
  };
  return labels[action];
}

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
  return status.components.filter((component) => component.can_update || component.status === "update_available").length;
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

export function alertCenterIcon(severity: AlertCenterItem["severity"]): LucideIcon {
  const icons: Record<AlertCenterItem["severity"], LucideIcon> = {
    blocker: AlertTriangle,
    warning: AlertTriangle,
    info: Bell,
  };
  return icons[severity];
}

export function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function moonrakerWebsocketUrl(moonrakerUrl: string): string | null {
  try {
    const url = new URL(moonrakerUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/websocket";
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return null;
  }
}

export function parseMoonrakerUpdateMessage(rawData: string): { message: string; complete: boolean } | null {
  try {
    const payload = JSON.parse(rawData) as {
      method?: string;
      params?: Array<{
        application?: string;
        message?: string;
        complete?: boolean;
      }>;
    };
    if (payload.method !== "notify_update_response") {
      return null;
    }
    const response = payload.params?.[0];
    if (!response?.message) {
      return null;
    }
    const application = response.application ? `${response.application}: ` : "";
    return {
      message: `${application}${response.message}`,
      complete: Boolean(response.complete),
    };
  } catch {
    return null;
  }
}

export function formatUpdatePhase(phase: UpdateDialogState["phase"]) {
  const labels: Record<UpdateDialogState["phase"], string> = {
    confirm: "Aguardando confirmação",
    running: "Update em andamento",
    done: "Update concluído",
    failed: "Update com erro",
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

export function formatBoolean(value: boolean | null | undefined) {
  if (typeof value !== "boolean") {
    return "-";
  }
  return value ? "sim" : "não";
}

export function formatConnectionType(connectionType: BoardPreset["connection_type"]) {
  const labels: Record<BoardPreset["connection_type"], string> = {
    usb: "USB",
    can: "CAN",
    usb_can_bridge: "USB-CAN bridge",
  };
  return labels[connectionType];
}

export function formatCalibrationCategory(category: string) {
  const labels: Record<string, string> = {
    extrusao_base: "extrusão base",
    validacao_mecanica: "validação mecânica",
    nivelamento: "nivelamento",
    probe: "probe",
    primeira_camada: "primeira camada",
    material: "material",
    extrusao: "extrusão",
    movimento: "movimento",
    qualidade: "qualidade",
    temperatura: "temperatura",
    perifericos: "periféricos",
    dimensional: "dimensional",
  };
  return labels[category] ?? category;
}

export function formatExecutionMode(mode: CalibrationTestRecord["execution_mode"]) {
  const labels: Record<CalibrationTestRecord["execution_mode"], string> = {
    read_only: "somente leitura",
    manual: "manual",
    gcode_review_required: "G-code exige revisão",
    blocked_while_printing: "bloqueado imprimindo",
  };
  return labels[mode];
}

export function formatRiskLevel(riskLevel: CalibrationTestRecord["risk_level"]) {
  const labels: Record<CalibrationTestRecord["risk_level"], string> = {
    low: "baixo",
    medium: "médio",
    high: "alto",
  };
  return labels[riskLevel];
}

export function formatCalibrationResult(resultStatus: CalibrationRunRecord["result_status"]) {
  const labels: Record<CalibrationRunRecord["result_status"], string> = {
    passed: "aprovado",
    warning: "atenção",
    failed: "falhou",
    skipped: "ignorado",
  };
  return labels[resultStatus];
}

export function formatCalibrationExecutionStatus(status: string) {
  const labels: Record<string, string> = {
    executed: "executado",
    blocked: "bloqueado",
    failed: "falhou",
    failed_partial: "falhou parcialmente",
  };
  return labels[status] ?? status;
}

export function calibrationExecutionRowClass(status: string) {
  if (status === "executed") {
    return "passed";
  }
  if (status === "failed" || status === "failed_partial") {
    return "failed";
  }
  return "warning";
}

export function summarizeCalibrationExecutionFinalState(execution: CalibrationExecutionRecord) {
  const finalState = latestCalibrationExecutionFinalState(execution);
  if (!finalState) {
    return `${execution.sent_commands.length}/${execution.commands.length} comando(s) confirmado(s)`;
  }
  const klipper = typeof finalState.klipper_state === "string" ? finalState.klipper_state : "-";
  const klippy = typeof finalState.klippy_state === "string" ? finalState.klippy_state : "-";
  const printState = typeof finalState.print_state === "string" && finalState.print_state ? finalState.print_state : "-";
  const homedAxes = typeof finalState.homed_axes === "string" && finalState.homed_axes ? ` · homed ${finalState.homed_axes}` : "";
  return `Final: Klipper ${klipper} · Klippy ${klippy} · print ${printState}${homedAxes}`;
}

export function formatCalibrationExecutionResult(execution: CalibrationExecutionRecord) {
  return JSON.stringify(execution.result, null, 2);
}

export function buildCalibrationExecutionNotes(execution: CalibrationExecutionRecord) {
  const commandText = execution.sent_commands.length ? execution.sent_commands.join(", ") : "-";
  return [
    execution.message,
    summarizeCalibrationExecutionFinalState(execution),
    `Comandos confirmados: ${commandText}`,
    "Retorno final Moonraker:",
    formatCalibrationExecutionResult(execution),
  ].filter(Boolean).join("\n");
}

export function latestCalibrationExecutionFinalState(execution: CalibrationExecutionRecord) {
  for (let index = execution.result.length - 1; index >= 0; index -= 1) {
    const item = execution.result[index];
    const finalState = item.final_state;
    if (finalState && typeof finalState === "object" && !Array.isArray(finalState)) {
      return finalState as Record<string, unknown>;
    }
  }
  return null;
}

export function formatCalibrationTestTitle(testKey: string, tests: CalibrationTestRecord[]) {
  return tests.find((test) => test.test_key === testKey)?.title ?? testKey;
}

export function formatCalibrationSequenceStatus(status: CalibrationSequencePlan["steps"][number]["status"]) {
  if (status === "completed") {
    return "concluído";
  }
  if (status === "skipped") {
    return "pulado";
  }
  return "pendente";
}

export function groupCalibrationSteps(steps: CalibrationSequencePlan["steps"]) {
  const groups = new Map<string, CalibrationSequencePlan["steps"]>();
  steps.forEach((step) => {
    const current = groups.get(step.phase) ?? [];
    current.push(step);
    groups.set(step.phase, current);
  });
  return Array.from(groups.entries()).map(([phase, phaseSteps]) => ({
    phase,
    steps: phaseSteps,
    completed: phaseSteps.filter((step) => step.status === "completed").length,
  }));
}

export function formatCalibrationPhase(phase: string) {
  const labels: Record<string, string> = {
    "01_base_mecanica": "1. Base mecânica",
    "02_temperatura": "2. Temperatura",
    "03_extrusao_base": "3. Extrusão base",
    "04_probe_mesa": "4. Probe e mesa",
    "05_primeira_camada": "5. Primeira camada",
    "06_material": "6. Material e fluxo",
    "07_movimento": "7. Movimento e vibração",
    "08_acabamento": "8. Acabamento",
    "09_dimensional": "9. Dimensional",
    "10_perifericos": "10. Periféricos",
  };
  return labels[phase] ?? phase.replace(/^[0-9]+_/, "").replaceAll("_", " ");
}

export function getCalibrationResultFormConfig(test: CalibrationTestRecord): CalibrationResultFormConfig {
  const base: CalibrationResultFormConfig = {
    summary: "Registre o que foi verificado neste item. O histórico serve para liberar a próxima revisão com evidência local.",
    observedLabel: "Resultado objetivo",
    observedPlaceholder: "Ex.: aprovado sem folgas, range 0.012 mm, temperatura estável",
    notesLabel: "Evidência e observações",
    notesPlaceholder: "O que foi visto, corrigido, medido ou precisa ser revisado depois",
    showMaterial: false,
    showPlate: false,
    showNozzle: false,
  };
  if (test.test_key === "mechanical_preflight" || test.category === "validacao_mecanica") {
    return {
      ...base,
      summary: "Use este registro para confirmar a inspeção física antes de ajustes por software.",
      observedLabel: "Resumo da inspeção",
      observedPlaceholder: "Ex.: correias firmes, toolhead sem folga, cabos livres",
      notesLabel: "Problemas encontrados ou correções feitas",
      notesPlaceholder: "Ex.: reapertado parafuso X, cabo do toolhead reposicionado, sem ação necessária",
    };
  }
  if (test.category === "temperatura") {
    return {
      ...base,
      observedLabel: "Temperatura e estabilidade",
      observedPlaceholder: "Ex.: 220 °C estável, overshoot baixo, mesa estabilizou em 60 °C",
      notesLabel: "Condição do teste",
      notesPlaceholder: "Material usado, tempo de estabilização, oscilação observada ou erro do Klipper",
      showMaterial: true,
    };
  }
  if (test.category === "primeira_camada") {
    return {
      ...base,
      summary: "Este resultado deve refletir o teste real de primeira camada. Use o perfil aprovado abaixo só quando este teste estiver bom.",
      observedLabel: "Z-offset/resultado visual",
      observedPlaceholder: "Ex.: -0.295, linhas aderidas sem raspar",
      notesLabel: "Aderência e aparência",
      notesPlaceholder: "Uniformidade, cantos, excesso de esmagamento, limpeza da mesa e ajuste usado",
      showMaterial: true,
      showPlate: true,
      showNozzle: true,
    };
  }
  if (test.category === "material" || test.category === "extrusao" || test.category === "extrusao_base") {
    return {
      ...base,
      observedLabel: "Valor medido ou escolhido",
      observedPlaceholder: "Ex.: flow 0.96, PA 0.035, 18 mm3/s, extrusão real 49.6 mm",
      notesLabel: "Material, perfil e evidência",
      notesPlaceholder: "Marca/cor do filamento, perfil do slicer, peça usada, falhas ou aprovação visual",
      showMaterial: true,
      showPlate: test.category === "material",
      showNozzle: true,
    };
  }
  if (test.category === "probe" || test.category === "nivelamento") {
    return {
      ...base,
      observedLabel: "Medição ou conclusão",
      observedPlaceholder: "Ex.: probe repetível, QGL dentro da tolerância, offset XY conferido",
      notesLabel: "Condição da mesa/probe",
      notesPlaceholder: "Estado da chapa, bico limpo, range, retries, ajuste manual ou bloqueio encontrado",
      showPlate: true,
      showNozzle: true,
    };
  }
  if (test.category === "movimento" || test.category === "qualidade" || test.category === "dimensional") {
    return {
      ...base,
      observedLabel: "Medição ou artefato observado",
      observedPlaceholder: "Ex.: sem ringing visível, X 20.02 mm, sem layer shift",
      notesLabel: "Peça de teste e interpretação",
      notesPlaceholder: "Velocidade, aceleração, medidas, foto/referência e próximos ajustes",
      showMaterial: true,
      showNozzle: true,
    };
  }
  return base;
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
    set_fan: [{ name: "speed_percent", type: "number", default: 0, min: 0, max: 100 }],
    set_led: [
      { name: "led_name", type: "text", default: "" },
      { name: "brightness_percent", type: "number", default: 0, min: 0, max: 100 },
    ],
  };
  return specs[actionId] ?? [];
}

export function buildOperationActionPayload(values: Record<string, string>) {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => {
      const numericValue = Number(value);
      return [key, value.trim() !== "" && Number.isFinite(numericValue) ? numericValue : value];
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
