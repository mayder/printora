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
  | "handleAlertCenterAction"
  | "loading"
  | "printers"
  | "setAlertCenterOpen"
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
    handleAlertCenterAction,
    loading,
    printers,
    setAlertCenterOpen,
  } = props;
  const [printerFilter, setPrinterFilter] = React.useState("all");
  React.useEffect(() => {
    if (alertCenterOpen) {
      setPrinterFilter("all");
    }
  }, [alertCenterOpen]);
  const filteredAlertCenterItems = React.useMemo(() => {
    if (printerFilter === "all") {
      return alertCenterItems;
    }
    return alertCenterItems.filter((item: any) => String(item.printerId ?? "") === printerFilter);
  }, [alertCenterItems, printerFilter]);
  const pendingUpdates = filteredAlertCenterItems.filter((item: any) =>
    item.actionKind === "open_updates" || item.actionKind === "run_update" || item.actionKind === "refresh_update",
  ).length;
  const usePrinterButtons = printers.length <= 6;
  const printerFilterOptions = [{ id: "all", name: "Todas" }, ...printers.map((printer: any) => ({ id: String(printer.id), name: printer.name }))];

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
                <Badge icon={AlertTriangle} label="Bloqueios" value={filteredAlertCenterItems.filter((item: any) => item.severity === "blocker").length} />
                <Badge icon={AlertTriangle} label="Alertas" value={filteredAlertCenterItems.filter((item: any) => item.severity === "warning").length} />
                <Badge icon={RefreshCw} label="Updates" value={pendingUpdates} />
                <Badge icon={Bell} label="Total" value={filteredAlertCenterItems.length} />
              </div>
              <div className="alert-center-filter">
                <span>Impressora</span>
                {usePrinterButtons ? (
                  <div className="alert-center-filter-buttons" role="group" aria-label="Filtrar alertas por impressora">
                    {printerFilterOptions.map((option) => (
                      <button
                        key={option.id}
                        type="button"
                        className={printerFilter === option.id ? "active" : ""}
                        onClick={() => setPrinterFilter(option.id)}
                      >
                        {option.name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <select value={printerFilter} onChange={(event) => setPrinterFilter(event.target.value)} aria-label="Filtrar alertas por impressora">
                    <option value="all">Todas as impressoras</option>
                    {printers.map((printer: any) => (
                      <option key={printer.id} value={String(printer.id)}>
                        {printer.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <div className="alert-center-list">
                {filteredAlertCenterItems.length === 0 ? (
                  <div className="empty-state">
                    <CheckCircle2 size={22} />
                    <strong>Nenhum alerta ativo</strong>
                    <p className="muted">Não há bloqueios, riscos ou updates pendentes para este filtro.</p>
                  </div>
                ) : null}
                {filteredAlertCenterItems.map((item: any) => (
                  <div key={item.id} className={`alert-center-row ${item.severity}`}>
                    <div className="alert-center-icon">
                      {React.createElement(alertCenterIcon(item.severity), { size: 17 })}
                    </div>
                    <div>
                      <div className="alert-center-row-header">
                        <div>
                          <strong>{item.title}</strong>
                          <span>{item.source}</span>
                          {item.printerName ? <small>Impressora: {item.printerName}</small> : null}
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
