import { Metric } from "../components/common";
import type { PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type OverviewScreenProps = ScreenPropsFor<
  | "Database"
  | "Plus"
  | "RefreshCw"
  | "ShieldCheck"
  | "alertBlockerCount"
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
  | "openPrinterDetail"
  | "operationState"
  | "primaryRiskItem"
  | "riskClass"
  | "riskLabel"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "printers"
  | "setAlertCenterOpen"
  | "snapshots"
  | "status"
  | "totalPrintHours"
  | "updateStatus"
  | "alertWarningCount"
>;

export function OverviewScreen(props: OverviewScreenProps) {
  const {
    Database,
    Plus,
    RefreshCw,
    ShieldCheck,
    alertBlockerCount,
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
    openPrinterDetail,
    operationState,
    primaryRiskItem,
    riskClass,
    riskLabel,
    selectedPrinter,
    selectedPrinterId,
    printers,
    setAlertCenterOpen,
    snapshots,
    status,
    totalPrintHours,
    updateStatus,
    alertWarningCount,
  } = props;

  return (
    <>
        <article className="panel wide panel-section panel-overview">
          <div className="overview-hero">
            <div className="overview-status-card">
              <span className="status-pill active">
                <span />
                Frota
              </span>
              <h2>Visão geral</h2>
              <p>Resumo global da frota. Abra uma impressora para acessar operação, updates, calibração, firmware, manutenção e diagnóstico.</p>
              <div className="overview-status-grid">
                <Metric label="Impressoras" value={String(printers.length)} />
                <Metric label="Agentes online" value={String(printers.filter((printer: PrinterRecord) => printer.cloud_status === "online").length)} />
                <Metric label="Aguardando agente" value={String(printers.filter((printer: PrinterRecord) => printer.cloud_status === "aguardando_pareamento").length)} />
                <Metric label="Snapshots conhecidos" value={String(printers.filter((printer: PrinterRecord) => printer.latest_snapshot_at).length)} />
                <Metric label="Contexto rápido" value={selectedPrinter?.name ?? "-"} />
              </div>
            </div>
            <div className={`overview-risk-card ${riskClass}`}>
              <span>Alertas do contexto rápido</span>
              <strong>{selectedPrinter ? riskLabel : "Sem impressora aberta"}</strong>
              <p>{selectedPrinter ? health?.summary ?? "Sem health check carregado para o contexto rápido." : "Selecione uma impressora na lista para carregar dados operacionais."}</p>
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
                <span>{alertBlockerCount} bloqueio(s)</span>
                <span>{alertWarningCount} alerta(s)</span>
                <span>{snapshots.length} snapshot(s) carregado(s)</span>
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
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId ? openPrinterDetail(selectedPrinterId, "summary") : undefined} disabled={!selectedPrinterId || loading}>
              <ShieldCheck size={15} />
              Abrir contexto
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={!selectedPrinterId || loading}>
              <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
              Atualizar contexto
            </button>
          </div>
        </article>

        <article className="panel wide panel-section panel-printers">
          <div className="panel-heading">
            <div>
              <h2>Impressoras recentes</h2>
              <p className="muted">Ações operacionais ficam no detalhe do registro, não no menu principal.</p>
            </div>
          </div>
          <div className="printer-dashboard">
            {printers.length === 0 ? <p className="muted">Nenhuma impressora cadastrada.</p> : null}
            {printers.slice(0, 6).map((printer: PrinterRecord) => (
              <div key={printer.id} className="printer-card">
                <div className="printer-card-header">
                  <div>
                    <strong>{printer.name}</strong>
                    <span>{printer.cloud_model || "Modelo não informado"} · {printer.location || "sem localização"}</span>
                  </div>
                  <span className="status-pill">{printer.cloud_status}</span>
                </div>
                <div className="printer-card-grid">
                  <Metric label="Agentes" value={String(printer.active_agent_count)} />
                  <Metric label="Último contato" value={printer.latest_agent_last_seen_at ?? "-"} />
                  <Metric label="Snapshot" value={printer.latest_snapshot_at ?? "-"} />
                </div>
                <div className="printer-card-actions">
                  <button type="button" className="primary-button" onClick={() => openPrinterDetail(printer.id, "summary")} disabled={loading}>
                    Abrir detalhe
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>


    </>
  );
}
