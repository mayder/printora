import React from "react";
import { Badge } from "../common";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

export type AlertCenterModalProps = ScreenPropsFor<
  | "AlertTriangle"
  | "Bell"
  | "CheckCircle2"
  | "RefreshCw"
  | "X"
  | "alertCenterIcon"
  | "alertCenterItems"
  | "alertCenterOpen"
  | "countPendingUpdates"
  | "handleAlertCenterAction"
  | "loading"
  | "setAlertCenterOpen"
  | "updateStatus"
>;

export function AlertCenterModal(props: AlertCenterModalProps) {
  const {
    AlertTriangle,
    Bell,
    CheckCircle2,
    RefreshCw,
    X,
    alertCenterIcon,
    alertCenterItems,
    alertCenterOpen,
    countPendingUpdates,
    handleAlertCenterAction,
    loading,
    setAlertCenterOpen,
    updateStatus,
  } = props;

  return (
    <>
        {alertCenterOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Central de alertas">
            <div className="modal-card alert-center-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <Bell size={20} />
                    Central de alertas
                  </h2>
                  <p>Frota · riscos, agentes, updates e avisos consolidados.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setAlertCenterOpen(false)}>
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <div className="overview-strip">
                <Badge icon={AlertTriangle} label="Bloqueios" value={alertCenterItems.filter((item: any) => item.severity === "blocker").length} />
                <Badge icon={AlertTriangle} label="Alertas" value={alertCenterItems.filter((item: any) => item.severity === "warning").length} />
                <Badge icon={RefreshCw} label="Updates" value={countPendingUpdates(updateStatus)} />
                <Badge icon={Bell} label="Total" value={alertCenterItems.length} />
              </div>
              <div className="alert-center-list">
                {alertCenterItems.length === 0 ? (
                  <div className="empty-state">
                    <CheckCircle2 size={22} />
                    <strong>Nenhum alerta ativo</strong>
                    <p className="muted">Não há bloqueios, riscos ou updates pendentes nos dados carregados da frota.</p>
                  </div>
                ) : null}
                {alertCenterItems.map((item: any) => (
                  <div key={item.id} className={`alert-center-row ${item.severity}`}>
                    <div className="alert-center-icon">
                      {React.createElement(alertCenterIcon(item.severity), { size: 17 })}
                    </div>
                    <div>
                      <div className="alert-center-row-header">
                        <div>
                          <strong>{item.title}</strong>
                          <span>{item.source}</span>
                        </div>
                        <button type="button" className="secondary-button compact" onClick={() => void handleAlertCenterAction(item)} disabled={loading}>
                          {item.actionLabel}
                        </button>
                      </div>
                      <dl className="alert-center-explain">
                        <div>
                          <dt>Por que aparece</dt>
                          <dd>{item.reason}</dd>
                        </div>
                        <div>
                          <dt>Evidência</dt>
                          <dd>{item.detail}</dd>
                        </div>
                        <div>
                          <dt>Como resolver</dt>
                          <dd>{item.action}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
    </>
  );
}
