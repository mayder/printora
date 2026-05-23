import React from "react";
import { Badge, ConnectionTestRow, Metric } from "../common";
import type { ScreenProps } from "../../screens/ScreenProps";
import type { MaintenanceEventRecord } from "../../types";

export function PrinterModal(props: ScreenProps) {
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
        {printerModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Cadastrar impressora">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <h2>{printerModalMode === "edit" ? "Editar impressora" : "Cadastrar impressora"}</h2>
                  <p>Configure Moonraker e, se quiser auditoria completa, o acesso SSH do host.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                  Fechar
                </button>
              </div>
              <div className="modal-actions">
                {printerModalMode === "create" ? (
                  <button type="button" className="secondary-button" onClick={() => void discoverPrinters()} disabled={loading}>
                    <Search size={16} />
                    Buscar na rede
                  </button>
                ) : null}
                <button type="button" className="secondary-button" onClick={() => void testPrinterConnections()} disabled={loading}>
                  <Radio size={16} />
                  Testar conexões
                </button>
                <span>
                  {printerModalMode === "create"
                    ? "Buscar usa HTTP GET em `/server/info`, sem G-code e sem cadastro automático."
                    : "Teste seguro: valida Moonraker e porta SSH sem enviar G-code."}
                </span>
              </div>
              {printerModalMode === "create" && discovery ? (
                <div className="discovery-box">
                  <div className="discovery-summary">
                    <strong>
                      {discovery.candidates.length} Moonraker encontrado(s) em {discovery.cidr}
                    </strong>
                    <span>
                      {discovery.scanned_hosts} hosts verificados · modo {discovery.safe_mode}
                    </span>
                  </div>
                  {discovery.warnings.map((warning: any) => (
                    <small key={warning} className="muted">
                      {warning}
                    </small>
                  ))}
                  <div className="discovery-list">
                    {discovery.candidates.length === 0 ? <p className="muted">Nenhuma impressora encontrada na rede atual.</p> : null}
                    {discovery.candidates.map((candidate: any) => (
                      <div key={candidate.moonraker_url} className="discovery-row">
                        <div>
                          <strong>{candidate.name}</strong>
                          <span>{candidate.moonraker_url}</span>
                          <small>
                            Klippy: {candidate.klippy_state ?? "-"} · Moonraker: {candidate.moonraker_version ?? "-"}
                          </small>
                        </div>
                        {candidate.already_registered ? (
                          <span className="registered-badge">já cadastrada</span>
                        ) : (
                          <button type="button" onClick={() => useDiscoveredPrinter(candidate)} disabled={loading}>
                            Usar dados
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              {printerConnectionTest ? (
                <div className="connection-test-box">
                  <ConnectionTestRow label="Moonraker" result={printerConnectionTest.moonraker} />
                  <ConnectionTestRow label="SSH" result={printerConnectionTest.ssh} emptyDetail="Preencha host SSH para testar a porta." />
                </div>
              ) : null}
              <form className="printer-access-form" onSubmit={(event: any) => void createPrinter(event)}>
                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Conexão Moonraker</strong>
                    <span>Usada para status, snapshots e leitura segura via HTTP.</span>
                  </div>
                  <div className="form-grid two-columns">
                    <label className="form-field">
                      <span>Nome</span>
                      <input
                        aria-label="Nome da impressora"
                        value={newPrinterName}
                        onChange={(event: any) => setNewPrinterName(event.target.value)}
                        placeholder="Voron 2.4"
                      />
                    </label>
                    <label className="form-field">
                      <span>URL Moonraker</span>
                      <input
                        aria-label="URL Moonraker"
                        value={newPrinterUrl}
                        onChange={(event: any) => setNewPrinterUrl(event.target.value)}
                        placeholder="http://voron.local:7125"
                      />
                    </label>
                  </div>
                </section>

                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Acesso SSH</strong>
                    <span>Necessário para auditoria profunda, CAN, systemd, backups locais e firmware.</span>
                  </div>
                  <div className="form-grid ssh-grid">
                    <label className="form-field">
                      <span>Host SSH</span>
                      <input
                        aria-label="Host SSH"
                        value={newPrinterSshHost}
                        onChange={(event: any) => setNewPrinterSshHost(event.target.value)}
                        placeholder="voron.local"
                      />
                    </label>
                    <label className="form-field compact-field">
                      <span>Porta</span>
                      <input
                        aria-label="Porta SSH"
                        type="number"
                        min="1"
                        max="65535"
                        value={newPrinterSshPort}
                        onChange={(event: any) => setNewPrinterSshPort(Number(event.target.value))}
                        placeholder="22"
                      />
                    </label>
                    <label className="form-field">
                      <span>Usuário</span>
                      <input
                        aria-label="Usuário SSH"
                        value={newPrinterSshUser}
                        onChange={(event: any) => setNewPrinterSshUser(event.target.value)}
                        placeholder="pi"
                      />
                    </label>
                    <label className="form-field">
                      <span>{printerModalMode === "edit" ? "Nova senha opcional" : "Senha"}</span>
                      <input
                        aria-label="Senha SSH"
                        type="password"
                        value={newPrinterSshCredential}
                        onChange={(event: any) => setNewPrinterSshCredential(event.target.value)}
                        placeholder={printerModalMode === "edit" ? "Deixe vazio para manter a atual" : "Senha SSH"}
                      />
                    </label>
                  </div>
                  <small className="form-note">
                    O valor sensível não é retornado pela API. Em edição, deixe a senha vazia para manter a credencial atual.
                  </small>
                </section>

                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading || (!maintenanceDoneDisableReminder && maintenanceDoneIntervalKind === "print_hours" && !maintenancePrintHoursAvailable)}>
                    <Plus size={16} />
                    {printerModalMode === "edit" ? "Salvar impressora" : "Cadastrar impressora"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
    </>
  );
}
