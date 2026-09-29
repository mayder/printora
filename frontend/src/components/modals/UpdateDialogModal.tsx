import React from "react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

export type UpdateDialogModalProps = ScreenPropsFor<
  | "RefreshCw"
  | "X"
  | "authUser"
  | "closeUpdateDialog"
  | "formatUpdatePhase"
  | "loadUpdateStatus"
  | "loading"
  | "patchUpdateDialog"
  | "runUpdate"
  | "runRollback"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setUpdateDialog"
  | "status"
  | "updateDialog"
  | "updateLogs"
  | "updatePhaseIcon"
>;

export function UpdateDialogModal(props: UpdateDialogModalProps) {
  const {
    RefreshCw,
    X,
    authUser,
    closeUpdateDialog,
    formatUpdatePhase,
    loadUpdateStatus,
    loading,
    patchUpdateDialog,
    runUpdate,
    runRollback,
    selectedPrinter,
    selectedPrinterId,
    setUpdateDialog,
    status,
    updateDialog,
    updateLogs,
    updatePhaseIcon,
  } = props;
  const usesMfa = Boolean(authUser?.mfa_enabled);

  return (
    <>
        {updateDialog?.open ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Atualizar componente">
            <div className="modal-card update-modal-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <RefreshCw size={20} />
                    {updateDialog.action === "rollback" ? "Rollback" : "Atualizar"} {updateDialog.label}
                  </h2>
                  <p>{selectedPrinter?.name ?? "Impressora"}</p>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => {
                    void closeUpdateDialog();
                  }}
                  disabled={updateDialog.phase === "running"}
                >
                  <X size={16} />
                  Fechar
                </button>
              </div>

              {updateDialog.phase === "confirm" ? (
                <div className="update-confirm-box">
                  <div className="finding monitorar">
                    <div>
                      <strong>{updateDialog.requiresConfirmation ? "Confirmação crítica necessária" : "Confirmação necessária"}</strong>
                      <span>{updateDialog.action === "rollback" ? "rollback mutável" : "operação mutável"}</span>
                    </div>
                    <p>
                      {updateDialog.action === "rollback"
                        ? "O Moonraker vai tentar voltar este componente para a versão anterior registrada. Não execute se houver impressão em andamento."
                        : "O Moonraker pode reiniciar serviços durante o update. Não execute se houver impressão em andamento."}
                    </p>
                    {updateDialog.riskReason ? <small>{updateDialog.riskReason}</small> : null}
                    <small>O Printora acompanhará o status pelo agente e confirmará o resultado ao final.</small>
                  </div>
                  {updateDialog.requiresConfirmation ? (
                    <label className="confirmation-field">
                      <span>
                        Digite <strong>{updateDialog.action === "rollback" ? "ROLLBACK UPDATE" : "ATUALIZAR COM RISCO"}</strong>
                      </span>
                      <input
                        value={updateDialog.confirmationPhrase}
                        onChange={(event) => patchUpdateDialog({ confirmationPhrase: event.target.value })}
                        disabled={loading}
                      />
                    </label>
                  ) : null}
                  {authUser ? (
                    <div className="auth-stack">
                      <p>
                        <strong>Autorize esta operação.</strong>{" "}
                        Informe {usesMfa ? "um código 2FA novo" : "a senha atual da sua conta"}.
                        A autorização é de uso único.
                      </p>
                      <label>
                        <span>{usesMfa ? "Código 2FA" : "Senha atual da conta"}</span>
                        <input
                          value={updateDialog.authorizationCredential}
                          onChange={(event) =>
                            patchUpdateDialog({ authorizationCredential: event.target.value, authorizationError: null })
                          }
                          type={usesMfa ? "text" : "password"}
                          inputMode={usesMfa ? "numeric" : undefined}
                          autoComplete={usesMfa ? "one-time-code" : "current-password"}
                          disabled={loading}
                        />
                      </label>
                      {updateDialog.authorizationError ? (
                        <p className="form-error" role="alert">{updateDialog.authorizationError}</p>
                      ) : null}
                    </div>
                  ) : null}
                  <div className="modal-footer">
                    <button type="button" className="ghost-button" onClick={() => setUpdateDialog(null)}>
                      Cancelar
                    </button>
                    <button
                      type="button"
                      className={updateDialog.action === "rollback" ? "danger-button" : "primary-button"}
                      onClick={() => {
                        if (updateDialog.action === "rollback") {
                          void runRollback(updateDialog.target);
                          return;
                        }
                        void runUpdate(updateDialog.target);
                      }}
                      disabled={
                        loading ||
                        (updateDialog.requiresConfirmation &&
                          updateDialog.confirmationPhrase.trim() !==
                            (updateDialog.action === "rollback" ? "ROLLBACK UPDATE" : "ATUALIZAR COM RISCO"))
                      }
                    >
                      <RefreshCw className={loading ? "button-busy-icon" : undefined} size={16} />
                      {updateDialog.action === "rollback" ? "Iniciar rollback" : "Iniciar update"}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className={`update-progress-status ${updateDialog.phase}`}>
                    {React.createElement(updatePhaseIcon(updateDialog.phase), { size: 18 })}
                    <strong>{formatUpdatePhase(updateDialog.phase)}</strong>
                  </div>
                  <div className="update-log-list" aria-live="polite">
                    {updateLogs.length === 0 ? <p className="muted">Aguardando mensagens do Moonraker...</p> : null}
                    {updateLogs.map((log: any) => (
                      <div key={log.id} className={`update-log-row ${log.level}`}>
                        <time>{log.time}</time>
                        <span>{log.message}</span>
                      </div>
                    ))}
                  </div>
                  <div className="modal-footer">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        if (selectedPrinterId) {
                          void loadUpdateStatus(selectedPrinterId);
                        }
                      }}
                      disabled={!selectedPrinterId || loading}
                    >
                      <RefreshCw className={loading ? "button-busy-icon" : undefined} size={16} />
                      Recarregar status
                    </button>
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => {
                        void closeUpdateDialog();
                      }}
                      disabled={updateDialog.phase === "running"}
                    >
                      <X size={16} />
                      Fechar
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        ) : null}
    </>
  );
}
