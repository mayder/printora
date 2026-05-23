import { Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type OverviewScreenProps = ScreenPropsFor<
  | "Database"
  | "Plus"
  | "RefreshCw"
  | "ShieldCheck"
  | "alertCount"
  | "captureSnapshot"
  | "countPendingUpdates"
  | "formatChecklistDataState"
  | "formatHours"
  | "formatUnknown"
  | "handleAlertCenterAction"
  | "health"
  | "lastReadingLabel"
  | "loadPrinterHealth"
  | "loadSelectedPrinterStatus"
  | "loading"
  | "moonrakerOnline"
  | "openCreatePrinterModal"
  | "operationState"
  | "primaryRiskItem"
  | "riskClass"
  | "riskLabel"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setAlertCenterOpen"
  | "snapshots"
  | "status"
  | "totalPrintHours"
  | "updateStatus"
>;

export function OverviewScreen(props: OverviewScreenProps) {
  const {
    Database,
    Plus,
    RefreshCw,
    ShieldCheck,
    alertCount,
    captureSnapshot,
    countPendingUpdates,
    formatChecklistDataState,
    formatHours,
    formatUnknown,
    handleAlertCenterAction,
    health,
    lastReadingLabel,
    loadPrinterHealth,
    loadSelectedPrinterStatus,
    loading,
    moonrakerOnline,
    openCreatePrinterModal,
    operationState,
    primaryRiskItem,
    riskClass,
    riskLabel,
    selectedPrinter,
    selectedPrinterId,
    setAlertCenterOpen,
    snapshots,
    status,
    totalPrintHours,
    updateStatus,
  } = props;

  return (
    <>
        <article className="panel wide panel-section panel-overview">
          <div className="overview-hero">
            <div className="overview-status-card">
              <span className={`status-pill ${moonrakerOnline ? "online" : "offline"}`}>
                <span />
                Moonraker {moonrakerOnline ? "online" : "offline"}
              </span>
              <h2>{selectedPrinter?.name ?? "Nenhuma impressora selecionada"}</h2>
              <p>{selectedPrinter?.moonraker_url ?? "Cadastre uma impressora para carregar status, snapshots e health check."}</p>
              <div className="overview-status-grid">
                <Metric label="Estado" value={formatUnknown(operationState)} />
                <Metric label="Horas impressas" value={typeof totalPrintHours === "number" ? formatHours(totalPrintHours) : "-"} />
                <Metric label="Última leitura" value={lastReadingLabel} />
                <Metric label="Origem" value={health?.data_state ? formatChecklistDataState(health.data_state) : "-"} />
                <Metric label="Updates" value={String(countPendingUpdates(updateStatus))} />
              </div>
            </div>
            <div className={`overview-risk-card ${riskClass}`}>
              <span>Risco atual</span>
              <strong>{riskLabel}</strong>
              <p>{health?.summary ?? "Sem health check carregado para a impressora ativa."}</p>
              {primaryRiskItem ? (
                <div className="overview-risk-main">
                  <span>{primaryRiskItem.severity === "blocker" ? "Bloqueio principal" : "Alerta principal"}</span>
                  <strong>{primaryRiskItem.title}</strong>
                  <p>{primaryRiskItem.reason}</p>
                  <button type="button" className="secondary-button compact" onClick={() => void handleAlertCenterAction(primaryRiskItem)} disabled={loading}>
                    {primaryRiskItem.actionLabel}
                  </button>
                </div>
              ) : null}
              <div className="overview-risk-counts">
                <span>{health?.counts.blocker ?? 0} bloqueio(s)</span>
                <span>{health?.counts.warning ?? 0} alerta(s)</span>
                <span>{snapshots.length} snapshot(s)</span>
              </div>
              {alertCount > 0 ? (
                <button type="button" className="ghost-button compact" onClick={() => setAlertCenterOpen(true)}>
                  Ver todos os alertas
                </button>
              ) : null}
            </div>
          </div>
          <div className="overview-quick-actions" aria-label="Ações rápidas">
            <button type="button" className="primary-button" onClick={openCreatePrinterModal}>
              <Plus size={15} />
              Adicionar impressora
            </button>
            <button type="button" className="secondary-button" onClick={() => void captureSnapshot()} disabled={!selectedPrinterId || loading}>
              <Database size={15} />
              Capturar snapshot
            </button>
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId ? void loadPrinterHealth(selectedPrinterId) : undefined} disabled={!selectedPrinterId || loading}>
              <ShieldCheck size={15} />
              Health check
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={!selectedPrinterId || loading}>
              <RefreshCw size={15} />
              Atualizar status
            </button>
          </div>
        </article>


    </>
  );
}
