import { X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";
import type { CalibrationRunRecord } from "../../types";

type CalibrationResultModalProps = ScreenPropsFor<
  | "calibrationExecutionConsoleExcerpt"
  | "calibrationExecutionPidParameters"
  | "calibrationExecutionRowClass"
  | "calibrationExecutionRequiresSaveConfig"
  | "calibrationMaterial"
  | "calibrationNotes"
  | "calibrationNozzle"
  | "calibrationObservedValue"
  | "calibrationPlateName"
  | "calibrationResultExecutions"
  | "calibrationResultFormConfig"
  | "calibrationResultFormOpen"
  | "calibrationResultRuns"
  | "calibrationResultStatus"
  | "calibrationResultTest"
  | "createCalibrationRun"
  | "formatCalibrationExecutionStatus"
  | "formatCalibrationResult"
  | "loading"
  | "selectedPrinterId"
  | "setCalibrationMaterial"
  | "setCalibrationNotes"
  | "setCalibrationNozzle"
  | "setCalibrationObservedValue"
  | "setCalibrationPlateName"
  | "setCalibrationResultFormOpen"
  | "setCalibrationResultStatus"
  | "setCalibrationResultTestKey"
  | "summarizeCalibrationExecutionFinalState"
>;

export function CalibrationResultModal(props: CalibrationResultModalProps) {
  const {
    calibrationExecutionRowClass,
    calibrationExecutionConsoleExcerpt,
    calibrationExecutionPidParameters,
    calibrationExecutionRequiresSaveConfig,
    calibrationMaterial,
    calibrationNotes,
    calibrationNozzle,
    calibrationObservedValue,
    calibrationPlateName,
    calibrationResultExecutions,
    calibrationResultFormConfig,
    calibrationResultFormOpen,
    calibrationResultRuns,
    calibrationResultStatus,
    calibrationResultTest,
    createCalibrationRun,
    formatCalibrationExecutionStatus,
    formatCalibrationResult,
    loading,
    selectedPrinterId,
    setCalibrationMaterial,
    setCalibrationNotes,
    setCalibrationNozzle,
    setCalibrationObservedValue,
    setCalibrationPlateName,
    setCalibrationResultFormOpen,
    setCalibrationResultStatus,
    setCalibrationResultTestKey,
    summarizeCalibrationExecutionFinalState,
  } = props;

  if (!calibrationResultTest) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Resultados de ${calibrationResultTest.title}`}>
      <div className="modal-card test-modal-card">
        <div className="modal-header">
          <div>
            <h2>Resultados - {calibrationResultTest.title}</h2>
            <p>Histórico deste teste na impressora selecionada.</p>
          </div>
          <button type="button" className="icon-button" onClick={() => setCalibrationResultTestKey(null)} aria-label="Fechar resultado">
            <X size={18} />
          </button>
        </div>
        <div className="test-result-history">
          {calibrationResultExecutions.map((execution) => {
            const consoleExcerpt = calibrationExecutionConsoleExcerpt(execution);
            const pidParameters = calibrationExecutionPidParameters(execution);
            return (
              <div key={`execution-${execution.id}`} className={`test-history-row ${calibrationExecutionRowClass(execution.status)}`}>
                <strong>{formatCalibrationExecutionStatus(execution.status)}</strong>
                <span>
                  {execution.created_at} · {execution.sent_commands.length} comando(s)
                </span>
                {execution.message ? <small>{execution.message}</small> : null}
                <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
                {pidParameters ? (
                  <small>
                    PID: Kp {pidParameters.kp} · Ki {pidParameters.ki} · Kd {pidParameters.kd}
                  </small>
                ) : null}
                {calibrationExecutionRequiresSaveConfig(execution) ? (
                  <div className="calibration-save-config-note">
                    O Klipper calculou novos valores, mas ainda precisa de SAVE_CONFIG para gravar no printer.cfg e reiniciar o firmware.
                  </div>
                ) : null}
                {consoleExcerpt.length ? <pre className="calibration-console-excerpt">{consoleExcerpt.join("\n")}</pre> : null}
              </div>
            );
          })}
          {calibrationResultRuns.map((run) => (
            <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
              <strong>{formatCalibrationResult(run.result_status)}</strong>
              <span>
                {run.created_at} · {run.material || "-"} · {run.plate_name || "-"} · {run.nozzle || "-"}
              </span>
              {run.observed_value ? <small>Valor: {run.observed_value}</small> : null}
              {run.notes ? <small>{run.notes}</small> : null}
            </div>
          ))}
          {!calibrationResultExecutions.length && !calibrationResultRuns.length ? (
            <p className="muted">Ainda não há resultados para este teste.</p>
          ) : null}
        </div>
        {!calibrationResultFormOpen ? (
          <div className="modal-footer">
            <button type="button" className="secondary-button" onClick={() => setCalibrationResultTestKey(null)}>
              Fechar
            </button>
            <button type="button" className="primary-button" onClick={() => setCalibrationResultFormOpen(true)} disabled={!selectedPrinterId || loading}>
              Adicionar resultado
            </button>
          </div>
        ) : null}
        {calibrationResultFormOpen ? (
          <form className="test-result-form" onSubmit={(event) => void createCalibrationRun(event)}>
            {calibrationResultFormConfig ? <p className="muted">{calibrationResultFormConfig.summary}</p> : null}
            <select
              aria-label="Resultado do teste"
              value={calibrationResultStatus}
              onChange={(event) => setCalibrationResultStatus(event.target.value as CalibrationRunRecord["result_status"])}
            >
              <option value="passed">aprovado</option>
              <option value="warning">atenção</option>
              <option value="failed">falhou</option>
              <option value="skipped">ignorado</option>
            </select>
            {calibrationResultFormConfig?.showMaterial ? (
              <label>
                <span>Material</span>
                <input value={calibrationMaterial} onChange={(event) => setCalibrationMaterial(event.target.value)} placeholder="Ex.: PLA, ABS, ASA" />
              </label>
            ) : null}
            {calibrationResultFormConfig?.showPlate ? (
              <label>
                <span>Chapa</span>
                <input value={calibrationPlateName} onChange={(event) => setCalibrationPlateName(event.target.value)} placeholder="Ex.: Texturizada, lisa, PEI" />
              </label>
            ) : null}
            {calibrationResultFormConfig?.showNozzle ? (
              <label>
                <span>Toolhead/nozzle</span>
                <input value={calibrationNozzle} onChange={(event) => setCalibrationNozzle(event.target.value)} placeholder="Ex.: T0, T1, 0.4" />
              </label>
            ) : null}
            <label>
              <span>{calibrationResultFormConfig?.observedLabel ?? "Valor observado"}</span>
              <input
                value={calibrationObservedValue}
                onChange={(event) => setCalibrationObservedValue(event.target.value)}
                placeholder={calibrationResultFormConfig?.observedPlaceholder ?? "Resumo objetivo do resultado"}
              />
            </label>
            <label>
              <span>{calibrationResultFormConfig?.notesLabel ?? "Notas"}</span>
              <textarea
                value={calibrationNotes}
                onChange={(event) => setCalibrationNotes(event.target.value)}
                placeholder={calibrationResultFormConfig?.notesPlaceholder ?? "Detalhes úteis para repetir ou investigar depois"}
              />
            </label>
            <div className="modal-footer">
              <button type="button" className="secondary-button" onClick={() => setCalibrationResultFormOpen(false)}>
                Cancelar
              </button>
              <button type="submit" className="primary-button" disabled={!selectedPrinterId || loading}>
                Salvar resultado
              </button>
            </div>
          </form>
        ) : null}
      </div>
    </div>
  );
}
