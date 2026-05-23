import React from "react";
import { Badge, Metric, OperationActionParameterFields } from "../components/common";
import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenProps } from "./ScreenProps";
import type { MoonrakerStatus, DiscoveredPrinter, PrinterDiscoveryResponse, ConnectionCheckResult, PrinterConnectionTestResponse, PrinterRecord, SnapshotRecord, SnapshotDiffItem, SnapshotDiff, OperationMetric, OperationTemperature, OperationFan, OperationTemperatureHistoryRow, OperationAction, OperationCapability, OperationActionPreview, OperationActionParameterSpec, OperationActionPreviewRecord, OperationActionExecutionAttempt, OperationStatusResponse, BackupPolicyRecord, BackupRunRecord, BackupArchiveCompareResponse, BackupRestorePlanResponse, SanitizedReport, MaintenanceEventRecord, MaintenanceTaskRecord, MaintenanceSummary, MaintenancePrintHoursStatus, ZOffsetRecord, ZOffsetWizardPlan, CanBusRecord, CanBusSummary, CanBusRecordComparison, PluginAuditItem, PluginAuditResponse, ReleaseRecord, SystemReleasesResponse, UpdateActionResponse, UpdateLogEntry, UpdateDialogState, BoardPreset, FirmwareBoardRecord, FirmwareBuildRunRecord, FirmwareBuildPreflight, FirmwareFlashRunRecord, FirmwareFlashPreflight, FirmwareRecoveryPlan, BackupRestoreGateResponse, CalibrationTestRecord, CalibrationAvailableTestsResponse, CalibrationRunRecord, CalibrationResultFormConfig, CalibrationSummary, CalibrationSequencePlan, CalibrationPreflight, CalibrationExecutionRecord, ThemeMode } from "../types";

export function OperationScreen(props: ScreenProps) {
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
        <article className="panel wide panel-section panel-operation">
          <div className="panel-heading">
            <div>
              <h2>Operação read-only</h2>
              <p className="muted">{operationStatus?.summary ?? "Aguardando dados da impressora selecionada."}</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId && void loadOperationStatus(selectedPrinterId)} disabled={!selectedPrinterId || loading}>
              <RefreshCw size={15} />
              Recarregar
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadOfflineOperationFixture()} disabled={loading}>
              <Database size={15} />
              Exemplo offline
            </button>
          </div>
          <div className="overview-strip dense-toolbar">
            <Badge icon={Printer} label="Impressora" value={selectedPrinter?.name ?? "-"} />
            <Badge icon={Radio} label="Moonraker" value={operationStatus?.connected ? "online" : "offline"} />
            <Badge icon={ShieldCheck} label="Modo" value={operationStatus?.safe_mode ?? "read_only"} />
            <Badge icon={Database} label="Dados" value={formatOperationDataState(operationStatus?.data_state)} />
            <Badge icon={Gauge} label="Comandos" value={operationStatus?.can_send_commands ? "habilitados" : "bloqueados"} />
          </div>
          {operationStatus?.data_state === "offline" ? (
            <div className="operation-state offline">
              <AlertTriangle size={17} />
              <div>
                <strong>Sem leitura ao vivo</strong>
                <span>{operationStatus.error ?? "A impressora pode estar desligada ou fora da rede."}</span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "fixture" ? (
            <div className="operation-state fixture">
              <Database size={17} />
              <div>
                <strong>Fixture local</strong>
                <span>Dados simulados para validar layout com a impressora desligada. Nenhum endpoint da impressora foi chamado.</span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "last_snapshot" ? (
            <div className="operation-state last-snapshot">
              <Database size={17} />
              <div>
                <strong>Último estado conhecido</strong>
                <span>
                  Snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
                  A impressora não foi consultada ao exibir estes dados.
                </span>
              </div>
            </div>
          ) : null}
          <div className="operation-grid">
            <section className="operation-panel">
              <h3>System Loads</h3>
              <div className="section-summary">
                {operationStatus?.system_loads.map((metric: any) => (
                  <Metric key={metric.label} label={metric.label} value={formatOperationValue(metric.value, metric.unit)} />
                ))}
              </div>
            </section>

            <section className="operation-panel">
              <h3>Temperaturas</h3>
              <div className="temperature-list">
                <div className="list-table-header temperature-row">
                  <strong>Sensor</strong>
                  <span>Leitura</span>
                  <small>Potência</small>
                </div>
                {operationStatus?.temperatures.length === 0 ? <p className="muted">Nenhum heater ou sensor retornado pelo Moonraker.</p> : null}
                {operationStatus?.temperatures.map((item: any) => (
                  <div key={item.name} className="temperature-row">
                    <strong>{item.name}</strong>
                    <span>
                      {formatTemperature(item.temperature)} / alvo {formatTemperature(item.target)}
                    </span>
                    <small>Potência: {formatPercent(item.power)}</small>
                  </div>
                ))}
              </div>
            </section>

            <details className="operation-panel wide-operation-panel collapsible-panel">
              <summary>Histórico de temperaturas</summary>
              <div className="temperature-history">
                {buildTemperatureSeries(operationStatus?.temperature_history ?? []).length === 0 ? (
                  <p className="muted">Nenhum snapshot com temperatura disponível para histórico.</p>
                ) : null}
                {buildTemperatureSeries(operationStatus?.temperature_history ?? []).map((series: any) => (
                  <div key={series.name} className="temperature-history-row">
                    <div className="temperature-history-label">
                      <strong>{series.name}</strong>
                      <span>
                        {formatTemperature(series.min)} - {formatTemperature(series.max)}
                      </span>
                    </div>
                    <div className="temperature-sparkline" aria-label={`Histórico ${series.name}`}>
                      {series.points.map((point: any) => (
                        <span
                          key={`${series.name}-${point.snapshotId}-${point.createdAt}`}
                          style={{ height: `${temperatureBarHeight(point.temperature, series.min, series.max)}%` }}
                          title={`${point.createdAt}: ${formatTemperature(point.temperature)}`}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </details>

            <section className="operation-panel">
              <h3>Toolhead</h3>
              <div className="section-summary">
                <Metric label="Posição" value={formatPosition(operationStatus?.toolhead.position)} />
                <Metric label="Home" value={formatUnknown(operationStatus?.toolhead.homed_axes ?? "-")} />
                <Metric label="Velocidade máx." value={formatOperationValue(operationStatus?.toolhead.max_velocity, "mm/s")} />
                <Metric label="Aceleração máx." value={formatOperationValue(operationStatus?.toolhead.max_accel, "mm/s²")} />
                <Metric label="Speed factor" value={formatPercent(operationStatus?.toolhead.speed_factor)} />
              </div>
            </section>

            <section className="operation-panel">
              <h3>Extruder</h3>
              <div className="section-summary">
                <Metric label="Pressure advance" value={formatUnknown(operationStatus?.extruder.pressure_advance ?? "-")} />
                <Metric label="Smooth time" value={formatOperationValue(operationStatus?.extruder.smooth_time, "s")} />
                <Metric label="Extrusion factor" value={formatPercent(operationStatus?.extruder.extrusion_factor)} />
                <Metric label="Filamento usado" value={formatOperationValue(operationStatus?.extruder.filament_used, "mm")} />
              </div>
            </section>

            <section className="operation-panel wide-operation-panel">
              <h3>Miscellaneous</h3>
              <div className="section-summary">
                <Metric label="Print state" value={operationStatus?.miscellaneous.print_state ?? "-"} />
                <Metric label="Arquivo" value={operationStatus?.miscellaneous.filename || "-"} />
                <Metric label="Progresso" value={formatPercent(operationStatus?.miscellaneous.progress)} />
                <Metric label="Mensagem" value={operationStatus?.miscellaneous.message || "-"} />
              </div>
              <div className="fan-list">
                {operationStatus?.miscellaneous.fans?.length === 0 ? <p className="muted">Nenhum fan retornado pelo Moonraker.</p> : null}
                {operationStatus?.miscellaneous.fans?.map((fan: any) => (
                  <div key={fan.name} className="fan-row">
                    <strong>{fan.name}</strong>
                    <span>{formatPercent(fan.speed)}</span>
                    <small>RPM: {formatUnknown(fan.rpm ?? "-")}</small>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>


    </>
  );
}
