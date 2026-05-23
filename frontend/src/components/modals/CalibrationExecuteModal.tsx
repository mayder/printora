import { X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

type CalibrationExecuteModalProps = ScreenPropsFor<
  | "buildCalibrationExecutionNotes"
  | "calibrationExecuteTest"
  | "calibrationExecutionResult"
  | "calibrationExecutionRowClass"
  | "calibrationGcodeReviewed"
  | "calibrationOperatorPresent"
  | "calibrationPreflight"
  | "executeCalibrationGcode"
  | "formatCalibrationExecutionResult"
  | "formatCalibrationExecutionStatus"
  | "loading"
  | "openCalibrationResult"
  | "selectedPrinterId"
  | "setCalibrationExecuteTestKey"
  | "setCalibrationExecutionConfirmation"
  | "setCalibrationGcodeReviewed"
  | "setCalibrationNotes"
  | "setCalibrationObservedValue"
  | "setCalibrationOperatorPresent"
  | "summarizeCalibrationExecutionFinalState"
>;

export function CalibrationExecuteModal(props: CalibrationExecuteModalProps) {
  const {
    buildCalibrationExecutionNotes,
    calibrationExecuteTest,
    calibrationExecutionResult,
    calibrationExecutionRowClass,
    calibrationGcodeReviewed,
    calibrationOperatorPresent,
    calibrationPreflight,
    executeCalibrationGcode,
    formatCalibrationExecutionResult,
    formatCalibrationExecutionStatus,
    loading,
    openCalibrationResult,
    selectedPrinterId,
    setCalibrationExecuteTestKey,
    setCalibrationExecutionConfirmation,
    setCalibrationGcodeReviewed,
    setCalibrationNotes,
    setCalibrationObservedValue,
    setCalibrationOperatorPresent,
    summarizeCalibrationExecutionFinalState,
  } = props;

  if (!calibrationExecuteTest) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Executar ${calibrationExecuteTest.title}`}>
      <div className="modal-card test-modal-card">
        <div className="modal-header">
          <div>
            <h2>{calibrationExecuteTest.title}</h2>
            <p>{calibrationPreflight?.summary ?? "Preflight será validado antes do envio."}</p>
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
            {calibrationPreflight.block_reasons.map((reason) => (
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
              onChange={(event) => setCalibrationGcodeReviewed(event.target.checked)}
            />
            Revisei o G-code
          </label>
          <label className="inline-check">
            <input
              type="checkbox"
              checked={calibrationOperatorPresent}
              onChange={(event) => setCalibrationOperatorPresent(event.target.checked)}
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
  );
}
