import { Badge, Metric } from "../components/common";
import { formatDateTime } from "../utils/formatters";
import type { AlertCenterItem } from "../alertCenter";
import type { AgentPairingOverview, PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type OverviewScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "Gauge"
  | "Plus"
  | "Printer"
  | "Radio"
  | "RefreshCw"
  | "Server"
  | "ShieldCheck"
  | "alertBlockerCount"
  | "alertCenterItems"
  | "alertCount"
  | "alertWarningCount"
  | "agentUpdateManifest"
  | "fleetPairingOverviews"
  | "loadFleetAgentPairings"
  | "loadPrinters"
  | "loading"
  | "openCreatePrinterModal"
  | "openPrinterDetail"
  | "printers"
  | "setActiveSection"
  | "setAlertCenterOpen"
>;

export function OverviewScreen(props: OverviewScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    Gauge,
    Plus,
    Printer,
    Radio,
    RefreshCw,
    Server,
    ShieldCheck,
    alertBlockerCount,
    alertCenterItems,
    alertCount,
    alertWarningCount,
    agentUpdateManifest,
    fleetPairingOverviews,
    loadFleetAgentPairings,
    loadPrinters,
    loading,
    openCreatePrinterModal,
    openPrinterDetail,
    printers,
    setActiveSection,
    setAlertCenterOpen,
  } = props;
  const fleet = buildFleetOverview(printers, fleetPairingOverviews, agentUpdateManifest?.recommended_version, alertCenterItems);
  const topPrinters = orderPrintersForDashboard(printers).slice(0, 6);

  async function refreshFleet() {
    await Promise.allSettled([loadPrinters(), loadFleetAgentPairings()]);
  }

  async function refreshPrinterAgentStatus(printer: PrinterRecord) {
    await Promise.allSettled([loadPrinters(), loadFleetAgentPairings([printer.id])]);
  }

  return (
    <>
      <article className="panel wide panel-section panel-overview">
        <div className="panel-heading">
          <div>
            <h2>Dashboard da frota</h2>
            <p className="muted">Visão consolidada para decidir onde atuar antes de abrir um registro.</p>
          </div>
          <div className="printer-card-actions">
            <button type="button" className="secondary-button" onClick={() => void refreshFleet()} disabled={loading}>
              <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
              Atualizar frota
            </button>
            <button type="button" className="primary-button" onClick={openCreatePrinterModal}>
              <Plus size={15} />
              Adicionar impressora
            </button>
          </div>
        </div>

        <div className="overview-strip">
          <Badge icon={Server} label="Impressoras" value={fleet.totalPrinters} />
          <Badge icon={Radio} label="Agentes online" value={fleet.onlinePrinters} />
          <Badge icon={AlertTriangle} label="Atenção" value={fleet.attentionPrinters} />
          <Badge icon={Gauge} label="Versão esperada" value={agentUpdateManifest?.recommended_version ?? "-"} />
        </div>

        <div className="fleet-dashboard-grid">
          <section className="fleet-dashboard-card">
            <span>Operação</span>
            <strong>{fleet.onlinePrinters}/{fleet.totalPrinters}</strong>
            <p>Impressoras com agente online para operar, atualizar e diagnosticar pelo sistema.</p>
            <div className="fleet-dashboard-metrics">
              <Metric label="Offline/degradadas" value={String(fleet.unhealthyPrinters)} />
              <Metric label="Sem agente" value={String(fleet.withoutAgent)} />
            </div>
          </section>

          <section className="fleet-dashboard-card">
            <span>Agentes</span>
            <strong>{fleet.agentCount}</strong>
            <p>Agentes pareados na frota. Versões antigas devem ser atualizadas pelo detalhe do agente ou impressora.</p>
            <div className="fleet-dashboard-metrics">
              <Metric label="Desatualizados" value={String(fleet.outdatedAgents)} />
              <Metric label="Snapshots" value={String(fleet.snapshotPrinters)} />
            </div>
          </section>

          <section className="fleet-dashboard-card">
            <span>Alertas</span>
            <strong>{alertCount}</strong>
            <p>Consolida alertas de frota e do contexto carregado para direcionar manutenção, update ou diagnóstico.</p>
            <div className="fleet-dashboard-metrics">
              <Metric label="Bloqueios" value={String(alertBlockerCount)} />
              <Metric label="Avisos" value={String(alertWarningCount)} />
            </div>
            {alertCount > 0 ? (
              <button type="button" className="secondary-button compact" onClick={() => setAlertCenterOpen(true)}>
                Ver alertas
              </button>
            ) : null}
          </section>
        </div>
      </article>

      <article className="panel wide panel-section panel-overview">
        <div className="panel-heading">
          <div>
            <h2>Áreas operacionais</h2>
            <p className="muted">Atalhos globais para listas e para as abas de cada impressora.</p>
          </div>
        </div>
        <div className="fleet-action-grid">
          <button type="button" className="fleet-action-card" onClick={() => setActiveSection("printers")}>
            <Printer size={18} />
            <strong>Impressoras</strong>
            <span>{fleet.totalPrinters} registro(s)</span>
          </button>
          <button type="button" className="fleet-action-card" onClick={() => setActiveSection("agents")}>
            <Radio size={18} />
            <strong>Agentes</strong>
            <span>{fleet.agentCount} pareado(s)</span>
          </button>
          <button type="button" className="fleet-action-card" onClick={() => openFirstPrinterTab(printers, openPrinterDetail, "updates")} disabled={!printers.length}>
            <RefreshCw size={18} />
            <strong>Atualizações</strong>
            <span>{fleet.outdatedAgents} agente(s) antigo(s)</span>
          </button>
          <button type="button" className="fleet-action-card" onClick={() => openFirstPrinterTab(printers, openPrinterDetail, "maintenance")} disabled={!printers.length}>
            <ShieldCheck size={18} />
            <strong>Manutenção</strong>
            <span>{fleet.maintenanceAlerts} alerta(s)</span>
          </button>
          <button type="button" className="fleet-action-card" onClick={() => openFirstPrinterTab(printers, openPrinterDetail, "tests")} disabled={!printers.length}>
            <CheckCircle2 size={18} />
            <strong>Calibração</strong>
            <span>Abrir rotina por impressora</span>
          </button>
          <button type="button" className="fleet-action-card" onClick={() => openFirstPrinterTab(printers, openPrinterDetail, "reports")} disabled={!printers.length}>
            <Gauge size={18} />
            <strong>Diagnóstico</strong>
            <span>{fleet.snapshotPrinters} com snapshot</span>
          </button>
        </div>
      </article>

      <article className="panel wide panel-section panel-overview">
        <div className="panel-heading">
          <div>
            <h2>Impressoras que pedem atenção</h2>
            <p className="muted">Abra o detalhe para operar, atualizar, calibrar, manter ou diagnosticar o registro.</p>
          </div>
        </div>
        <div className="printer-dashboard">
          {topPrinters.length === 0 ? <p className="muted">Nenhuma impressora cadastrada.</p> : null}
          {topPrinters.map((printer) => (
            <div key={printer.id} className="printer-card">
              <div className="printer-card-header">
                <div>
                  <strong>{printer.name}</strong>
                  <span>{printer.cloud_model || "Modelo não informado"} · {printer.location || "sem localização"}</span>
                </div>
                <div className="status-inline-actions">
                  <span className={`status-pill ${printer.cloud_status === "online" ? "up_to_date" : "warning"}`}>{printer.cloud_status}</span>
                  {printer.cloud_status !== "online" ? (
                    <button
                      type="button"
                      className="icon-button status-refresh-button"
                      onClick={() => void refreshPrinterAgentStatus(printer)}
                      disabled={loading}
                      title="Atualizar status do agente"
                      aria-label={`Atualizar status do agente ${printer.name}`}
                    >
                      <RefreshCw className={loading ? "button-busy-icon" : undefined} size={14} />
                    </button>
                  ) : null}
                </div>
              </div>
              <div className="printer-card-grid">
                <Metric label="Agentes" value={String(printer.active_agent_count)} />
                <Metric label="Versão agente" value={printer.latest_agent_version ?? "-"} />
                <Metric label="Último contato" value={formatDateTime(printer.latest_agent_last_seen_at)} />
                <Metric label="Snapshot" value={formatDateTime(printer.latest_snapshot_at)} />
              </div>
              <div className="printer-card-actions">
                <button type="button" className="primary-button" onClick={() => openPrinterDetail(printer.id, "summary")} disabled={loading}>
                  Resumo
                </button>
                <button type="button" className="secondary-button" onClick={() => openPrinterDetail(printer.id, "updates")} disabled={loading}>
                  Atualizações
                </button>
                <button type="button" className="secondary-button" onClick={() => openPrinterDetail(printer.id, "maintenance")} disabled={loading}>
                  Manutenção
                </button>
                <button type="button" className="secondary-button" onClick={() => openPrinterDetail(printer.id, "agents")} disabled={loading}>
                  Agentes
                </button>
              </div>
            </div>
          ))}
        </div>
      </article>
    </>
  );
}

type FleetOverview = {
  agentCount: number;
  attentionPrinters: number;
  maintenanceAlerts: number;
  onlinePrinters: number;
  outdatedAgents: number;
  snapshotPrinters: number;
  totalPrinters: number;
  unhealthyPrinters: number;
  withoutAgent: number;
};

function buildFleetOverview(
  printers: PrinterRecord[],
  pairings: Record<number, AgentPairingOverview>,
  expectedAgentVersion: string | undefined,
  alerts: AlertCenterItem[],
): FleetOverview {
  const agents = Object.values(pairings).flatMap((overview) => overview.agents);
  const fallbackAgentCount = printers.reduce((total, printer) => total + printer.active_agent_count, 0);
  return {
    agentCount: agents.length || fallbackAgentCount,
    attentionPrinters: printers.filter((printer) => printer.cloud_status !== "online").length,
    maintenanceAlerts: alerts.filter((item) => item.source === "Manutenção").length,
    onlinePrinters: printers.filter((printer) => printer.cloud_status === "online").length,
    outdatedAgents: expectedAgentVersion
      ? agents.filter((agent) => agent.agent_version && agent.agent_version !== expectedAgentVersion).length ||
        printers.filter((printer) => printer.latest_agent_version && printer.latest_agent_version !== expectedAgentVersion).length
      : 0,
    snapshotPrinters: printers.filter((printer) => printer.latest_snapshot_at).length,
    totalPrinters: printers.length,
    unhealthyPrinters: printers.filter((printer) => printer.cloud_status === "offline" || printer.cloud_status === "degradado").length,
    withoutAgent: printers.filter((printer) => printer.cloud_status === "sem_agente" || printer.cloud_status === "aguardando_pareamento").length,
  };
}

function orderPrintersForDashboard(printers: PrinterRecord[]) {
  return [...printers].sort((left, right) => printerPriority(right) - printerPriority(left));
}

function printerPriority(printer: PrinterRecord) {
  if (printer.cloud_status === "offline" || printer.cloud_status === "degradado") return 4;
  if (printer.cloud_status === "sem_agente" || printer.cloud_status === "aguardando_pareamento") return 3;
  if (!printer.latest_snapshot_at) return 2;
  if (!printer.latest_agent_last_seen_at) return 1;
  return 0;
}

function openFirstPrinterTab(
  printers: PrinterRecord[],
  openPrinterDetail: (printerId?: number, tab?: "summary" | "operation" | "updates" | "tests" | "firmware" | "maintenance" | "reports" | "agents") => void,
  tab: "summary" | "operation" | "updates" | "tests" | "firmware" | "maintenance" | "reports" | "agents",
) {
  const firstPrinter = orderPrintersForDashboard(printers)[0];
  if (firstPrinter) {
    openPrinterDetail(firstPrinter.id, tab);
  }
}
