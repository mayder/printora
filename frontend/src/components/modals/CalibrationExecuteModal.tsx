import { LoaderCircle, X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";
import { ConfigRemediationPanel } from "./ConfigRemediationPanel";

type CalibrationExecuteModalProps = ScreenPropsFor<
  | "applyCalibrationConfigRemediation"
  | "buildCalibrationExecutionNotes"
  | "calibrationConfigRemediationApplyResult"
  | "calibrationConfigRemediationBusy"
  | "calibrationConfigRemediationError"
  | "calibrationConfigRemediationPreview"
  | "calibrationConfigRemediationSelectedIds"
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
  | "calibrationSaveConfigBusy"
  | "calibrationSaveConfigError"
  | "calibrationSaveConfigResult"
  | "executeCalibrationGcode"
  | "formatCalibrationExecutionResult"
  | "formatCalibrationExecutionStatus"
  | "formatSaveConfigFailureMessage"
  | "loading"
  | "openCalibrationResult"
  | "operationStatus"
  | "previewCalibrationConfigRemediation"
  | "selectedPrinterId"
  | "saveCalibrationConfigFromExecution"
  | "setCalibrationExecuteTestKey"
  | "setCalibrationExecutionConfirmation"
  | "setCalibrationGcodeReviewed"
  | "setCalibrationNotes"
  | "setCalibrationObservedValue"
  | "setCalibrationOperatorPresent"
  | "summarizeCalibrationExecutionFinalState"
  | "toggleCalibrationConfigRemediationTarget"
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
    calibrationSaveConfigBusy,
    calibrationSaveConfigError,
    calibrationSaveConfigResult,
    applyCalibrationConfigRemediation,
    calibrationConfigRemediationApplyResult,
    calibrationConfigRemediationBusy,
    calibrationConfigRemediationError,
    calibrationConfigRemediationPreview,
    calibrationConfigRemediationSelectedIds,
    executeCalibrationGcode,
    formatCalibrationExecutionResult,
    formatCalibrationExecutionStatus,
    formatSaveConfigFailureMessage,
    loading,
    openCalibrationResult,
    operationStatus,
    previewCalibrationConfigRemediation,
    selectedPrinterId,
    saveCalibrationConfigFromExecution,
    setCalibrationExecuteTestKey,
    setCalibrationExecutionConfirmation,
    setCalibrationGcodeReviewed,
    setCalibrationNotes,
    setCalibrationObservedValue,
    setCalibrationOperatorPresent,
    summarizeCalibrationExecutionFinalState,
    toggleCalibrationConfigRemediationTarget,
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
  const executionCompleted = calibrationExecutionResult?.status === "executed";
  const saveConfigRequired = calibrationExecutionResult ? calibrationExecutionRequiresSaveConfig(calibrationExecutionResult) : false;
  const saveConfigExecuted = calibrationSaveConfigResult?.status === "executed";

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
            {saveConfigRequired ? (
              <div className="calibration-save-config-note">
                <span>Valores calculados. Para aplicar no printer.cfg, execute SAVE_CONFIG. O Klipper será reiniciado.</span>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void saveCalibrationConfigFromExecution()}
                  disabled={!selectedPrinterId || loading || calibrationSaveConfigBusy || saveConfigExecuted}
                >
                  {calibrationSaveConfigBusy ? "Salvando" : saveConfigExecuted ? "Config salva" : "Salvar config"}
                </button>
              </div>
            ) : null}
            {calibrationSaveConfigResult ? (
              <small>
                SAVE_CONFIG: {calibrationSaveConfigResult.status}
                {calibrationSaveConfigResult.block_reason ? ` · ${calibrationSaveConfigResult.block_reason}` : ""}
              </small>
            ) : null}
            {calibrationSaveConfigError || calibrationSaveConfigResult?.status === "failed" ? (
              <small className="calibration-save-config-error">{formatSaveConfigFailureMessage(calibrationSaveConfigResult, calibrationSaveConfigError)}</small>
            ) : null}
            {saveConfigRequired && (calibrationSaveConfigError || calibrationSaveConfigResult?.status === "failed") && resultPidParameters ? (
              <ConfigRemediationPanel
                busy={calibrationConfigRemediationBusy}
                error={calibrationConfigRemediationError}
                preview={calibrationConfigRemediationPreview}
                applyResult={calibrationConfigRemediationApplyResult}
                selectedIds={calibrationConfigRemediationSelectedIds}
                onPreview={() => void previewCalibrationConfigRemediation()}
                onApply={() => void applyCalibrationConfigRemediation()}
                onToggle={toggleCalibrationConfigRemediationTarget}
              />
            ) : null}
            {resultConsoleExcerpt.length ? <pre className="calibration-console-excerpt">{resultConsoleExcerpt.join("\n")}</pre> : null}
            <details>
              <summary>JSON técnico</summary>
              <pre>{formatCalibrationExecutionResult(calibrationExecutionResult)}</pre>
            </details>
          </div>
        ) : null}
        <div className="modal-footer">
          <button type="button" className="secondary-button" onClick={() => setCalibrationExecuteTestKey(null)}>
            Cancelar
          </button>
          {executionCompleted ? (
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
            disabled={
              !selectedPrinterId ||
              loading ||
              calibrationExecutionBusy ||
              executionCompleted ||
              !calibrationGcodeReviewed ||
              !calibrationOperatorPresent ||
              !calibrationPreflight ||
              calibrationPreflight.blocked
            }
          >
            {calibrationExecutionBusy ? "Executando" : executionCompleted ? "Executado" : "Executar agora"}
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
