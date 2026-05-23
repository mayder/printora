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
import { buildAlertCenterItems } from "../alertCenter";
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

  let operation: ReturnType<typeof useOperation>;
  let settings: ReturnType<typeof useSettings>;
  let reports: ReturnType<typeof useReports>;
  let firmware: ReturnType<typeof useFirmware>;
  let calibration: ReturnType<typeof useCalibration>;
  let maintenance: ReturnType<typeof useMaintenance>;
  let updates: ReturnType<typeof useUpdates>;

  async function loadPrinterLocalContext(printerId: number) {
    await Promise.allSettled([
      operation.loadOperationActionHistory(printerId),
      operation.loadOperationExecutionHistory(printerId),
      reports.loadSnapshots(printerId),
      reports.loadBackups(printerId),
      maintenance.loadMaintenance(printerId),
      calibration.loadZOffsets(printerId),
      settings.loadCanRecords(printerId),
      firmware.loadPluginAudit(printerId),
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

  const shell = useAppShell(printers.selectedPrinterId);
  operation = useOperation({
    selectedPrinterId: printers.selectedPrinterId,
    setActiveSection: shell.setActiveSection,
    setError,
    setLoading,
  });
  settings = useSettings({ selectedPrinterId: printers.selectedPrinterId, setError, setLoading });
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
    setError,
    setLoading,
  });

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([firmware.loadBoardPresets(), printers.loadPrinters()]);
      void settings.loadGlobalDiagnostics();
      void selfUpdate.loadSystemReleases();
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
    if (!printers.selectedPrinterId || !["calibration", "tests"].includes(shell.activeSection)) {
      return;
    }
    void calibration.loadCalibrationTests(printers.selectedPrinterId);
    void calibration.loadCalibrationRuns(printers.selectedPrinterId);
    if (shell.activeSection === "calibration") {
      void operation.loadOperationStatus(printers.selectedPrinterId);
      void calibration.loadZOffsets(printers.selectedPrinterId);
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

  const alertCenterItems = buildAlertCenterItems({
    health: settings.health,
    updateStatus: updates.updateStatus,
    checklist: settings.checklist,
    audit: settings.audit,
  });
  const alertCount = alertCenterItems.length;
  const primaryRiskItem = alertCenterItems.find((item) => item.severity === "blocker") ?? alertCenterItems.find((item) => item.severity === "warning") ?? null;
  const latestSnapshot = reports.snapshots[0];
  const moonrakerOnline = settings.health?.connected ?? settings.status?.connected ?? false;
  const displayDecision = formatters.displayHealthDecision(settings.health);
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
    bedTemperature,
    displayDecision,
    error,
    handleAlertCenterAction: updates.handleAlertCenterAction,
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
    setError,
    setLoading,
    topbarAlertTone,
    topbarPrimaryAction,
    totalPrintHours,
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
    visibleNavGroups: shell.visibleNavGroups,
  };
}

export type PrintoraScreenProps = ReturnType<typeof usePrintoraApp>["screenProps"];
