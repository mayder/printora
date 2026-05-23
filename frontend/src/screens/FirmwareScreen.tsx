import React from "react";
import { Badge, Metric, OperationActionParameterFields } from "../components/common";
import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenProps } from "./ScreenProps";
import type { MoonrakerStatus, DiscoveredPrinter, PrinterDiscoveryResponse, ConnectionCheckResult, PrinterConnectionTestResponse, PrinterRecord, SnapshotRecord, SnapshotDiffItem, SnapshotDiff, OperationMetric, OperationTemperature, OperationFan, OperationTemperatureHistoryRow, OperationAction, OperationCapability, OperationActionPreview, OperationActionParameterSpec, OperationActionPreviewRecord, OperationActionExecutionAttempt, OperationStatusResponse, BackupPolicyRecord, BackupRunRecord, BackupArchiveCompareResponse, BackupRestorePlanResponse, SanitizedReport, MaintenanceEventRecord, MaintenanceTaskRecord, MaintenanceSummary, MaintenancePrintHoursStatus, ZOffsetRecord, ZOffsetWizardPlan, CanBusRecord, CanBusSummary, CanBusRecordComparison, PluginAuditItem, PluginAuditResponse, ReleaseRecord, SystemReleasesResponse, UpdateActionResponse, UpdateLogEntry, UpdateDialogState, BoardPreset, FirmwareBoardRecord, FirmwareBuildRunRecord, FirmwareBuildPreflight, FirmwareFlashRunRecord, FirmwareFlashPreflight, FirmwareRecoveryPlan, BackupRestoreGateResponse, CalibrationTestRecord, CalibrationAvailableTestsResponse, CalibrationRunRecord, CalibrationResultFormConfig, CalibrationSummary, CalibrationSequencePlan, CalibrationPreflight, CalibrationExecutionRecord, ThemeMode } from "../types";

export function FirmwareScreen(props: ScreenProps) {
  const {
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
  } = props;

  return (
    <>
        <article className="panel wide panel-section panel-firmware">
          <div className="panel-heading">
            <h2>Mods e plugins</h2>
            <strong>{pluginAudit?.summary ?? "Sem snapshot analisado"}</strong>
          </div>
          <div className="plugin-actions">
            <button type="button" onClick={() => selectedPrinterId && void loadPluginAudit(selectedPrinterId)} disabled={!selectedPrinterId || loading}>
              Reanalisar
            </button>
            <span>Leitura baseada no último snapshot Moonraker/Update Manager. Não remove nem altera nada.</span>
          </div>
          <div className="plugin-summary">
            <Badge label="Detectados" value={pluginAudit?.counts.detected ?? 0} />
            <Badge label="Risco" value={pluginAudit?.counts.risky ?? 0} />
            <Badge label="Investigar" value={pluginAudit?.counts.investigate ?? 0} />
            <Badge label="Desconhecidos" value={pluginAudit?.counts.unknown ?? 0} />
          </div>
          {pluginAudit?.unknown_update_manager_components.length ? (
            <div className="plugin-unknown">
              <strong>Componentes fora do catálogo</strong>
              <span>{pluginAudit.unknown_update_manager_components.join(" · ")}</span>
            </div>
          ) : null}
          <div className="plugin-list">
            {pluginAudit?.items.map((item: any) => (
              <div key={item.name} className={`plugin-row ${item.classification} ${item.detected ? "detected" : "missing"}`}>
                <div>
                  <strong>{item.title}</strong>
                  <span>
                    {item.detected ? "detectado" : "não detectado"} · {formatPluginClassification(item.classification)}
                  </span>
                  <small>
                    Versão: {item.version ?? "-"} · dirty: {formatBoolean(item.dirty)} · behind:{" "}
                    {formatOptionalInt(item.commits_behind)}
                  </small>
                  <small>Ação: {formatPluginAction(item.action)}</small>
                </div>
                <p>{item.risk}</p>
                <small>{item.recommendation}</small>
                <small>Evidência: {item.evidence.join(" · ")}</small>
                <small>Gate: {item.removal_gates.join(" · ")}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-firmware">
          <div className="panel-heading">
            <h2>Firmware Manager</h2>
            <strong>{firmwareBoards.length} placas cadastradas</strong>
          </div>
          <p className="muted">
            Cadastro local de MCUs, presets, build e flash planejados. Flash permanece somente em dry-run nesta etapa.
          </p>
          <div className="dense-toolbar firmware-filter-toolbar" aria-label="Filtros de firmware">
            <button type="button" className={firmwareFilter === "all" ? "active" : ""} onClick={() => setFirmwareFilter("all")}>
              Todas
            </button>
            <button type="button" className={firmwareFilter === "can" ? "active" : ""} onClick={() => setFirmwareFilter("can")}>
              CAN
            </button>
            <button type="button" className={firmwareFilter === "usb" ? "active" : ""} onClick={() => setFirmwareFilter("usb")}>
              USB
            </button>
            <span>{visibleFirmwareBoards.length} placa(s) visíveis</span>
          </div>
          <form className="firmware-board-form" onSubmit={(event: any) => void createFirmwareBoard(event)}>
            <input
              aria-label="Nome da placa"
              value={firmwareBoardName}
              onChange={(event: any) => setFirmwareBoardName(event.target.value)}
              placeholder="EBB T0"
            />
            <select
              aria-label="Preset da placa"
              value={firmwareBoardPresetId}
              onChange={(event: any) => {
                setFirmwareBoardPresetId(event.target.value);
                setFirmwareBoardConfigFile(`firmware/${event.target.value}.config`);
              }}
            >
              {boardPresets.map((preset: any) => (
                <option key={preset.id} value={preset.id}>
                  {preset.vendor} · {preset.name}
                </option>
              ))}
            </select>
            <input
              aria-label="UUID CAN"
              value={firmwareBoardCanUuid}
              onChange={(event: any) => setFirmwareBoardCanUuid(event.target.value)}
              placeholder="UUID CAN"
            />
            <input
              aria-label="Interface CAN"
              value={firmwareBoardCanInterface}
              onChange={(event: any) => setFirmwareBoardCanInterface(event.target.value)}
              placeholder="can0"
            />
            <input
              aria-label="Arquivo .config"
              value={firmwareBoardConfigFile}
              onChange={(event: any) => setFirmwareBoardConfigFile(event.target.value)}
              placeholder="firmware/ebb_t0.config"
            />
            <textarea
              aria-label="Notas da placa"
              value={firmwareBoardNotes}
              onChange={(event: any) => setFirmwareBoardNotes(event.target.value)}
              placeholder="Ex.: toolhead CAN, Katapult já instalado"
            />
            <button type="submit" disabled={!selectedPrinterId || loading || boardPresets.length === 0}>
              Cadastrar placa
            </button>
          </form>
          <div className="firmware-board-list">
            <div className="list-table-header firmware-board-row">
              <strong>Placa</strong>
              <span>Conexão</span>
              <small>Ações</small>
            </div>
            {visibleFirmwareBoards.length === 0 ? <p className="muted">Nenhuma placa cadastrada para este filtro.</p> : null}
            {visibleFirmwareBoards.map((board: any) => (
              <div key={board.id} className="firmware-board-row">
                <div>
                  <strong>{board.name}</strong>
                  <span>
                    {board.preset_id} · {board.mcu} · {formatConnectionType(board.connection_type)}
                  </span>
                  <small>
                    flash futuro: {board.flash_method} · config: {board.config_file}
                  </small>
                </div>
                <div>
                  <span>CAN UUID: {board.can_uuid ?? "-"}</span>
                  <small>Interface: {board.can_interface}</small>
                </div>
                <div>
                  <small>{board.notes || "Sem notas."}</small>
                  <button type="button" onClick={() => void validateFirmwareBuildPreflight(board.id)} disabled={loading}>
                    Preflight build
                  </button>
                  <button type="button" onClick={() => void createFirmwareBuildDryRun(board.id)} disabled={loading}>
                    Dry-run build
                  </button>
                  <button type="button" onClick={() => void createFirmwareFlashDryRun(board.id)} disabled={loading}>
                    Dry-run flash
                  </button>
                  <button type="button" onClick={() => void validateFirmwareFlashPreflight(board.id)} disabled={loading}>
                    Preflight flash
                  </button>
                  <button type="button" onClick={() => void loadFirmwareRecoveryPlan(board.id)} disabled={loading}>
                    Plano recuperação
                  </button>
                  <button
                    type="button"
                    onClick={() => void validateFirmwareFlashGate(board.id)}
                    disabled={loading || firmwareFlashConfirmation !== "BLOCK_REAL_FLASH"}
                  >
                    Validar gate flash
                  </button>
                  <button
                    type="button"
                    onClick={() => void executeFirmwareBuildLocal(board.id)}
                    disabled={loading || firmwareBuildConfirmation !== "EXECUTE_LOCAL_BUILD_NO_FLASH"}
                  >
                    Executar build local
                  </button>
                </div>
              </div>
            ))}
          </div>
          {firmwareRecoveryPlan ? (
            <details className="firmware-run-row" open>
              <summary>
                Recuperação · {firmwareRecoveryPlan.board_name} · {firmwareRecoveryPlan.flash_method}
              </summary>
              <div className="firmware-run-detail">
                <small>
                  Modo: {firmwareRecoveryPlan.safe_mode} · bloqueado: {formatBoolean(firmwareRecoveryPlan.blocked)}
                </small>
                <strong>Pré-condições</strong>
                <ol>
                  {firmwareRecoveryPlan.prerequisites.map((item: any) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <strong>Recuperação</strong>
                <ol>
                  {firmwareRecoveryPlan.recovery_steps.map((item: any) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <strong>Validação</strong>
                <ol>
                  {firmwareRecoveryPlan.validation_steps.map((item: any) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <small>{firmwareRecoveryPlan.rollback_notes.join(" · ")}</small>
              </div>
            </details>
          ) : null}
          {firmwareBuildPreflight ? (
            <details className="firmware-run-row" open>
              <summary>
                Preflight build · {firmwareBuildPreflight.board_name} · bloqueado:{" "}
                {formatBoolean(firmwareBuildPreflight.blocked)}
              </summary>
              <div className="firmware-run-detail">
                <small>
                  Modo: {firmwareBuildPreflight.safe_mode} · execução liberada:{" "}
                  {formatBoolean(firmwareBuildPreflight.can_execute_build)}
                </small>
                <small>Klipper: {firmwareBuildPreflight.klipper_path}</small>
                <small>Config: {firmwareBuildPreflight.config_file}</small>
                <small>Output esperado: {firmwareBuildPreflight.expected_build_output}</small>
                <strong>Checks</strong>
                <ol>
                  {firmwareBuildPreflight.checks.map((item: any) => (
                    <li key={item.key}>
                      {item.label}: {item.status} · {item.detail}
                    </li>
                  ))}
                </ol>
                <strong>Preview</strong>
                <pre>{firmwareBuildPreflight.commands_preview.join("\n")}</pre>
                <small>{firmwareBuildPreflight.message}</small>
              </div>
            </details>
          ) : null}
          {firmwareFlashPreflight ? (
            <details className="firmware-run-row" open>
              <summary>
                Preflight flash · {firmwareFlashPreflight.board_name} · bloqueado:{" "}
                {formatBoolean(firmwareFlashPreflight.blocked)}
              </summary>
              <div className="firmware-run-detail">
                <small>
                  Modo: {firmwareFlashPreflight.safe_mode} · execução liberada:{" "}
                  {formatBoolean(firmwareFlashPreflight.can_execute_flash)}
                </small>
                <small>
                  Klipper: {firmwareFlashPreflight.klipper_state ?? "-"} · Klippy:{" "}
                  {firmwareFlashPreflight.klippy_state ?? "-"} · print: {firmwareFlashPreflight.print_state || "-"}
                </small>
                <small>
                  Método: {firmwareFlashPreflight.flash_method} · CAN: {firmwareFlashPreflight.can_uuid ?? "-"} ·{" "}
                  interface {firmwareFlashPreflight.can_interface}
                </small>
                <small>Binário: {firmwareFlashPreflight.binary_path}</small>
                <strong>Checks</strong>
                <ol>
                  {firmwareFlashPreflight.checks.map((item: any) => (
                    <li key={item.key}>
                      {item.label}: {item.status} · {item.detail}
                    </li>
                  ))}
                </ol>
                <strong>Preview bloqueado</strong>
                <pre>{firmwareFlashPreflight.commands_preview.join("\n")}</pre>
                <strong>Rollback futuro</strong>
                <ol>
                  {firmwareFlashPreflight.rollback_plan.map((item: any) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <small>{firmwareFlashPreflight.message}</small>
              </div>
            </details>
          ) : null}
          <details className="collapsible-panel firmware-control-panel" open>
            <summary>Parâmetros de build e flash</summary>
          <div className="firmware-build-controls">
            <input
              aria-label="Caminho do Klipper"
              value={firmwareKlipperPath}
              onChange={(event: any) => setFirmwareKlipperPath(event.target.value)}
              placeholder="~/klipper"
            />
            <input
              aria-label="Diretório raiz dos builds"
              value={firmwareOutputRoot}
              onChange={(event: any) => setFirmwareOutputRoot(event.target.value)}
              placeholder="~/printer_data/firmware_builds"
            />
            <input
              aria-label="Confirmação do build local"
              value={firmwareBuildConfirmation}
              onChange={(event: any) => setFirmwareBuildConfirmation(event.target.value)}
              placeholder="EXECUTE_LOCAL_BUILD_NO_FLASH"
            />
            <input
              aria-label="Binário para dry-run de flash"
              value={firmwareFlashBinaryPath}
              onChange={(event: any) => setFirmwareFlashBinaryPath(event.target.value)}
              placeholder="binário opcional para dry-run de flash"
            />
            <input
              aria-label="Confirmação do gate de flash"
              value={firmwareFlashConfirmation}
              onChange={(event: any) => setFirmwareFlashConfirmation(event.target.value)}
              placeholder="BLOCK_REAL_FLASH"
            />
          </div>
          </details>
          <details className="collapsible-panel firmware-history-panel">
            <summary>Histórico de builds</summary>
          <div className="firmware-run-list">
            {firmwareBuildRuns.length === 0 ? <p className="muted">Nenhum dry-run de firmware registrado.</p> : null}
            {firmwareBuildRuns.map((run: any) => (
              <details key={run.id} className="firmware-run-row">
                <summary>
                  #{run.id} · placa #{run.board_id} · {run.status} · {run.created_at}
                </summary>
                <div className="firmware-run-detail">
                  <small>Output: {run.output_dir}</small>
                  <small>Backup .config: {run.config_backup_path}</small>
                  <small>Binário planejado: {run.binary_output_path}</small>
                  <strong>Checklist</strong>
                  <ol>
                    {run.checklist.map((item: any) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                  <strong>Comandos planejados</strong>
                  <pre>{run.commands.join("\n")}</pre>
                  <small>{run.message}</small>
                </div>
              </details>
            ))}
          </div>
          </details>
          <details className="collapsible-panel firmware-history-panel">
            <summary>Histórico de flash</summary>
          <div className="firmware-run-list">
            {firmwareFlashRuns.length === 0 ? <p className="muted">Nenhum dry-run de flash registrado.</p> : null}
            {firmwareFlashRuns.map((run: any) => (
              <details key={run.id} className="firmware-run-row">
                <summary>
                  Flash #{run.id} · placa #{run.board_id} · {run.status} · {run.created_at}
                </summary>
                <div className="firmware-run-detail">
                  <small>Método: {run.flash_method}</small>
                  <small>Binário: {run.binary_path}</small>
                  <small>
                    CAN: {run.can_uuid ?? "-"} · interface {run.can_interface}
                  </small>
                  <strong>Checklist</strong>
                  <ol>
                    {run.checklist.map((item: any) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                  <strong>Comandos planejados</strong>
                  <pre>{run.commands.join("\n")}</pre>
                  <small>{run.message}</small>
                </div>
              </details>
            ))}
          </div>
          </details>
          <details className="preset-details">
            <summary>Presets disponíveis ({boardPresets.length})</summary>
            <div className="preset-list">
              {boardPresets.map((preset: any) => (
                <div key={preset.id} className="preset-row">
                  <strong>{preset.name}</strong>
                  <span>
                    {preset.mcu} · {formatConnectionType(preset.connection_type)} · {preset.default_flash_method}
                  </span>
                  <small>
                    bootloader: {preset.bootloader_offset} · output: {preset.build_output} · pins:{" "}
                    {preset.canbus_pins ?? "-"}
                  </small>
                </div>
              ))}
            </div>
          </details>
        </article>


    </>
  );
}
