import React from "react";
import { Badge } from "../components/common";
import type { UpdateComponent } from "../alertCenter";
import type { ScreenPropsFor } from "./ScreenProps";

type UpdatesScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "Gauge"
  | "RefreshCw"
  | "checklist"
  | "checklistDotClass"
  | "formatChecklistDataState"
  | "formatUpdateStatus"
  | "loading"
  | "openRollbackDialog"
  | "openUpdateDialog"
  | "refreshUpdateStatus"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "status"
  | "updateActionResult"
  | "updateStatus"
  | "updateStatusIcon"
>;

export function UpdatesScreen(props: UpdatesScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    Gauge,
    RefreshCw,
    checklist,
    checklistDotClass,
    formatChecklistDataState,
    formatUpdateStatus,
    loading,
    openRollbackDialog,
    openUpdateDialog,
    refreshUpdateStatus,
    selectedPrinter,
    selectedPrinterId,
    status,
    updateActionResult,
    updateStatus,
    updateStatusIcon,
  } = props;
  const pendingUpdateCount = updateStatus?.components.filter(isPendingUpdateComponent).length ?? 0;
  const riskyPendingCount = updateStatus?.components.filter((component) => component.can_update && component.requires_confirmation).length ?? 0;
  const orderedComponents = orderUpdateComponents(updateStatus?.components ?? []);

  return (
    <>
        <article className="panel wide panel-section panel-updates">
          <div className="panel-heading">
            <div>
              <h2>Atualizações</h2>
              <p className="muted">Componentes do Update Manager para {selectedPrinter?.name ?? "a impressora selecionada"}.</p>
            </div>
            <div className="panel-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => void refreshUpdateStatus()}
                disabled={!selectedPrinterId || loading || updateStatus?.busy}
              >
                <RefreshCw size={15} />
                Reanalisar
              </button>
              {pendingUpdateCount > 1 ? (
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => openUpdateDialog("all")}
                  disabled={!selectedPrinterId || loading || updateStatus?.busy}
                >
                  <RefreshCw size={15} />
                  {riskyPendingCount > 0 ? "Atualizar tudo com risco" : "Atualizar tudo"}
                </button>
              ) : null}
            </div>
          </div>
          <div className="overview-strip">
            <Badge icon={RefreshCw} label="Pendentes" value={updateStatus?.counts.update_available ?? 0} />
            <Badge icon={AlertTriangle} label="Alertas" value={updateStatus?.counts.warning ?? 0} />
            <Badge icon={CheckCircle2} label="Atualizados" value={updateStatus?.counts.up_to_date ?? 0} />
            <Badge icon={Gauge} label="Estado" value={updateStatus?.busy ? "ocupado" : updateStatus?.summary ?? "-"} />
          </div>
          {updateActionResult ? (
            <div className="action-result">
              <strong>{updateActionResult.message}</strong>
              <span>Alvo: {updateActionResult.target}</span>
            </div>
          ) : null}
          <div className="update-list">
            {updateStatus?.components.length === 0 ? <p className="muted">Nenhum componente retornado pelo Update Manager.</p> : null}
            {orderedComponents.map((component) => (
              <div key={component.name} className={`update-row ${component.status}`}>
                <div className="update-main">
                  <div className="update-component-copy">
                    <strong className="update-title">
                      {React.createElement(updateStatusIcon(component.status), { size: 16 })}
                      {component.title}
                    </strong>
                    <span>
                      {component.current_version ?? "-"} {component.remote_version ? `→ ${component.remote_version}` : ""}
                    </span>
                    <small>
                      {component.configured_type} · behind {component.commits_behind_count} · packages {component.package_count}
                    </small>
                  </div>
                  <span className={`status-pill ${component.status}`}>{formatUpdateStatus(component.status)}</span>
                </div>
                {component.warnings.length || component.anomalies.length ? (
                  <small className="update-warning">
                    {[...component.warnings, ...component.anomalies].join(" · ")}
                  </small>
                ) : null}
                {component.requires_confirmation ? (
                  <div className="update-risk">
                    <AlertTriangle size={15} />
                    <span>{component.risk_reason ?? "Atualizacao de risco alto exige confirmacao explicita."}</span>
                  </div>
                ) : null}
                {component.can_rollback ? (
                  <small className="update-rollback-note">Rollback disponível para {component.rollback_version}.</small>
                ) : null}
                <div className="update-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void refreshUpdateStatus(component.name)}
                    disabled={!selectedPrinterId || loading || updateStatus?.busy}
                  >
                    <RefreshCw size={15} />
                    Reanalisar
                  </button>
                  {component.can_update ? (
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => openUpdateDialog(component.name)}
                      disabled={!selectedPrinterId || loading || updateStatus?.busy}
                    >
                      <RefreshCw size={15} />
                      Atualizar
                    </button>
                  ) : (
                    <button type="button" className="secondary-button" disabled>
                      <CheckCircle2 size={15} />
                      Atualizado
                    </button>
                  )}
                  {component.can_rollback ? (
                    <button
                      type="button"
                      className="danger-button"
                      onClick={() => openRollbackDialog(component)}
                      disabled={!selectedPrinterId || loading || updateStatus?.busy}
                    >
                      <RefreshCw size={15} />
                      Rollback
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className={`panel wide ${checklist?.can_print ? "ok" : "warn"} panel-section panel-updates post-update-checklist`}>
          <h2>Checklist pós-update</h2>
          <strong className="summary">{checklist?.summary ?? "Aguardando dados"}</strong>
          {checklist ? (
            <div className="checklist-meta">
              <span>{formatChecklistDataState(checklist.data_state)}</span>
              <span>{checklist.source}</span>
            </div>
          ) : null}
          <div className="checks">
            {checklist?.items.map((item: any) => (
              <div key={item.key} className="check">
                <span className={checklistDotClass(item)} />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </article>


    </>
  );
}

function orderUpdateComponents(components: UpdateComponent[]): UpdateComponent[] {
  return components
    .map((component, index) => ({ component, index }))
    .sort((left, right) => {
      const leftPending = isPendingUpdateComponent(left.component);
      const rightPending = isPendingUpdateComponent(right.component);
      if (leftPending !== rightPending) {
        return leftPending ? -1 : 1;
      }
      if (leftPending && rightPending) {
        const scoreDelta = updateAgeScore(right.component) - updateAgeScore(left.component);
        if (scoreDelta !== 0) {
          return scoreDelta;
        }
      }
      return left.index - right.index;
    })
    .map((item) => item.component);
}

function isPendingUpdateComponent(component: UpdateComponent): boolean {
  return component.can_update || component.status === "update_available";
}

function updateAgeScore(component: UpdateComponent): number {
  return component.commits_behind_count + component.package_count;
}
