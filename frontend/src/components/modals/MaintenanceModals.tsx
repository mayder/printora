import React from "react";
import { Badge, ConnectionTestRow, Metric } from "../common";
import type { ScreenProps } from "../../screens/ScreenProps";
import type { MaintenanceEventRecord } from "../../types";

export function MaintenanceModals(props: ScreenProps) {
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
        {maintenanceDoneTask ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Registrar ${maintenanceDoneTask.name}`}>
            <div className="modal-card maintenance-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{maintenanceDoneTask.name}</h2>
                  <p>{selectedPrinter?.name ?? "Impressora"} · {formatLocalDateTime(new Date())}</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setMaintenanceDoneTask(null)}>
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <form className="maintenance-modal-form" onSubmit={(event: any) => void submitMaintenanceDone(event)}>
                <div className="maintenance-selected-printer">
                  <span>Impressora selecionada</span>
                  <strong>{selectedPrinter?.name ?? "Impressora"}</strong>
                  <small>{selectedPrinter?.moonraker_url ?? "-"}</small>
                </div>
                <div className="maintenance-modal-summary">
                  <Metric label="Componente" value={maintenanceDoneTask.component} />
                  <Metric label="Última" value={formatOptionalLocalDateTime(maintenanceDoneTask.last_done_at)} />
                  <Metric label="Lembrete atual" value={maintenanceDoneTask.is_active ? formatMaintenanceInterval(maintenanceDoneTask) : "sem lembrete"} />
                </div>
                {maintenancePrintHoursAvailable ? (
                  <div className="maintenance-print-hours-banner">
                    <Timer size={16} />
                    <span>Horas atuais de impressão</span>
                    <strong>{formatHours(maintenancePrintHours.total_print_hours ?? 0)}</strong>
                  </div>
                ) : (
                  <p className="maintenance-modal-hint">{maintenanceHoursDisabledMessage}</p>
                )}
                <label className="form-field">
                  <span>Observação</span>
                  <textarea
                    value={maintenanceDoneNotes}
                    onChange={(event: any) => setMaintenanceDoneNotes(event.target.value)}
                    placeholder="O que foi feito, peça trocada, condição encontrada..."
                  />
                </label>
                <p className="maintenance-modal-hint">
                  Com o prazo preenchido, o Printora volta a avisar quando vencer. Se deixar vazio, esta rotina fica registrada e não gera novo lembrete.
                </p>
                <div className="form-grid two-columns">
                  <label className="form-field">
                    <span>Lembrar por</span>
                    <select
                      value={maintenanceDoneIntervalKind}
                      onChange={(event: any) => {
                        const value = event.target.value as "days" | "print_hours";
                        if (value === "print_hours" && !maintenancePrintHoursAvailable) {
                          return;
                        }
                        setMaintenanceDoneIntervalKind(value);
                        setMaintenanceDoneDisableReminder(false);
                      }}
                      disabled={maintenanceDoneDisableReminder}
                    >
                      <option value="days">Dias</option>
                      <option value="print_hours" disabled={!maintenancePrintHoursAvailable}>Horas de impressão</option>
                    </select>
                  </label>
                  <label className="form-field">
                    <span>Valor</span>
                    <input
                      type="number"
                      min="1"
                      max={maintenanceDoneIntervalKind === "days" ? "3650" : "100000"}
                      step={maintenanceDoneIntervalKind === "days" ? "1" : "0.1"}
                      value={maintenanceDoneIntervalValue}
                      onChange={(event: any) => {
                        setMaintenanceDoneIntervalValue(event.target.value);
                        setMaintenanceDoneDisableReminder(false);
                      }}
                      placeholder="Vazio para nunca lembrar"
                      disabled={maintenanceDoneDisableReminder}
                    />
                  </label>
                </div>
                <div className="form-grid two-columns">
                  <label className="inline-check maintenance-no-reminder">
                    <input
                      type="checkbox"
                      checked={maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim()}
                      onChange={(event: any) => {
                        setMaintenanceDoneDisableReminder(event.target.checked);
                        if (event.target.checked) {
                          setMaintenanceDoneIntervalValue("");
                        }
                      }}
                    />
                    Não lembrar de novo
                  </label>
                </div>
                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setMaintenanceDoneTask(null)}>
                    <X size={16} />
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading}>
                    <CheckCircle2 size={16} />
                    Confirmar manutenção
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        {maintenanceFreeModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Registro livre de manutenção">
            <div className="modal-card maintenance-modal-card">
              <div className="modal-header">
                <div>
                  <h2>Registro livre</h2>
                  <p>{selectedPrinter?.name ?? "Impressora"} · {formatLocalDateTime(new Date())}</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setMaintenanceFreeModalOpen(false)}>
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <form className="maintenance-modal-form" onSubmit={(event: any) => void submitMaintenanceFreeEvent(event)}>
                <div className="maintenance-selected-printer">
                  <span>Impressora selecionada</span>
                  <strong>{selectedPrinter?.name ?? "Impressora"}</strong>
                  <small>{selectedPrinter?.moonraker_url ?? "-"}</small>
                </div>
                <div className="form-grid two-columns">
                  <label className="form-field">
                    <span>Tipo</span>
                    <select
                      value={maintenanceEventType}
                      onChange={(event: any) => setMaintenanceEventType(event.target.value as MaintenanceEventRecord["event_type"])}
                      required
                    >
                      <option value="" disabled>
                        Selecione o tipo
                      </option>
                      <option value="maintenance">manutenção</option>
                      <option value="failure">falha</option>
                      <option value="adjustment">ajuste</option>
                      <option value="note">nota</option>
                    </select>
                  </label>
                  <label className="form-field">
                    <span>Componente</span>
                    <input value={maintenanceComponent} onChange={(event: any) => setMaintenanceComponent(event.target.value)} required />
                  </label>
                </div>
                <label className="form-field">
                  <span>Título</span>
                  <input value={maintenanceTitle} onChange={(event: any) => setMaintenanceTitle(event.target.value)} required />
                </label>
                <label className="form-field">
                  <span>Notas</span>
                  <textarea value={maintenanceNotes} onChange={(event: any) => setMaintenanceNotes(event.target.value)} />
                </label>
                <label className="inline-check maintenance-no-reminder">
                  <input
                    type="checkbox"
                    checked={maintenanceFreeReminderEnabled}
                    onChange={(event: any) => {
                      setMaintenanceFreeReminderEnabled(event.target.checked);
                      if (!event.target.checked) {
                        setMaintenanceFreeIntervalValue("");
                      }
                    }}
                  />
                  Criar lembrete recorrente
                </label>
                {maintenanceFreeReminderEnabled ? (
                  <div className="form-grid two-columns">
                    <label className="form-field">
                      <span>Lembrar por</span>
                      <select
                        value={maintenanceFreeIntervalKind}
                        onChange={(event: any) => {
                          const value = event.target.value as "days" | "print_hours";
                          if (value === "print_hours" && !maintenancePrintHoursAvailable) {
                            return;
                          }
                          setMaintenanceFreeIntervalKind(value);
                        }}
                      >
                        <option value="days">Dias</option>
                        <option value="print_hours" disabled={!maintenancePrintHoursAvailable}>Horas de impressão</option>
                      </select>
                    </label>
                    <label className="form-field">
                      <span>Valor</span>
                      <input
                        type="number"
                        min="1"
                        max={maintenanceFreeIntervalKind === "days" ? "3650" : "100000"}
                        step={maintenanceFreeIntervalKind === "days" ? "1" : "0.1"}
                        value={maintenanceFreeIntervalValue}
                        onChange={(event: any) => setMaintenanceFreeIntervalValue(event.target.value)}
                        required={maintenanceFreeReminderEnabled}
                      />
                    </label>
                  </div>
                ) : null}
                <p className="maintenance-modal-hint">
                  {maintenancePrintHoursAvailable
                    ? `Horas atuais de impressão: ${formatHours(maintenancePrintHours.total_print_hours ?? 0)}.`
                    : `Sem lembrete recorrente, o registro fica apenas no histórico. ${maintenanceHoursDisabledMessage}`}
                </p>
                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setMaintenanceFreeModalOpen(false)}>
                    <X size={16} />
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading || !maintenanceEventType || !maintenanceComponent.trim() || !maintenanceTitle.trim() || (maintenanceFreeReminderEnabled && maintenanceFreeIntervalKind === "print_hours" && !maintenancePrintHoursAvailable)}>
                    <CheckCircle2 size={16} />
                    Salvar registro
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
    </>
  );
}
