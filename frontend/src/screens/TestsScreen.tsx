import type { ScreenPropsFor } from "./ScreenProps";

type TestsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "HelpCircle"
  | "History"
  | "Play"
  | "calibrationActivityCleared"
  | "calibrationExecutionResult"
  | "calibrationExecutionRowClass"
  | "calibrationExecutions"
  | "calibrationHiddenTests"
  | "calibrationRuns"
  | "calibrationSummary"
  | "calibrationTests"
  | "formatCalibrationCategory"
  | "formatCalibrationExecutionStatus"
  | "formatCalibrationResult"
  | "formatCalibrationTestTitle"
  | "formatRiskLevel"
  | "loading"
  | "openCalibrationExecute"
  | "openCalibrationResult"
  | "recentCalibrationActivityCount"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setCalibrationActivityCleared"
  | "setCalibrationExecutionResult"
  | "setCalibrationHelpTestKey"
  | "setTestFilter"
  | "status"
  | "summarizeCalibrationExecutionFinalState"
  | "testFilter"
  | "visibleCalibrationTests"
  | "visibleHiddenCalibrationTests"
>;

export function TestsScreen(props: TestsScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    HelpCircle,
    History,
    Play,
    calibrationActivityCleared,
    calibrationExecutionResult,
    calibrationExecutionRowClass,
    calibrationExecutions,
    calibrationHiddenTests,
    calibrationRuns,
    calibrationSummary,
    calibrationTests,
    formatCalibrationCategory,
    formatCalibrationExecutionStatus,
    formatCalibrationResult,
    formatCalibrationTestTitle,
    formatRiskLevel,
    loading,
    openCalibrationExecute,
    openCalibrationResult,
    recentCalibrationActivityCount,
    selectedPrinter,
    selectedPrinterId,
    setCalibrationActivityCleared,
    setCalibrationExecutionResult,
    setCalibrationHelpTestKey,
    setTestFilter,
    status,
    summarizeCalibrationExecutionFinalState,
    testFilter,
    visibleCalibrationTests,
    visibleHiddenCalibrationTests,
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

    </>
  );
}
