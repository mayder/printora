import { Badge, Metric } from "../components/common";
import { AgentsScreen } from "./AgentsScreen";
import { FirmwareScreen } from "./FirmwareScreen";
import { MaintenanceScreen } from "./MaintenanceScreen";
import { MonitoringScreen } from "./MonitoringScreen";
import { ReportsScreen } from "./ReportsScreen";
import { TestsScreen } from "./TestsScreen";
import { UpdatesScreen } from "./UpdatesScreen";
import type { PrinterDetailTab, PrintoraScreenProps } from "../hooks/usePrintoraApp";

type PrinterDetailScreenProps = PrintoraScreenProps;

const printerTabs: Array<{ key: PrinterDetailTab; label: string }> = [
  { key: "summary", label: "Resumo" },
  { key: "operation", label: "Operação" },
  { key: "updates", label: "Atualizações" },
  { key: "tests", label: "Calibração" },
  { key: "firmware", label: "Firmware" },
  { key: "maintenance", label: "Manutenção" },
  { key: "reports", label: "Diagnóstico" },
  { key: "agents", label: "Agentes" },
];

export function PrinterDetailScreen(props: PrinterDetailScreenProps) {
  const {
    ArrowLeft,
    Database,
    Gauge,
    Printer,
    Radio,
    RefreshCw,
    Settings,
    ShieldCheck,
    captureSnapshot,
    countPendingUpdates,
    formatChecklistDataState,
    formatDecision,
    formatHours,
    formatSshStatus,
    formatUnknown,
    handleAlertCenterAction,
    health,
    lastReadingLabel,
    loadAgentSupport,
    loadFleetAgentPairings,
    loadPrinterPairing,
    loadPrinterHealth,
    loadPrinters,
    loadSelectedPrinterStatus,
    loading,
    moonrakerOnline,
    operationState,
    primaryRiskItem,
    printerDetailTab,
    riskClass,
    riskLabel,
    selectedPrinter,
    selectedPrinterId,
    setActiveSection,
    setAlertCenterOpen,
    setPrinterDetailTab,
    snapshots,
    totalPrintHours,
    updateStatus,
    alertBlockerCount,
    alertWarningCount,
  } = props;

  if (!selectedPrinter || !selectedPrinterId) {
    return (
      <article className="panel wide panel-section panel-printers">
        <div className="panel-heading">
          <div>
            <h2>Nenhuma impressora selecionada</h2>
            <p className="muted">Abra uma impressora pela lista para acessar operação, diagnóstico, manutenção e agentes.</p>
          </div>
          <button type="button" className="primary-button" onClick={() => setActiveSection("printers")}>
            <Printer size={16} />
            Ver impressoras
          </button>
        </div>
      </article>
    );
  }

  async function refreshSelectedPrinterAgentStatus() {
    if (!selectedPrinterId) {
      return;
    }
    await Promise.allSettled([
      loadPrinters(),
      loadFleetAgentPairings([selectedPrinterId]),
      loadPrinterPairing(selectedPrinterId),
      loadAgentSupport(selectedPrinterId),
    ]);
  }

  const activeContent = (() => {
    switch (printerDetailTab) {
      case "operation":
        return <MonitoringScreen {...props} />;
      case "updates":
        return <UpdatesScreen {...props} />;
      case "tests":
        return <TestsScreen {...props} />;
      case "firmware":
        return <FirmwareScreen {...props} />;
      case "maintenance":
        return <MaintenanceScreen {...props} />;
      case "reports":
        return <ReportsScreen {...props} />;
      case "agents":
        return <AgentsScreen {...props} embeddedPrinterContext />;
      default:
        return (
          <article className="panel wide panel-section panel-overview">
            <div className="overview-hero">
              <div className="overview-status-card">
                <span className={`status-pill ${moonrakerOnline ? "online" : "offline"}`}>
                  <span />
                  Moonraker {moonrakerOnline ? "online" : "offline"}
                </span>
                <h2>{selectedPrinter.name}</h2>
                <p>{selectedPrinter.moonraker_url}</p>
                <div className="overview-status-grid">
                  <Metric label="Estado" value={formatUnknown(operationState)} />
                  <Metric label="Horas impressas" value={typeof totalPrintHours === "number" ? formatHours(totalPrintHours) : "-"} />
                  <Metric label="Última leitura" value={lastReadingLabel} />
                  <Metric label="Origem" value={health?.data_state ? formatChecklistDataState(health.data_state) : "-"} />
                  <Metric label="Updates" value={String(countPendingUpdates(updateStatus))} />
                  <Metric label="SSH" value={formatSshStatus(selectedPrinter)} />
                </div>
              </div>
              <div className={`overview-risk-card ${riskClass}`}>
                <span>Risco atual</span>
                <strong>{riskLabel}</strong>
                <p>{health?.summary ?? "Sem health check carregado para esta impressora."}</p>
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
                  <span>{snapshots.length} snapshot(s)</span>
                </div>
                {props.alertCount > 0 ? (
                  <button type="button" className="ghost-button compact" onClick={() => setAlertCenterOpen(true)}>
                    Ver todos os alertas
                  </button>
                ) : null}
              </div>
            </div>
            <div className="overview-quick-actions" aria-label="Ações rápidas da impressora">
              <button type="button" className="secondary-button" onClick={() => void captureSnapshot()} disabled={loading}>
                <Database size={15} />
                Capturar snapshot
              </button>
              <button type="button" className="secondary-button" onClick={() => void loadPrinterHealth(selectedPrinterId)} disabled={loading}>
                <ShieldCheck size={15} />
                Health check
              </button>
              <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={loading}>
                <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
                Atualizar status
              </button>
            </div>
          </article>
        );
    }
  })();

  return (
    <>
      <article className="panel wide printer-detail-header">
        <div className="panel-heading">
          <div>
            <button type="button" className="ghost-button compact" onClick={() => setActiveSection("printers")}>
              <ArrowLeft size={15} />
              Impressoras
            </button>
            <h2>{selectedPrinter.name}</h2>
            <p className="muted">{selectedPrinter.cloud_model || "Modelo não informado"} · {selectedPrinter.location || "sem localização"}</p>
          </div>
          <div className="overview-strip">
            <Badge icon={Gauge} label="Decisão" value={formatDecision(health?.decision)} />
            <div className="badge-with-action">
              <Badge icon={Radio} label="Agente" value={selectedPrinter.cloud_status} />
              {selectedPrinter.cloud_status !== "online" ? (
                <button
                  type="button"
                  className="icon-button status-refresh-button"
                  onClick={() => void refreshSelectedPrinterAgentStatus()}
                  disabled={loading}
                  title="Atualizar status do agente"
                  aria-label={`Atualizar status do agente ${selectedPrinter.name}`}
                >
                  <RefreshCw className={loading ? "button-busy-icon" : undefined} size={14} />
                </button>
              ) : null}
            </div>
            <Badge icon={Settings} label="Auditoria" value={selectedPrinter.host_audit_mode} />
          </div>
        </div>
        <div className="detail-tabbar" role="tablist" aria-label="Navegação da impressora">
          {printerTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              role="tab"
              className={printerDetailTab === tab.key ? "active" : ""}
              aria-selected={printerDetailTab === tab.key}
              onClick={() => setPrinterDetailTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </article>
      {activeContent}
    </>
  );
}
