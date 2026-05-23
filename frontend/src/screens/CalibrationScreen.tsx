import React from "react";
import { Badge, Metric, OperationActionParameterFields } from "../components/common";
import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenProps } from "./ScreenProps";
import type { MoonrakerStatus, DiscoveredPrinter, PrinterDiscoveryResponse, ConnectionCheckResult, PrinterConnectionTestResponse, PrinterRecord, SnapshotRecord, SnapshotDiffItem, SnapshotDiff, OperationMetric, OperationTemperature, OperationFan, OperationTemperatureHistoryRow, OperationAction, OperationCapability, OperationActionPreview, OperationActionParameterSpec, OperationActionPreviewRecord, OperationActionExecutionAttempt, OperationStatusResponse, BackupPolicyRecord, BackupRunRecord, BackupArchiveCompareResponse, BackupRestorePlanResponse, SanitizedReport, MaintenanceEventRecord, MaintenanceTaskRecord, MaintenanceSummary, MaintenancePrintHoursStatus, ZOffsetRecord, ZOffsetWizardPlan, CanBusRecord, CanBusSummary, CanBusRecordComparison, PluginAuditItem, PluginAuditResponse, ReleaseRecord, SystemReleasesResponse, UpdateActionResponse, UpdateLogEntry, UpdateDialogState, BoardPreset, FirmwareBoardRecord, FirmwareBuildRunRecord, FirmwareBuildPreflight, FirmwareFlashRunRecord, FirmwareFlashPreflight, FirmwareRecoveryPlan, BackupRestoreGateResponse, CalibrationTestRecord, CalibrationAvailableTestsResponse, CalibrationRunRecord, CalibrationResultFormConfig, CalibrationSummary, CalibrationSequencePlan, CalibrationPreflight, CalibrationExecutionRecord, ThemeMode } from "../types";

export function CalibrationScreen(props: ScreenProps) {
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
        <article className="panel wide panel-section panel-calibration">
          <div className="panel-heading">
            <div>
              <h2>Contexto de calibração</h2>
              <p className="muted">Estado da impressora ativa, sequência recomendada e histórico local.</p>
            </div>
            <strong>{selectedPrinter?.name ?? "Sem impressora"}</strong>
          </div>
          <div className="calibration-summary">
            <Badge label="Origem" value={formatOperationDataState(operationStatus?.data_state)} />
            <Badge label="Print state" value={operationStatus?.miscellaneous.print_state ?? "-"} />
            <Badge label="Hotend" value={formatTemperature(hotendTemperature?.temperature)} />
            <Badge label="Mesa" value={formatTemperature(bedTemperature?.temperature)} />
            <Badge label="Catálogo" value={calibrationSummary?.catalog_count ?? calibrationTests.length + calibrationHiddenTests.length} />
            <Badge label="Liberados" value={calibrationTests.length} />
            <Badge label="Bloqueados" value={calibrationBlockedGcodeCount} />
            <Badge label="Último Z" value={formatLatestZOffset(zOffsetRecords[0])} />
          </div>
          {operationStatus?.data_state === "last_snapshot" ? (
            <div className="operation-state last-snapshot">
              <Database size={17} />
              <div>
                <strong>Usando último snapshot conhecido</strong>
                <span>
                  Snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
                  A impressora selecionada existe, mas a leitura ao vivo do Moonraker não respondeu neste carregamento.
                </span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "offline" ? (
            <div className="operation-state offline">
              <AlertTriangle size={17} />
              <div>
                <strong>Moonraker sem leitura ao vivo</strong>
                <span>{operationStatus.error ?? "A tela mantém catálogo e histórico local, mas bloqueia testes que exigem G-code."}</span>
              </div>
            </div>
          ) : null}
          <div className="calibration-flow-grid">
            <section className="calibration-recommendations calibration-roadmap-panel">
              <div className="section-heading-compact">
                <strong>Sequência de calibração</strong>
                <span>{visibleCalibrationCompletedSteps}/{calibrationSequencePreview.length} visíveis tratados</span>
              </div>
              <p className="muted calibration-section-note">
                Siga de cima para baixo quando fizer sentido. Itens com G-code somem sem leitura ao vivo; use Pular para seguir sem aprovar.
              </p>
              {calibrationHiddenTests.length ? (
                <p className="muted calibration-section-note">
                  {calibrationHiddenTests.length} item(ns) que dependem da impressora online estão ocultos neste contexto.
                </p>
              ) : null}
              {calibrationSequencePreview.length === 0 ? <p className="muted">Aguardando sequência da impressora selecionada.</p> : null}
              <ol className="calibration-sequence-list">
                {calibrationSequencePreview.map((step: any) => {
                  const stepTest = calibrationTests.find((test: any) => test.test_key === step.test_key);
                  const hiddenReason = calibrationHiddenTests.find((test: any) => test.test_key === step.test_key)?.reason;
                  return (
                    <li key={`${step.order}-${step.test_key}`} className={`calibration-sequence-row ${step.status}`}>
                      <span className="calibration-step-index">{step.order}</span>
                      <span className="calibration-step-phase">{formatCalibrationPhase(step.phase).replace(/^\d+\.\s*/, "")}</span>
                      <span className="calibration-step-main">
                        <strong>{step.title}</strong>
                        <small>{formatExecutionMode(step.execution_mode)} · risco {formatRiskLevel(step.risk_level)}</small>
                      </span>
                      <em>{hiddenReason ? "bloqueado" : formatCalibrationSequenceStatus(step.status)}</em>
                      <span className="calibration-step-actions">
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => stepTest && setCalibrationHelpTestKey(stepTest.test_key)}
                          disabled={!stepTest}
                          aria-label={`Ajuda de ${step.title}`}
                          title="Ajuda"
                        >
                          <HelpCircle size={16} />
                        </button>
                        {stepTest?.gcode.length ? (
                          <button
                            type="button"
                            className="icon-button calibration-action-icon"
                            onClick={() => void openCalibrationExecute(stepTest)}
                            disabled={!selectedPrinterId || loading || Boolean(hiddenReason)}
                            aria-label={`Executar ${step.title}`}
                            title="Executar"
                          >
                            <Play size={16} />
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="icon-button calibration-action-icon"
                            onClick={() => stepTest && openCalibrationResult(stepTest, true)}
                            disabled={!selectedPrinterId || loading || !stepTest}
                            aria-label={`Registrar resultado de ${step.title}`}
                            title="Registrar"
                          >
                            <ClipboardCheck size={16} />
                          </button>
                        )}
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => stepTest && openCalibrationResult(stepTest, true, "skipped")}
                          disabled={!selectedPrinterId || loading || !stepTest}
                          aria-label={`Pular ${step.title}`}
                          title="Pular"
                        >
                          <SkipForward size={16} />
                        </button>
                      </span>
                    </li>
                  );
                })}
              </ol>
            </section>
            <section className="calibration-recommendations calibration-action-panel">
              <div className="section-heading-compact">
                <strong>Próximo ajuste</strong>
                <span>{calibrationVisibleGcodeCount} com G-code liberado(s)</span>
              </div>
              {visibleCalibrationRecommendations.length === 0 ? <p className="muted">Sem recomendações pendentes visíveis neste contexto.</p> : null}
              {visibleCalibrationRecommendations.map((test: any) => {
                const blockedReason = calibrationHiddenTests.find((hidden: any) => hidden.test_key === test.test_key)?.reason;
                const availableTest = calibrationTests.find((candidate: any) => candidate.test_key === test.test_key);
                return (
                  <div key={test.test_key} className={`calibration-next-row ${test.risk_level}`}>
                    <span className="calibration-next-title">
                      <strong>{test.title}</strong>
                      <em>{blockedReason ? "bloqueado" : "disponível"}</em>
                    </span>
                    <small>{formatCalibrationCategory(test.category)} · risco {formatRiskLevel(test.risk_level)}</small>
                    <small>{blockedReason ?? test.reason}</small>
                    <span className="calibration-next-actions">
                      <button
                        type="button"
                        className="icon-button calibration-action-icon"
                        onClick={() => availableTest && setCalibrationHelpTestKey(availableTest.test_key)}
                        disabled={!availableTest}
                        aria-label={`Ver orientação de ${test.title}`}
                        title="Ver orientação"
                      >
                        <HelpCircle size={16} />
                      </button>
                      {availableTest?.gcode.length ? (
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => void openCalibrationExecute(availableTest)}
                          disabled={!selectedPrinterId || loading || Boolean(blockedReason)}
                          aria-label={`Executar ${test.title} com confirmação`}
                          title="Executar com confirmação"
                        >
                          <Play size={16} />
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => availableTest && openCalibrationResult(availableTest, true)}
                          disabled={!selectedPrinterId || loading || !availableTest}
                          aria-label={`Registrar resultado de ${test.title}`}
                          title="Registrar resultado"
                        >
                          <ClipboardCheck size={16} />
                        </button>
                      )}
                    </span>
                  </div>
                );
              })}
            </section>
          </div>
        </article>

        <article className="panel wide panel-section panel-calibration calibration-fine-tune-panel">
          <div className="panel-heading">
            <div>
              <h2>Perfil aprovado de primeira camada</h2>
              <p className="muted">Registre apenas depois de aprovar a primeira camada. Futuramente este perfil deve ser sugerido pelos resultados acima.</p>
            </div>
            <strong>{formatLatestZOffset(zOffsetRecords[0])}</strong>
          </div>
          {!zOffsetFormOpen ? (
            <div className="first-layer-empty-state">
              <div>
                <strong>O que será registrado?</strong>
                <span>
                  Chapa usada, material, toolhead/nozzle, valor final de Z-offset e observações do teste. O app usa isso para comparar ajustes futuros.
                </span>
              </div>
              <button type="button" onClick={() => setZOffsetFormOpen(true)} disabled={!selectedPrinterId || loading}>
                Registrar perfil aprovado
              </button>
            </div>
          ) : null}
          {zOffsetFormOpen ? (
            <div className="wizard-actions">
              <button type="button" onClick={() => void evaluateZOffsetWizard()} disabled={!selectedPrinterId || loading}>
                Avaliar antes de salvar
              </button>
              <span>Preencha com o material e o valor real usado no teste. Nada é assumido automaticamente.</span>
            </div>
          ) : null}
          {zOffsetWizardPlan ? (
            <div className={`z-offset-wizard ${zOffsetWizardPlan.alert_level}`}>
              <div>
                <strong>{formatZOffsetAlert(zOffsetWizardPlan.alert_level)}</strong>
                <span>{zOffsetWizardPlan.recommendation}</span>
              </div>
              <div className="wizard-summary">
                <Badge label="Anterior" value={formatOptionalNumber(zOffsetWizardPlan.previous_offset_value)} />
                <Badge label="Novo" value={zOffsetWizardPlan.proposed_offset_value.toFixed(3)} />
                <Badge label="Delta" value={formatOptionalNumber(zOffsetWizardPlan.delta_value)} />
                <Badge label="Modo" value={zOffsetWizardPlan.safe_mode} />
              </div>
              <div className="wizard-steps">
                {zOffsetWizardPlan.steps.map((step: any) => (
                  <label key={step.key} className="wizard-step">
                    <input
                      type="checkbox"
                      checked={zOffsetWizardChecks[step.key] ?? false}
                      onChange={() => toggleWizardCheck(step.key)}
                    />
                    <span>
                      <strong>{step.title}</strong>
                      <small>{step.detail}</small>
                      {step.command ? <code>{step.command}</code> : null}
                    </span>
                  </label>
                ))}
              </div>
              <small className="muted">
                Checklist confirmado: {confirmedWizardSteps(zOffsetWizardChecks)}/{zOffsetWizardPlan.steps.length}
              </small>
            </div>
          ) : null}
          {zOffsetFormOpen ? (
            <form className="z-offset-form" onSubmit={(event: any) => void createZOffsetRecord(event)}>
              <label>
                <span>Chapa</span>
                <input
                  aria-label="Chapa"
                  value={zOffsetPlateName}
                  onChange={(event: any) => setZOffsetPlateName(event.target.value)}
                  placeholder="Ex.: Texturizada, lisa, PEI"
                />
              </label>
              <label>
                <span>Material</span>
                <input
                  aria-label="Material"
                  value={zOffsetMaterial}
                  onChange={(event: any) => setZOffsetMaterial(event.target.value)}
                  placeholder="Ex.: PLA, ABS, ASA"
                />
              </label>
              <label>
                <span>Toolhead/nozzle</span>
                <input
                  aria-label="Nozzle ou toolhead"
                  value={zOffsetNozzle}
                  onChange={(event: any) => setZOffsetNozzle(event.target.value)}
                  placeholder="Ex.: T0, T1, 0.4"
                />
              </label>
              <label>
                <span>Z-offset aprovado</span>
                <input
                  aria-label="Valor do Z-offset"
                  type="number"
                  step="0.001"
                  value={zOffsetValue}
                  onChange={(event: any) => setZOffsetValue(event.target.value)}
                  placeholder="Ex.: -0.295"
                />
              </label>
              <label>
                <span>Observação</span>
                <textarea
                  aria-label="Notas do Z-offset"
                  value={zOffsetNotes}
                  onChange={(event: any) => setZOffsetNotes(event.target.value)}
                  placeholder="Ex.: primeira camada uniforme após limpeza da mesa"
                />
              </label>
              <div className="z-offset-form-actions">
                <button type="button" onClick={() => setZOffsetFormOpen(false)}>
                  Cancelar
                </button>
                <button type="submit" disabled={!selectedPrinterId || loading}>
                  Salvar perfil
                </button>
              </div>
            </form>
          ) : null}
          <div className="z-offset-list">
            {zOffsetRecords.length === 0 ? <p className="muted">Nenhum perfil aprovado registrado ainda.</p> : null}
            {zOffsetRecords.map((record: any) => (
              <div key={record.id} className={`z-offset-row ${record.alert_level}`}>
                <div>
                  <strong>{record.offset_value.toFixed(3)}</strong>
                  <span>
                    {record.plate_name} · {record.material} · {record.nozzle} · {record.recorded_at}
                  </span>
                  <small>
                    Anterior: {formatOptionalNumber(record.previous_offset_value)} · Delta:{" "}
                    {formatOptionalNumber(record.delta_value)} · {formatZOffsetAlert(record.alert_level)}
                  </small>
                  {record.notes ? <small>{record.notes}</small> : null}
                </div>
              </div>
            ))}
          </div>
        </article>


    </>
  );
}
