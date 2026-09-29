import { Metric } from "../common";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

export type SelfUpdateModalProps = ScreenPropsFor<
  | "ShieldAlert"
  | "ShieldCheck"
  | "Undo2"
  | "X"
  | "applySelfUpdate"
  | "canRollbackSelfUpdateRun"
  | "formatSelfUpdateEnvironment"
  | "formatSelfUpdateStatus"
  | "formatSelfUpdateStepStatus"
  | "rollbackSelfUpdate"
  | "selfUpdateApplying"
  | "selfUpdateCompletedStepCount"
  | "selfUpdateConfirmation"
  | "selfUpdateConnectionLost"
  | "selfUpdateMessage"
  | "selfUpdateModalOpen"
  | "selfUpdatePlan"
  | "selfUpdateProgressPercent"
  | "selfUpdateRollbackConfirmation"
  | "selfUpdateRollingBack"
  | "selfUpdateStepClass"
  | "selfUpdateStepDetail"
  | "setSelfUpdateConfirmation"
  | "setSelfUpdateModalOpen"
  | "setSelfUpdateRollbackConfirmation"
  | "status"
  | "systemReleases"
  | "visibleSelfUpdateSteps"
>;

export function SelfUpdateModal(props: SelfUpdateModalProps) {
  const {
    ShieldAlert,
    ShieldCheck,
    Undo2,
    X,
    applySelfUpdate,
    canRollbackSelfUpdateRun,
    formatSelfUpdateEnvironment,
    formatSelfUpdateStatus,
    formatSelfUpdateStepStatus,
    rollbackSelfUpdate,
    selfUpdateApplying,
    selfUpdateCompletedStepCount,
    selfUpdateConfirmation,
    selfUpdateConnectionLost,
    selfUpdateMessage,
    selfUpdateModalOpen,
    selfUpdatePlan,
    selfUpdateProgressPercent,
    selfUpdateRollbackConfirmation,
    selfUpdateRollingBack,
    selfUpdateStepClass,
    selfUpdateStepDetail,
    setSelfUpdateConfirmation,
    setSelfUpdateModalOpen,
    setSelfUpdateRollbackConfirmation,
    status,
    systemReleases,
    visibleSelfUpdateSteps,
  } = props;

  return (
    <>
        {selfUpdateModalOpen && selfUpdatePlan ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Update do Printora">
            <div className="modal-card self-update-modal-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <ShieldCheck size={20} />
                    Update do Printora
                  </h2>
                  <p>
                    {systemReleases?.installed_version ?? "-"} → {selfUpdatePlan.run.target_tag} ·{" "}
                    {formatSelfUpdateEnvironment(selfUpdatePlan.run.environment)}
                  </p>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setSelfUpdateModalOpen(false)}
                  disabled={selfUpdateApplying || selfUpdateRollingBack}
                >
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <div className="self-update-summary">
                <Metric label="Versão instalada" value={systemReleases?.installed_version ?? "-"} />
                <Metric label="Versão alvo" value={selfUpdatePlan.run.target_tag} />
                <Metric label="Ambiente" value={formatSelfUpdateEnvironment(selfUpdatePlan.run.environment)} />
                <Metric label="Status" value={formatSelfUpdateStatus(selfUpdatePlan.run.status)} />
              </div>
              {selfUpdatePlan.update_supported ? (
                <div className="action-result warning">
                  <strong>Atenção</strong>
                  <span>O Printora pode reiniciar durante o update. Se a conexão cair, aguarde e recarregue a página.</span>
                </div>
              ) : (
                <div className="action-result warning">
                  <strong>Ambiente sem apply automático</strong>
                  <span>A atualização automática ainda não está habilitada nesta instalação.</span>
                </div>
              )}
              {selfUpdateConnectionLost ? (
                <div className="action-result warning">
                  <strong>O Printora pode estar reiniciando</strong>
                  <span>Aguarde e recarregue.</span>
                </div>
              ) : null}
              {selfUpdateMessage ? (
                <div className="action-result">
                  <strong>Status</strong>
                  <span>{selfUpdateMessage}</span>
                </div>
              ) : null}
              <div className="self-update-backups">
                <strong>Proteção antes da atualização</strong>
                <span>Os dados e a versão anterior serão preservados para recuperação.</span>
              </div>
              {selfUpdatePlan.run.status !== "planned" && (
                <>
                  <div className={`self-update-progress ${selfUpdatePlan.run.status === "running" ? "active" : ""}`}>
                    <div><strong>Linha do tempo</strong><span>{selfUpdateCompletedStepCount(selfUpdatePlan.run)} de {selfUpdatePlan.run.steps.length} etapas concluídas</span></div>
                    <div className="self-update-progress-track"><span style={{ width: `${selfUpdateProgressPercent(selfUpdatePlan.run)}%` }} /></div>
                  </div>
                  <div className="update-log-list self-update-log-list" aria-live="polite">
                    {visibleSelfUpdateSteps(selfUpdatePlan.run).map((step: any) => (
                      <div key={step.id} className={`update-log-row ${selfUpdateStepClass(step.status)}`}>
                        <time>{formatSelfUpdateStepStatus(step.status)}</time>
                        <span><strong>{step.title}</strong><small>{selfUpdateStepDetail(step)}</small></span>
                      </div>
                    ))}
                  </div>
                </>
              )}
              {selfUpdatePlan.update_supported && selfUpdatePlan.run.status === "planned" ? (
                <div className="self-update-confirm">
                  <label>
                    Confirmação
                    <input
                      value={selfUpdateConfirmation}
                      onChange={(event: any) => setSelfUpdateConfirmation(event.target.value)}
                      placeholder="ATUALIZAR PRINTORA"
                    />
                  </label>
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => void applySelfUpdate()}
                    disabled={selfUpdateApplying || selfUpdateConfirmation !== "ATUALIZAR PRINTORA"}
                  >
                    <ShieldAlert size={16} />
                    Aplicar update
                  </button>
                </div>
              ) : null}
              {canRollbackSelfUpdateRun(selfUpdatePlan.run) ? (
                <div className="self-update-confirm">
                  <label>
                    Confirmação de rollback
                    <input
                      value={selfUpdateRollbackConfirmation}
                      onChange={(event: any) => setSelfUpdateRollbackConfirmation(event.target.value)}
                      placeholder="ROLLBACK PRINTORA"
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void rollbackSelfUpdate(selfUpdatePlan.run.id)}
                    disabled={selfUpdateRollingBack || selfUpdateRollbackConfirmation !== "ROLLBACK PRINTORA"}
                  >
                    <Undo2 size={16} />
                    Aplicar rollback
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
    </>
  );
}
