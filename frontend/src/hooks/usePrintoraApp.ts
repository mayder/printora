import React from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  Camera,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileText,
  Gauge,
  HelpCircle,
  History,
  Hourglass,
  Info,
  Menu,
  Moon,
  Play,
  Plus,
  Printer,
  Radio,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldAlert,
  ShieldCheck,
  SkipForward,
  SlidersHorizontal,
  Sun,
  Timer,
  Trash2,
  Undo2,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import { buildAlertCenterItems, type HealthResponse } from "../alertCenter";
import * as formatters from "../utils/formatters";
import * as selfUpdateHelpers from "../selfUpdate";
import { useAppShell } from "./domains/useAppShell";
import { useCalibration } from "./domains/useCalibration";
import { useFirmware } from "./domains/useFirmware";
import { useMaintenance } from "./domains/useMaintenance";
import { useOperation } from "./domains/useOperation";
import { usePrinters } from "./domains/usePrinters";
import { useReports } from "./domains/useReports";
import { useSelfUpdate } from "./domains/useSelfUpdate";
import { useSettings } from "./domains/useSettings";
import { useUpdates } from "./domains/useUpdates";
import type { PrinterAvailability } from "../app/navigation";
import type { ConfirmActionOptions, ConfirmDialogState, ShowToastOptions, ToastRecord } from "../types";

const icons = {
  Activity,
  AlertTriangle,
  Bell,
  CalendarDays,
  Camera,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileText,
  Gauge,
  HelpCircle,
  History,
  Hourglass,
  Info,
  Menu,
  Moon,
  Play,
  Plus,
  Printer,
  Radio,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldAlert,
  ShieldCheck,
  SkipForward,
  SlidersHorizontal,
  Sun,
  Timer,
  Trash2,
  Undo2,
  Wrench,
  X,
  Zap,
};

export function usePrintoraApp() {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = React.useState<ConfirmDialogState>({
    open: false,
    tone: "info",
    title: "",
    detail: "",
    confirmLabel: "Confirmar",
    cancelLabel: "Cancelar",
  });
  const [toasts, setToasts] = React.useState<ToastRecord[]>([]);
  const confirmResolverRef = React.useRef<((confirmed: boolean) => void) | null>(null);
  const toastIdRef = React.useRef(0);

  let operation: ReturnType<typeof useOperation>;
  let settings: ReturnType<typeof useSettings>;
  let reports: ReturnType<typeof useReports>;
  let firmware: ReturnType<typeof useFirmware>;
  let calibration: ReturnType<typeof useCalibration>;
  let maintenance: ReturnType<typeof useMaintenance>;
  let updates: ReturnType<typeof useUpdates>;

  function confirmAction(options: ConfirmActionOptions): Promise<boolean> {
    confirmResolverRef.current?.(false);
    setConfirmDialog({
      open: true,
      tone: options.tone ?? "info",
      title: options.title,
      detail: options.detail,
      evidence: options.evidence,
      confirmLabel: options.confirmLabel ?? "Confirmar",
      cancelLabel: options.cancelLabel ?? "Cancelar",
    });
    return new Promise((resolve) => {
      confirmResolverRef.current = resolve;
    });
  }

  function resolveConfirmDialog(confirmed: boolean) {
    confirmResolverRef.current?.(confirmed);
    confirmResolverRef.current = null;
    setConfirmDialog((currentDialog) => ({ ...currentDialog, open: false }));
  }

  function showToast(options: ShowToastOptions) {
    const id = toastIdRef.current + 1;
    toastIdRef.current = id;
    setToasts((currentToasts) => [
      ...currentToasts,
      {
        id,
        tone: options.tone ?? "info",
        title: options.title,
        detail: options.detail,
      },
    ].slice(-4));
    window.setTimeout(() => dismissToast(id), 5000);
  }

  function dismissToast(toastId: number) {
    setToasts((currentToasts) => currentToasts.filter((toast) => toast.id !== toastId));
  }

  async function loadPrinterLocalContext(printerId: number) {
    await Promise.allSettled([
      operation.loadOperationActionHistory(printerId),
      operation.loadOperationExecutionHistory(printerId),
      reports.loadSnapshots(printerId),
      reports.loadBackups(printerId),
      maintenance.loadMaintenance(printerId),
      calibration.loadZOffsets(printerId),
      settings.loadCanRecords(printerId),
      firmware.loadFirmwareHardwareInventory(printerId),
      firmware.loadFirmwareBoards(printerId),
      firmware.loadFirmwareBuildRuns(printerId),
      firmware.loadFirmwareFlashRuns(printerId),
      calibration.loadCalibrationRuns(printerId),
    ]);
  }

  async function loadPrinterLiveContext(printerId: number) {
    await Promise.allSettled([
      settings.loadPrinterChecklist(printerId),
      operation.loadOperationStatus(printerId),
      settings.loadPrinterAudit(printerId),
      settings.loadPrinterHealth(printerId),
      updates.loadUpdateStatus(printerId),
      calibration.loadCalibrationTests(printerId),
    ]);
  }

  async function loadPrinterContext(printerId: number) {
    await loadPrinterLocalContext(printerId);
    void loadPrinterLiveContext(printerId);
  }

  const printers = usePrinters({
    loadOperationStatus: (printerId) => operation.loadOperationStatus(printerId),
    loadPrinterContext,
    loadPrinterHealth: (printerId) => settings.loadPrinterHealth(printerId),
    loadUpdateStatus: (printerId) => updates.loadUpdateStatus(printerId),
    onSelectPrinter: () => {
      reports.setSanitizedReport(null);
      operation.resetOperationSelection();
    },
    setError,
    setLoading,
    setStatus: (value) => settings.setStatus(value),
  });

  settings = useSettings({ selectedPrinterId: printers.selectedPrinterId, setError, setLoading });
  const printerAvailability = getPrinterAvailability(printers.selectedPrinterId, settings.health);
  const shell = useAppShell(printerAvailability);
  operation = useOperation({
    selectedPrinterId: printers.selectedPrinterId,
    setActiveSection: shell.setActiveSection,
    setError,
    setLoading,
  });
  reports = useReports({
    selectedPrinterId: printers.selectedPrinterId,
    loadPrinterHealth: settings.loadPrinterHealth,
    setError,
    setLoading,
  });
  maintenance = useMaintenance({ selectedPrinterId: printers.selectedPrinterId, setError, setLoading });
  calibration = useCalibration({ selectedPrinterId: printers.selectedPrinterId, setError, setLoading });
  firmware = useFirmware({ selectedPrinterId: printers.selectedPrinterId, setError, setLoading });
  const selfUpdate = useSelfUpdate();
  updates = useUpdates({
    selectedPrinter: printers.selectedPrinter,
    selectedPrinterId: printers.selectedPrinterId,
    loadOperationStatus: operation.loadOperationStatus,
    loadPrinterAudit: settings.loadPrinterAudit,
    loadPrinterChecklist: settings.loadPrinterChecklist,
    loadPrinterHealth: settings.loadPrinterHealth,
    setActiveSection: shell.setActiveSection,
    setAlertCenterOpen: shell.setAlertCenterOpen,
    confirmAction,
    showToast,
    setError,
    setLoading,
  });

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([firmware.loadBoardPresets(), printers.loadPrinters()]);
      void settings.loadGlobalDiagnostics();
      void selfUpdate.loadSelfUpdateHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    void loadStatus();
  }, []);

  React.useEffect(() => {
    if (!printers.selectedPrinterId || shell.activeSection !== "tests") {
      return;
    }
    void calibration.loadCalibrationTests(printers.selectedPrinterId);
    void calibration.loadCalibrationRuns(printers.selectedPrinterId);
    void calibration.loadZOffsets(printers.selectedPrinterId);
  }, [shell.activeSection, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (shell.activeSection === "settings" && !selfUpdate.systemReleases && !selfUpdate.releaseLoading) {
      void selfUpdate.loadSystemReleases();
    }
    if (shell.activeSection === "reports" && printers.selectedPrinterId) {
      void settings.loadPrinterNetworkDiagnostics(printers.selectedPrinterId);
    }
  }, [shell.activeSection, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (!printers.selectedPrinterId || shell.activeSection !== "monitoring") {
      return;
    }
    void operation.loadOperationStatus(printers.selectedPrinterId, { preserveData: true });
    const refreshId = window.setInterval(() => {
      void operation.loadOperationStatus(printers.selectedPrinterId!, { preserveData: true });
      void settings.loadPrinterHealth(printers.selectedPrinterId!);
      void settings.loadCanRecords(printers.selectedPrinterId!);
    }, 5000);
    return () => window.clearInterval(refreshId);
  }, [shell.activeSection, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (!printers.selectedPrinterId || printerAvailability !== "offline") {
      return;
    }
    const refreshId = window.setInterval(() => {
      void operation.loadOperationStatus(printers.selectedPrinterId!, { preserveData: true });
      void settings.loadPrinterHealth(printers.selectedPrinterId!);
    }, 60000);
    return () => window.clearInterval(refreshId);
  }, [printerAvailability, printers.selectedPrinterId]);

  const liveOperationHealth = buildLiveOperationHealth(settings.health, operation.operationStatus);
  const alertCenterItems = buildAlertCenterItems({
    health: liveOperationHealth,
    updateStatus: updates.updateStatus,
    checklist: settings.checklist,
    audit: settings.audit,
    maintenanceTasks: maintenance.maintenanceTasks,
  });
  const alertCount = alertCenterItems.length;
  const alertBlockerCount = alertCenterItems.filter((item) => item.severity === "blocker").length;
  const alertWarningCount = alertCenterItems.filter((item) => item.severity === "warning").length;
  const primaryRiskItem = alertCenterItems.find((item) => item.severity === "blocker") ?? alertCenterItems.find((item) => item.severity === "warning") ?? null;
  const latestSnapshot = reports.snapshots[0];
  const moonrakerOnline = operation.operationStatus?.connected ?? liveOperationHealth?.connected ?? settings.status?.connected ?? false;
  const displayDecision = formatters.displayHealthDecision(liveOperationHealth);
  const operationState = operation.operationStatus?.miscellaneous.print_state ?? settings.status?.printer?.state ?? settings.health?.metrics.klipper_state ?? "-";
  const totalPrintHours = operation.operationStatus?.miscellaneous.total_print_hours;
  const riskClass = formatters.overviewRiskClass(displayDecision);
  const riskLabel = formatters.formatDecision(displayDecision);
  const lastReadingLabel = latestSnapshot
    ? `Snapshot #${latestSnapshot.id} · ${latestSnapshot.created_at}`
    : settings.health?.data_state
      ? formatters.formatChecklistDataState(settings.health.data_state)
      : "Sem leitura";
  const topbarAlertTone = alertCenterItems.some((item) => item.severity === "blocker")
    ? "danger"
    : alertCenterItems.some((item) => item.severity === "warning")
      ? "warning"
      : "ok";
  const hotendTemperature = operation.operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bedTemperature = operation.operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const topbarPrimaryAction = (() => {
    if (shell.activeSection === "printers") {
      return { icon: Plus, label: "Adicionar", disabled: loading, run: printers.openCreatePrinterModal };
    }
    if (shell.activeSection === "reports") {
      return { icon: Camera, label: "Snapshot", disabled: !printers.selectedPrinterId || loading, run: reports.captureSnapshot };
    }
    if (shell.activeSection === "updates") {
      return {
        icon: RefreshCw,
        label: "Reanalisar",
        disabled: !printers.selectedPrinterId || loading || Boolean(updates.updateStatus?.busy),
        run: () => updates.refreshUpdateStatus(),
      };
    }
    if (shell.activeSection === "settings") {
      return {
        icon: Settings,
        label: printers.selectedPrinter ? "Editar" : "Adicionar",
        disabled: loading,
        run: () => (printers.selectedPrinter ? printers.openEditPrinterModal(printers.selectedPrinter) : printers.openCreatePrinterModal()),
      };
    }
    if (shell.activeSection === "about") {
      return { icon: ShieldCheck, label: "Licença", disabled: loading, run: () => shell.setActiveSection("license") };
    }
    if (shell.activeSection === "license") {
      return { icon: Info, label: "Sobre", disabled: loading, run: () => shell.setActiveSection("about") };
    }
    return {
      icon: RefreshCw,
      label: loading ? "Atualizando" : "Atualizar",
      disabled: loading || (!printers.selectedPrinterId && shell.activeSection !== "overview"),
      run: () => (printers.selectedPrinterId ? printers.loadSelectedPrinterStatus() : loadStatus()),
    };
  })();
  const TopbarPrimaryIcon = topbarPrimaryAction.icon;

  const screenProps = {
    ...icons,
    ...formatters,
    ...selfUpdateHelpers,
    ...shell,
    ...printers,
    ...operation,
    ...settings,
    ...reports,
    ...maintenance,
    ...calibration,
    ...firmware,
    ...selfUpdate,
    ...updates,
    TopbarPrimaryIcon,
    alertCenterItems,
    alertCount,
    alertBlockerCount,
    alertWarningCount,
    bedTemperature,
    confirmDialog,
    displayDecision,
    dismissToast,
    error,
    handleAlertCenterAction: updates.handleAlertCenterAction,
    health: liveOperationHealth,
    hotendTemperature,
    lastReadingLabel,
    latestSnapshot,
    loadPrinterContext,
    loadPrinterLiveContext,
    loadPrinterLocalContext,
    loadStatus,
    loading,
    moonrakerOnline,
    operationState,
    primaryRiskItem,
    riskClass,
    riskLabel,
    resolveConfirmDialog,
    setError,
    setLoading,
    topbarAlertTone,
    topbarPrimaryAction,
    totalPrintHours,
    toasts,
  };

  return {
    ActiveIcon: shell.ActiveIcon,
    ThemeIcon: shell.ThemeIcon,
    TopbarPrimaryIcon,
    activeSection: shell.activeSection,
    activeSectionMeta: shell.activeSectionMeta,
    alertCount,
    error,
    mobileNavOpen: shell.mobileNavOpen,
    printers: printers.printers,
    screenProps,
    selectPrinter: printers.selectPrinter,
    selectedPrinter: printers.selectedPrinter,
    selectedPrinterId: printers.selectedPrinterId,
    setActiveSection: shell.setActiveSection,
    setAlertCenterOpen: shell.setAlertCenterOpen,
    setMobileNavOpen: shell.setMobileNavOpen,
    setTheme: shell.setTheme,
    theme: shell.theme,
    topbarAlertTone,
    topbarPrimaryAction,
    toasts,
    dismissToast,
    visibleNavGroups: shell.visibleNavGroups,
  };
}

function getPrinterAvailability(selectedPrinterId: number | null, health: HealthResponse | null): PrinterAvailability {
  if (!selectedPrinterId) {
    return "none";
  }
  if (!health) {
    return "unknown";
  }
  if (!health.connected) {
    return "offline";
  }
  if (health.printer_id !== selectedPrinterId) {
    return "unknown";
  }
  return health.connected ? "online" : "offline";
}

function buildLiveOperationHealth(
  health: HealthResponse | null,
  operationStatus: { connected: boolean; data_state: string; printer_id: number } | null,
): HealthResponse | null {
  if (!health || !operationStatus?.connected || operationStatus.printer_id !== health.printer_id) {
    return health;
  }
  if (health.connected && health.data_state === "live") {
    return health;
  }
  return {
    ...health,
    connected: true,
    data_state: "live",
    source: operationStatus.data_state === "live" ? "operation/status" : health.source,
    error: null,
    decision: health.decision === "nao_imprimir" ? "monitorar" : health.decision,
    summary: health.summary === "Não imprima ainda" ? "Monitorar" : health.summary,
    items: health.items.filter((item) => item.key !== "data_state" && item.key !== "moonraker_unreachable"),
  };
}

export type PrintoraScreenProps = ReturnType<typeof usePrintoraApp>["screenProps"];
