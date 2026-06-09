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
  | "calibrationLiveConsole"
  | "calibrationLiveConsoleError"
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
    calibrationLiveConsole,
    calibrationLiveConsoleError,
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
  const visibleConsole = calibrationLiveConsole.length ? calibrationLiveConsole : resultConsoleExcerpt;
  const resultPidParameters = calibrationExecutionResult ? calibrationExecutionPidParameters(calibrationExecutionResult) : null;
  const livePidParameters = resultPidParameters ?? extractPidParametersFromConsole(visibleConsole);
  const executionCompleted = calibrationExecutionResult?.status === "executed";
  const executionRunning = calibrationExecutionResult?.status === "dispatched_unconfirmed";
  const saveConfigRequired = calibrationExecutionResult ? calibrationExecutionRequiresSaveConfig(calibrationExecutionResult) : false;
  const liveSaveConfigRequired = visibleConsole.join("\n").toUpperCase().includes("SAVE_CONFIG");
  const effectiveSaveConfigRequired = saveConfigRequired || liveSaveConfigRequired;
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
        {calibrationExecutionBusy || executionRunning || operationStatus ? (
          <div className={`calibration-live-progress ${calibrationExecutionBusy || executionRunning ? "running" : ""}`}>
            <div>
              <strong>{calibrationExecutionBusy || executionRunning ? "Acompanhando comando" : "Status ao vivo"}</strong>
              <span>{operationStatus?.connected ? "Leitura Moonraker/Printora ativa" : "Aguardando leitura ao vivo"}</span>
            </div>
            {calibrationExecutionBusy || executionRunning ? (
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
            {livePidParameters ? (
              <small>
                PID: Kp {livePidParameters.kp} · Ki {livePidParameters.ki} · Kd {livePidParameters.kd}
              </small>
            ) : null}
            {effectiveSaveConfigRequired ? (
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
            {effectiveSaveConfigRequired && (calibrationSaveConfigError || calibrationSaveConfigResult?.status === "failed") && livePidParameters ? (
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
            {executionRunning || visibleConsole.length ? (
              <div className="calibration-live-console-panel">
                <div>
                  <strong>{executionRunning ? "Console ao vivo do Printora" : "Console registrado"}</strong>
                  <span>
                    {executionRunning
                      ? "Atualiza automaticamente enquanto a impressora termina o comando."
                      : "Trecho salvo com o resultado da execução."}
                  </span>
                </div>
                {calibrationLiveConsoleError ? <small className="calibration-save-config-error">{calibrationLiveConsoleError}</small> : null}
                <pre className="calibration-console-excerpt">
                  {visibleConsole.length ? visibleConsole.join("\n") : "Aguardando novas linhas do console..."}
                </pre>
              </div>
            ) : null}
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
              executionRunning ||
              executionCompleted ||
              !calibrationGcodeReviewed ||
              !calibrationOperatorPresent ||
              !calibrationPreflight ||
              calibrationPreflight.blocked
            }
          >
            {calibrationExecutionBusy ? "Executando" : executionRunning ? "Acompanhando" : executionCompleted ? "Executado" : "Executar agora"}
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

function extractPidParametersFromConsole(lines: string[]) {
  const match = lines
    .join("\n")
    .match(/pid_Kp=(?<kp>[0-9.]+)\s+pid_Ki=(?<ki>[0-9.]+)\s+pid_Kd=(?<kd>[0-9.]+)/);
  if (!match?.groups) {
    return null;
  }
  return {
    kp: Number(match.groups.kp),
    ki: Number(match.groups.ki),
    kd: Number(match.groups.kd),
  };
}
