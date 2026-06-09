import { Badge } from "../components/common";
import { calibrationLiveEvidenceLabel, calibrationVisualState, isCalibrationVerifiedByLiveStatus } from "../utils/calibrationLiveState";
import { formatDateTime } from "../utils/formatters";
import type { ScreenPropsFor } from "./ScreenProps";

type TestsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "HelpCircle"
  | "History"
  | "Play"
  | "SkipForward"
  | "bedTemperature"
  | "calibrationBlockedGcodeCount"
  | "calibrationActivityCleared"
  | "calibrationExecutionResult"
  | "calibrationExecutionRowClass"
  | "calibrationExecutions"
  | "calibrationHiddenTests"
  | "calibrationSequencePreview"
  | "calibrationRuns"
  | "calibrationSummary"
  | "calibrationTests"
  | "confirmedWizardSteps"
  | "createZOffsetRecord"
  | "evaluateZOffsetWizard"
  | "formatCalibrationCategory"
  | "formatCalibrationExecutionStatus"
  | "formatCalibrationResult"
  | "formatCalibrationTestTitle"
  | "formatExecutionMode"
  | "formatLatestZOffset"
  | "formatOperationDataState"
  | "formatOptionalNumber"
  | "formatRiskLevel"
  | "formatTemperature"
  | "formatZOffsetAlert"
  | "hotendTemperature"
  | "loading"
  | "openCalibrationExecute"
  | "openCalibrationResult"
  | "operationStatus"
  | "recentCalibrationActivityCount"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setCalibrationActivityCleared"
  | "setCalibrationExecutionResult"
  | "setCalibrationHelpTestKey"
  | "setTestFilter"
  | "setTestSearch"
  | "setTestUsageFilter"
  | "setZOffsetFormOpen"
  | "setZOffsetMaterial"
  | "setZOffsetNotes"
  | "setZOffsetNozzle"
  | "setZOffsetPlateName"
  | "setZOffsetValue"
  | "status"
  | "summarizeCalibrationExecutionFinalState"
  | "testFilter"
  | "testSearch"
  | "testUsageFilter"
  | "toggleWizardCheck"
  | "visibleCalibrationTests"
  | "visibleHiddenCalibrationTests"
  | "zOffsetFormOpen"
  | "zOffsetMaterial"
  | "zOffsetNotes"
  | "zOffsetNozzle"
  | "zOffsetPlateName"
  | "zOffsetRecords"
  | "zOffsetValue"
  | "zOffsetWizardChecks"
  | "zOffsetWizardPlan"
>;

function calibrationUsage(test: any) {
  const printLikeCategories = new Set(["primeira_camada", "material", "extrusao", "qualidade", "dimensional"]);
  if (printLikeCategories.has(test.category)) {
    return {
      label: "Imprime teste",
      className: "print",
      detail: "gera evidência visual ou peça de calibração",
    };
  }
  if (test.gcode.length > 0) {
    return {
      label: "Movimenta/aquece",
      className: "movement",
      detail: "executa comando na máquina sem peça impressa",
    };
  }
  return {
    label: "Inspeção manual",
    className: "manual",
    detail: "registro visual ou ajuste guiado pelo operador",
  };
}

export function TestsScreen(props: TestsScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    HelpCircle,
    History,
    Play,
    SkipForward,
    bedTemperature,
    calibrationBlockedGcodeCount,
    calibrationActivityCleared,
    calibrationExecutionResult,
    calibrationExecutionRowClass,
    calibrationExecutions,
    calibrationHiddenTests,
    calibrationSequencePreview,
    calibrationRuns,
    calibrationSummary,
    calibrationTests,
    confirmedWizardSteps,
    createZOffsetRecord,
    evaluateZOffsetWizard,
    formatCalibrationCategory,
    formatCalibrationExecutionStatus,
    formatCalibrationResult,
    formatCalibrationTestTitle,
    formatExecutionMode,
    formatLatestZOffset,
    formatOperationDataState,
    formatOptionalNumber,
    formatRiskLevel,
    formatTemperature,
    formatZOffsetAlert,
    hotendTemperature,
    loading,
    openCalibrationExecute,
    openCalibrationResult,
    operationStatus,
    recentCalibrationActivityCount,
    selectedPrinter,
    selectedPrinterId,
    setCalibrationActivityCleared,
    setCalibrationExecutionResult,
    setCalibrationHelpTestKey,
    setTestFilter,
    setTestSearch,
    setTestUsageFilter,
    setZOffsetFormOpen,
    setZOffsetMaterial,
    setZOffsetNotes,
    setZOffsetNozzle,
    setZOffsetPlateName,
    setZOffsetValue,
    status,
    summarizeCalibrationExecutionFinalState,
    testFilter,
    testSearch,
    testUsageFilter,
    toggleWizardCheck,
    visibleCalibrationTests,
    visibleHiddenCalibrationTests,
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
  const liveCompletedStepCount = calibrationSequencePreview.filter((step: any) =>
    step.status === "completed" || step.status === "skipped" || isCalibrationVerifiedByLiveStatus(step.test_key, operationStatus),
  ).length;

  return (
    <>
        <article className="panel wide panel-section panel-tests">
          <div className="panel-heading">
            <h2>Calibração da impressora</h2>
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
              <span>calibrações executáveis</span>
            </div>
            <div>
              <strong>{calibrationHiddenTests.length}</strong>
              <span>bloqueados pelo contexto</span>
            </div>
            <div>
              <strong>{liveCompletedStepCount}/{calibrationSequencePreview.length}</strong>
              <span>sequência tratada</span>
            </div>
            {operationStatus ? (
              <>
                <div>
                  <strong>{formatOperationDataState(operationStatus.data_state)}</strong>
                  <span>origem dos dados</span>
                </div>
                <div>
                  <strong>{operationStatus.miscellaneous?.print_state ?? "-"}</strong>
                  <span>print state</span>
                </div>
              </>
            ) : null}
            <div>
              <strong>{formatLatestZOffset(zOffsetRecords[0])}</strong>
              <span>último Z</span>
            </div>
            {operationStatus ? (
              <>
                <div>
                  <strong>{formatTemperature(hotendTemperature?.temperature)}</strong>
                  <span>hotend</span>
                </div>
                <div>
                  <strong>{formatTemperature(bedTemperature?.temperature)}</strong>
                  <span>mesa</span>
                </div>
              </>
            ) : null}
          </div>
          <div className="dense-toolbar calibration-filter-bar" aria-label="Filtros de calibração">
            <label className="calibration-search-field">
              <span>Buscar</span>
              <input
                value={testSearch}
                onChange={(event) => setTestSearch(event.target.value)}
                placeholder="Digite nome, categoria, objetivo ou modo"
              />
            </label>
            <div className="calibration-filter-group">
              <span>Execução</span>
              <div className="filter-toolbar" aria-label="Tipo de execução">
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
            </div>
            <div className="calibration-filter-group">
              <span>Uso</span>
              <div className="filter-toolbar" aria-label="Uso operacional">
                <button type="button" className={testUsageFilter === "all" ? "active" : ""} onClick={() => setTestUsageFilter("all")}>
                  Todos usos
                </button>
                <button type="button" className={testUsageFilter === "print" ? "active" : ""} onClick={() => setTestUsageFilter("print")}>
                  Imprime teste
                </button>
                <button type="button" className={testUsageFilter === "movement" ? "active" : ""} onClick={() => setTestUsageFilter("movement")}>
                  Movimenta/aquece
                </button>
                <button type="button" className={testUsageFilter === "manual" ? "active" : ""} onClick={() => setTestUsageFilter("manual")}>
                  Inspeção manual
                </button>
              </div>
            </div>
          </div>
          <div className="test-card-grid">
            {visibleCalibrationTests.map((test: any) => {
              const lastRun = calibrationRuns.find((run: any) => run.test_key === test.test_key);
              const lastExecution = calibrationExecutions.find((execution: any) => execution.test_key === test.test_key);
              const sequenceStep = calibrationSequencePreview.find((step: any) => step.test_key === test.test_key);
              const usage = calibrationUsage(test);
              const liveEvidence = calibrationLiveEvidenceLabel(test.test_key, operationStatus);
              const visualState = calibrationVisualState(test, lastRun, lastExecution, operationStatus);
              return (
                <article key={test.test_key} className={`test-card ${visualState}`}>
                  <div className="test-card-title">
                    <span className="test-card-sequence" title="Ordem sugerida na sequência de calibração">
                      {sequenceStep?.order ?? test.sort_order}
                    </span>
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
                  <div className={`test-card-usage ${usage.className}`}>
                    <strong>{usage.label}</strong>
                    <span>{usage.detail}</span>
                  </div>
                  <div className="test-card-meta">
                    <span>Risco: {formatRiskLevel(test.risk_level)}</span>
                    <span>{formatExecutionMode(test.execution_mode)}</span>
                    <span>{lastRun ? `Último: ${formatCalibrationResult(lastRun.result_status)}` : liveEvidence || "Sem resultado"}</span>
                  </div>
                  {lastExecution ? (
                    <small>
                      Última execução: {lastExecution.status} · {lastExecution.sent_commands.length} comando(s)
                    </small>
                  ) : null}
                  <div className="test-card-actions has-skip">
                    {test.gcode.length ? (
                      <button type="button" className="maintenance-done-button calibration-main-action" onClick={() => void openCalibrationExecute(test)} disabled={!selectedPrinterId || loading}>
                        <Play size={15} />
                        Executar
                      </button>
                    ) : (
                      <button type="button" className="maintenance-done-button calibration-main-action" onClick={() => openCalibrationResult(test, true)} disabled={!selectedPrinterId || loading}>
                        <CheckCircle2 size={15} />
                        Registrar
                      </button>
                    )}
                    <button type="button" className="secondary-button" onClick={() => openCalibrationResult(test)} disabled={!selectedPrinterId || loading}>
                      <History size={15} />
                      Histórico
                    </button>
                    <button type="button" className="secondary-button" onClick={() => openCalibrationResult(test, true, "skipped")} disabled={!selectedPrinterId || loading}>
                      <SkipForward size={15} />
                      Pular
                    </button>
                  </div>
                </article>
              );
            })}
            {visibleHiddenCalibrationTests.map((test: any) => (
              <article key={test.test_key} className="test-card high blocked hidden-test-card">
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

        <article className="panel wide panel-section panel-tests test-first-layer-panel calibration-fine-tune-panel">
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
                <input aria-label="Chapa" value={zOffsetPlateName} onChange={(event: any) => setZOffsetPlateName(event.target.value)} placeholder="Ex.: Texturizada, lisa, PEI" />
              </label>
              <label>
                <span>Material</span>
                <input aria-label="Material" value={zOffsetMaterial} onChange={(event: any) => setZOffsetMaterial(event.target.value)} placeholder="Ex.: PLA, ABS, ASA" />
              </label>
              <label>
                <span>Toolhead/nozzle</span>
                <input aria-label="Nozzle ou toolhead" value={zOffsetNozzle} onChange={(event: any) => setZOffsetNozzle(event.target.value)} placeholder="Ex.: T0, T1, 0.4" />
              </label>
              <label>
                <span>Z-offset aprovado</span>
                <input aria-label="Valor do Z-offset" type="number" step="0.001" value={zOffsetValue} onChange={(event: any) => setZOffsetValue(event.target.value)} placeholder="Ex.: -0.295" />
              </label>
              <label>
                <span>Observação</span>
                <textarea aria-label="Notas do Z-offset" value={zOffsetNotes} onChange={(event: any) => setZOffsetNotes(event.target.value)} placeholder="Ex.: primeira camada uniforme após limpeza da mesa" />
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
                  {formatCalibrationExecutionStatus(execution.status)} · {formatDateTime(execution.created_at)}
                </span>
                <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
              </div>
            ))}
          {!calibrationActivityCleared &&
            calibrationRuns.slice(0, 4).map((run: any) => (
              <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
                <strong>{run.test_title}</strong>
                <span>
                  {formatCalibrationResult(run.result_status)} · {formatDateTime(run.created_at)}
                </span>
              </div>
            ))}
          {!calibrationActivityCleared && !calibrationExecutions.length && !calibrationRuns.length ? (
            <p className="muted">Nenhuma atividade registrada ainda.</p>
          ) : null}
        </details>

    </>
  );
}
