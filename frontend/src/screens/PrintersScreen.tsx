import { Badge, Metric } from "../components/common";
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
  | "audit"
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
  | "status"
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
    audit,
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
    status,
  } = props;

  return (
    <>
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
            {printers.map((printer: any) => (
              <div key={printer.id} className={`printer-card ${printer.id === selectedPrinterId ? "active" : ""}`}>
                <div className="printer-card-header">
                  <div>
                    <strong>{printer.name}</strong>
                    <span>{printer.moonraker_url}</span>
                  </div>
                  <span className={printer.id === selectedPrinterId ? "status-pill active" : "status-pill"}>
                    {printer.id === selectedPrinterId ? "ativa" : "cadastrada"}
                  </span>
                </div>
                <div className="printer-card-grid">
                  <Metric label="Host audit" value={printer.host_audit_mode} />
                  <Metric label="SSH" value={formatSshStatus(printer)} />
                  <Metric label="Klipper" value={printer.id === selectedPrinterId ? health?.metrics.klipper_state ? String(health.metrics.klipper_state) : "-" : "-"} />
                  <Metric label="Moonraker" value={printer.id === selectedPrinterId ? health?.metrics.moonraker_version ? String(health.metrics.moonraker_version) : "-" : "-"} />
                </div>
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


    </>
  );
}
