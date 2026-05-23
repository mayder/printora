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
  Home,
  History,
  Hourglass,
  ListChecks,
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
  ShieldCheck,
  ShieldAlert,
  SkipForward,
  SlidersHorizontal,
  Timer,
  Sun,
  Trash2,
  Undo2,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import { useSelectedPrinterPreference } from "../selectedPrinterPreference";
import { appSections, getInitialSection, navGroups, onlinePrinterSections, selectedPrinterLocalSections, type AppSection } from "../app/navigation";
import type {
  MoonrakerStatus,
  DiscoveredPrinter,
  PrinterDiscoveryResponse,
  ConnectionCheckResult,
  PrinterConnectionTestResponse,
  PrinterRecord,
  SnapshotRecord,
  SnapshotDiffItem,
  SnapshotDiff,
  OperationMetric,
  OperationTemperature,
  OperationFan,
  OperationTemperatureHistoryRow,
  OperationAction,
  OperationCapability,
  OperationActionPreview,
  OperationActionParameterSpec,
  OperationActionPreviewRecord,
  OperationActionExecutionAttempt,
  OperationStatusResponse,
  BackupPolicyRecord,
  BackupRunRecord,
  BackupArchiveCompareResponse,
  BackupRestorePlanResponse,
  SanitizedReport,
  MaintenanceEventRecord,
  MaintenanceTaskRecord,
  MaintenanceSummary,
  MaintenancePrintHoursStatus,
  ZOffsetRecord,
  ZOffsetWizardPlan,
  CanBusRecord,
  CanBusSummary,
  CanBusRecordComparison,
  PluginAuditItem,
  PluginAuditResponse,
  ReleaseRecord,
  SystemReleasesResponse,
  UpdateActionResponse,
  UpdateLogEntry,
  UpdateDialogState,
  BoardPreset,
  FirmwareBoardRecord,
  FirmwareBuildRunRecord,
  FirmwareBuildPreflight,
  FirmwareFlashRunRecord,
  FirmwareFlashPreflight,
  FirmwareRecoveryPlan,
  BackupRestoreGateResponse,
  CalibrationTestRecord,
  CalibrationAvailableTestsResponse,
  CalibrationRunRecord,
  CalibrationResultFormConfig,
  CalibrationSummary,
  CalibrationSequencePlan,
  CalibrationPreflight,
  CalibrationExecutionRecord,
  ThemeMode
} from "../types";
import {
  formatClassification,
  formatMetricLabel,
  validatePrinterConnectionInput,
  extractHost,
  formatSshStatus,
  formatSeverity,
  formatHealthSeverity,
  formatRedaction,
  formatMaintenanceEventType,
  formatOptionalLocalDateTime,
  formatLocalDateTime,
  formatDueStatus,
  formatMaintenanceInterval,
  formatMaintenanceIntervalValue,
  formatPrintHoursDueLine,
  formatOptionalHours,
  formatHours,
  formatLatestZOffset,
  formatZOffsetAlert,
  formatOptionalNumber,
  formatOptionalInt,
  formatLatestCan,
  formatCanAlert,
  formatPluginClassification,
  formatPluginAction,
  formatUpdateStatus,
  formatReleaseUpdateStatus,
  formatReleaseSourceStatus,
  releaseStatusPillClass,
  releasePanelClass,
  countPendingUpdates,
  isUpdateTargetConfirmedUpdated,
  alertCenterIcon,
  delay,
  moonrakerWebsocketUrl,
  parseMoonrakerUpdateMessage,
  formatUpdatePhase,
  updatePhaseIcon,
  updateStatusIcon,
  formatBoolean,
  formatConnectionType,
  formatCalibrationCategory,
  formatExecutionMode,
  formatRiskLevel,
  formatCalibrationResult,
  formatCalibrationExecutionStatus,
  calibrationExecutionRowClass,
  summarizeCalibrationExecutionFinalState,
  formatCalibrationExecutionResult,
  buildCalibrationExecutionNotes,
  latestCalibrationExecutionFinalState,
  formatCalibrationTestTitle,
  formatCalibrationSequenceStatus,
  groupCalibrationSteps,
  formatCalibrationPhase,
  getCalibrationResultFormConfig,
  confirmedWizardSteps,
  formatDecision,
  displayHealthDecision,
  healthPanelClass,
  overviewRiskClass,
  healthFindingClass,
  checklistDotClass,
  formatChecklistDataState,
  buildTemperatureSeries,
  temperatureBarHeight,
  operationActionParameterSpecs,
  buildOperationActionPayload,
  formatOperationParameterLabel,
  formatOperationActionId,
  formatOperationCapabilityStatus,
  formatRollbackPlan,
  formatOperationDataState,
  formatOperationValue,
  formatTemperature,
  formatPercent,
  formatPosition,
  formatUnknown
} from "../utils/formatters";
import { backupApi } from "../services/backupApi";
import { calibrationApi } from "../services/calibrationApi";
import { canApi } from "../services/canApi";
import { diagnosticsApi } from "../services/diagnosticsApi";
import { firmwareApi } from "../services/firmwareApi";
import { maintenanceApi } from "../services/maintenanceApi";
import { operationApi } from "../services/operationApi";
import { pluginApi } from "../services/pluginApi";
import { printerApi } from "../services/printerApi";
import { reportsApi } from "../services/reportsApi";
import { systemApi } from "../services/systemApi";
import { updatesApi } from "../services/updatesApi";
import { zOffsetApi } from "../services/zOffsetApi";
import { readApiError } from "../services/http";
import {
  buildAlertCenterItems,
  type AlertCenterItem,
  type AuditFinding,
  type AuditResponse,
  type ChecklistItem,
  type ChecklistResponse,
  type HealthItem,
  type HealthResponse,
  type UpdateComponent,
  type UpdateStatusResponse,
} from "../alertCenter";
import {
  canRollbackSelfUpdateRun,
  formatSelfUpdateEnvironment,
  formatSelfUpdateStatus,
  formatSelfUpdateStepStatus,
  isSelfUpdateEnvironmentSupported,
  selfUpdateCompletedStepCount,
  selfUpdateProgressPercent,
  selfUpdateRunClass,
  selfUpdateStepClass,
  selfUpdateStepDetail,
  visibleSelfUpdateSteps,
} from "../selfUpdate";
import type {
  SelfUpdateApplyResponse,
  SelfUpdateHistoryResponse,
  SelfUpdatePlanResponse,
  SelfUpdateRollbackResponse,
  SelfUpdateRunRecord,
} from "../selfUpdate";

export function usePrintoraApp() {
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = useSelectedPrinterPreference();
  const [activeSection, setActiveSection] = React.useState<AppSection>(() => getInitialSection());
  const [discovery, setDiscovery] = React.useState<PrinterDiscoveryResponse | null>(null);
  const [printerModalOpen, setPrinterModalOpen] = React.useState(false);
  const [printerModalMode, setPrinterModalMode] = React.useState<"create" | "edit">("create");
  const [editingPrinterId, setEditingPrinterId] = React.useState<number | null>(null);
  const [theme, setTheme] = React.useState<ThemeMode>(() => {
    const storedTheme = window.localStorage.getItem("printora-theme");
    return storedTheme === "light" ? "light" : "dark";
  });
  const [newPrinterName, setNewPrinterName] = React.useState("Voron - Mayder");
  const [newPrinterUrl, setNewPrinterUrl] = React.useState("http://voron.local:7125");
  const [newPrinterSshHost, setNewPrinterSshHost] = React.useState("");
  const [newPrinterSshPort, setNewPrinterSshPort] = React.useState(22);
  const [newPrinterSshUser, setNewPrinterSshUser] = React.useState("");
  const [newPrinterSshCredential, setNewPrinterSshCredential] = React.useState("");
  const [printerConnectionTest, setPrinterConnectionTest] = React.useState<PrinterConnectionTestResponse | null>(null);
  const [snapshots, setSnapshots] = React.useState<SnapshotRecord[]>([]);
  const [fromSnapshotId, setFromSnapshotId] = React.useState<number | null>(null);
  const [toSnapshotId, setToSnapshotId] = React.useState<number | null>(null);
  const [snapshotDiff, setSnapshotDiff] = React.useState<SnapshotDiff | null>(null);
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [operationStatus, setOperationStatus] = React.useState<OperationStatusResponse | null>(null);
  const [operationActionPreview, setOperationActionPreview] = React.useState<OperationActionPreview | null>(null);
  const [operationActionHistory, setOperationActionHistory] = React.useState<OperationActionPreviewRecord[]>([]);
  const [operationExecutionHistory, setOperationExecutionHistory] = React.useState<OperationActionExecutionAttempt[]>([]);
  const [operationActionParameters, setOperationActionParameters] = React.useState<Record<string, Record<string, string>>>({});
  const [operationExecutionPhrase, setOperationExecutionPhrase] = React.useState("");
  const [operationExecutionAttempt, setOperationExecutionAttempt] = React.useState<OperationActionExecutionAttempt | null>(null);
  const [updateStatus, setUpdateStatus] = React.useState<UpdateStatusResponse | null>(null);
  const [systemReleases, setSystemReleases] = React.useState<SystemReleasesResponse | null>(null);
  const [releaseLoading, setReleaseLoading] = React.useState(false);
  const [releaseError, setReleaseError] = React.useState<string | null>(null);
  const displayedReleaseRows = React.useMemo(() => {
    if (!systemReleases) {
      return [];
    }
    return systemReleases.releases.filter((release) => release.tag !== systemReleases.latest_release?.tag);
  }, [systemReleases]);
  const [selfUpdatePlan, setSelfUpdatePlan] = React.useState<SelfUpdatePlanResponse | null>(null);
  const [selfUpdateHistory, setSelfUpdateHistory] = React.useState<SelfUpdateRunRecord[]>([]);
  const [selfUpdateModalOpen, setSelfUpdateModalOpen] = React.useState(false);
  const [selfUpdateApplying, setSelfUpdateApplying] = React.useState(false);
  const [selfUpdateRollingBack, setSelfUpdateRollingBack] = React.useState(false);
  const [selfUpdateConfirmation, setSelfUpdateConfirmation] = React.useState("");
  const [selfUpdateRollbackConfirmation, setSelfUpdateRollbackConfirmation] = React.useState("");
  const [selfUpdateMessage, setSelfUpdateMessage] = React.useState<string | null>(null);
  const [selfUpdateConnectionLost, setSelfUpdateConnectionLost] = React.useState(false);
  const [updateActionResult, setUpdateActionResult] = React.useState<UpdateActionResponse | null>(null);
  const [updateDialog, setUpdateDialog] = React.useState<UpdateDialogState | null>(null);
  const [updateLogs, setUpdateLogs] = React.useState<UpdateLogEntry[]>([]);
  const [alertCenterOpen, setAlertCenterOpen] = React.useState(false);
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
  const [audit, setAudit] = React.useState<AuditResponse | null>(null);
  const [hostAudit, setHostAudit] = React.useState<AuditResponse | null>(null);
  const [backupPolicies, setBackupPolicies] = React.useState<BackupPolicyRecord[]>([]);
  const [backupRuns, setBackupRuns] = React.useState<BackupRunRecord[]>([]);
  const [backupCompareResult, setBackupCompareResult] = React.useState<BackupArchiveCompareResponse | null>(null);
  const [backupRestorePlan, setBackupRestorePlan] = React.useState<BackupRestorePlanResponse | null>(null);
  const [backupRestoreGate, setBackupRestoreGate] = React.useState<BackupRestoreGateResponse | null>(null);
  const [sanitizedReport, setSanitizedReport] = React.useState<SanitizedReport | null>(null);
  const [maintenanceEvents, setMaintenanceEvents] = React.useState<MaintenanceEventRecord[]>([]);
  const [maintenanceTasks, setMaintenanceTasks] = React.useState<MaintenanceTaskRecord[]>([]);
  const [maintenanceSummary, setMaintenanceSummary] = React.useState<MaintenanceSummary | null>(null);
  const [maintenancePrintHours, setMaintenancePrintHours] = React.useState<MaintenancePrintHoursStatus | null>(null);
  const [zOffsetRecords, setZOffsetRecords] = React.useState<ZOffsetRecord[]>([]);
  const [canRecords, setCanRecords] = React.useState<CanBusRecord[]>([]);
  const [canSummary, setCanSummary] = React.useState<CanBusSummary | null>(null);
  const [canComparison, setCanComparison] = React.useState<CanBusRecordComparison | null>(null);
  const [pluginAudit, setPluginAudit] = React.useState<PluginAuditResponse | null>(null);
  const [boardPresets, setBoardPresets] = React.useState<BoardPreset[]>([]);
  const [firmwareBoards, setFirmwareBoards] = React.useState<FirmwareBoardRecord[]>([]);
  const [firmwareBuildRuns, setFirmwareBuildRuns] = React.useState<FirmwareBuildRunRecord[]>([]);
  const [firmwareFlashRuns, setFirmwareFlashRuns] = React.useState<FirmwareFlashRunRecord[]>([]);
  const [firmwareRecoveryPlan, setFirmwareRecoveryPlan] = React.useState<FirmwareRecoveryPlan | null>(null);
  const [firmwareBuildPreflight, setFirmwareBuildPreflight] = React.useState<FirmwareBuildPreflight | null>(null);
  const [firmwareFlashPreflight, setFirmwareFlashPreflight] = React.useState<FirmwareFlashPreflight | null>(null);
  const [calibrationTests, setCalibrationTests] = React.useState<CalibrationTestRecord[]>([]);
  const [calibrationHiddenTests, setCalibrationHiddenTests] = React.useState<CalibrationAvailableTestsResponse["hidden_tests"]>([]);
  const [calibrationRuns, setCalibrationRuns] = React.useState<CalibrationRunRecord[]>([]);
  const [calibrationSummary, setCalibrationSummary] = React.useState<CalibrationSummary | null>(null);
  const [calibrationSequence, setCalibrationSequence] = React.useState<CalibrationSequencePlan | null>(null);
  const [calibrationPreflight, setCalibrationPreflight] = React.useState<CalibrationPreflight | null>(null);
  const [calibrationExecutions, setCalibrationExecutions] = React.useState<CalibrationExecutionRecord[]>([]);
  const [calibrationExecutionResult, setCalibrationExecutionResult] = React.useState<CalibrationExecutionRecord | null>(null);
  const [calibrationHelpTestKey, setCalibrationHelpTestKey] = React.useState<string | null>(null);
  const [calibrationExecuteTestKey, setCalibrationExecuteTestKey] = React.useState<string | null>(null);
  const [calibrationResultTestKey, setCalibrationResultTestKey] = React.useState<string | null>(null);
  const [calibrationResultFormOpen, setCalibrationResultFormOpen] = React.useState(false);
  const [calibrationActivityCleared, setCalibrationActivityCleared] = React.useState(false);
  const [testFilter, setTestFilter] = React.useState<"all" | "executable" | "manual" | "blocked">("all");
  const [maintenanceFilter, setMaintenanceFilter] = React.useState<"all" | "due" | "soon" | "ok">("all");
  const [firmwareFilter, setFirmwareFilter] = React.useState<"all" | "can" | "usb">("all");
  const [zOffsetWizardPlan, setZOffsetWizardPlan] = React.useState<ZOffsetWizardPlan | null>(null);
  const [zOffsetWizardChecks, setZOffsetWizardChecks] = React.useState<Record<string, boolean>>({});
  const [zOffsetFormOpen, setZOffsetFormOpen] = React.useState(false);
  const [maintenanceEventType, setMaintenanceEventType] =
    React.useState<MaintenanceEventRecord["event_type"] | "">("");
  const [maintenanceComponent, setMaintenanceComponent] = React.useState("");
  const [maintenanceTitle, setMaintenanceTitle] = React.useState("");
  const [maintenanceNotes, setMaintenanceNotes] = React.useState("");
  const [maintenanceDoneTask, setMaintenanceDoneTask] = React.useState<MaintenanceTaskRecord | null>(null);
  const [maintenanceDoneNotes, setMaintenanceDoneNotes] = React.useState("");
  const [maintenanceDoneIntervalKind, setMaintenanceDoneIntervalKind] = React.useState<"days" | "print_hours">("days");
  const [maintenanceDoneIntervalValue, setMaintenanceDoneIntervalValue] = React.useState("");
  const [maintenanceDoneDisableReminder, setMaintenanceDoneDisableReminder] = React.useState(false);
  const [maintenanceFreeModalOpen, setMaintenanceFreeModalOpen] = React.useState(false);
  const [maintenanceFreeReminderEnabled, setMaintenanceFreeReminderEnabled] = React.useState(false);
  const [maintenanceFreeIntervalKind, setMaintenanceFreeIntervalKind] = React.useState<"days" | "print_hours">("days");
  const [maintenanceFreeIntervalValue, setMaintenanceFreeIntervalValue] = React.useState("");
  const [zOffsetPlateName, setZOffsetPlateName] = React.useState("");
  const [zOffsetMaterial, setZOffsetMaterial] = React.useState("");
  const [zOffsetNozzle, setZOffsetNozzle] = React.useState("");
  const [zOffsetValue, setZOffsetValue] = React.useState("");
  const [zOffsetNotes, setZOffsetNotes] = React.useState("");
  const [canInterfaceName, setCanInterfaceName] = React.useState("can0");
  const [canRxError, setCanRxError] = React.useState(0);
  const [canTxError, setCanTxError] = React.useState(0);
  const [canTxRetries, setCanTxRetries] = React.useState(0);
  const [canBusState, setCanBusState] = React.useState("ERROR-ACTIVE");
  const [canBitrate, setCanBitrate] = React.useState(1000000);
  const [canNotes, setCanNotes] = React.useState("");
  const [canRawOutput, setCanRawOutput] = React.useState("");
  const [firmwareBoardName, setFirmwareBoardName] = React.useState("EBB T0");
  const [firmwareBoardPresetId, setFirmwareBoardPresetId] = React.useState("btt_ebb36_g0b1_can");
  const [firmwareBoardCanUuid, setFirmwareBoardCanUuid] = React.useState("");
  const [firmwareBoardCanInterface, setFirmwareBoardCanInterface] = React.useState("can0");
  const [firmwareBoardConfigFile, setFirmwareBoardConfigFile] = React.useState("firmware/ebb_t0.config");
  const [firmwareBoardNotes, setFirmwareBoardNotes] = React.useState("");
  const [firmwareKlipperPath, setFirmwareKlipperPath] = React.useState("~/klipper");
  const [firmwareOutputRoot, setFirmwareOutputRoot] = React.useState("~/printer_data/firmware_builds");
  const [firmwareBuildConfirmation, setFirmwareBuildConfirmation] = React.useState("");
  const [firmwareFlashBinaryPath, setFirmwareFlashBinaryPath] = React.useState("");
  const [firmwareFlashConfirmation, setFirmwareFlashConfirmation] = React.useState("");
  const [calibrationTestKey, setCalibrationTestKey] = React.useState("probe_accuracy_center");
  const [calibrationResultStatus, setCalibrationResultStatus] =
    React.useState<CalibrationRunRecord["result_status"]>("passed");
  const [calibrationMaterial, setCalibrationMaterial] = React.useState("PLA");
  const [calibrationPlateName, setCalibrationPlateName] = React.useState("Texturizada");
  const [calibrationNozzle, setCalibrationNozzle] = React.useState("T0");
  const [calibrationObservedValue, setCalibrationObservedValue] = React.useState("");
  const [calibrationNotes, setCalibrationNotes] = React.useState("");
  const [calibrationGcodeReviewed, setCalibrationGcodeReviewed] = React.useState(false);
  const [calibrationPhotoReference, setCalibrationPhotoReference] = React.useState("");
  const [calibrationOperatorPresent, setCalibrationOperatorPresent] = React.useState(false);
  const [calibrationExecutionConfirmation, setCalibrationExecutionConfirmation] = React.useState("");
  const [backupName, setBackupName] = React.useState("Config backup");
  const [backupSourcePath, setBackupSourcePath] = React.useState("/home/pi/printer_data/config");
  const [backupDestinationPath, setBackupDestinationPath] = React.useState("/home/pi/printer_data/backups/printora");
  const [backupDryRunOnly, setBackupDryRunOnly] = React.useState(true);
  const [backupCompareBasePath, setBackupCompareBasePath] = React.useState("");
  const [backupCompareTargetPath, setBackupCompareTargetPath] = React.useState("");
  const [backupRestoreArchivePath, setBackupRestoreArchivePath] = React.useState("");
  const [backupRestoreRoot, setBackupRestoreRoot] = React.useState("/home/pi/printer_data/config");
  const [backupRestoreFiles, setBackupRestoreFiles] = React.useState("printer.cfg");
  const [backupRestoreConfirmation, setBackupRestoreConfirmation] = React.useState("");
  const updateSocketRef = React.useRef<WebSocket | null>(null);
  const updateLogIdRef = React.useRef(0);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([loadBoardPresets(), loadPrinters()]);
      void loadGlobalDiagnostics();
      void loadSystemReleases();
      void loadSelfUpdateHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadGlobalDiagnostics() {
    const [statusResponse, checklistResponse, hostAuditResponse] = await Promise.allSettled([
      diagnosticsApi.moonrakerStatus(),
      diagnosticsApi.postUpdateChecklist(),
      diagnosticsApi.hostReadOnlyAudit(),
    ]);
    if (statusResponse.status === "fulfilled" && statusResponse.value.ok) {
      setStatus((await statusResponse.value.json()) as MoonrakerStatus);
    }
    if (checklistResponse.status === "fulfilled" && checklistResponse.value.ok) {
      setChecklist((await checklistResponse.value.json()) as ChecklistResponse);
    }
    if (hostAuditResponse.status === "fulfilled" && hostAuditResponse.value.ok) {
      setHostAudit((await hostAuditResponse.value.json()) as AuditResponse);
    }
  }

  async function loadSystemReleases() {
    setReleaseLoading(true);
    setReleaseError(null);
    try {
      const response = await systemApi.releases();
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setSystemReleases((await response.json()) as SystemReleasesResponse);
    } catch (err) {
      setReleaseError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setReleaseLoading(false);
    }
  }

  async function loadSelfUpdateHistory() {
    try {
      const response = await systemApi.updateHistory();
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as SelfUpdateHistoryResponse;
      setSelfUpdateHistory(payload.runs);
    } catch {
      // Histórico não deve bloquear o restante da tela.
    }
  }

  async function planSelfUpdate() {
    const targetTag = systemReleases?.latest_release?.tag;
    if (!targetTag) {
      return;
    }
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    setReleaseLoading(true);
    try {
      const response = await systemApi.planUpdate({
          target_tag: targetTag,
          source_url: systemReleases.latest_release?.url ?? null,
        });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdatePlanResponse;
      setSelfUpdatePlan(payload);
      setSelfUpdateConfirmation("");
      setSelfUpdateRollbackConfirmation("");
      setSelfUpdateModalOpen(true);
      await loadSelfUpdateHistory();
    } catch (err) {
      setSelfUpdateMessage(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setReleaseLoading(false);
    }
  }

  async function startSelfUpdateFlow() {
    const plannedRun = selfUpdatePlan?.run;
    if (plannedRun && plannedRun.target_tag === systemReleases?.latest_release?.tag && plannedRun.status === "planned") return void setSelfUpdateModalOpen(true);
    await planSelfUpdate();
  }

  async function applySelfUpdate() {
    const targetTag = selfUpdatePlan?.run.target_tag ?? systemReleases?.latest_release?.tag;
    if (!targetTag) {
      return;
    }
    setSelfUpdateApplying(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await systemApi.applyUpdate({
          target_tag: targetTag,
          source_url: systemReleases?.latest_release?.url ?? selfUpdatePlan?.run.source_url ?? null,
          confirmation_phrase: selfUpdateConfirmation,
        });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateApplyResponse;
      setSelfUpdatePlan({
        safe_mode: "apply",
        update_supported: isSelfUpdateEnvironmentSupported(payload.run.environment),
        can_apply: false,
        message: payload.message,
        run: payload.run,
      });
      setSelfUpdateMessage(payload.message);
      const finalRun = await pollSelfUpdateRun(payload.run.id);
      await loadSelfUpdateHistory();
      if (finalRun?.status === "succeeded" || finalRun?.status === "rolled_back") {
        await loadSystemReleases();
      }
    } catch (err) {
      setSelfUpdateConnectionLost(true);
      setSelfUpdateMessage(err instanceof Error ? err.message : "O Printora pode estar reiniciando. Aguarde e recarregue.");
    } finally {
      setSelfUpdateApplying(false);
    }
  }

  async function pollSelfUpdateRun(runId: number): Promise<SelfUpdateRunRecord | null> {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      try {
        const response = await systemApi.updateRun(runId);
        if (!response.ok) {
          throw new Error(await readApiError(response));
        }
        const run = (await response.json()) as SelfUpdateRunRecord;
        setSelfUpdatePlan((current) =>
          current ? { ...current, run, message: current.message } : { safe_mode: "poll", update_supported: isSelfUpdateEnvironmentSupported(run.environment), can_apply: false, message: "Status atualizado.", run },
        );
        if (run.status !== "running") {
          return run;
        }
      } catch {
        setSelfUpdateConnectionLost(true);
        setSelfUpdateMessage("O Printora pode estar reiniciando. Aguarde e recarregue.");
        window.setTimeout(() => {
          void loadSystemReleases();
          void loadSelfUpdateHistory();
        }, 8000);
        return null;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 2000));
    }
    return null;
  }

  async function rollbackSelfUpdate(runId: number) {
    setSelfUpdateRollingBack(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await systemApi.rollbackUpdate({
          run_id: runId,
          confirmation_phrase: selfUpdateRollbackConfirmation,
        });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateRollbackResponse;
      setSelfUpdatePlan({
        safe_mode: "rollback",
        update_supported: isSelfUpdateEnvironmentSupported(payload.rollback_run.environment),
        can_apply: false,
        message: payload.message,
        run: payload.rollback_run,
      });
      setSelfUpdateMessage(payload.message);
      const finalRun = await pollSelfUpdateRun(payload.rollback_run.id);
      await loadSelfUpdateHistory();
      if (finalRun?.status === "succeeded" || finalRun?.status === "rolled_back") {
        await loadSystemReleases();
      }
    } catch (err) {
      setSelfUpdateConnectionLost(true);
      setSelfUpdateMessage(err instanceof Error ? err.message : "O Printora pode estar reiniciando. Aguarde e recarregue.");
    } finally {
      setSelfUpdateRollingBack(false);
    }
  }

  async function loadPrinters() {
    const response = await printerApi.list();
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { printers: PrinterRecord[] };
    setPrinters(payload.printers);
    const nextSelected = payload.printers.some((printer) => printer.id === selectedPrinterId) ? selectedPrinterId : payload.printers[0]?.id ?? null;
    setSelectedPrinterId(nextSelected);
    if (nextSelected) {
      await loadPrinterContext(nextSelected);
    }
  }

  async function loadPrinterContext(printerId: number) {
    await loadPrinterLocalContext(printerId);
    void loadPrinterLiveContext(printerId);
  }

  async function loadPrinterLocalContext(printerId: number) {
    await Promise.allSettled([
      loadOperationActionHistory(printerId),
      loadOperationExecutionHistory(printerId),
      loadSnapshots(printerId),
      loadBackups(printerId),
      loadMaintenance(printerId),
      loadZOffsets(printerId),
      loadCanRecords(printerId),
      loadPluginAudit(printerId),
      loadFirmwareBoards(printerId),
      loadFirmwareBuildRuns(printerId),
      loadFirmwareFlashRuns(printerId),
      loadCalibrationRuns(printerId),
    ]);
  }

  async function loadPrinterLiveContext(printerId: number) {
    await Promise.allSettled([
      loadPrinterChecklist(printerId),
      loadOperationStatus(printerId),
      loadPrinterAudit(printerId),
      loadPrinterHealth(printerId),
      loadUpdateStatus(printerId),
      loadCalibrationTests(printerId),
    ]);
  }

  async function loadPrinterChecklist(printerId: number) {
    const response = await printerApi.checklist(printerId);
    if (!response.ok) {
      setChecklist(null);
      return;
    }
    setChecklist((await response.json()) as ChecklistResponse);
  }

  async function loadPrinterAudit(printerId: number) {
    setAudit(null);
    const response = await printerApi.audit(printerId);
    if (!response.ok) {
      return;
    }
    setAudit((await response.json()) as AuditResponse);
  }

  async function loadOperationStatus(printerId: number, options?: { preserveData?: boolean }) {
    if (!options?.preserveData) {
      setOperationStatus(null);
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    }
    const response = await operationApi.status(printerId);
    if (!response.ok) {
      return;
    }
    setOperationStatus((await response.json()) as OperationStatusResponse);
  }

  async function loadOperationActionHistory(printerId: number) {
    const response = await operationApi.actionHistory(printerId);
    if (!response.ok) {
      setOperationActionHistory([]);
      return;
    }
    const payload = (await response.json()) as { previews: OperationActionPreviewRecord[] };
    setOperationActionHistory(payload.previews);
  }

  async function loadOperationExecutionHistory(printerId: number) {
    const response = await operationApi.executionHistory(printerId);
    if (!response.ok) {
      setOperationExecutionHistory([]);
      return;
    }
    const payload = (await response.json()) as { attempts: OperationActionExecutionAttempt[] };
    setOperationExecutionHistory(payload.attempts);
  }

  async function loadOfflineOperationFixture() {
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.offlineFixture();
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationStatus((await response.json()) as OperationStatusResponse);
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
      setActiveSection("operation");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function previewOperationAction(action: OperationAction) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para gerar a prévia da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.preview(selectedPrinterId, { action_id: action.id, parameters: buildOperationActionPayload(operationActionParameters[action.id] ?? {}) });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationActionPreview((await response.json()) as OperationActionPreview);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
      await loadOperationActionHistory(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function preflightOperationAction(action: OperationAction) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para validar o preflight da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.preflight(selectedPrinterId, { action_id: action.id, parameters: buildOperationActionPayload(operationActionParameters[action.id] ?? {}) });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationActionPreview((await response.json()) as OperationActionPreview);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function updateOperationActionParameter(actionId: string, parameterName: string, value: string) {
    setOperationActionParameters((current) => ({
      ...current,
      [actionId]: {
        ...(current[actionId] ?? {}),
        [parameterName]: value,
      },
    }));
  }

  async function validateOperationExecutionGate() {
    if (!selectedPrinterId || !operationActionPreview?.history_id) {
      setError("Gere uma prévia antes de validar a execução.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.execute(selectedPrinterId, {
          preview_id: operationActionPreview.history_id,
          confirmation_phrase: operationExecutionPhrase,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationExecutionAttempt((await response.json()) as OperationActionExecutionAttempt);
      await loadOperationExecutionHistory(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function selectPrinter(printerId: number) {
    setSelectedPrinterId(printerId);
    setSanitizedReport(null);
    setOperationActionHistory([]);
    setOperationExecutionHistory([]);
    setOperationExecutionPhrase("");
    setOperationExecutionAttempt(null);
    void loadPrinterContext(printerId);
  }

  async function createPrinter(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const validationError = validatePrinterConnectionInput(newPrinterUrl, newPrinterSshHost);
      if (validationError) {
        setError(validationError);
        return;
      }
      const payload = {
        name: newPrinterName.trim(),
        moonraker_url: newPrinterUrl.trim(),
        host_audit_mode: newPrinterSshHost && newPrinterSshUser ? "ssh" : "local",
        ssh_host: newPrinterSshHost.trim() || null,
        ssh_port: newPrinterSshPort,
        ssh_username: newPrinterSshUser.trim() || null,
        ssh_credential: newPrinterSshCredential || null,
      };
      const response = await printerApi.save(printerModalMode === "edit" ? editingPrinterId : null, payload);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const created = (await response.json()) as PrinterRecord;
      await loadPrinters();
      setSelectedPrinterId(created.id);
      await loadPrinterContext(created.id);
      setPrinterModalOpen(false);
      setNewPrinterSshCredential("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function discoverPrinters() {
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.discover();
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setDiscovery((await response.json()) as PrinterDiscoveryResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function testPrinterConnections() {
    setLoading(true);
    setError(null);
    setPrinterConnectionTest(null);
    try {
      const validationError = validatePrinterConnectionInput(newPrinterUrl, newPrinterSshHost);
      if (validationError) {
        setError(validationError);
        return;
      }
      const response = await printerApi.testConnection({
          moonraker_url: newPrinterUrl.trim(),
          ssh_host: newPrinterSshHost.trim() || null,
          ssh_port: newPrinterSshPort,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setPrinterConnectionTest((await response.json()) as PrinterConnectionTestResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function useDiscoveredPrinter(candidate: DiscoveredPrinter) {
    setNewPrinterName(candidate.name);
    setNewPrinterUrl(candidate.moonraker_url);
    setNewPrinterSshHost(extractHost(candidate.moonraker_url));
    setPrinterConnectionTest(null);
  }

  function openCreatePrinterModal() {
    setPrinterModalMode("create");
    setEditingPrinterId(null);
    setNewPrinterName("Voron - Mayder");
    setNewPrinterUrl("http://voron.local:7125");
    setNewPrinterSshHost("");
    setNewPrinterSshPort(22);
    setNewPrinterSshUser("");
    setNewPrinterSshCredential("");
    setDiscovery(null);
    setPrinterConnectionTest(null);
    setPrinterModalOpen(true);
  }

  function openEditPrinterModal(printer: PrinterRecord) {
    setPrinterModalMode("edit");
    setEditingPrinterId(printer.id);
    setNewPrinterName(printer.name);
    setNewPrinterUrl(printer.moonraker_url);
    setNewPrinterSshHost(printer.ssh_host ?? extractHost(printer.moonraker_url));
    setNewPrinterSshPort(printer.ssh_port ?? 22);
    setNewPrinterSshUser(printer.ssh_username ?? "");
    setNewPrinterSshCredential("");
    setDiscovery(null);
    setPrinterConnectionTest(null);
    setPrinterModalOpen(true);
  }

  async function loadSelectedPrinterStatus() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.moonrakerStatus(selectedPrinterId);
      const payload = (await response.json()) as MoonrakerStatus;
      setStatus(payload);
      await loadOperationStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
      await loadUpdateStatus(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function captureSnapshot() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.captureSnapshot(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadSnapshots(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadSnapshots(printerId: number) {
    const response = await printerApi.snapshots(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { snapshots: SnapshotRecord[] };
    setSnapshots(payload.snapshots);
    setSnapshotDiff(null);
    if (payload.snapshots.length >= 2) {
      setFromSnapshotId(payload.snapshots[1].id);
      setToSnapshotId(payload.snapshots[0].id);
    } else {
      setFromSnapshotId(payload.snapshots[0]?.id ?? null);
      setToSnapshotId(payload.snapshots[0]?.id ?? null);
    }
  }

  async function loadPrinterHealth(printerId: number) {
    const response = await printerApi.health(printerId);
    if (!response.ok) {
      return;
    }
    setHealth((await response.json()) as HealthResponse);
  }

  async function loadUpdateStatus(printerId: number): Promise<UpdateStatusResponse | null> {
    const response = await updatesApi.status(printerId);
    if (!response.ok) {
      return null;
    }
    const status = (await response.json()) as UpdateStatusResponse;
    setUpdateStatus(status);
    setError(null);
    return status;
  }

  async function refreshUpdateStatus(componentName?: string) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await updatesApi.refresh(selectedPrinterId, { name: componentName ?? null });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setUpdateActionResult((await response.json()) as UpdateActionResponse);
      await loadUpdateStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function handleAlertCenterAction(item: AlertCenterItem) {
    if (!selectedPrinterId) {
      return;
    }
    if (item.actionKind === "open_updates") {
      setActiveSection("updates");
      setAlertCenterOpen(false);
      return;
    }
    if (item.actionKind === "run_update") {
      setActiveSection("updates");
      setAlertCenterOpen(false);
      openUpdateDialog(item.target ?? "all");
      return;
    }
    if (item.actionKind === "refresh_update") {
      await refreshUpdateStatus(item.target);
      return;
    }
    if (item.actionKind === "open_monitoring") {
      setActiveSection("monitoring");
      setAlertCenterOpen(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([
        loadPrinterChecklist(selectedPrinterId),
        loadOperationStatus(selectedPrinterId),
        loadPrinterAudit(selectedPrinterId),
        loadPrinterHealth(selectedPrinterId),
        loadUpdateStatus(selectedPrinterId),
      ]);
    } finally {
      setLoading(false);
    }
  }

  function appendUpdateLog(level: UpdateLogEntry["level"], message: string) {
    const id = updateLogIdRef.current + 1;
    updateLogIdRef.current = id;
    setUpdateLogs((currentLogs) => [
      ...currentLogs,
      {
        id,
        level,
        message,
        time: new Date().toLocaleTimeString("pt-BR", { hour12: false }),
      },
    ]);
  }

  function openUpdateDialog(target: string) {
    if (!selectedPrinterId) {
      return;
    }
    const selectedLabel = target === "all" ? "todos os componentes" : target;
    setError(null);
    setUpdateActionResult(null);
    setUpdateLogs([]);
    updateLogIdRef.current = 0;
    setUpdateDialog({ open: true, target, label: selectedLabel, phase: "confirm" });
  }

  function closeUpdateSocket() {
    updateSocketRef.current?.close();
    updateSocketRef.current = null;
  }

  function connectUpdateSocket(printer: PrinterRecord) {
    closeUpdateSocket();
    const websocketUrl = moonrakerWebsocketUrl(printer.moonraker_url);
    if (!websocketUrl) {
      appendUpdateLog("warning", "Nao foi possivel montar a URL WebSocket do Moonraker. O update continua sem log ao vivo.");
      return;
    }
    appendUpdateLog("info", `Conectando ao log ao vivo em ${websocketUrl}`);
    const socket = new WebSocket(websocketUrl);
    updateSocketRef.current = socket;
    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          jsonrpc: "2.0",
          method: "server.connection.identify",
          params: {
            client_name: "Printora",
            version: "0.1.8",
            type: "web",
            url: "https://github.com/printora/printora",
          },
          id: 1,
        }),
      );
      appendUpdateLog("success", "Log ao vivo conectado.");
    };
    socket.onerror = () => appendUpdateLog("warning", "WebSocket do Moonraker indisponivel. O update continua via HTTP.");
    socket.onclose = () => {
      if (updateSocketRef.current === socket) {
        appendUpdateLog("warning", "Conexao de log encerrada. Moonraker pode estar reiniciando.");
      }
    };
    socket.onmessage = (event) => {
      const updateMessage = parseMoonrakerUpdateMessage(event.data);
      if (!updateMessage) {
        return;
      }
      appendUpdateLog(updateMessage.complete ? "success" : "info", updateMessage.message);
      if (updateMessage.complete) {
        setUpdateDialog((currentDialog) =>
          currentDialog && currentDialog.phase === "running" ? { ...currentDialog, phase: "done" } : currentDialog,
        );
      }
    };
  }

  async function runUpdate(target: string) {
    if (!selectedPrinterId || !selectedPrinter) {
      return;
    }
    setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "running" } : currentDialog));
    connectUpdateSocket(selectedPrinter);
    appendUpdateLog("info", `Solicitando update de ${target === "all" ? "todos os componentes" : target}.`);
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await updatesApi.run(selectedPrinterId, { target });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const actionResult = (await response.json()) as UpdateActionResponse;
      setUpdateActionResult(actionResult);
      appendUpdateLog("success", actionResult.message);
      await loadUpdateStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
      setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "done" } : currentDialog));
    } catch (err) {
      const latestStatus = await reloadUpdateStatusAfterUpdateError(selectedPrinterId, target);
      await loadPrinterHealth(selectedPrinterId);
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        setUpdateActionResult({
          safe_mode: "moonraker_update_manager",
          action: "update",
          target,
          accepted: true,
          message:
            "Update aplicado. O Moonraker ficou temporariamente indisponível no fim da operação, mas a reanálise confirmou que está atualizado.",
          result: {},
        });
        appendUpdateLog(
          "success",
          "Update confirmado apos reanalise. O erro HTTP provavelmente veio de reinicio temporario do Moonraker.",
        );
        setError(null);
        setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "done" } : currentDialog));
      } else {
        const errorMessage = err instanceof Error ? err.message : "Erro desconhecido";
        appendUpdateLog("error", errorMessage);
        setError(errorMessage);
        setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "failed" } : currentDialog));
      }
    } finally {
      setLoading(false);
    }
  }

  async function reloadUpdateStatusAfterUpdateError(printerId: number, target: string): Promise<UpdateStatusResponse | null> {
    const retryDelaysMs = [0, 1500, 3500];
    let latestStatus: UpdateStatusResponse | null = null;
    for (const retryDelayMs of retryDelaysMs) {
      if (retryDelayMs > 0) {
        appendUpdateLog("info", "Revalidando status do Update Manager apos indisponibilidade temporaria.");
        await delay(retryDelayMs);
      }
      try {
        latestStatus = await loadUpdateStatus(printerId);
      } catch {
        latestStatus = null;
      }
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        return latestStatus;
      }
    }
    return latestStatus;
  }

  async function loadBackups(printerId: number) {
    const [policiesResponse, runsResponse] = await Promise.all([
      backupApi.policies(printerId),
      backupApi.runs(printerId),
    ]);
    if (policiesResponse.ok) {
      const payload = (await policiesResponse.json()) as { policies: BackupPolicyRecord[] };
      setBackupPolicies(payload.policies);
    }
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: BackupRunRecord[] };
      setBackupRuns(payload.runs);
    }
  }

  async function loadSanitizedReport() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await reportsApi.sanitized(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSanitizedReport((await response.json()) as SanitizedReport);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadMaintenance(printerId: number, refreshPrintHours = true) {
    const [eventsResponse, tasksResponse, summaryResponse] = await Promise.all([
      maintenanceApi.events(printerId),
      maintenanceApi.tasks(printerId),
      maintenanceApi.summary(printerId),
    ]);
    let loadedTasks: MaintenanceTaskRecord[] | null = null;
    let loadedSummary: MaintenanceSummary | null = null;
    if (eventsResponse.ok) {
      const payload = (await eventsResponse.json()) as { events: MaintenanceEventRecord[] };
      setMaintenanceEvents(payload.events);
    }
    if (tasksResponse.ok) {
      const payload = (await tasksResponse.json()) as { tasks: MaintenanceTaskRecord[] };
      loadedTasks = payload.tasks;
      setMaintenanceTasks(payload.tasks);
    }
    if (summaryResponse.ok) {
      loadedSummary = (await summaryResponse.json()) as MaintenanceSummary;
      setMaintenanceSummary(loadedSummary);
    }
    if (loadedTasks?.length === 0 && loadedSummary && loadedSummary.recommended_tasks.length > 0) {
      const response = await maintenanceApi.createDefaults(printerId);
      if (response.ok) {
        await loadMaintenance(printerId);
      }
    }
    if (refreshPrintHours) {
      void maintenanceApi.printHours(printerId)
        .then(async (response) => {
          if (!response.ok) {
            setMaintenancePrintHours({ available: false, total_print_hours: null, source: "unavailable" });
            return undefined;
          }
          const payload = (await response.json()) as MaintenancePrintHoursStatus;
          setMaintenancePrintHours(payload);
          return loadMaintenance(printerId, false);
        })
        .catch(() => setMaintenancePrintHours({ available: false, total_print_hours: null, source: "unavailable" }));
    }
  }

  async function loadZOffsets(printerId: number) {
    const response = await zOffsetApi.list(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { records: ZOffsetRecord[] };
    setZOffsetRecords(payload.records);
  }

  async function loadCanRecords(printerId: number) {
    const [recordsResponse, summaryResponse] = await Promise.all([
      canApi.records(printerId),
      canApi.summary(printerId),
    ]);
    if (recordsResponse.ok) {
      const payload = (await recordsResponse.json()) as { records: CanBusRecord[] };
      setCanRecords(payload.records);
    }
    if (summaryResponse.ok) {
      setCanSummary((await summaryResponse.json()) as CanBusSummary);
    }
  }

  async function loadPluginAudit(printerId: number) {
    const response = await pluginApi.audit(printerId);
    if (!response.ok) {
      return;
    }
    setPluginAudit((await response.json()) as PluginAuditResponse);
  }

  async function loadBoardPresets() {
    const response = await firmwareApi.boardPresets();
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { presets: BoardPreset[] };
    setBoardPresets(payload.presets);
  }

  async function loadFirmwareBoards(printerId: number) {
    const response = await firmwareApi.boards(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { boards: FirmwareBoardRecord[] };
    setFirmwareBoards(payload.boards);
  }

  async function loadFirmwareBuildRuns(printerId: number) {
    const response = await firmwareApi.buildRuns(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: FirmwareBuildRunRecord[] };
    setFirmwareBuildRuns(payload.runs);
  }

  async function loadFirmwareFlashRuns(printerId: number) {
    const response = await firmwareApi.flashRuns(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: FirmwareFlashRunRecord[] };
    setFirmwareFlashRuns(payload.runs);
  }

  async function loadCalibrationTests(printerId?: number) {
    const response = await calibrationApi.availableTests(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { tests: CalibrationTestRecord[] } | CalibrationAvailableTestsResponse;
    setCalibrationTests(payload.tests);
    setCalibrationHiddenTests("hidden_tests" in payload ? payload.hidden_tests : []);
    setCalibrationTestKey((current) => {
      if (current && payload.tests.some((test) => test.test_key === current)) {
        return current;
      }
      return payload.tests[0]?.test_key || "";
    });
  }

  async function loadCalibrationRuns(printerId: number) {
    const [runsResponse, summaryResponse, sequenceResponse, executionsResponse] = await Promise.all([
      calibrationApi.runs(printerId),
      calibrationApi.summary(printerId),
      calibrationApi.sequence(printerId),
      calibrationApi.executions(printerId),
    ]);
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: CalibrationRunRecord[] };
      setCalibrationRuns(payload.runs);
    }
    if (summaryResponse.ok) {
      setCalibrationSummary((await summaryResponse.json()) as CalibrationSummary);
    }
    if (sequenceResponse.ok) {
      setCalibrationSequence((await sequenceResponse.json()) as CalibrationSequencePlan);
    }
    if (executionsResponse.ok) {
      const payload = (await executionsResponse.json()) as { executions: CalibrationExecutionRecord[] };
      setCalibrationExecutions(payload.executions);
    }
  }

  async function createCalibrationRun(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.createRun(selectedPrinterId, {
          test_key: calibrationTestKey,
          result_status: calibrationResultStatus,
          material: calibrationMaterial,
          plate_name: calibrationPlateName,
          nozzle: calibrationNozzle,
          observed_value: calibrationObservedValue,
          notes: calibrationNotes,
          gcode_reviewed: calibrationGcodeReviewed,
          photo_reference: calibrationPhotoReference || null,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationObservedValue("");
      setCalibrationNotes("");
      setCalibrationGcodeReviewed(false);
      setCalibrationPhotoReference("");
      setCalibrationResultTestKey(null);
      setCalibrationResultFormOpen(false);
      setCalibrationActivityCleared(false);
      await loadCalibrationRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadCalibrationPreflight() {
    if (!selectedPrinterId || !calibrationTestKey) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.preflight(selectedPrinterId, calibrationTestKey);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationPreflight((await response.json()) as CalibrationPreflight);
      setCalibrationExecutionResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function openCalibrationExecute(test: CalibrationTestRecord) {
    setCalibrationTestKey(test.test_key);
    setCalibrationExecuteTestKey(test.test_key);
    setCalibrationExecutionResult(null);
    setCalibrationPreflight(null);
    setCalibrationGcodeReviewed(false);
    setCalibrationOperatorPresent(false);
    setCalibrationExecutionConfirmation("");
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.preflight(selectedPrinterId, test.test_key);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationPreflight((await response.json()) as CalibrationPreflight);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function openCalibrationResult(
    test: CalibrationTestRecord,
    showForm = false,
    resultStatus: CalibrationRunRecord["result_status"] = "passed",
  ) {
    const formConfig = getCalibrationResultFormConfig(test);
    setCalibrationTestKey(test.test_key);
    setCalibrationResultTestKey(test.test_key);
    setCalibrationResultFormOpen(showForm);
    setCalibrationResultStatus(resultStatus);
    setCalibrationObservedValue("");
    setCalibrationNotes("");
    setCalibrationPhotoReference("");
    setCalibrationGcodeReviewed(test.gcode.length === 0);
    if (!formConfig.showMaterial) {
      setCalibrationMaterial("");
    } else if (!calibrationMaterial.trim()) {
      setCalibrationMaterial("PLA");
    }
    if (!formConfig.showPlate) {
      setCalibrationPlateName("");
    } else if (!calibrationPlateName.trim()) {
      setCalibrationPlateName("Texturizada");
    }
    if (!formConfig.showNozzle) {
      setCalibrationNozzle("");
    } else if (!calibrationNozzle.trim()) {
      setCalibrationNozzle("T0");
    }
  }

  async function executeCalibrationGcode(confirmationOverride?: string) {
    if (!selectedPrinterId || !calibrationTestKey) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.execute(selectedPrinterId, {
          test_key: calibrationTestKey,
          confirmation: confirmationOverride ?? calibrationExecutionConfirmation,
          operator_present: calibrationOperatorPresent,
          gcode_reviewed: calibrationGcodeReviewed,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as CalibrationExecutionRecord;
      setCalibrationExecutionResult(payload);
      setCalibrationActivityCleared(false);
      await loadCalibrationRuns(selectedPrinterId);
      if (payload.status === "executed") {
        setCalibrationOperatorPresent(false);
        setCalibrationGcodeReviewed(false);
        setCalibrationExecutionConfirmation("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareBoard(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.createBoard(selectedPrinterId, {
          name: firmwareBoardName,
          preset_id: firmwareBoardPresetId,
          can_uuid: firmwareBoardCanUuid || null,
          can_interface: firmwareBoardCanInterface,
          config_file: firmwareBoardConfigFile || null,
          notes: firmwareBoardNotes,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareBoardNotes("");
      await loadFirmwareBoards(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareBuildDryRun(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.buildDryRun(boardId, {
          klipper_path: firmwareKlipperPath,
          output_root: firmwareOutputRoot,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareBuildRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareBuildPreflight(boardId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.buildPreflight(boardId, {
          klipper_path: firmwareKlipperPath,
          output_root: firmwareOutputRoot,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareBuildPreflight((await response.json()) as FirmwareBuildPreflight);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function executeFirmwareBuildLocal(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.executeBuildLocal(boardId, {
          klipper_path: firmwareKlipperPath,
          output_root: firmwareOutputRoot,
          confirmation: firmwareBuildConfirmation,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareBuildRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareFlashDryRun(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await firmwareApi.flashDryRun(boardId, {
          build_run_id: latestBuildRun?.id ?? null,
          binary_path: firmwareFlashBinaryPath || null,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareFlashRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareFlashPreflight(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await firmwareApi.flashPreflight(boardId, {
          build_run_id: latestBuildRun?.id ?? null,
          binary_path: firmwareFlashBinaryPath || null,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareFlashPreflight((await response.json()) as FirmwareFlashPreflight);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareFlashGate(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await firmwareApi.executeFlash(boardId, {
          build_run_id: latestBuildRun?.id ?? null,
          binary_path: firmwareFlashBinaryPath || null,
          confirmation: firmwareFlashConfirmation,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareFlashRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadFirmwareRecoveryPlan(boardId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.recoveryPlan(boardId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareRecoveryPlan((await response.json()) as FirmwareRecoveryPlan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createCanRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await canApi.createRecord(selectedPrinterId, {
          interface_name: canInterfaceName,
          rx_error: canRxError,
          tx_error: canTxError,
          tx_retries: canTxRetries,
          bus_state: canBusState,
          bitrate: canBitrate,
          notes: canNotes,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCanNotes("");
      setCanRawOutput("");
      await loadCanRecords(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function parseCanRawOutput() {
    if (!selectedPrinterId || !canRawOutput.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await canApi.parse(selectedPrinterId, { interface_name: canInterfaceName, output: canRawOutput });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const parsed = (await response.json()) as {
        interface_name: string;
        rx_error: number;
        tx_error: number;
        tx_retries: number;
        bus_state?: string | null;
        bitrate?: number | null;
        notes: string;
      };
      setCanInterfaceName(parsed.interface_name);
      setCanRxError(parsed.rx_error);
      setCanTxError(parsed.tx_error);
      setCanTxRetries(parsed.tx_retries);
      setCanBusState(parsed.bus_state ?? "");
      setCanBitrate(parsed.bitrate ?? 1000000);
      setCanNotes(parsed.notes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareLatestCanRecords() {
    if (!selectedPrinterId || canRecords.length < 2) {
      return;
    }
    const pair = findLatestComparableCanRecords(canRecords);
    if (!pair) {
      setError("Não há duas leituras da mesma interface CAN para comparar.");
      return;
    }
    const { after, before } = pair;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        before_record_id: String(before.id),
        after_record_id: String(after.id),
      });
      const response = await canApi.compare(selectedPrinterId, params);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCanComparison((await response.json()) as CanBusRecordComparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function findLatestComparableCanRecords(records: CanBusRecord[]) {
    for (let afterIndex = 0; afterIndex < records.length; afterIndex += 1) {
      const after = records[afterIndex];
      const before = records.slice(afterIndex + 1).find((record) => record.interface_name === after.interface_name);
      if (before) {
        return { after, before };
      }
    }
    return null;
  }

  async function createZOffsetRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    const parsedOffset = Number(zOffsetValue);
    if (!zOffsetPlateName.trim() || !zOffsetMaterial.trim() || !zOffsetNozzle.trim() || !Number.isFinite(parsedOffset)) {
      setError("Preencha chapa, material, toolhead e um Z-offset válido antes de registrar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await zOffsetApi.create(selectedPrinterId, {
          plate_name: zOffsetPlateName.trim(),
          material: zOffsetMaterial.trim(),
          nozzle: zOffsetNozzle.trim(),
          offset_value: parsedOffset,
          notes: zOffsetNotes,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setZOffsetNotes("");
      setZOffsetFormOpen(false);
      setZOffsetWizardPlan(null);
      setZOffsetWizardChecks({});
      await loadZOffsets(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function evaluateZOffsetWizard() {
    if (!selectedPrinterId) {
      return;
    }
    const parsedOffset = Number(zOffsetValue);
    if (!zOffsetPlateName.trim() || !zOffsetMaterial.trim() || !zOffsetNozzle.trim() || !Number.isFinite(parsedOffset)) {
      setError("Preencha chapa, material, toolhead e um Z-offset válido antes de avaliar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams({
        plate_name: zOffsetPlateName.trim(),
        material: zOffsetMaterial.trim(),
        nozzle: zOffsetNozzle.trim(),
        proposed_offset_value: String(parsedOffset),
      });
      const response = await zOffsetApi.wizardPlan(selectedPrinterId, query);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const plan = (await response.json()) as ZOffsetWizardPlan;
      setZOffsetWizardPlan(plan);
      setZOffsetWizardChecks(
        Object.fromEntries(plan.steps.filter((step) => step.must_confirm).map((step) => [step.key, false])),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function toggleWizardCheck(key: string) {
    setZOffsetWizardChecks((current) => ({ ...current, [key]: !current[key] }));
  }

  function openMaintenanceDoneModal(task: MaintenanceTaskRecord) {
    setMaintenanceDoneTask(task);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind(task.interval_kind);
    setMaintenanceDoneIntervalValue(task.is_active ? formatMaintenanceIntervalValue(task) : "");
    setMaintenanceDoneDisableReminder(!task.is_active);
  }

  function openMaintenanceFreeModal() {
    setMaintenanceEventType("");
    setMaintenanceComponent("");
    setMaintenanceTitle("");
    setMaintenanceNotes("");
    setMaintenanceFreeReminderEnabled(false);
    setMaintenanceFreeIntervalKind("days");
    setMaintenanceFreeIntervalValue("");
    setMaintenanceFreeModalOpen(true);
  }

  async function completeMaintenanceTask(
    taskId: number,
    notes = "Concluído pelo painel Printora.",
    nextIntervalKind?: "days" | "print_hours" | null,
    nextIntervalValue?: number | null,
    disableReminder = false,
  ): Promise<boolean> {
    if (!selectedPrinterId) {
      return false;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.completeTask(taskId, {
          notes,
          next_interval_kind: nextIntervalKind ?? null,
          next_interval_value: nextIntervalValue ?? null,
          next_interval_days: nextIntervalKind === "days" ? nextIntervalValue ?? null : null,
          disable_reminder: disableReminder,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function submitMaintenanceDone(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!maintenanceDoneTask) {
      return;
    }
    const interval = maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim()
      ? null
      : Number(maintenanceDoneIntervalValue);
    if (!maintenanceDoneDisableReminder && maintenanceDoneIntervalKind === "print_hours" && !maintenancePrintHours?.available) {
      setError("Horas de impressão indisponíveis. Ligue a impressora para usar lembrete por horas.");
      return;
    }
    const completed = await completeMaintenanceTask(
      maintenanceDoneTask.id,
      maintenanceDoneNotes.trim() || "Manutenção realizada.",
      maintenanceDoneDisableReminder || interval === null ? null : maintenanceDoneIntervalKind,
      interval,
      maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim(),
    );
    if (!completed) {
      return;
    }
    setMaintenanceDoneTask(null);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind("days");
    setMaintenanceDoneIntervalValue("");
    setMaintenanceDoneDisableReminder(false);
  }

  async function deleteLatestMaintenanceTaskEvent(taskId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.latestTaskEvent(taskId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createDefaultMaintenanceTasks() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.createDefaults(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function submitMaintenanceFreeEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId || !maintenanceEventType || !maintenanceComponent.trim() || !maintenanceTitle.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const performedAt = new Date().toISOString();
      const response = await maintenanceApi.createEvent(selectedPrinterId, {
          event_type: maintenanceEventType,
          component: maintenanceComponent.trim(),
          title: maintenanceTitle.trim(),
          notes: maintenanceNotes,
          performed_at: performedAt,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const reminderValue = maintenanceFreeReminderEnabled && maintenanceFreeIntervalValue.trim()
        ? Number(maintenanceFreeIntervalValue)
        : null;
      if (maintenanceFreeReminderEnabled && maintenanceFreeIntervalKind === "print_hours" && !maintenancePrintHours?.available) {
        throw new Error("Horas de impressão indisponíveis. Ligue a impressora para usar lembrete por horas.");
      }
      if (reminderValue) {
        const taskResponse = await maintenanceApi.createTask(selectedPrinterId, {
            name: maintenanceTitle,
            component: maintenanceComponent.trim(),
            interval_days: maintenanceFreeIntervalKind === "days" ? reminderValue : 30,
            interval_kind: maintenanceFreeIntervalKind,
            interval_value: reminderValue,
            last_done_at: performedAt,
          });
        if (!taskResponse.ok) {
          throw new Error(await taskResponse.text());
        }
      }
      setMaintenanceEventType("");
      setMaintenanceComponent("");
      setMaintenanceTitle("");
      setMaintenanceNotes("");
      setMaintenanceFreeReminderEnabled(false);
      setMaintenanceFreeIntervalKind("days");
      setMaintenanceFreeIntervalValue("");
      setMaintenanceFreeModalOpen(false);
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function deleteMaintenanceEvent(eventId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.deleteEvent(eventId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupPolicy(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.createPolicy(selectedPrinterId, {
          name: backupName,
          source_path: backupSourcePath,
          destination_path: backupDestinationPath,
          dry_run_only: backupDryRunOnly,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function executeLocalBackup(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.executeLocal(policyId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupDryRun(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.dryRun(policyId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareBackupArchives() {
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.compareArchives({
          base_archive_path: backupCompareBasePath,
          target_archive_path: backupCompareTargetPath,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupCompareResult((await response.json()) as BackupArchiveCompareResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupRestorePlan() {
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.restorePlan({
          archive_path: backupRestoreArchivePath,
          restore_root: backupRestoreRoot,
          files: backupRestoreFiles.split("\n").map((item) => item.trim()).filter(Boolean),
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupRestorePlan((await response.json()) as BackupRestorePlanResponse);
      setBackupRestoreGate(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateBackupRestoreGate() {
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.restoreGate({
          archive_path: backupRestoreArchivePath,
          restore_root: backupRestoreRoot,
          files: backupRestoreFiles.split("\n").map((item) => item.trim()).filter(Boolean),
          confirmation: backupRestoreConfirmation,
        });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupRestoreGate((await response.json()) as BackupRestoreGateResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareSnapshots() {
    if (!selectedPrinterId || !fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.snapshotDiff(selectedPrinterId, fromSnapshotId, toSnapshotId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSnapshotDiff((await response.json()) as SnapshotDiff);
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
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("printora-theme", theme);
  }, [theme]);

  React.useEffect(() => {
    if (!selectedPrinterId || !["calibration", "tests"].includes(activeSection)) {
      return;
    }
    void loadCalibrationTests(selectedPrinterId);
    void loadCalibrationRuns(selectedPrinterId);
    if (activeSection === "calibration") {
      void loadOperationStatus(selectedPrinterId);
      void loadZOffsets(selectedPrinterId);
    }
  }, [activeSection, selectedPrinterId]);

  React.useEffect(() => {
    if (!selectedPrinterId || activeSection !== "monitoring") {
      return;
    }
    void loadOperationStatus(selectedPrinterId, { preserveData: true });
    const refreshId = window.setInterval(() => {
      void loadOperationStatus(selectedPrinterId, { preserveData: true });
      void loadPrinterHealth(selectedPrinterId);
      void loadCanRecords(selectedPrinterId);
    }, 5000);
    return () => window.clearInterval(refreshId);
  }, [activeSection, selectedPrinterId]);

  React.useEffect(() => () => closeUpdateSocket(), []);

  const activeSectionMeta = appSections.find((section) => section.key === activeSection) ?? appSections[0];
  const selectedPrinter = printers.find((printer) => printer.id === selectedPrinterId);
  const selectedCalibrationTest = calibrationTests.find((test) => test.test_key === calibrationTestKey) ?? calibrationTests[0];
  const calibrationHelpTest = calibrationTests.find((test) => test.test_key === calibrationHelpTestKey);
  const calibrationExecuteTest = calibrationTests.find((test) => test.test_key === calibrationExecuteTestKey);
  const calibrationResultTest = calibrationTests.find((test) => test.test_key === calibrationResultTestKey);
  const calibrationResultFormConfig = calibrationResultTest
    ? getCalibrationResultFormConfig(calibrationResultTest)
    : null;
  const calibrationResultRuns = calibrationResultTest
    ? calibrationRuns.filter((run) => run.test_key === calibrationResultTest.test_key)
    : [];
  const calibrationResultExecutions = calibrationResultTest
    ? calibrationExecutions.filter((execution) => execution.test_key === calibrationResultTest.test_key)
    : [];
  const calibrationVisibleGcodeCount = calibrationTests.filter((test) => test.gcode.length > 0).length;
  const calibrationBlockedGcodeCount = calibrationHiddenTests.length;
  const calibrationRecommended = calibrationSummary?.recommended_next_tests.slice(0, 5) ?? [];
  const hiddenCalibrationKeys = new Set(calibrationHiddenTests.map((test) => test.test_key));
  const calibrationSequencePreview = (calibrationSequence?.steps ?? []).filter((step) => !hiddenCalibrationKeys.has(step.test_key));
  const visibleCalibrationCompletedSteps = calibrationSequencePreview.filter((step) => step.status === "completed" || step.status === "skipped").length;
  const visibleCalibrationRecommendations = calibrationRecommended.filter((test) => !hiddenCalibrationKeys.has(test.test_key));
  const visibleCalibrationTests = calibrationTests.filter((test) => {
    if (testFilter === "executable") {
      return test.gcode.length > 0;
    }
    if (testFilter === "manual") {
      return test.gcode.length === 0;
    }
    return testFilter !== "blocked";
  });
  const visibleHiddenCalibrationTests = testFilter === "all" || testFilter === "blocked" ? calibrationHiddenTests : [];
  const visibleMaintenanceTasks = maintenanceTasks.filter((task) => {
    if (maintenanceFilter === "all") {
      return true;
    }
    return task.due_status === maintenanceFilter;
  });
  const nextMaintenanceTask = maintenanceSummary?.next_due_task;
  const maintenancePrintHoursAvailable =
    maintenancePrintHours?.available && typeof maintenancePrintHours.total_print_hours === "number";
  const maintenanceHoursDisabledMessage = "Horas de impressão indisponíveis. Ligue a impressora para habilitar.";
  const visibleFirmwareBoards = firmwareBoards.filter((board) => {
    if (firmwareFilter === "can") {
      return board.connection_type === "can" || board.connection_type === "usb_can_bridge";
    }
    if (firmwareFilter === "usb") {
      return board.connection_type === "usb";
    }
    return true;
  });
  const hotendTemperature = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bedTemperature = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const recentCalibrationActivityCount =
    (calibrationExecutionResult ? 1 : 0) + calibrationExecutions.slice(0, 4).length + calibrationRuns.slice(0, 4).length;
  const ActiveIcon = activeSectionMeta.icon;
  const ThemeIcon = theme === "dark" ? Sun : Moon;
  const alertCenterItems = buildAlertCenterItems({ health, updateStatus, checklist, audit });
  const alertCount = alertCenterItems.length;
  const primaryRiskItem = alertCenterItems.find((item) => item.severity === "blocker") ?? alertCenterItems.find((item) => item.severity === "warning") ?? null;
  const latestSnapshot = snapshots[0];
  const moonrakerOnline = health?.connected ?? status?.connected ?? false;
  const displayDecision = displayHealthDecision(health);
  const visibleNavGroups = React.useMemo(
    () =>
      navGroups
        .map((group) => ({
          ...group,
          sections: group.sections.filter((sectionKey) => {
            if (onlinePrinterSections.has(sectionKey)) {
              return Boolean(selectedPrinterId);
            }
            if (selectedPrinterLocalSections.has(sectionKey)) {
              return Boolean(selectedPrinterId);
            }
            return true;
          }),
        }))
        .filter((group) => group.sections.length > 0),
    [selectedPrinterId],
  );
  const operationState = operationStatus?.miscellaneous.print_state ?? status?.printer?.state ?? health?.metrics.klipper_state ?? "-";
  const totalPrintHours = operationStatus?.miscellaneous.total_print_hours;
  const riskClass = overviewRiskClass(displayDecision);
  const riskLabel = formatDecision(displayDecision);
  const lastReadingLabel = latestSnapshot
    ? `Snapshot #${latestSnapshot.id} · ${latestSnapshot.created_at}`
    : health?.data_state
      ? formatChecklistDataState(health.data_state)
      : "Sem leitura";
  const topbarAlertTone = alertCenterItems.some((item) => item.severity === "blocker")
    ? "danger"
    : alertCenterItems.some((item) => item.severity === "warning")
      ? "warning"
      : "ok";
  const topbarPrimaryAction = (() => {
    if (activeSection === "printers") {
      return {
        icon: Plus,
        label: "Adicionar",
        disabled: loading,
        run: openCreatePrinterModal,
      };
    }
    if (activeSection === "reports") {
      return {
        icon: Camera,
        label: "Snapshot",
        disabled: !selectedPrinterId || loading,
        run: captureSnapshot,
      };
    }
    if (activeSection === "updates") {
      return {
        icon: RefreshCw,
        label: "Reanalisar",
        disabled: !selectedPrinterId || loading || Boolean(updateStatus?.busy),
        run: () => refreshUpdateStatus(),
      };
    }
    if (activeSection === "settings") {
      return {
        icon: Settings,
        label: selectedPrinter ? "Editar" : "Adicionar",
        disabled: loading,
        run: () => (selectedPrinter ? openEditPrinterModal(selectedPrinter) : openCreatePrinterModal()),
      };
    }
    return {
      icon: RefreshCw,
      label: loading ? "Atualizando" : "Atualizar",
      disabled: loading || (!selectedPrinterId && activeSection !== "overview"),
      run: () => (selectedPrinterId ? loadSelectedPrinterStatus() : loadStatus()),
    };
  })();
  const TopbarPrimaryIcon = topbarPrimaryAction.icon;

  const screenProps = {
    ActiveIcon,
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
    ThemeIcon,
    Timer,
    TopbarPrimaryIcon,
    Trash2,
    Undo2,
    Wrench,
    X,
    Zap,
    activeSection,
    activeSectionMeta,
    alertCenterIcon,
    alertCenterItems,
    alertCenterOpen,
    alertCount,
    appendUpdateLog,
    applySelfUpdate,
    audit,
    backupCompareBasePath,
    backupCompareResult,
    backupCompareTargetPath,
    backupDestinationPath,
    backupDryRunOnly,
    backupName,
    backupPolicies,
    backupRestoreArchivePath,
    backupRestoreConfirmation,
    backupRestoreFiles,
    backupRestoreGate,
    backupRestorePlan,
    backupRestoreRoot,
    backupRuns,
    backupSourcePath,
    bedTemperature,
    boardPresets,
    buildCalibrationExecutionNotes,
    buildOperationActionPayload,
    buildTemperatureSeries,
    calibrationActivityCleared,
    calibrationBlockedGcodeCount,
    calibrationExecuteTest,
    calibrationExecuteTestKey,
    calibrationExecutionConfirmation,
    calibrationExecutionResult,
    calibrationExecutionRowClass,
    calibrationExecutions,
    calibrationGcodeReviewed,
    calibrationHelpTest,
    calibrationHelpTestKey,
    calibrationHiddenTests,
    calibrationMaterial,
    calibrationNotes,
    calibrationNozzle,
    calibrationObservedValue,
    calibrationOperatorPresent,
    calibrationPhotoReference,
    calibrationPlateName,
    calibrationPreflight,
    calibrationRecommended,
    calibrationResultExecutions,
    calibrationResultFormConfig,
    calibrationResultFormOpen,
    calibrationResultRuns,
    calibrationResultStatus,
    calibrationResultTest,
    calibrationResultTestKey,
    calibrationRuns,
    calibrationSequence,
    calibrationSequencePreview,
    calibrationSummary,
    calibrationTestKey,
    calibrationTests,
    calibrationVisibleGcodeCount,
    canBitrate,
    canBusState,
    canComparison,
    canInterfaceName,
    canNotes,
    canRawOutput,
    canRecords,
    canRollbackSelfUpdateRun,
    canRxError,
    canSummary,
    canTxError,
    canTxRetries,
    captureSnapshot,
    checklist,
    checklistDotClass,
    closeUpdateSocket,
    compareBackupArchives,
    compareLatestCanRecords,
    compareSnapshots,
    completeMaintenanceTask,
    confirmedWizardSteps,
    connectUpdateSocket,
    countPendingUpdates,
    createBackupDryRun,
    createBackupPolicy,
    createBackupRestorePlan,
    createCalibrationRun,
    createCanRecord,
    createDefaultMaintenanceTasks,
    createFirmwareBoard,
    createFirmwareBuildDryRun,
    createFirmwareFlashDryRun,
    createPrinter,
    createZOffsetRecord,
    delay,
    deleteLatestMaintenanceTaskEvent,
    deleteMaintenanceEvent,
    discoverPrinters,
    discovery,
    displayDecision,
    displayHealthDecision,
    displayedReleaseRows,
    editingPrinterId,
    error,
    evaluateZOffsetWizard,
    executeCalibrationGcode,
    executeFirmwareBuildLocal,
    executeLocalBackup,
    extractHost,
    findLatestComparableCanRecords,
    firmwareBoardCanInterface,
    firmwareBoardCanUuid,
    firmwareBoardConfigFile,
    firmwareBoardName,
    firmwareBoardNotes,
    firmwareBoardPresetId,
    firmwareBoards,
    firmwareBuildConfirmation,
    firmwareBuildPreflight,
    firmwareBuildRuns,
    firmwareFilter,
    firmwareFlashBinaryPath,
    firmwareFlashConfirmation,
    firmwareFlashPreflight,
    firmwareFlashRuns,
    firmwareKlipperPath,
    firmwareOutputRoot,
    firmwareRecoveryPlan,
    formatBoolean,
    formatCalibrationCategory,
    formatCalibrationExecutionResult,
    formatCalibrationExecutionStatus,
    formatCalibrationPhase,
    formatCalibrationResult,
    formatCalibrationSequenceStatus,
    formatCalibrationTestTitle,
    formatCanAlert,
    formatChecklistDataState,
    formatClassification,
    formatConnectionType,
    formatDecision,
    formatDueStatus,
    formatExecutionMode,
    formatHealthSeverity,
    formatHours,
    formatLatestCan,
    formatLatestZOffset,
    formatLocalDateTime,
    formatMaintenanceEventType,
    formatMaintenanceInterval,
    formatMaintenanceIntervalValue,
    formatMetricLabel,
    formatOperationActionId,
    formatOperationCapabilityStatus,
    formatOperationDataState,
    formatOperationParameterLabel,
    formatOperationValue,
    formatOptionalHours,
    formatOptionalInt,
    formatOptionalLocalDateTime,
    formatOptionalNumber,
    formatPercent,
    formatPluginAction,
    formatPluginClassification,
    formatPosition,
    formatPrintHoursDueLine,
    formatRedaction,
    formatReleaseSourceStatus,
    formatReleaseUpdateStatus,
    formatRiskLevel,
    formatRollbackPlan,
    formatSelfUpdateEnvironment,
    formatSelfUpdateStatus,
    formatSelfUpdateStepStatus,
    formatSeverity,
    formatSshStatus,
    formatTemperature,
    formatUnknown,
    formatUpdatePhase,
    formatUpdateStatus,
    formatZOffsetAlert,
    fromSnapshotId,
    getCalibrationResultFormConfig,
    groupCalibrationSteps,
    handleAlertCenterAction,
    health,
    healthFindingClass,
    healthPanelClass,
    hiddenCalibrationKeys,
    hostAudit,
    hotendTemperature,
    isSelfUpdateEnvironmentSupported,
    isUpdateTargetConfirmedUpdated,
    lastReadingLabel,
    latestCalibrationExecutionFinalState,
    latestSnapshot,
    loadBackups,
    loadBoardPresets,
    loadCalibrationPreflight,
    loadCalibrationRuns,
    loadCalibrationTests,
    loadCanRecords,
    loadFirmwareBoards,
    loadFirmwareBuildRuns,
    loadFirmwareFlashRuns,
    loadFirmwareRecoveryPlan,
    loadGlobalDiagnostics,
    loadMaintenance,
    loadOfflineOperationFixture,
    loadOperationActionHistory,
    loadOperationExecutionHistory,
    loadOperationStatus,
    loadPluginAudit,
    loadPrinterAudit,
    loadPrinterChecklist,
    loadPrinterContext,
    loadPrinterHealth,
    loadPrinterLiveContext,
    loadPrinterLocalContext,
    loadPrinters,
    loadSanitizedReport,
    loadSelectedPrinterStatus,
    loadSelfUpdateHistory,
    loadSnapshots,
    loadStatus,
    loadSystemReleases,
    loadUpdateStatus,
    loadZOffsets,
    loading,
    maintenanceComponent,
    maintenanceDoneDisableReminder,
    maintenanceDoneIntervalKind,
    maintenanceDoneIntervalValue,
    maintenanceDoneNotes,
    maintenanceDoneTask,
    maintenanceEventType,
    maintenanceEvents,
    maintenanceFilter,
    maintenanceFreeIntervalKind,
    maintenanceFreeIntervalValue,
    maintenanceFreeModalOpen,
    maintenanceFreeReminderEnabled,
    maintenanceHoursDisabledMessage,
    maintenanceNotes,
    maintenancePrintHours,
    maintenancePrintHoursAvailable,
    maintenanceSummary,
    maintenanceTasks,
    maintenanceTitle,
    mobileNavOpen,
    moonrakerOnline,
    moonrakerWebsocketUrl,
    newPrinterName,
    newPrinterSshCredential,
    newPrinterSshHost,
    newPrinterSshPort,
    newPrinterSshUser,
    newPrinterUrl,
    nextMaintenanceTask,
    openCalibrationExecute,
    openCalibrationResult,
    openCreatePrinterModal,
    openEditPrinterModal,
    openMaintenanceDoneModal,
    openMaintenanceFreeModal,
    openUpdateDialog,
    operationActionHistory,
    operationActionParameterSpecs,
    operationActionParameters,
    operationActionPreview,
    operationExecutionAttempt,
    operationExecutionHistory,
    operationExecutionPhrase,
    operationState,
    operationStatus,
    overviewRiskClass,
    parseCanRawOutput,
    parseMoonrakerUpdateMessage,
    planSelfUpdate,
    pluginAudit,
    pollSelfUpdateRun,
    preflightOperationAction,
    previewOperationAction,
    primaryRiskItem,
    printerConnectionTest,
    printerModalMode,
    printerModalOpen,
    printers,
    recentCalibrationActivityCount,
    refreshUpdateStatus,
    releaseError,
    releaseLoading,
    releasePanelClass,
    releaseStatusPillClass,
    reloadUpdateStatusAfterUpdateError,
    riskClass,
    riskLabel,
    rollbackSelfUpdate,
    runUpdate,
    sanitizedReport,
    selectPrinter,
    selectedCalibrationTest,
    selectedPrinter,
    selectedPrinterId,
    selfUpdateApplying,
    selfUpdateCompletedStepCount,
    selfUpdateConfirmation,
    selfUpdateConnectionLost,
    selfUpdateHistory,
    selfUpdateMessage,
    selfUpdateModalOpen,
    selfUpdatePlan,
    selfUpdateProgressPercent,
    selfUpdateRollbackConfirmation,
    selfUpdateRollingBack,
    selfUpdateRunClass,
    selfUpdateStepClass,
    selfUpdateStepDetail,
    setActiveSection,
    setAlertCenterOpen,
    setAudit,
    setBackupCompareBasePath,
    setBackupCompareResult,
    setBackupCompareTargetPath,
    setBackupDestinationPath,
    setBackupDryRunOnly,
    setBackupName,
    setBackupPolicies,
    setBackupRestoreArchivePath,
    setBackupRestoreConfirmation,
    setBackupRestoreFiles,
    setBackupRestoreGate,
    setBackupRestorePlan,
    setBackupRestoreRoot,
    setBackupRuns,
    setBackupSourcePath,
    setBoardPresets,
    setCalibrationActivityCleared,
    setCalibrationExecuteTestKey,
    setCalibrationExecutionConfirmation,
    setCalibrationExecutionResult,
    setCalibrationExecutions,
    setCalibrationGcodeReviewed,
    setCalibrationHelpTestKey,
    setCalibrationHiddenTests,
    setCalibrationMaterial,
    setCalibrationNotes,
    setCalibrationNozzle,
    setCalibrationObservedValue,
    setCalibrationOperatorPresent,
    setCalibrationPhotoReference,
    setCalibrationPlateName,
    setCalibrationPreflight,
    setCalibrationResultFormOpen,
    setCalibrationResultStatus,
    setCalibrationResultTestKey,
    setCalibrationRuns,
    setCalibrationSequence,
    setCalibrationSummary,
    setCalibrationTestKey,
    setCalibrationTests,
    setCanBitrate,
    setCanBusState,
    setCanComparison,
    setCanInterfaceName,
    setCanNotes,
    setCanRawOutput,
    setCanRecords,
    setCanRxError,
    setCanSummary,
    setCanTxError,
    setCanTxRetries,
    setChecklist,
    setDiscovery,
    setEditingPrinterId,
    setError,
    setFirmwareBoardCanInterface,
    setFirmwareBoardCanUuid,
    setFirmwareBoardConfigFile,
    setFirmwareBoardName,
    setFirmwareBoardNotes,
    setFirmwareBoardPresetId,
    setFirmwareBoards,
    setFirmwareBuildConfirmation,
    setFirmwareBuildPreflight,
    setFirmwareBuildRuns,
    setFirmwareFilter,
    setFirmwareFlashBinaryPath,
    setFirmwareFlashConfirmation,
    setFirmwareFlashPreflight,
    setFirmwareFlashRuns,
    setFirmwareKlipperPath,
    setFirmwareOutputRoot,
    setFirmwareRecoveryPlan,
    setFromSnapshotId,
    setHealth,
    setHostAudit,
    setLoading,
    setMaintenanceComponent,
    setMaintenanceDoneDisableReminder,
    setMaintenanceDoneIntervalKind,
    setMaintenanceDoneIntervalValue,
    setMaintenanceDoneNotes,
    setMaintenanceDoneTask,
    setMaintenanceEventType,
    setMaintenanceEvents,
    setMaintenanceFilter,
    setMaintenanceFreeIntervalKind,
    setMaintenanceFreeIntervalValue,
    setMaintenanceFreeModalOpen,
    setMaintenanceFreeReminderEnabled,
    setMaintenanceNotes,
    setMaintenancePrintHours,
    setMaintenanceSummary,
    setMaintenanceTasks,
    setMaintenanceTitle,
    setMobileNavOpen,
    setNewPrinterName,
    setNewPrinterSshCredential,
    setNewPrinterSshHost,
    setNewPrinterSshPort,
    setNewPrinterSshUser,
    setNewPrinterUrl,
    setOperationActionHistory,
    setOperationActionParameters,
    setOperationActionPreview,
    setOperationExecutionAttempt,
    setOperationExecutionHistory,
    setOperationExecutionPhrase,
    setOperationStatus,
    setPluginAudit,
    setPrinterConnectionTest,
    setPrinterModalMode,
    setPrinterModalOpen,
    setPrinters,
    setReleaseError,
    setReleaseLoading,
    setSanitizedReport,
    setSelectedPrinterId,
    setSelfUpdateApplying,
    setSelfUpdateConfirmation,
    setSelfUpdateConnectionLost,
    setSelfUpdateHistory,
    setSelfUpdateMessage,
    setSelfUpdateModalOpen,
    setSelfUpdatePlan,
    setSelfUpdateRollbackConfirmation,
    setSelfUpdateRollingBack,
    setSnapshotDiff,
    setSnapshots,
    setStatus,
    setSystemReleases,
    setTestFilter,
    setTheme,
    setToSnapshotId,
    setUpdateActionResult,
    setUpdateDialog,
    setUpdateLogs,
    setUpdateStatus,
    setZOffsetFormOpen,
    setZOffsetMaterial,
    setZOffsetNotes,
    setZOffsetNozzle,
    setZOffsetPlateName,
    setZOffsetRecords,
    setZOffsetValue,
    setZOffsetWizardChecks,
    setZOffsetWizardPlan,
    snapshotDiff,
    snapshots,
    startSelfUpdateFlow,
    status,
    submitMaintenanceDone,
    submitMaintenanceFreeEvent,
    summarizeCalibrationExecutionFinalState,
    systemReleases,
    temperatureBarHeight,
    testFilter,
    testPrinterConnections,
    theme,
    toSnapshotId,
    toggleWizardCheck,
    topbarAlertTone,
    topbarPrimaryAction,
    totalPrintHours,
    updateActionResult,
    updateDialog,
    updateLogIdRef,
    updateLogs,
    updateOperationActionParameter,
    updatePhaseIcon,
    updateSocketRef,
    updateStatus,
    updateStatusIcon,
    useDiscoveredPrinter,
    validateBackupRestoreGate,
    validateFirmwareBuildPreflight,
    validateFirmwareFlashGate,
    validateFirmwareFlashPreflight,
    validateOperationExecutionGate,
    validatePrinterConnectionInput,
    visibleCalibrationCompletedSteps,
    visibleCalibrationRecommendations,
    visibleCalibrationTests,
    visibleFirmwareBoards,
    visibleHiddenCalibrationTests,
    visibleMaintenanceTasks,
    visibleNavGroups,
    visibleSelfUpdateSteps,
    zOffsetFormOpen,
    zOffsetMaterial,
    zOffsetNotes,
    zOffsetNozzle,
    zOffsetPlateName,
    zOffsetRecords,
    zOffsetValue,
    zOffsetWizardChecks,
    zOffsetWizardPlan,
  };

  React.useEffect(() => {
    if (onlinePrinterSections.has(activeSection) && !selectedPrinterId) {
      setActiveSection("overview");
      return;
    }
    if (selectedPrinterLocalSections.has(activeSection) && !selectedPrinterId) {
      setActiveSection("overview");
    }
  }, [activeSection, selectedPrinterId]);


  return {
    ActiveIcon,
    ThemeIcon,
    TopbarPrimaryIcon,
    activeSection,
    activeSectionMeta,
    alertCount,
    error,
    mobileNavOpen,
    printers,
    screenProps,
    selectPrinter,
    selectedPrinter,
    selectedPrinterId,
    setActiveSection,
    setAlertCenterOpen,
    setMobileNavOpen,
    setTheme,
    theme,
    topbarAlertTone,
    topbarPrimaryAction,
    visibleNavGroups,
  };
}
