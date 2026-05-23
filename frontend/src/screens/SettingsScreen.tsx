import React from "react";
import { Badge, Metric, OperationActionParameterFields } from "../components/common";
import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenProps } from "./ScreenProps";
import type { MoonrakerStatus, DiscoveredPrinter, PrinterDiscoveryResponse, ConnectionCheckResult, PrinterConnectionTestResponse, PrinterRecord, SnapshotRecord, SnapshotDiffItem, SnapshotDiff, OperationMetric, OperationTemperature, OperationFan, OperationTemperatureHistoryRow, OperationAction, OperationCapability, OperationActionPreview, OperationActionParameterSpec, OperationActionPreviewRecord, OperationActionExecutionAttempt, OperationStatusResponse, BackupPolicyRecord, BackupRunRecord, BackupArchiveCompareResponse, BackupRestorePlanResponse, SanitizedReport, MaintenanceEventRecord, MaintenanceTaskRecord, MaintenanceSummary, MaintenancePrintHoursStatus, ZOffsetRecord, ZOffsetWizardPlan, CanBusRecord, CanBusSummary, CanBusRecordComparison, PluginAuditItem, PluginAuditResponse, ReleaseRecord, SystemReleasesResponse, UpdateActionResponse, UpdateLogEntry, UpdateDialogState, BoardPreset, FirmwareBoardRecord, FirmwareBuildRunRecord, FirmwareBuildPreflight, FirmwareFlashRunRecord, FirmwareFlashPreflight, FirmwareRecoveryPlan, BackupRestoreGateResponse, CalibrationTestRecord, CalibrationAvailableTestsResponse, CalibrationRunRecord, CalibrationResultFormConfig, CalibrationSummary, CalibrationSequencePlan, CalibrationPreflight, CalibrationExecutionRecord, ThemeMode } from "../types";

export function SettingsScreen(props: ScreenProps) {
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
        <article className="panel wide panel-section panel-settings">
          <div className="panel-heading">
            <h2>Registro técnico CAN</h2>
            <strong>{formatCanAlert(canSummary?.overall_alert ?? canRecords[0]?.alert_level ?? "ok")}</strong>
          </div>
          <div className="can-summary">
            <Badge label="Modo" value={canSummary?.safe_mode ?? "manual_read_only"} />
            <Badge label="Dados" value={canSummary?.data_state === "manual_records" ? "registros manuais" : "sem registros"} />
            <Badge label="OK" value={canSummary?.counts.ok ?? 0} />
            <Badge label="Monitorar" value={canSummary?.counts.monitorar ?? 0} />
            <Badge label="Problemas" value={canSummary?.counts.problema ?? 0} />
          </div>
          <div className="panel-actions">
            <button type="button" className="secondary-button" onClick={() => void compareLatestCanRecords()} disabled={!selectedPrinterId || loading || canRecords.length < 2}>
              Comparar últimas leituras
            </button>
          </div>
          {canSummary?.data_state === "no_data" ? (
            <p className="muted">Nenhuma leitura CAN local registrada. Este formulário é técnico e não aparece na tela de monitoramento.</p>
          ) : null}
          {canComparison ? (
            <div className={`can-row ${canComparison.alert_level}`}>
              <strong>Comparação #{canComparison.before_record_id} → #{canComparison.after_record_id}</strong>
              <span>
                {canComparison.interface_name} · rx={canComparison.delta_rx_error} · tx={canComparison.delta_tx_error} · retries={canComparison.delta_tx_retries}
              </span>
              <small>{canComparison.diagnosis}</small>
              <small>{canComparison.recommended_actions.join(" · ")}</small>
            </div>
          ) : null}
          <div className="can-parser">
            <textarea
              aria-label="Saída bruta ip link CAN"
              value={canRawOutput}
              onChange={(event: any) => setCanRawOutput(event.target.value)}
              placeholder="Cole aqui a saída de ip -details -statistics link show can0 para preencher os campos."
            />
            <button type="button" className="secondary-button" onClick={() => void parseCanRawOutput()} disabled={!selectedPrinterId || loading || !canRawOutput.trim()}>
              Extrair leitura
            </button>
          </div>
          <form className="can-form" onSubmit={(event: any) => void createCanRecord(event)}>
            <input
              aria-label="Interface CAN"
              value={canInterfaceName}
              onChange={(event: any) => setCanInterfaceName(event.target.value)}
              placeholder="can0"
            />
            <input
              aria-label="RX error"
              type="number"
              min="0"
              value={canRxError}
              onChange={(event: any) => setCanRxError(Number(event.target.value))}
            />
            <input
              aria-label="TX error"
              type="number"
              min="0"
              value={canTxError}
              onChange={(event: any) => setCanTxError(Number(event.target.value))}
            />
            <input
              aria-label="TX retries"
              type="number"
              min="0"
              value={canTxRetries}
              onChange={(event: any) => setCanTxRetries(Number(event.target.value))}
            />
            <input
              aria-label="Estado do barramento"
              value={canBusState}
              onChange={(event: any) => setCanBusState(event.target.value)}
              placeholder="ERROR-ACTIVE"
            />
            <input
              aria-label="Bitrate CAN"
              type="number"
              min="1"
              value={canBitrate}
              onChange={(event: any) => setCanBitrate(Number(event.target.value))}
            />
            <textarea
              aria-label="Notas CAN"
              value={canNotes}
              onChange={(event: any) => setCanNotes(event.target.value)}
              placeholder="Ex.: leitura manual de ip -details -statistics link show can0"
            />
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Registrar
            </button>
          </form>
          <div className="can-list">
            {canRecords.length === 0 ? <p className="muted">Nenhuma leitura CAN registrada.</p> : null}
            {canRecords.map((record: any) => (
              <div key={record.id} className={`can-row ${record.alert_level}`}>
                <strong>{formatCanAlert(record.alert_level)}</strong>
                <span>
                  {record.interface_name} · rx={record.rx_error} · tx={record.tx_error} · retries={record.tx_retries} ·{" "}
                  {record.recorded_at}
                </span>
                <small>
                  Delta rx={formatOptionalInt(record.delta_rx_error)} · tx={formatOptionalInt(record.delta_tx_error)} ·
                  retries={formatOptionalInt(record.delta_tx_retries)}
                </small>
                <small>
                  Estado: {record.bus_state ?? "-"} · bitrate: {record.bitrate ?? "-"}
                </small>
                <small>{record.diagnosis}</small>
                {record.recommended_actions.length ? <small>{record.recommended_actions.join(" · ")}</small> : null}
                {record.notes ? <small>{record.notes}</small> : null}
              </div>
            ))}
          </div>
        </article>

        <article className={`panel wide panel-section panel-settings releases-panel ${releasePanelClass(systemReleases)}`}>
          <div className="panel-header-row">
            <div>
              <h2>Releases do Printora</h2>
              <p>{releaseLoading ? "Consultando GitHub Releases..." : systemReleases?.message ?? "Status ainda não carregado."}</p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={() => void loadSystemReleases()}
              disabled={releaseLoading}
            >
              <RefreshCw size={16} />
              {releaseLoading ? "Verificando" : "Verificar releases"}
            </button>
          </div>
          <div className="release-summary-grid">
            <Metric label="Versão instalada" value={systemReleases?.installed_version ?? "-"} />
            <Metric label="Última release" value={systemReleases?.latest_release?.tag ?? "-"} />
            <Metric label="Canal" value={systemReleases?.channel ?? "-"} />
            <Metric label="Status" value={formatReleaseUpdateStatus(systemReleases, releaseLoading, releaseError)} />
          </div>
          {releaseError ? (
            <div className="action-result warning">
              <strong>Erro de rede</strong>
              <span>{releaseError}</span>
            </div>
          ) : null}
          {systemReleases?.error ? (
            <div className="action-result warning">
              <strong>{formatReleaseSourceStatus(systemReleases.status)}</strong>
              <span>{systemReleases.error}</span>
            </div>
          ) : null}
          {systemReleases?.latest_release ? (
            <div className="release-latest-card">
              <div>
                <span className={`status-pill ${releaseStatusPillClass(systemReleases)}`}>
                  {formatReleaseUpdateStatus(systemReleases, false, null)}
                </span>
                <strong>{systemReleases.latest_release.name}</strong>
                <small>
                  {systemReleases.latest_release.tag} · {systemReleases.latest_release.published_at ?? "sem data"} · {systemReleases.latest_release.channel}
                </small>
              </div>
              <p>{systemReleases.latest_release.changelog_summary || "Sem changelog informado."}</p>
              {systemReleases.latest_release_available ? (
                <div className="update-actions">
                  <button type="button" className="secondary-button" onClick={() => void startSelfUpdateFlow()} disabled={releaseLoading}>
                    <ShieldAlert size={16} />
                    Atualizar agora
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
          {selfUpdateMessage ? (
            <div className={`action-result ${selfUpdateConnectionLost ? "warning" : ""}`}>
              <strong>{selfUpdateConnectionLost ? "Conexão interrompida" : "Updater do Printora"}</strong>
              <span>{selfUpdateMessage}</span>
            </div>
          ) : null}
          <div className="release-list">
            <details className="collapsible-panel">
              <summary>Releases anteriores</summary>
              {releaseLoading ? <p className="muted">Carregando releases de produção...</p> : null}
              {!releaseLoading && displayedReleaseRows.length === 0 ? (
                <p className="muted">Nenhuma release anterior para listar.</p>
              ) : null}
              {displayedReleaseRows.map((release: any) => (
                <div key={release.tag} className={`release-row ${release.installed ? "installed" : ""}`}>
                  <div>
                    <strong>{release.name}</strong>
                    <span>
                      {release.tag} · {release.published_at ?? "sem data"} · {release.installed ? "instalada" : release.channel}
                    </span>
                  </div>
                  <p>{release.changelog_summary || "Sem changelog informado."}</p>
                </div>
              ))}
            </details>
          </div>
          <div className="self-update-history">
            <div className="panel-header-row compact">
              <div>
                <h3>Histórico de updates</h3>
              </div>
              <button type="button" className="ghost-button" onClick={() => void loadSelfUpdateHistory()}>
                <History size={15} />
                Recarregar
              </button>
            </div>
            {selfUpdateHistory.length === 0 ? <p className="muted">Nenhum update do Printora registrado.</p> : null}
            {selfUpdateHistory.slice(0, 5).map((run: any) => (
              <div key={run.id} className={`update-row ${selfUpdateRunClass(run.status)}`}>
                <div className="update-main">
                  <div>
                    <strong>#{run.id} · {run.target_tag}</strong>
                    <span>
                      {formatSelfUpdateStatus(run.status)} · {run.created_at}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                      setSelfUpdateConfirmation("");
                      setSelfUpdateRollbackConfirmation("");
                      setSelfUpdatePlan({
                        safe_mode: "history",
                        update_supported: isSelfUpdateEnvironmentSupported(run.environment),
                        can_apply: false,
                        message: "Detalhes do update registrado.",
                        run,
                      });
                      setSelfUpdateModalOpen(true);
                    }}
                  >
                    <FileText size={15} />
                    Ver detalhes
                  </button>
                  {canRollbackSelfUpdateRun(run) ? (
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        setSelfUpdateConfirmation("");
                        setSelfUpdateRollbackConfirmation("");
                        setSelfUpdatePlan({
                          safe_mode: "history",
                          update_supported: isSelfUpdateEnvironmentSupported(run.environment),
                          can_apply: false,
                          message: "Revise os detalhes antes do rollback.",
                          run,
                        });
                        setSelfUpdateModalOpen(true);
                      }}
                    >
                      <Undo2 size={15} />
                      Rollback
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </article>

        <details className="panel wide panel-section panel-settings collapsible-panel host-diagnostics-panel">
          <summary>Diagnóstico avançado do host</summary>
          <p className="muted">Leitura técnica do computador onde o Printora roda. Use quando precisar investigar systemd, CAN, symlinks ou repositórios locais.</p>
          <strong className="summary">{hostAudit?.summary ?? "Aguardando dados"}</strong>
          <div className="audit-counts">
            <Badge icon={Settings} label="Modo" value={hostAudit?.mode ?? "-"} />
            <Badge icon={Activity} label="Executou" value={hostAudit?.executed ? "sim" : "não"} />
            <Badge icon={AlertTriangle} label="Monitorar" value={hostAudit?.counts.monitorar ?? 0} />
            <Badge icon={ShieldCheck} label="Corrigir" value={hostAudit?.counts.corrigir_agora ?? 0} />
          </div>
          <div className="section-summary">
            {hostAudit?.section_summary
              ? Object.entries(hostAudit.section_summary).map(([key, value]) => (
                  <Metric key={key} label={formatMetricLabel(key)} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {hostAudit?.findings.map((finding: any) => (
              <div key={finding.id} className={`finding ${finding.severity}`}>
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.category} · {formatClassification(finding.classification)}</span>
                </div>
                <p>{finding.detail}</p>
                <small>{finding.safe_action}</small>
              </div>
            ))}
          </div>
        </details>

    </>
  );
}
