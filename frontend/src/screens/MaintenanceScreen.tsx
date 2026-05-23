import React from "react";
import { Badge, Metric, OperationActionParameterFields } from "../components/common";
import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenProps } from "./ScreenProps";
import type { MoonrakerStatus, DiscoveredPrinter, PrinterDiscoveryResponse, ConnectionCheckResult, PrinterConnectionTestResponse, PrinterRecord, SnapshotRecord, SnapshotDiffItem, SnapshotDiff, OperationMetric, OperationTemperature, OperationFan, OperationTemperatureHistoryRow, OperationAction, OperationCapability, OperationActionPreview, OperationActionParameterSpec, OperationActionPreviewRecord, OperationActionExecutionAttempt, OperationStatusResponse, BackupPolicyRecord, BackupRunRecord, BackupArchiveCompareResponse, BackupRestorePlanResponse, SanitizedReport, MaintenanceEventRecord, MaintenanceTaskRecord, MaintenanceSummary, MaintenancePrintHoursStatus, ZOffsetRecord, ZOffsetWizardPlan, CanBusRecord, CanBusSummary, CanBusRecordComparison, PluginAuditItem, PluginAuditResponse, ReleaseRecord, SystemReleasesResponse, UpdateActionResponse, UpdateLogEntry, UpdateDialogState, BoardPreset, FirmwareBoardRecord, FirmwareBuildRunRecord, FirmwareBuildPreflight, FirmwareFlashRunRecord, FirmwareFlashPreflight, FirmwareRecoveryPlan, BackupRestoreGateResponse, CalibrationTestRecord, CalibrationAvailableTestsResponse, CalibrationRunRecord, CalibrationResultFormConfig, CalibrationSummary, CalibrationSequencePlan, CalibrationPreflight, CalibrationExecutionRecord, ThemeMode } from "../types";

export function MaintenanceScreen(props: ScreenProps) {
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
        <article className="panel wide panel-section panel-maintenance">
          <div className="maintenance-workspace">
            <section className="maintenance-hero">
              <div>
                <span className="section-kicker">Plano preventivo</span>
                <h2>{selectedPrinter?.name ?? "Impressora"}</h2>
                <p>
                  {nextMaintenanceTask
                    ? `${nextMaintenanceTask.name}: ${formatDueStatus(nextMaintenanceTask)}`
                    : "Nenhuma rotina preventiva criada."}
                </p>
              </div>
              <div className="maintenance-hero-actions">
                {maintenancePrintHoursAvailable ? (
                  <div className="maintenance-print-hours-chip">
                    <Timer size={16} />
                    <span>Total de impressão</span>
                    <strong>{formatHours(maintenancePrintHours.total_print_hours ?? 0)}</strong>
                  </div>
                ) : null}
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void createDefaultMaintenanceTasks()}
                  disabled={!selectedPrinterId || loading || maintenanceSummary?.recommended_tasks.length === 0}
                >
                  <Plus size={16} />
                  Recarregar catálogo
                </button>
              </div>
            </section>

            <div className="maintenance-status-grid">
              <Metric label="Vencidas" value={String(maintenanceSummary?.counts.due ?? 0)} />
              <Metric label="Próximas" value={String(maintenanceSummary?.counts.soon ?? 0)} />
              <Metric label="Em dia" value={String(maintenanceSummary?.counts.ok ?? 0)} />
              <Metric label="Registradas" value={String(maintenanceTasks.length)} />
            </div>

            <section className="maintenance-panel-card">
              <div className="maintenance-section-heading">
                <div>
                  <h3>Rotinas preventivas</h3>
                  <p className="muted">Cada rotina gera alerta quando vencer.</p>
                </div>
                <div className="dense-toolbar filter-toolbar" aria-label="Filtros de manutenção">
                  <button type="button" className={maintenanceFilter === "all" ? "active" : ""} onClick={() => setMaintenanceFilter("all")}>
                    Todas
                  </button>
                  <button type="button" className={maintenanceFilter === "due" ? "active" : ""} onClick={() => setMaintenanceFilter("due")}>
                    Vencidas
                  </button>
                  <button type="button" className={maintenanceFilter === "soon" ? "active" : ""} onClick={() => setMaintenanceFilter("soon")}>
                    Próximas
                  </button>
                  <button type="button" className={maintenanceFilter === "ok" ? "active" : ""} onClick={() => setMaintenanceFilter("ok")}>
                    Em dia
                  </button>
                </div>
              </div>

              {visibleMaintenanceTasks.length === 0 ? (
                <div className="empty-maintenance-state">
                  <strong>Nenhuma rotina neste filtro.</strong>
                  <span>O catálogo padrão será carregado automaticamente para esta impressora.</span>
                </div>
              ) : null}

              <div className="maintenance-card-grid">
                {visibleMaintenanceTasks.map((task: any) => (
                  <article key={task.id} className={`maintenance-task-card ${task.is_active ? task.due_status : "inactive"}`}>
                    <div className="maintenance-task-card-header">
                      <span className={`status-pill ${task.is_active ? task.due_status : "inactive"}`}>{formatDueStatus(task)}</span>
                      <strong>{task.name}</strong>
                    </div>
                    <div className="maintenance-task-meta">
                      <span>{task.component}</span>
                      <span>{task.is_active ? formatMaintenanceInterval(task) : "Sem lembrete recorrente"}</span>
                      <span>Última: {formatOptionalLocalDateTime(task.last_done_at)}</span>
                      {task.interval_kind === "print_hours" ? (
                        <>
                          <span>Base: {formatOptionalHours(task.last_done_print_hours)}</span>
                          <span>Atual: {formatOptionalHours(task.current_print_hours)}{task.current_print_hours_source === "cached" ? " · desatualizado" : ""}</span>
                          <span>{formatPrintHoursDueLine(task)}</span>
                        </>
                      ) : null}
                    </div>
                    <div className="maintenance-card-actions">
                      <button type="button" className="maintenance-done-button" onClick={() => openMaintenanceDoneModal(task)} disabled={loading}>
                        <CheckCircle2 size={14} />
                        Marcar feita
                      </button>
                      {task.last_done_at ? (
                        <button
                          type="button"
                          className="ghost-button danger-ghost"
                          onClick={() => void deleteLatestMaintenanceTaskEvent(task.id)}
                          disabled={loading}
                        >
                          <Undo2 size={14} />
                          Desfazer
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>

              {maintenanceSummary?.recommended_tasks.length ? (
                <div className="maintenance-catalog-note">
                  <strong>{maintenanceSummary.recommended_tasks.length} rotina(s) do catálogo ainda não foram ativadas.</strong>
                  <button type="button" className="secondary-button" onClick={() => void createDefaultMaintenanceTasks()} disabled={!selectedPrinterId || loading}>
                    Ativar restantes
                  </button>
                </div>
              ) : null}
            </section>

            <section
              className="maintenance-free-card"
              role="button"
              tabIndex={0}
              onClick={() => openMaintenanceFreeModal()}
              onKeyDown={(event: any) => {
                if (event.key === "Enter" || event.key === " ") {
                  openMaintenanceFreeModal();
                }
              }}
            >
              <div>
                <span className="section-kicker">Registro livre</span>
                <h3>Falha, ajuste ou anotação</h3>
                <p>Use para algo que não está no catálogo. Pode virar lembrete, se você definir um prazo.</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => openMaintenanceFreeModal()}>
                <Plus size={16} />
                Adicionar registro
              </button>
            </section>

            <section className="maintenance-panel-card">
              <div className="maintenance-section-heading">
                <div>
                  <h3>Histórico</h3>
                  <p className="muted">{maintenanceEvents.length} registro(s)</p>
                </div>
              </div>
              <div className="maintenance-timeline">
                {maintenanceEvents.length === 0 ? <p className="muted">Nenhum evento registrado.</p> : null}
                {maintenanceEvents.map((event: any) => (
                  <div key={event.id} className="maintenance-event-row">
                    <div className="maintenance-event-content">
                      <strong>{event.title}</strong>
                      <span>
                        {formatMaintenanceEventType(event.event_type)} · {event.component ?? "-"} · {formatLocalDateTime(event.performed_at)}
                      </span>
                      {event.notes ? <small>{event.notes}</small> : null}
                    </div>
                    <button
                      type="button"
                      className="ghost-button danger-ghost"
                      onClick={() => void deleteMaintenanceEvent(event.id)}
                      disabled={loading}
                    >
                      <Trash2 size={14} />
                      Remover
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>


    </>
  );
}
