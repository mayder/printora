import { Download, Save, Trash2, X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";
import type { CalibrationRunRecord } from "../../types";
import { calibrationExecutionConfigRemediationApplied, formatDateTime } from "../../utils/formatters";
import { ConfigRemediationPanel } from "./ConfigRemediationPanel";

type CalibrationResultModalProps = ScreenPropsFor<
  | "applyCalibrationConfigRemediation"
  | "calibrationConfigRemediationApplyResult"
  | "calibrationConfigRemediationBusy"
  | "calibrationConfigRemediationError"
  | "calibrationConfigRemediationPreview"
  | "calibrationConfigRemediationSelectedIds"
  | "calibrationExecutionConsoleExcerpt"
  | "calibrationExecutionPidParameters"
  | "calibrationExecutionRowClass"
  | "calibrationExecutionRequiresSaveConfig"
  | "calibrationSaveConfigBusy"
  | "calibrationSaveConfigError"
  | "calibrationSaveConfigExecutionId"
  | "calibrationSaveConfigResult"
  | "calibrationConfigRemediationExecutionId"
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
  | "deleteCalibrationExecutionHistoryItem"
  | "deleteCalibrationRunHistoryItem"
  | "downloadCalibrationExecutionHistoryItem"
  | "downloadCalibrationRunHistoryItem"
  | "formatCalibrationExecutionStatus"
  | "formatCalibrationResult"
  | "formatSaveConfigFailureMessage"
  | "latestCalibrationExecutionIdByTest"
  | "latestCalibrationRunIdByTest"
  | "loading"
  | "previewCalibrationConfigRemediation"
  | "saveCalibrationConfigFromExecution"
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
  | "toggleCalibrationConfigRemediationTarget"
>;

export function CalibrationResultModal(props: CalibrationResultModalProps) {
  const {
    calibrationExecutionRowClass,
    calibrationExecutionConsoleExcerpt,
    calibrationExecutionPidParameters,
    calibrationExecutionRequiresSaveConfig,
    calibrationSaveConfigBusy,
    calibrationSaveConfigError,
    calibrationSaveConfigExecutionId,
    calibrationSaveConfigResult,
    calibrationConfigRemediationExecutionId,
    applyCalibrationConfigRemediation,
    calibrationConfigRemediationApplyResult,
    calibrationConfigRemediationBusy,
    calibrationConfigRemediationError,
    calibrationConfigRemediationPreview,
    calibrationConfigRemediationSelectedIds,
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
    deleteCalibrationExecutionHistoryItem,
    deleteCalibrationRunHistoryItem,
    downloadCalibrationExecutionHistoryItem,
    downloadCalibrationRunHistoryItem,
    formatCalibrationExecutionStatus,
    formatCalibrationResult,
    formatSaveConfigFailureMessage,
    latestCalibrationExecutionIdByTest,
    latestCalibrationRunIdByTest,
    loading,
    previewCalibrationConfigRemediation,
    saveCalibrationConfigFromExecution,
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
    toggleCalibrationConfigRemediationTarget,
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
            const isLatestExecution = latestCalibrationExecutionIdByTest.get(execution.test_key) === execution.id;
            const canDeleteExecution = !isLatestExecution;
            const saveConfigRequired = execution.status === "executed" && calibrationExecutionRequiresSaveConfig(execution);
            const saveConfigMatchesExecution = calibrationSaveConfigExecutionId === execution.id;
            const remediationMatchesExecution = calibrationConfigRemediationExecutionId === execution.id;
            const remediationApplied =
              calibrationExecutionConfigRemediationApplied(execution) ||
              (remediationMatchesExecution && calibrationConfigRemediationApplyResult?.status === "applied");
            const saveConfigExecuted = saveConfigMatchesExecution && calibrationSaveConfigResult?.status === "executed";
            const saveConfigFailed =
              saveConfigMatchesExecution &&
              !remediationApplied &&
              (Boolean(calibrationSaveConfigError) || calibrationSaveConfigResult?.status === "failed");
            const matchingSaveConfigResult = saveConfigMatchesExecution ? calibrationSaveConfigResult : null;
            const matchingPreview = remediationMatchesExecution ? calibrationConfigRemediationPreview : null;
            const matchingApplyResult = remediationMatchesExecution ? calibrationConfigRemediationApplyResult : null;
            const showRemediationPanel = pidParameters && (saveConfigFailed || Boolean(matchingPreview) || Boolean(matchingApplyResult));
            return (
              <div key={`execution-${execution.id}`} className={`test-history-row ${calibrationExecutionRowClass(execution.status)}`}>
                <div className="test-history-row-heading">
                  <strong>{formatCalibrationExecutionStatus(execution.status)}</strong>
                  <div className="test-history-actions">
                    {saveConfigRequired ? (
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => void saveCalibrationConfigFromExecution({ execution })}
                        disabled={!selectedPrinterId || loading || calibrationSaveConfigBusy || saveConfigExecuted || remediationApplied}
                        title="Salvar config"
                        aria-label="Salvar config"
                      >
                        <Save size={15} />
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => downloadCalibrationExecutionHistoryItem(execution)}
                      title="Baixar JSON"
                      aria-label="Baixar execução em JSON"
                    >
                      <Download size={15} />
                    </button>
                    {canDeleteExecution ? (
                      <button
                        type="button"
                        className="icon-button danger-inline"
                        onClick={() => void deleteCalibrationExecutionHistoryItem(execution)}
                        disabled={loading}
                        title="Apagar"
                        aria-label="Apagar execução"
                      >
                        <Trash2 size={15} />
                      </button>
                    ) : null}
                  </div>
                </div>
                <span>
                  {formatDateTime(execution.created_at)} · {execution.sent_commands.length} comando(s)
                </span>
                {execution.message ? <small>{execution.message}</small> : null}
                <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
                {pidParameters ? (
                  <small>
                    PID: Kp {pidParameters.kp} · Ki {pidParameters.ki} · Kd {pidParameters.kd}
                  </small>
                ) : null}
                {calibrationExecutionRequiresSaveConfig(execution) && !remediationApplied ? (
                  <div className="calibration-save-config-note">
                    <span>O Klipper calculou novos valores, mas ainda precisa de SAVE_CONFIG para gravar no printer.cfg e reiniciar o firmware.</span>
                    {saveConfigRequired ? (
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => void saveCalibrationConfigFromExecution({ execution })}
                        disabled={!selectedPrinterId || loading || calibrationSaveConfigBusy || saveConfigExecuted || remediationApplied}
                      >
                        {calibrationSaveConfigBusy ? "Salvando" : saveConfigExecuted ? "Config salva" : "Salvar config"}
                      </button>
                    ) : null}
                  </div>
                ) : null}
                {remediationApplied ? (
                  <small>Config aplicada no arquivo incluído com backup; o erro original do SAVE_CONFIG já foi tratado.</small>
                ) : null}
                {saveConfigRequired && matchingSaveConfigResult && !remediationApplied ? (
                  <small>
                    SAVE_CONFIG: {matchingSaveConfigResult.status}
                    {matchingSaveConfigResult.block_reason ? ` · ${matchingSaveConfigResult.block_reason}` : ""}
                  </small>
                ) : null}
                {saveConfigFailed ? (
                  <small className="calibration-save-config-error">{formatSaveConfigFailureMessage(matchingSaveConfigResult, calibrationSaveConfigError)}</small>
                ) : null}
                {showRemediationPanel ? (
                  <ConfigRemediationPanel
                    busy={calibrationConfigRemediationBusy}
                    error={calibrationConfigRemediationError}
                    preview={matchingPreview}
                    applyResult={matchingApplyResult}
                    selectedIds={calibrationConfigRemediationSelectedIds}
                    onPreview={() => void previewCalibrationConfigRemediation(execution)}
                    onApply={() => void applyCalibrationConfigRemediation({ execution })}
                    onToggle={toggleCalibrationConfigRemediationTarget}
                  />
                ) : null}
                {consoleExcerpt.length ? <pre className="calibration-console-excerpt">{consoleExcerpt.join("\n")}</pre> : null}
              </div>
            );
          })}
          {calibrationResultRuns.map((run) => {
            const isLatestRun = latestCalibrationRunIdByTest.get(run.test_key) === run.id;
            return (
              <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
                <div className="test-history-row-heading">
                  <strong>{formatCalibrationResult(run.result_status)}</strong>
                  <div className="test-history-actions">
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => downloadCalibrationRunHistoryItem(run)}
                      title="Baixar JSON"
                      aria-label="Baixar resultado em JSON"
                    >
                      <Download size={15} />
                    </button>
                    {!isLatestRun ? (
                      <button
                        type="button"
                        className="icon-button danger-inline"
                        onClick={() => void deleteCalibrationRunHistoryItem(run)}
                        disabled={loading}
                        title="Apagar"
                        aria-label="Apagar resultado"
                      >
                        <Trash2 size={15} />
                      </button>
                    ) : null}
                  </div>
                </div>
                <span>
                  {formatDateTime(run.created_at)} · {run.material || "-"} · {run.plate_name || "-"} · {run.nozzle || "-"}
                </span>
                {run.observed_value ? <small>Valor: {run.observed_value}</small> : null}
                {run.notes ? <small>{run.notes}</small> : null}
              </div>
            );
          })}
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
