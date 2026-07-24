import { useState } from "react";
import { Badge, Metric } from "../components/common";
import { formatDateTime } from "../utils/formatters";
import type { PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type PrinterCardAction = "agent-status" | "status" | "snapshot";

type PrintersScreenProps = ScreenPropsFor<
  | "Camera"
  | "CheckCircle2"
  | "Database"
  | "Gauge"
  | "Plus"
  | "Printer"
  | "Radio"
  | "RefreshCw"
  | "Server"
  | "Settings"
  | "captureSnapshotForPrinter"
  | "loadFleetAgentPairings"
  | "loadPrinterPairing"
  | "loadPrinters"
  | "loadPrinterStatus"
  | "openCreatePrinterModal"
  | "openEditPrinterModal"
  | "openPrinterDetail"
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
    RefreshCw,
    Server,
    Settings,
    captureSnapshotForPrinter,
    loadFleetAgentPairings,
    loadPrinterPairing,
    loadPrinters,
    loadPrinterStatus,
    openCreatePrinterModal,
    openEditPrinterModal,
    openPrinterDetail,
    printers,
    selectPrinter,
    selectedPrinter,
    selectedPrinterId,
    snapshots,
  } = props;
  const [busyPrinterActions, setBusyPrinterActions] = useState<Set<string>>(() => new Set());

  async function refreshPrinterAgentStatus(printer: PrinterRecord) {
    await Promise.allSettled([
      loadPrinters(),
      loadFleetAgentPairings([printer.id]),
      loadPrinterPairing(printer.id),
    ]);
  }

  async function runPrinterAction(printerId: number, action: PrinterCardAction, task: () => Promise<void>) {
    const key = printerActionKey(printerId, action);
    setBusyPrinterActions((current) => {
      const next = new Set(current);
      next.add(key);
      return next;
    });
    try {
      await task();
    } finally {
      setBusyPrinterActions((current) => {
        const next = new Set(current);
        next.delete(key);
        return next;
      });
    }
  }

  function isPrinterActionBusy(printerId: number, action: PrinterCardAction) {
    return busyPrinterActions.has(printerActionKey(printerId, action));
  }

  return (
    <article className="panel wide panel-section panel-printers">
      <div className="panel-heading">
        <div>
          <h2>Impressoras</h2>
          <p className="muted">Lista da frota. Operação, diagnóstico, atualização e manutenção ficam dentro do detalhe de cada impressora.</p>
        </div>
        <button type="button" className="primary-button" onClick={openCreatePrinterModal}>
          <Plus size={16} />
          Adicionar impressora
        </button>
      </div>
      <div className="overview-strip">
        <Badge icon={Server} label="Impressoras" value={printers.length} />
        <Badge icon={Printer} label="Contexto rápido" value={selectedPrinter?.name ?? "-"} />
        <Badge icon={Gauge} label="Escopo" value="frota" />
        <Badge icon={Database} label="Snapshots" value={snapshots.length} />
      </div>
      <div className="printer-dashboard">
        {printers.length === 0 ? <p className="muted">Nenhuma impressora cadastrada.</p> : null}
        {printers.map((printer: PrinterRecord) => {
          const agentStatusBusy = isPrinterActionBusy(printer.id, "agent-status");
          const statusBusy = isPrinterActionBusy(printer.id, "status");
          const snapshotBusy = isPrinterActionBusy(printer.id, "snapshot");
          return (
            <div key={printer.id} className={`printer-card ${printer.id === selectedPrinterId ? "active" : ""}`}>
              <div className="printer-card-header">
                <div>
                  <strong>{printer.name}</strong>
                  <span>{printer.cloud_model || "Modelo não informado"} · {printer.location || "sem localização"}</span>
                </div>
                <div className="status-inline-actions">
                  <span className={`status-pill ${agentStatusTone(printer)}`}>
                    <Radio size={13} />
                    {formatAgentStatus(printer)}
                  </span>
                  {shouldShowAgentRefresh(printer) ? (
                    <button
                      type="button"
                      className="icon-button status-refresh-button"
                      onClick={() => void runPrinterAction(printer.id, "agent-status", () => refreshPrinterAgentStatus(printer))}
                      disabled={agentStatusBusy}
                      title="Atualizar status do agente"
                      aria-label={`Atualizar status do agente ${printer.name}`}
                    >
                      <RefreshCw className={agentStatusBusy ? "button-busy-icon" : undefined} size={14} />
                    </button>
                  ) : null}
                </div>
              </div>
              <div className="printer-card-grid">
                <Metric label="Organização" value={printer.organization_id ? `org #${printer.organization_id}` : "individual"} />
                <Metric label="Agente" value={formatAgentSummary(printer)} />
                <Metric label="Último snapshot" value={formatDateTime(printer.latest_snapshot_at)} />
                <Metric label="Último agente" value={formatDateTime(printer.latest_agent_last_seen_at)} />
                <Metric label="Conectividade" value={formatAgentStatus(printer)} />
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
                <button type="button" className="secondary-button" onClick={() => openEditPrinterModal(printer)}>
                  <Settings size={15} />
                  Editar
                </button>
                <button type="button" className="primary-button" onClick={() => openPrinterDetail(printer.id, "summary")}>
                  <Printer size={15} />
                  Detalhar
                </button>
                <button type="button" className="secondary-button" onClick={() => selectPrinter(printer.id)} disabled={printer.id === selectedPrinterId}>
                  <CheckCircle2 size={15} />
                  Contexto rápido
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void runPrinterAction(printer.id, "status", () => loadPrinterStatus(printer.id))}
                  disabled={statusBusy}
                >
                  <Radio className={statusBusy ? "button-busy-icon" : undefined} size={15} />
                  {statusBusy ? "Lendo" : "Ler status"}
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void runPrinterAction(printer.id, "snapshot", () => captureSnapshotForPrinter(printer.id))}
                  disabled={snapshotBusy}
                >
                  <Camera className={snapshotBusy ? "button-busy-icon" : undefined} size={15} />
                  {snapshotBusy ? "Capturando" : "Snapshot"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}

function printerActionKey(printerId: number, action: PrinterCardAction) {
  return `${printerId}:${action}`;
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

function shouldShowAgentRefresh(printer: PrinterRecord) {
  return printer.cloud_status !== "online";
}
