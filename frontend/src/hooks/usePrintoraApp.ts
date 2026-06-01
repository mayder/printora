import React from "react";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowUpCircle,
  Bell,
  Building2,
  Camera,
  CalendarDays,
  CheckCircle2,
  CircleSlash,
  ClipboardCheck,
  Database,
  FileText,
  Gauge,
  HelpCircle,
  History,
  Hourglass,
  Info,
  KeyRound,
  LogOut,
  Menu,
  Moon,
  Play,
  Plus,
  Printer,
  Pencil,
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
  UserRound,
  Users,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import {
  buildAlertCenterItems,
  type AuditResponse,
  type ChecklistResponse,
  type HealthResponse,
  type MaintenanceTaskAlert,
  type UpdateStatusResponse,
} from "../alertCenter";
import { maintenanceApi } from "../services/maintenanceApi";
import { printerApi } from "../services/printerApi";
import { updatesApi } from "../services/updatesApi";
import * as formatters from "../utils/formatters";
import * as selfUpdateHelpers from "../selfUpdate";
import { useAppShell } from "./domains/useAppShell";
import { useAuth } from "./domains/useAuth";
import { useCalibration } from "./domains/useCalibration";
import { useFirmware } from "./domains/useFirmware";
import { useMaintenance } from "./domains/useMaintenance";
import { useOperation } from "./domains/useOperation";
import { usePrinters } from "./domains/usePrinters";
import { useReports } from "./domains/useReports";
import { useSelfUpdate } from "./domains/useSelfUpdate";
import { useSettings } from "./domains/useSettings";
import { useSetup } from "./domains/useSetup";
import { useUpdates } from "./domains/useUpdates";
import type { PrinterAvailability } from "../app/navigation";
import type { AlertCenterItem } from "../alertCenter";
import type { ConfirmActionOptions, ConfirmDialogState, PrinterRecord, ShowToastOptions, ToastRecord } from "../types";

export type PrinterDetailTab =
  | "summary"
  | "operation"
  | "updates"
  | "tests"
  | "firmware"
  | "maintenance"
  | "reports"
  | "agents";

type FleetAlertContext = {
  health: HealthResponse | null;
  updateStatus: UpdateStatusResponse | null;
  checklist: ChecklistResponse | null;
  audit: AuditResponse | null;
  maintenanceTasks: MaintenanceTaskAlert[];
};

const icons = {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowUpCircle,
  Bell,
  Building2,
  CalendarDays,
  Camera,
  CheckCircle2,
  CircleSlash,
  ClipboardCheck,
  Database,
  FileText,
  Gauge,
  HelpCircle,
  History,
  Hourglass,
  Info,
  KeyRound,
  LogOut,
  Menu,
  Moon,
  Play,
  Plus,
  Pencil,
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
  UserRound,
  Users,
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
  const [printerDetailTab, setPrinterDetailTab] = React.useState<PrinterDetailTab>("summary");
  const [selectedAgentId, setSelectedAgentId] = React.useState<number | null>(null);
  const [fleetAlertContexts, setFleetAlertContexts] = React.useState<Record<number, FleetAlertContext>>({});
  const confirmResolverRef = React.useRef<((confirmed: boolean) => void) | null>(null);
  const toastIdRef = React.useRef(0);

  let operation: ReturnType<typeof useOperation>;
  let settings: ReturnType<typeof useSettings>;
  let reports: ReturnType<typeof useReports>;
  let firmware: ReturnType<typeof useFirmware>;
  let calibration: ReturnType<typeof useCalibration>;
  let maintenance: ReturnType<typeof useMaintenance>;
  let updates: ReturnType<typeof useUpdates>;
  let setup: ReturnType<typeof useSetup>;

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
        actionLabel: options.actionLabel,
        onAction: options.onAction,
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
      calibration.loadCalibrationRuns(printerId),
      printers.loadPrinterPairing(printerId),
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

  async function loadPrinterAlertContext(printerId: number): Promise<FleetAlertContext> {
    const [healthResponse, updateResponse, checklistResponse, auditResponse, tasksResponse] = await Promise.allSettled([
      printerApi.health(printerId),
      updatesApi.status(printerId),
      printerApi.checklist(printerId),
      printerApi.audit(printerId),
      maintenanceApi.tasks(printerId),
    ]);
    const health = await jsonFromSettled<HealthResponse>(healthResponse);
    const updateStatus = await jsonFromSettled<UpdateStatusResponse>(updateResponse);
    const checklist = await jsonFromSettled<ChecklistResponse>(checklistResponse);
    const audit = await jsonFromSettled<AuditResponse>(auditResponse);
    const tasksPayload = await jsonFromSettled<{ tasks: MaintenanceTaskAlert[] }>(tasksResponse);
    return {
      health,
      updateStatus,
      checklist,
      audit,
      maintenanceTasks: tasksPayload?.tasks ?? [],
    };
  }

  async function refreshPrinterAlertContext(printerId: number) {
    const context = await loadPrinterAlertContext(printerId);
    setFleetAlertContexts((currentContexts) => ({
      ...currentContexts,
      [printerId]: context,
    }));
    if (printerId === printers.selectedPrinterId) {
      void Promise.allSettled([
        settings.loadPrinterChecklist(printerId),
        operation.loadOperationStatus(printerId, { preserveData: true }),
        settings.loadPrinterAudit(printerId),
        settings.loadPrinterHealth(printerId),
        updates.loadUpdateStatus(printerId),
        maintenance.loadMaintenance(printerId),
      ]);
    }
  }

  async function refreshFleetAlertContexts(printerList: PrinterRecord[] = printers.printers) {
    if (printerList.length === 0) {
      setFleetAlertContexts({});
      return;
    }
    const contextEntries = await Promise.all(
      printerList.map(async (printer) => [printer.id, await loadPrinterAlertContext(printer.id)] as const),
    );
    setFleetAlertContexts(Object.fromEntries(contextEntries));
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
    showToast,
  });
  const auth = useAuth({ setError, setLoading });

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
  setup = useSetup({ setError, setLoading });
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

  function openPrinterDetail(printerId = printers.selectedPrinterId, tab: PrinterDetailTab = "summary") {
    if (!printerId) {
      shell.setActiveSection("printers");
      return;
    }
    setPrinterDetailTab(tab);
    if (printerId !== printers.selectedPrinterId) {
      printers.selectPrinter(printerId);
    } else {
      void loadPrinterContext(printerId);
    }
    shell.setActiveSection("printer-detail");
  }

  function openAgentDetail(printerId: number, agentId: number) {
    setSelectedAgentId(agentId);
    if (printerId !== printers.selectedPrinterId) {
      printers.selectPrinter(printerId);
    } else {
      void printers.loadPrinterPairing(printerId);
      void printers.loadAgentSupport(printerId);
      void printers.loadAgentInstallStatus(printerId);
    }
    shell.setActiveSection("agent-detail");
  }

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const user = await auth.loadAuth();
      if (!user) {
        return;
      }
      const catalogSummaryLoad = firmware.loadFirmwareCatalogSummary();
      await Promise.allSettled([firmware.loadBoardPresets(), printers.loadPrinters()]);
      await catalogSummaryLoad;
      void settings.loadGlobalDiagnostics();
      void setup.loadSetupHistory();
      if (user.email.toLowerCase() === "breno@mayder.com.br") {
        void selfUpdate.loadSelfUpdateHistory();
      }
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
    if (!auth.authUser) {
      return;
    }
    const testsActive = shell.activeSection === "tests" || (shell.activeSection === "printer-detail" && printerDetailTab === "tests");
    if (!printers.selectedPrinterId || !testsActive) {
      return;
    }
    void calibration.loadCalibrationTests(printers.selectedPrinterId);
    void calibration.loadCalibrationRuns(printers.selectedPrinterId);
    void calibration.loadZOffsets(printers.selectedPrinterId);
  }, [auth.authUser, shell.activeSection, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (!auth.authUser) {
      return;
    }
    const isPlatformAdmin = auth.authUser.email.toLowerCase() === "breno@mayder.com.br";
    if (shell.activeSection === "settings" && isPlatformAdmin && !selfUpdate.systemReleases && !selfUpdate.releaseLoading) {
      void selfUpdate.loadSystemReleases();
    }
    if ((shell.activeSection === "reports" || (shell.activeSection === "printer-detail" && printerDetailTab === "reports")) && printers.selectedPrinterId) {
      void settings.loadPrinterNetworkDiagnostics(printers.selectedPrinterId);
      void settings.loadCanRecords(printers.selectedPrinterId);
    }
    if (shell.activeSection === "setup") {
      void setup.loadSetupHistory();
    }
    if (shell.activeSection === "account") {
      void auth.loadAuth().then(() => auth.loadAgentCredentials());
    }
    if (shell.activeSection === "overview") {
      void printers.loadFleetAgentPairings();
      void printers.loadAgentUpdateManifest();
    }
    if (shell.activeSection === "agents" || (shell.activeSection === "printer-detail" && printerDetailTab === "agents") || shell.activeSection === "agent-detail") {
      void printers.loadFleetAgentPairings();
      void printers.loadAgentUpdateManifest();
      if (printers.selectedPrinterId) {
        void printers.loadPrinterPairing(printers.selectedPrinterId);
        void printers.loadAgentSupport(printers.selectedPrinterId);
      }
    }
  }, [auth.authUser, shell.activeSection, printerDetailTab, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (!auth.authUser) {
      return;
    }
    const operationActive = shell.activeSection === "monitoring" || (shell.activeSection === "printer-detail" && printerDetailTab === "operation");
    if (!printers.selectedPrinterId || !operationActive) {
      return;
    }
    void operation.loadOperationStatus(printers.selectedPrinterId, { preserveData: true });
    const refreshId = window.setInterval(() => {
      void operation.loadOperationStatus(printers.selectedPrinterId!, { preserveData: true });
      void settings.loadPrinterHealth(printers.selectedPrinterId!);
      void settings.loadCanRecords(printers.selectedPrinterId!);
    }, 5000);
    return () => window.clearInterval(refreshId);
  }, [auth.authUser, shell.activeSection, printerDetailTab, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (!auth.authUser) {
      return;
    }
    if (!printers.selectedPrinterId || printerAvailability !== "offline") {
      return;
    }
    const refreshId = window.setInterval(() => {
      void operation.loadOperationStatus(printers.selectedPrinterId!, { preserveData: true });
      void settings.loadPrinterHealth(printers.selectedPrinterId!);
    }, 60000);
    return () => window.clearInterval(refreshId);
  }, [auth.authUser, printerAvailability, printers.selectedPrinterId]);

  React.useEffect(() => {
    if (!auth.authUser) {
      return;
    }
    void loadStatus();
  }, [auth.authUser?.id]);

  const fleetPrinterIdsKey = React.useMemo(
    () => printers.printers.map((printer) => printer.id).sort((left, right) => left - right).join(","),
    [printers.printers],
  );

  React.useEffect(() => {
    if (!auth.authUser) {
      setFleetAlertContexts({});
      return;
    }
    if (printers.printers.length === 0) {
      setFleetAlertContexts({});
      return;
    }
    void refreshFleetAlertContexts(printers.printers);
    const refreshId = window.setInterval(() => void refreshFleetAlertContexts(printers.printers), 60000);
    return () => window.clearInterval(refreshId);
  }, [auth.authUser?.id, fleetPrinterIdsKey]);

  const liveOperationHealth = buildLiveOperationHealth(settings.health, operation.operationStatus);
  const fleetPrinterAlertItems = printers.printers.flatMap((printer) => {
    const context = fleetAlertContexts[printer.id];
    if (!context) {
      return [];
    }
    return buildPrinterAlertCenterItems(printer, context);
  });
  const alertCenterItems = [...buildFleetAlertCenterItems(printers.printers), ...fleetPrinterAlertItems];
  const alertCount = alertCenterItems.length;
  const alertBlockerCount = alertCenterItems.filter((item) => item.severity === "blocker").length;
  const alertWarningCount = alertCenterItems.filter((item) => item.severity === "warning").length;
  const selectedPrinterRiskItems = printers.selectedPrinterId
    ? alertCenterItems.filter((item) => item.printerId === printers.selectedPrinterId)
    : alertCenterItems;
  const primaryRiskItem =
    selectedPrinterRiskItems.find((item) => item.severity === "blocker") ??
    selectedPrinterRiskItems.find((item) => item.severity === "warning") ??
    null;
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
      return { icon: Plus, label: "Adicionar", disabled: loading, busy: false, run: printers.openCreatePrinterModal };
    }
    if (shell.activeSection === "reports") {
      return { icon: Camera, label: "Snapshot", disabled: !printers.selectedPrinterId || loading, busy: loading, run: reports.captureSnapshot };
    }
    if (shell.activeSection === "printer-detail") {
      if (printerDetailTab === "reports") {
        return { icon: Camera, label: "Snapshot", disabled: !printers.selectedPrinterId || loading, busy: loading, run: reports.captureSnapshot };
      }
      if (printerDetailTab === "updates") {
        return {
          icon: RefreshCw,
          label: "Reanalisar",
          disabled: !printers.selectedPrinterId || loading || Boolean(updates.updateStatus?.busy),
          busy: loading || Boolean(updates.updateStatus?.busy),
          run: () => updates.refreshUpdateStatus(),
        };
      }
      if (printerDetailTab === "agents") {
        return {
          icon: ClipboardCheck,
          label: "Instalação",
          disabled: !printers.selectedPrinterId || loading,
          busy: loading,
          run: () => printers.createAgentInstallPlan(),
        };
      }
      return {
        icon: RefreshCw,
        label: loading ? "Atualizando" : "Atualizar",
        disabled: !printers.selectedPrinterId || loading,
        busy: loading,
        run: () => printers.loadSelectedPrinterStatus(),
      };
    }
    if (shell.activeSection === "updates") {
      return {
        icon: RefreshCw,
        label: "Reanalisar",
        disabled: !printers.selectedPrinterId || loading || Boolean(updates.updateStatus?.busy),
        busy: loading || Boolean(updates.updateStatus?.busy),
        run: () => updates.refreshUpdateStatus(),
      };
    }
    if (shell.activeSection === "settings") {
      return {
        icon: Settings,
        label: printers.selectedPrinter ? "Editar" : "Adicionar",
        disabled: loading,
        busy: false,
        run: () => (printers.selectedPrinter ? printers.openEditPrinterModal(printers.selectedPrinter) : printers.openCreatePrinterModal()),
      };
    }
    if (shell.activeSection === "setup") {
      return {
        icon: Server,
        label: "Gerar plano",
        disabled: loading || setup.setupBusy || !setup.setupHost.trim() || !setup.setupUsername.trim(),
        busy: loading || setup.setupBusy,
        run: () => setup.runSetupPlan(),
      };
    }
    if (shell.activeSection === "about") {
      return { icon: ShieldCheck, label: "Licença", disabled: loading, busy: false, run: () => shell.setActiveSection("license") };
    }
    if (shell.activeSection === "license") {
      return { icon: Info, label: "Sobre", disabled: loading, busy: false, run: () => shell.setActiveSection("about") };
    }
    if (shell.activeSection === "account") {
      return {
        icon: auth.authUser ? ShieldCheck : UserRound,
        label: auth.authUser ? "Sessão" : "Entrar",
        disabled: loading,
        busy: loading,
        run: () => (auth.authUser ? auth.loadAuth() : auth.submitAuth()),
      };
    }
    return {
      icon: RefreshCw,
      label: loading ? "Atualizando" : "Atualizar",
      disabled: loading || (!printers.selectedPrinterId && shell.activeSection !== "overview"),
      busy: loading,
      run: () => (printers.selectedPrinterId ? printers.loadSelectedPrinterStatus() : loadStatus()),
    };
  })();
  const TopbarPrimaryIcon = topbarPrimaryAction.icon;

  async function handleAlertCenterAction(item: AlertCenterItem) {
    const targetPrinterId = getAlertTargetPrinterId(item);
    if (targetPrinterId && item.actionKind === "open_printer") {
      openPrinterDetail(targetPrinterId, "summary");
      shell.setAlertCenterOpen(false);
      return;
    }
    if (targetPrinterId && item.actionKind === "open_updates") {
      openPrinterDetail(targetPrinterId, "updates");
      shell.setAlertCenterOpen(false);
      return;
    }
    if (targetPrinterId && item.actionKind === "run_update") {
      openPrinterDetail(targetPrinterId, "updates");
      shell.setAlertCenterOpen(false);
      return;
    }
    if (targetPrinterId && item.actionKind === "open_monitoring") {
      openPrinterDetail(targetPrinterId, "operation");
      shell.setAlertCenterOpen(false);
      return;
    }
    if (targetPrinterId && item.actionKind === "open_maintenance") {
      openPrinterDetail(targetPrinterId, "maintenance");
      shell.setAlertCenterOpen(false);
      return;
    }
    if (targetPrinterId && (item.actionKind === "refresh_update" || item.actionKind === "revalidate")) {
      setLoading(true);
      setError(null);
      try {
        await refreshPrinterAlertContext(targetPrinterId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao atualizar alertas da impressora.");
      } finally {
        setLoading(false);
      }
      return;
    }
    await updates.handleAlertCenterAction(item);
  }

  const screenProps = {
    ...icons,
    ...formatters,
    ...selfUpdateHelpers,
    ...shell,
    ...printers,
    ...operation,
    ...settings,
    ...setup,
    ...auth,
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
    confirmAction,
    confirmDialog,
    displayDecision,
    dismissToast,
    error,
    handleAlertCenterAction,
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
    openAgentDetail,
    openPrinterDetail,
    operationState,
    primaryRiskItem,
    printerDetailTab,
    riskClass,
    riskLabel,
    resolveConfirmDialog,
    setError,
    setPrinterDetailTab,
    selectedAgentId,
    setSelectedAgentId,
    setLoading,
    showToast,
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

function buildFleetAlertCenterItems(printers: PrinterRecord[]): AlertCenterItem[] {
  return printers
    .filter((printer) => printer.cloud_status !== "online")
    .map((printer) => ({
      id: `fleet-printer-${printer.id}-${printer.cloud_status}`,
      source: `Frota · ${printer.name}`,
      printerId: printer.id,
      printerName: printer.name,
      title: fleetAlertTitle(printer),
      detail: fleetAlertDetail(printer),
      action: "Abra o detalhe da impressora para ver agente, último contato, suporte e próximos passos.",
      severity: printer.cloud_status === "sem_agente" ? "info" : "warning",
      reason: "A frota possui uma impressora que não está plenamente online pelo agente.",
      actionLabel: "Abrir impressora",
      actionKind: "open_printer",
      target: `printer:${printer.id}`,
    }));
}

function buildPrinterAlertCenterItems(printer: PrinterRecord, context: FleetAlertContext): AlertCenterItem[] {
  return buildAlertCenterItems(context).map((item) => ({
    ...item,
    id: `printer-${printer.id}-${item.id}`,
    printerId: printer.id,
    printerName: printer.name,
    source: `${printer.name} · ${item.source}`,
  }));
}

async function jsonFromSettled<T>(settled: PromiseSettledResult<Response>): Promise<T | null> {
  if (settled.status !== "fulfilled" || !settled.value.ok) {
    return null;
  }
  return (await settled.value.json()) as T;
}

function getAlertTargetPrinterId(item: AlertCenterItem): number | null {
  if (item.printerId) {
    return item.printerId;
  }
  if (!item.target?.startsWith("printer:")) {
    return null;
  }
  const printerId = Number(item.target.replace("printer:", ""));
  return Number.isFinite(printerId) ? printerId : null;
}

function fleetAlertTitle(printer: PrinterRecord) {
  if (printer.cloud_status === "offline") return `${printer.name}: agente offline`;
  if (printer.cloud_status === "degradado") return `${printer.name}: agente degradado`;
  if (printer.cloud_status === "aguardando_pareamento") return `${printer.name}: aguardando pareamento`;
  if (printer.cloud_status === "revogado") return `${printer.name}: agente revogado`;
  return `${printer.name}: sem agente`;
}

function fleetAlertDetail(printer: PrinterRecord) {
  const lastSeen = printer.latest_agent_last_seen_at ? `Último contato: ${printer.latest_agent_last_seen_at}.` : "Sem último contato registrado.";
  const snapshot = printer.latest_snapshot_at ? ` Último snapshot: ${printer.latest_snapshot_at}.` : "";
  return `${lastSeen}${snapshot}`;
}
