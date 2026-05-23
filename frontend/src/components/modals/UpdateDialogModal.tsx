import React from "react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

export type UpdateDialogModalProps = ScreenPropsFor<
  | "RefreshCw"
  | "X"
  | "closeUpdateSocket"
  | "formatUpdatePhase"
  | "loadUpdateStatus"
  | "loading"
  | "runUpdate"
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
    closeUpdateSocket,
    formatUpdatePhase,
    loadUpdateStatus,
    loading,
    runUpdate,
    selectedPrinter,
    selectedPrinterId,
    setUpdateDialog,
    status,
    updateDialog,
    updateLogs,
    updatePhaseIcon,
  } = props;

  return (
    <>
        {updateDialog?.open ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Atualizar componente">
            <div className="modal-card update-modal-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <RefreshCw size={20} />
                    Atualizar {updateDialog.label}
                  </h2>
                  <p>
                    {selectedPrinter?.name ?? "Impressora"} · {selectedPrinter?.moonraker_url ?? "Moonraker não selecionado"}
                  </p>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => {
                    closeUpdateSocket();
                    setUpdateDialog(null);
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
                      <strong>Confirmação necessária</strong>
                      <span>operação mutável</span>
                    </div>
                    <p>O Moonraker pode reiniciar serviços durante o update. Não execute se houver impressão em andamento.</p>
                    <small>O Printora vai abrir o log ao vivo do Moonraker e atualizar o status ao final.</small>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="ghost-button" onClick={() => setUpdateDialog(null)}>
                      Cancelar
                    </button>
                    <button type="button" className="primary-button" onClick={() => void runUpdate(updateDialog.target)} disabled={loading}>
                      <RefreshCw size={16} />
                      Iniciar update
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
                      <RefreshCw size={16} />
                      Recarregar status
                    </button>
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => {
                        closeUpdateSocket();
                        setUpdateDialog(null);
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
