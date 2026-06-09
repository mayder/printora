import { Badge } from "../components/common";
import { calibrationLiveEvidenceLabel, isCalibrationVerifiedByLiveStatus } from "../utils/calibrationLiveState";
import type { ScreenPropsFor } from "./ScreenProps";

type CalibrationScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "ClipboardCheck"
  | "Database"
  | "HelpCircle"
  | "Play"
  | "SkipForward"
  | "bedTemperature"
  | "calibrationBlockedGcodeCount"
  | "calibrationHiddenTests"
  | "calibrationSequencePreview"
  | "calibrationSummary"
  | "calibrationTests"
  | "calibrationVisibleGcodeCount"
  | "confirmedWizardSteps"
  | "createZOffsetRecord"
  | "error"
  | "evaluateZOffsetWizard"
  | "formatCalibrationCategory"
  | "formatCalibrationPhase"
  | "formatCalibrationSequenceStatus"
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
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setCalibrationHelpTestKey"
  | "setZOffsetFormOpen"
  | "setZOffsetMaterial"
  | "setZOffsetNotes"
  | "setZOffsetNozzle"
  | "setZOffsetPlateName"
  | "setZOffsetValue"
  | "status"
  | "toggleWizardCheck"
  | "visibleCalibrationRecommendations"
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

export function CalibrationScreen(props: CalibrationScreenProps) {
  const {
    AlertTriangle,
    ClipboardCheck,
    Database,
    HelpCircle,
    Play,
    SkipForward,
    bedTemperature,
    calibrationBlockedGcodeCount,
    calibrationHiddenTests,
    calibrationSequencePreview,
    calibrationSummary,
    calibrationTests,
    calibrationVisibleGcodeCount,
    confirmedWizardSteps,
    createZOffsetRecord,
    error,
    evaluateZOffsetWizard,
    formatCalibrationCategory,
    formatCalibrationPhase,
    formatCalibrationSequenceStatus,
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
    selectedPrinter,
    selectedPrinterId,
    setCalibrationHelpTestKey,
    setZOffsetFormOpen,
    setZOffsetMaterial,
    setZOffsetNotes,
    setZOffsetNozzle,
    setZOffsetPlateName,
    setZOffsetValue,
    status,
    toggleWizardCheck,
    visibleCalibrationRecommendations,
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
                <span>{liveCompletedStepCount}/{calibrationSequencePreview.length} visíveis tratados</span>
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
                  const liveEvidence = calibrationLiveEvidenceLabel(step.test_key, operationStatus);
                  const rowStatus = liveEvidence ? "completed live-verified" : step.status;
                  return (
                    <li key={`${step.order}-${step.test_key}`} className={`calibration-sequence-row ${rowStatus}`}>
                      <span className="calibration-step-index">{step.order}</span>
                      <span className="calibration-step-phase">{formatCalibrationPhase(step.phase).replace(/^\d+\.\s*/, "")}</span>
                      <span className="calibration-step-main">
                        <strong>{step.title}</strong>
                        <small>{liveEvidence || `${formatExecutionMode(step.execution_mode)} · risco ${formatRiskLevel(step.risk_level)}`}</small>
                      </span>
                      <em>{hiddenReason ? "bloqueado" : liveEvidence ? "detectado" : formatCalibrationSequenceStatus(step.status)}</em>
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
