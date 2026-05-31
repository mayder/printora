import { Badge, Metric } from "../components/common";
import type { PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type PrintersScreenProps = ScreenPropsFor<
  | "Camera"
  | "CheckCircle2"
  | "Database"
  | "Gauge"
  | "Plus"
  | "Printer"
  | "Radio"
  | "Server"
  | "Settings"
  | "captureSnapshot"
  | "formatDecision"
  | "formatSshStatus"
  | "health"
  | "loadSelectedPrinterStatus"
  | "loading"
  | "openCreatePrinterModal"
  | "openEditPrinterModal"
  | "printers"
  | "selectPrinter"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "snapshots"
>;

export function PrintersScreen(props: PrintersScreenProps) {
  const {
    Camera,
    CheckCircle2,
    Database,
    Gauge,
    Plus,
    Printer,
    Radio,
    Server,
    Settings,
    captureSnapshot,
    formatDecision,
    formatSshStatus,
    health,
    loadSelectedPrinterStatus,
    loading,
    openCreatePrinterModal,
    openEditPrinterModal,
    printers,
    selectPrinter,
    selectedPrinter,
    selectedPrinterId,
    snapshots,
  } = props;

  return (
    <article className="panel wide panel-section panel-printers">
      <div className="panel-heading">
        <div>
          <h2>Dashboard de impressoras</h2>
          <p className="muted">Visão rápida das impressoras cadastradas e do contexto ativo do sistema.</p>
        </div>
        <button type="button" className="primary-button" onClick={openCreatePrinterModal}>
          <Plus size={16} />
          Adicionar impressora
        </button>
      </div>
      <div className="overview-strip">
        <Badge icon={Server} label="Impressoras" value={printers.length} />
        <Badge icon={Printer} label="Ativa" value={selectedPrinter?.name ?? "-"} />
        <Badge icon={Gauge} label="Decisão" value={formatDecision(health?.decision)} />
        <Badge icon={Database} label="Snapshots" value={snapshots.length} />
      </div>
      <div className="printer-dashboard">
        {printers.length === 0 ? <p className="muted">Nenhuma impressora cadastrada.</p> : null}
        {printers.map((printer: PrinterRecord) => (
          <div key={printer.id} className={`printer-card ${printer.id === selectedPrinterId ? "active" : ""}`}>
            <div className="printer-card-header">
              <div>
                <strong>{printer.name}</strong>
                <span>{printer.cloud_model || "Modelo não informado"} · {printer.location || "sem localização"}</span>
              </div>
              <span className={`status-pill ${agentStatusTone(printer)}`}>
                <Radio size={13} />
                {formatAgentStatus(printer)}
              </span>
            </div>
            <div className="printer-card-grid">
              <Metric label="Organização" value={printer.organization_id ? `org #${printer.organization_id}` : "individual"} />
              <Metric label="Agente" value={formatAgentSummary(printer)} />
              <Metric label="Último snapshot" value={printer.latest_snapshot_at ?? "-"} />
              <Metric label="Último agente" value={printer.latest_agent_last_seen_at ?? "-"} />
              <Metric label="Host audit" value={printer.host_audit_mode} />
              <Metric label="SSH" value={formatSshStatus(printer)} />
              <Metric label="Klipper" value={printer.id === selectedPrinterId ? health?.metrics.klipper_state ? String(health.metrics.klipper_state) : "-" : "-"} />
              <Metric label="Moonraker" value={printer.id === selectedPrinterId ? health?.metrics.moonraker_version ? String(health.metrics.moonraker_version) : "-" : "-"} />
            </div>
            {printer.cloud_tags?.length ? (
              <div className="auth-list">
                {printer.cloud_tags.map((tag: string) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            ) : null}
            {printer.notes ? <p className="muted">{printer.notes}</p> : null}
            <div className="printer-card-actions">
              <button type="button" className="secondary-button" onClick={() => openEditPrinterModal(printer)} disabled={loading}>
                <Settings size={15} />
                Editar
              </button>
              <button type="button" className="secondary-button" onClick={() => selectPrinter(printer.id)} disabled={loading || printer.id === selectedPrinterId}>
                <CheckCircle2 size={15} />
                Selecionar
              </button>
              <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={!selectedPrinterId || printer.id !== selectedPrinterId || loading}>
                <Radio size={15} />
                Ler status
              </button>
              <button type="button" className="secondary-button" onClick={() => void captureSnapshot()} disabled={!selectedPrinterId || printer.id !== selectedPrinterId || loading}>
                <Camera size={15} />
                Snapshot
              </button>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function formatAgentStatus(printer: PrinterRecord) {
  if (printer.cloud_status === "online") return "Agente online";
  if (printer.cloud_status === "offline") return "Agente offline";
  if (printer.cloud_status === "aguardando_pareamento") return "Aguardando agente";
  if (printer.cloud_status === "revogado") return "Agente revogado";
  if (printer.cloud_status === "degradado") return "Agente degradado";
  return "Sem agente";
}

function formatAgentSummary(printer: PrinterRecord) {
  if (printer.active_agent_count <= 0) {
    return formatAgentStatus(printer);
  }
  const version = printer.latest_agent_version ? `v${printer.latest_agent_version}` : "versão -";
  return `${printer.active_agent_count} ativo · ${version}`;
}

function agentStatusTone(printer: PrinterRecord) {
  if (printer.cloud_status === "online") return "up_to_date";
  if (printer.cloud_status === "offline" || printer.cloud_status === "degradado") return "warning";
  if (printer.cloud_status === "aguardando_pareamento") return "update_available";
  if (printer.cloud_status === "revogado") return "silenced";
  return "";
}
