import React from "react";
import { Badge, Metric, OperationActionParameterFields } from "../components/common";
import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenProps } from "./ScreenProps";
import type { MoonrakerStatus, DiscoveredPrinter, PrinterDiscoveryResponse, ConnectionCheckResult, PrinterConnectionTestResponse, PrinterRecord, SnapshotRecord, SnapshotDiffItem, SnapshotDiff, OperationMetric, OperationTemperature, OperationFan, OperationTemperatureHistoryRow, OperationAction, OperationCapability, OperationActionPreview, OperationActionParameterSpec, OperationActionPreviewRecord, OperationActionExecutionAttempt, OperationStatusResponse, BackupPolicyRecord, BackupRunRecord, BackupArchiveCompareResponse, BackupRestorePlanResponse, SanitizedReport, MaintenanceEventRecord, MaintenanceTaskRecord, MaintenanceSummary, MaintenancePrintHoursStatus, ZOffsetRecord, ZOffsetWizardPlan, CanBusRecord, CanBusSummary, CanBusRecordComparison, PluginAuditItem, PluginAuditResponse, ReleaseRecord, SystemReleasesResponse, UpdateActionResponse, UpdateLogEntry, UpdateDialogState, BoardPreset, FirmwareBoardRecord, FirmwareBuildRunRecord, FirmwareBuildPreflight, FirmwareFlashRunRecord, FirmwareFlashPreflight, FirmwareRecoveryPlan, BackupRestoreGateResponse, CalibrationTestRecord, CalibrationAvailableTestsResponse, CalibrationRunRecord, CalibrationResultFormConfig, CalibrationSummary, CalibrationSequencePlan, CalibrationPreflight, CalibrationExecutionRecord, ThemeMode } from "../types";

export function TestsScreen(props: ScreenProps) {
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
        <article className="panel wide panel-section panel-tests">
          <div className="panel-heading">
            <h2>Testes da impressora</h2>
            <strong>{selectedPrinter?.name ?? "Sem impressora"}</strong>
          </div>
          <div className="test-board-header dense-toolbar">
            <div>
              <strong>{calibrationSummary?.run_count ?? calibrationRuns.length}</strong>
              <span>resultados registrados</span>
            </div>
            <div>
              <strong>{calibrationExecutions.filter((item: any) => item.status === "executed").length}</strong>
              <span>execuções feitas</span>
            </div>
            <div>
              <strong>{calibrationTests.filter((test: any) => test.gcode.length > 0).length}</strong>
              <span>testes executáveis</span>
            </div>
            <div>
              <strong>{calibrationHiddenTests.length}</strong>
              <span>bloqueados pelo contexto</span>
            </div>
          </div>
          <div className="dense-toolbar filter-toolbar" aria-label="Filtros de testes">
            <button type="button" className={testFilter === "all" ? "active" : ""} onClick={() => setTestFilter("all")}>
              Todos
            </button>
            <button type="button" className={testFilter === "executable" ? "active" : ""} onClick={() => setTestFilter("executable")}>
              Executáveis
            </button>
            <button type="button" className={testFilter === "manual" ? "active" : ""} onClick={() => setTestFilter("manual")}>
              Manuais
            </button>
            <button type="button" className={testFilter === "blocked" ? "active" : ""} onClick={() => setTestFilter("blocked")}>
              Bloqueados
            </button>
          </div>
          <div className="test-card-grid">
            {visibleCalibrationTests.map((test: any) => {
              const lastRun = calibrationRuns.find((run: any) => run.test_key === test.test_key);
              const lastExecution = calibrationExecutions.find((execution: any) => execution.test_key === test.test_key);
              return (
                <article key={test.test_key} className={`test-card ${test.risk_level}`}>
                  <div className="test-card-title">
                    <div>
                      <strong>{test.title}</strong>
                      <span>{formatCalibrationCategory(test.category)}</span>
                    </div>
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => setCalibrationHelpTestKey(test.test_key)}
                      aria-label={`Ajuda de ${test.title}`}
                    >
                      <HelpCircle size={16} />
                    </button>
                  </div>
                  <p>{test.objective}</p>
                  <div className="test-card-meta">
                    <span>Risco: {formatRiskLevel(test.risk_level)}</span>
                    <span>{test.gcode.length ? "Com G-code" : "Manual"}</span>
                    <span>{lastRun ? `Último: ${formatCalibrationResult(lastRun.result_status)}` : "Sem resultado"}</span>
                  </div>
                  {lastExecution ? (
                    <small>
                      Última execução: {lastExecution.status} · {lastExecution.sent_commands.length} comando(s)
                    </small>
                  ) : null}
                  <div className="test-card-actions">
                    {test.gcode.length ? (
                      <button type="button" className="primary-button" onClick={() => void openCalibrationExecute(test)} disabled={!selectedPrinterId || loading}>
                        <Play size={15} />
                        Executar
                      </button>
                    ) : (
                      <button type="button" className="primary-button" onClick={() => openCalibrationResult(test, true)} disabled={!selectedPrinterId || loading}>
                        <CheckCircle2 size={15} />
                        Registrar
                      </button>
                    )}
                    <button type="button" className="secondary-button" onClick={() => openCalibrationResult(test)} disabled={!selectedPrinterId || loading}>
                      <History size={15} />
                      Histórico
                    </button>
                  </div>
                </article>
              );
            })}
            {visibleHiddenCalibrationTests.map((test: any) => (
              <article key={test.test_key} className="test-card high blocked">
                <div className="test-card-title">
                  <div>
                    <strong>{test.title}</strong>
                    <span>bloqueado</span>
                  </div>
                  <AlertTriangle size={16} />
                </div>
                <p>{test.reason}</p>
                <div className="test-card-meta">
                  <span>Sem execução neste contexto</span>
                  <span>Disponível quando a capacidade for confirmada</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <details className="panel wide panel-section test-history-panel collapsible-panel">
          <summary>Atividade recente</summary>
          <div className="panel-heading">
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setCalibrationActivityCleared(true);
                setCalibrationExecutionResult(null);
              }}
              disabled={recentCalibrationActivityCount === 0}
            >
              Limpar visualização
            </button>
          </div>
          {calibrationActivityCleared ? <p className="muted">Atividade recente limpa nesta sessão.</p> : null}
          {!calibrationActivityCleared && calibrationExecutionResult ? (
            <div className={`test-history-row ${calibrationExecutionRowClass(calibrationExecutionResult.status)}`}>
              <strong>{formatCalibrationExecutionStatus(calibrationExecutionResult.status)}</strong>
              <span>{calibrationExecutionResult.message || "Sem mensagem."}</span>
              <small>{summarizeCalibrationExecutionFinalState(calibrationExecutionResult)}</small>
            </div>
          ) : null}
          {!calibrationActivityCleared &&
            calibrationExecutions.slice(0, 4).map((execution: any) => (
              <div key={execution.id} className={`test-history-row ${calibrationExecutionRowClass(execution.status)}`}>
                <strong>{formatCalibrationTestTitle(execution.test_key, calibrationTests)}</strong>
                <span>
                  {formatCalibrationExecutionStatus(execution.status)} · {execution.created_at}
                </span>
                <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
              </div>
            ))}
          {!calibrationActivityCleared &&
            calibrationRuns.slice(0, 4).map((run: any) => (
              <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
                <strong>{run.test_title}</strong>
                <span>
                  {formatCalibrationResult(run.result_status)} · {run.created_at}
                </span>
              </div>
            ))}
          {!calibrationActivityCleared && !calibrationExecutions.length && !calibrationRuns.length ? (
            <p className="muted">Nenhuma atividade registrada ainda.</p>
          ) : null}
        </details>

        {calibrationHelpTest ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Ajuda de ${calibrationHelpTest.title}`}>
            <div className="modal-card test-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{calibrationHelpTest.title}</h2>
                  <p>{calibrationHelpTest.objective}</p>
                </div>
                <button type="button" className="icon-button" onClick={() => setCalibrationHelpTestKey(null)} aria-label="Fechar ajuda">
                  <X size={18} />
                </button>
              </div>
              <div className="test-help-grid">
                <section>
                  <strong>Antes de começar</strong>
                  <ol>
                    {calibrationHelpTest.prerequisites.map((item: any) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                </section>
                <section>
                  <strong>Sucesso esperado</strong>
                  <ol>
                    {calibrationHelpTest.success_criteria.map((item: any) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                </section>
              </div>
              {calibrationHelpTest.gcode.length ? <pre>{calibrationHelpTest.gcode.join("\n")}</pre> : null}
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setCalibrationHelpTestKey(null)}>
                  Fechar
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {calibrationExecuteTest ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Executar ${calibrationExecuteTest.title}`}>
            <div className="modal-card test-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{calibrationExecuteTest.title}</h2>
                  <p>
                    {calibrationPreflight?.summary ?? "Preflight será validado antes do envio."}
                  </p>
                </div>
                <button type="button" className="icon-button" onClick={() => setCalibrationExecuteTestKey(null)} aria-label="Fechar execução">
                  <X size={18} />
                </button>
              </div>
              <div className={`test-preflight-status ${calibrationPreflight?.blocked ? "blocked" : "ready"}`}>
                <strong>{calibrationPreflight?.blocked ? "Bloqueado" : "Pronto para confirmação"}</strong>
                <span>
                  Klipper {calibrationPreflight?.klipper_state ?? "-"} · print {calibrationPreflight?.print_state || "-"}
                </span>
              </div>
              {calibrationPreflight?.block_reasons.length ? (
                <ul className="test-blockers">
                  {calibrationPreflight.block_reasons.map((reason: any) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              ) : null}
              <pre>{calibrationExecuteTest.gcode.join("\n")}</pre>
              <div className="test-confirm-grid">
                <label className="inline-check">
                  <input
                    type="checkbox"
                    checked={calibrationGcodeReviewed}
                    onChange={(event: any) => setCalibrationGcodeReviewed(event.target.checked)}
                  />
                  Revisei o G-code
                </label>
                <label className="inline-check">
                  <input
                    type="checkbox"
                    checked={calibrationOperatorPresent}
                    onChange={(event: any) => setCalibrationOperatorPresent(event.target.checked)}
                  />
                  Estou ao lado da impressora
                </label>
              </div>
              {calibrationExecutionResult ? (
                <div className={`test-history-row ${calibrationExecutionRowClass(calibrationExecutionResult.status)}`}>
                  <strong>{formatCalibrationExecutionStatus(calibrationExecutionResult.status)}</strong>
                  <span>{calibrationExecutionResult.message}</span>
                  <small>{summarizeCalibrationExecutionFinalState(calibrationExecutionResult)}</small>
                  <details>
                    <summary>Retorno registrado</summary>
                    <pre>{formatCalibrationExecutionResult(calibrationExecutionResult)}</pre>
                  </details>
                </div>
              ) : null}
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setCalibrationExecuteTestKey(null)}>
                  Cancelar
                </button>
                {calibrationExecutionResult?.status === "executed" ? (
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => {
                      setCalibrationExecuteTestKey(null);
                      openCalibrationResult(calibrationExecuteTest, true, "passed");
                      setCalibrationObservedValue(summarizeCalibrationExecutionFinalState(calibrationExecutionResult));
                      setCalibrationNotes(buildCalibrationExecutionNotes(calibrationExecutionResult));
                    }}
                  >
                    Registrar resultado
                  </button>
                ) : null}
                <button
                  type="button"
                  className="danger-button"
                  onClick={() => {
                    setCalibrationExecutionConfirmation("EXECUTE_CALIBRATION_GCODE");
                    void executeCalibrationGcode("EXECUTE_CALIBRATION_GCODE");
                  }}
                  disabled={!selectedPrinterId || loading || !calibrationGcodeReviewed || !calibrationOperatorPresent || !calibrationPreflight || calibrationPreflight.blocked}
                >
                  Executar agora
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {calibrationResultTest ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Resultados de ${calibrationResultTest.title}`}>
            <div className="modal-card test-modal-card">
              <div className="modal-header">
                <div>
                  <h2>Resultados - {calibrationResultTest.title}</h2>
                  <p>Histórico deste teste na impressora selecionada.</p>
                </div>
                <button type="button" className="icon-button" onClick={() => setCalibrationResultTestKey(null)} aria-label="Fechar resultado">
                  <X size={18} />
                </button>
              </div>
              <div className="test-result-history">
                {calibrationResultExecutions.map((execution: any) => (
                  <div key={`execution-${execution.id}`} className={`test-history-row ${calibrationExecutionRowClass(execution.status)}`}>
                    <strong>{formatCalibrationExecutionStatus(execution.status)}</strong>
                    <span>
                      {execution.created_at} · {execution.sent_commands.length} comando(s)
                    </span>
                    {execution.message ? <small>{execution.message}</small> : null}
                    <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
                  </div>
                ))}
                {calibrationResultRuns.map((run: any) => (
                  <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
                    <strong>{formatCalibrationResult(run.result_status)}</strong>
                    <span>
                      {run.created_at} · {run.material || "-"} · {run.plate_name || "-"} · {run.nozzle || "-"}
                    </span>
                    {run.observed_value ? <small>Valor: {run.observed_value}</small> : null}
                    {run.notes ? <small>{run.notes}</small> : null}
                  </div>
                ))}
                {!calibrationResultExecutions.length && !calibrationResultRuns.length ? (
                  <p className="muted">Ainda não há resultados para este teste.</p>
                ) : null}
              </div>
              {!calibrationResultFormOpen ? (
                <div className="modal-footer">
                  <button type="button" className="secondary-button" onClick={() => setCalibrationResultTestKey(null)}>
                    Fechar
                  </button>
                  <button type="button" className="primary-button" onClick={() => setCalibrationResultFormOpen(true)} disabled={!selectedPrinterId || loading}>
                    Adicionar resultado
                  </button>
                </div>
              ) : null}
              {calibrationResultFormOpen ? (
                <form className="test-result-form" onSubmit={(event: any) => void createCalibrationRun(event)}>
                  {calibrationResultFormConfig ? <p className="muted">{calibrationResultFormConfig.summary}</p> : null}
                  <select
                    aria-label="Resultado do teste"
                    value={calibrationResultStatus}
                    onChange={(event: any) => setCalibrationResultStatus(event.target.value as CalibrationRunRecord["result_status"])}
                  >
                    <option value="passed">aprovado</option>
                    <option value="warning">atenção</option>
                    <option value="failed">falhou</option>
                    <option value="skipped">ignorado</option>
                  </select>
                  {calibrationResultFormConfig?.showMaterial ? (
                    <label>
                      <span>Material</span>
                      <input value={calibrationMaterial} onChange={(event: any) => setCalibrationMaterial(event.target.value)} placeholder="Ex.: PLA, ABS, ASA" />
                    </label>
                  ) : null}
                  {calibrationResultFormConfig?.showPlate ? (
                    <label>
                      <span>Chapa</span>
                      <input value={calibrationPlateName} onChange={(event: any) => setCalibrationPlateName(event.target.value)} placeholder="Ex.: Texturizada, lisa, PEI" />
                    </label>
                  ) : null}
                  {calibrationResultFormConfig?.showNozzle ? (
                    <label>
                      <span>Toolhead/nozzle</span>
                      <input value={calibrationNozzle} onChange={(event: any) => setCalibrationNozzle(event.target.value)} placeholder="Ex.: T0, T1, 0.4" />
                    </label>
                  ) : null}
                  <label>
                    <span>{calibrationResultFormConfig?.observedLabel ?? "Valor observado"}</span>
                    <input
                      value={calibrationObservedValue}
                      onChange={(event: any) => setCalibrationObservedValue(event.target.value)}
                      placeholder={calibrationResultFormConfig?.observedPlaceholder ?? "Resumo objetivo do resultado"}
                    />
                  </label>
                  <label>
                    <span>{calibrationResultFormConfig?.notesLabel ?? "Notas"}</span>
                    <textarea
                      value={calibrationNotes}
                      onChange={(event: any) => setCalibrationNotes(event.target.value)}
                      placeholder={calibrationResultFormConfig?.notesPlaceholder ?? "Detalhes úteis para repetir ou investigar depois"}
                    />
                  </label>
                  <div className="modal-footer">
                    <button type="button" className="secondary-button" onClick={() => setCalibrationResultFormOpen(false)}>
                      Cancelar
                    </button>
                    <button type="submit" className="primary-button" disabled={!selectedPrinterId || loading}>
                      Salvar resultado
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          </div>
        ) : null}


    </>
  );
}
