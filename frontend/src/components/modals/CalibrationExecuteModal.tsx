import { LoaderCircle, X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

type CalibrationExecuteModalProps = ScreenPropsFor<
  | "buildCalibrationExecutionNotes"
  | "calibrationExecutionConsoleExcerpt"
  | "calibrationExecutionPidParameters"
  | "calibrationExecuteTest"
  | "calibrationExecutionBusy"
  | "calibrationExecutionResult"
  | "calibrationExecutionRowClass"
  | "calibrationExecutionRequiresSaveConfig"
  | "calibrationGcodeReviewed"
  | "calibrationOperatorPresent"
  | "calibrationPreflight"
  | "executeCalibrationGcode"
  | "formatCalibrationExecutionResult"
  | "formatCalibrationExecutionStatus"
  | "loading"
  | "openCalibrationResult"
  | "operationStatus"
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
    calibrationExecutionConsoleExcerpt,
    calibrationExecutionPidParameters,
    calibrationExecuteTest,
    calibrationExecutionBusy,
    calibrationExecutionResult,
    calibrationExecutionRowClass,
    calibrationExecutionRequiresSaveConfig,
    calibrationGcodeReviewed,
    calibrationOperatorPresent,
    calibrationPreflight,
    executeCalibrationGcode,
    formatCalibrationExecutionResult,
    formatCalibrationExecutionStatus,
    loading,
    openCalibrationResult,
    operationStatus,
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
  const liveHotend = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const liveBed = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const liveProgressRows = [
    ["Print state", operationStatus?.miscellaneous?.print_state ?? "-"],
    ["Hotend", formatLiveTemperature(liveHotend?.temperature, liveHotend?.target)],
    ["Mesa", formatLiveTemperature(liveBed?.temperature, liveBed?.target)],
    ["Home", String(operationStatus?.toolhead?.homed_axes ?? "-")],
    ["Posição", formatLivePosition(operationStatus?.toolhead?.position)],
  ];
  const resultConsoleExcerpt = calibrationExecutionResult ? calibrationExecutionConsoleExcerpt(calibrationExecutionResult) : [];
  const resultPidParameters = calibrationExecutionResult ? calibrationExecutionPidParameters(calibrationExecutionResult) : null;

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
        {calibrationExecutionBusy || operationStatus ? (
          <div className={`calibration-live-progress ${calibrationExecutionBusy ? "running" : ""}`}>
            <div>
              <strong>{calibrationExecutionBusy ? "Executando comando" : "Status ao vivo"}</strong>
              <span>{operationStatus?.connected ? "Leitura Moonraker/Printora ativa" : "Aguardando leitura ao vivo"}</span>
            </div>
            {calibrationExecutionBusy ? (
              <span className="calibration-live-running">
                <LoaderCircle size={15} />
                acompanhando a impressora
              </span>
            ) : null}
            <dl>
              {liveProgressRows.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null}
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
            {calibrationExecutionResult.block_reasons.length ? (
              <ul className="test-blockers">
                {calibrationExecutionResult.block_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
            <small>{summarizeCalibrationExecutionFinalState(calibrationExecutionResult)}</small>
            {resultPidParameters ? (
              <small>
                PID: Kp {resultPidParameters.kp} · Ki {resultPidParameters.ki} · Kd {resultPidParameters.kd}
              </small>
            ) : null}
            {calibrationExecutionRequiresSaveConfig(calibrationExecutionResult) ? (
              <div className="calibration-save-config-note">
                Valores calculados. Para aplicar no printer.cfg, execute SAVE_CONFIG pelo Mainsail ou pela ação Salvar config em Operação. O Klipper será reiniciado.
              </div>
            ) : null}
            {resultConsoleExcerpt.length ? <pre className="calibration-console-excerpt">{resultConsoleExcerpt.join("\n")}</pre> : null}
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
          {calibrationExecutionResult?.status === "executed" || calibrationExecutionResult?.status === "dispatched_unconfirmed" ? (
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
            disabled={!selectedPrinterId || loading || calibrationExecutionBusy || !calibrationGcodeReviewed || !calibrationOperatorPresent || !calibrationPreflight || calibrationPreflight.blocked}
          >
            {calibrationExecutionBusy ? "Executando" : "Executar agora"}
          </button>
        </div>
      </div>
    </div>
  );
}

function formatLiveTemperature(current: unknown, target: unknown) {
  const currentLabel = typeof current === "number" ? `${Number(current.toFixed(1))} °C` : "-";
  const targetLabel = typeof target === "number" ? `${Number(target.toFixed(1))} °C` : "-";
  return `${currentLabel} / ${targetLabel}`;
}

function formatLivePosition(value: unknown) {
  if (!Array.isArray(value)) {
    return "-";
  }
  return value
    .slice(0, 3)
    .map((axis) => (typeof axis === "number" ? Number(axis.toFixed(2)) : axis))
    .join(" / ");
}
