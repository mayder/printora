import { Badge, Metric } from "../components/common";
import type { AgentPairingOverview, PrinterAgentRecord, PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type AgentDetailScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "ArrowLeft"
  | "ClipboardCheck"
  | "FileText"
  | "Gauge"
  | "History"
  | "KeyRound"
  | "Printer"
  | "Radio"
  | "Server"
  | "ShieldAlert"
  | "Trash2"
  | "agentInstallStatus"
  | "agentSupport"
  | "agentSupportBundle"
  | "createAgentDoctorJob"
  | "fleetPairingOverviews"
  | "loadAgentSupport"
  | "loadAgentSupportBundle"
  | "loading"
  | "openPrinterDetail"
  | "printers"
  | "removePrinterAgent"
  | "revokePrinterAgent"
  | "rotatePrinterAgent"
  | "rotatedAgentCredential"
  | "selectedAgentId"
  | "selectedPrinterId"
  | "setActiveSection"
  | "setAgentSupportBundle"
  | "setRotatedAgentCredential"
>;

type AgentFleetRow = {
  agent: PrinterAgentRecord;
  overview: AgentPairingOverview;
  printer: PrinterRecord;
};

export function AgentDetailScreen(props: AgentDetailScreenProps) {
  const {
    AlertTriangle,
    ArrowLeft,
    ClipboardCheck,
    FileText,
    Gauge,
    History,
    KeyRound,
    Printer,
    Radio,
    Server,
    ShieldAlert,
    Trash2,
    agentSupport,
    agentSupportBundle,
    createAgentDoctorJob,
    fleetPairingOverviews,
    loadAgentSupport,
    loadAgentSupportBundle,
    loading,
    openPrinterDetail,
    printers,
    removePrinterAgent,
    revokePrinterAgent,
    rotatePrinterAgent,
    rotatedAgentCredential,
    selectedAgentId,
    selectedPrinterId,
    setActiveSection,
    setAgentSupportBundle,
    setRotatedAgentCredential,
  } = props;
  const rows = buildAgentRows(printers, fleetPairingOverviews);
  const row = rows.find((candidate) => candidate.agent.id === selectedAgentId) ?? rows.find((candidate) => candidate.printer.id === selectedPrinterId) ?? rows[0] ?? null;
  const health = agentSupport?.agents.find((item) => item.agent.id === row?.agent.id) ?? null;

  if (!row) {
    return (
      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Nenhum agente selecionado</h2>
            <p className="muted">Abra um agente pela lista para ver saúde, fila, doctor remoto e suporte.</p>
          </div>
          <button type="button" className="primary-button" onClick={() => setActiveSection("agents")}>
            <Radio size={16} />
            Ver agentes
          </button>
        </div>
      </article>
    );
  }

  return (
    <>
      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <button type="button" className="ghost-button compact" onClick={() => setActiveSection("agents")}>
              <ArrowLeft size={15} />
              Agentes
            </button>
            <h2>{row.agent.stable_id}</h2>
            <p className="muted">{row.printer.name} · {row.agent.platform || "plataforma não informada"}</p>
          </div>
          <div className="printer-card-actions">
            <button type="button" className="secondary-button" onClick={() => openPrinterDetail(row.printer.id, "summary")} disabled={loading}>
              <Printer size={15} />
              Impressora
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadAgentSupport(row.printer.id)} disabled={loading}>
              <Radio size={15} />
              Atualizar
            </button>
          </div>
        </div>
        <div className="overview-strip">
          <Badge icon={Server} label="Status" value={row.agent.status} />
          <Badge icon={Gauge} label="Versão" value={row.agent.agent_version ?? "-"} />
          <Badge icon={Radio} label="Último contato" value={row.agent.last_seen_at ?? "-"} />
          <Badge icon={KeyRound} label="Credencial" value={row.agent.credential_prefix} />
        </div>
        <div className="printer-card-grid">
          <Metric label="Impressora vinculada" value={row.printer.name} />
          <Metric label="Organização" value={row.printer.organization_id ? `org #${row.printer.organization_id}` : "individual"} />
          <Metric label="Pareado em" value={row.agent.paired_at} />
          <Metric label="Plataforma" value={row.agent.platform ?? "-"} />
          <Metric label="Agentes na impressora" value={String(row.overview.agents.length)} />
          <Metric label="Tokens pendentes" value={String(row.overview.pairing_tokens.filter((token) => token.status === "active").length)} />
        </div>
        <div className="printer-card-actions">
          <button type="button" className="secondary-button" onClick={() => void rotatePrinterAgent(row.agent.id, row.printer.id)} disabled={loading || row.agent.status === "revoked"}>
            <KeyRound size={15} />
            Rotacionar credencial
          </button>
          <button type="button" className="secondary-button" onClick={() => void revokePrinterAgent(row.agent.id, row.printer.id)} disabled={loading || row.agent.status === "revoked"}>
            <Trash2 size={15} />
            Revogar
          </button>
          {row.agent.status === "revoked" ? (
            <button type="button" className="secondary-button" onClick={() => void removePrinterAgent(row.agent.id, row.printer.id)} disabled={loading}>
              <Trash2 size={15} />
              Remover
            </button>
          ) : null}
        </div>
      </article>

      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Saúde e suporte</h2>
            <p className="muted">Diagnóstico do agente sem expor token, segredo ou payload sensível.</p>
          </div>
          <div className="printer-card-actions">
            <button type="button" className="secondary-button" onClick={() => void createAgentDoctorJob()} disabled={loading || row.agent.status !== "active"}>
              <ClipboardCheck size={15} />
              Doctor remoto
            </button>
            <button type="button" className="primary-button" onClick={() => void loadAgentSupportBundle()} disabled={loading}>
              <FileText size={16} />
              Pacote
            </button>
          </div>
        </div>
        <div className="overview-strip">
          <Badge icon={ShieldAlert} label="Alertas" value={agentSupport?.alerts.length ?? 0} />
          <Badge icon={History} label="Eventos" value={agentSupport?.recent_events.length ?? 0} />
          <Badge icon={Gauge} label="Fila" value={health ? `${health.pending_jobs} pend. / ${health.in_progress_jobs} exec.` : "-"} />
          <Badge icon={AlertTriangle} label="Falhas 24h" value={health?.failed_jobs_24h ?? 0} />
        </div>
        {health ? (
          <div className="printer-card">
            <div className="printer-card-header">
              <div>
                <strong>{health.online ? "Online" : "Offline"}</strong>
                <span>{health.diagnostic}</span>
              </div>
              <span className={health.online ? "status-pill active" : "status-pill"}>{health.state}</span>
            </div>
            <div className="printer-card-grid">
              <Metric label="Heartbeat" value={health.heartbeat_age_seconds == null ? "-" : `${health.heartbeat_age_seconds}s`} />
              <Metric label="Protocolo" value={health.protocol_compatible ? "compatível" : `v${health.protocol_version ?? "-"}`} />
              <Metric label="Versão esperada" value={health.expected_version} />
              <Metric label="Último job" value={health.latest_job?.job_type ?? "-"} />
            </div>
          </div>
        ) : (
          <p className="muted">Atualize o suporte para carregar a saúde deste agente.</p>
        )}
        {agentSupportBundle ? (
          <div className="agent-install-box">
            <div className="printer-card-header">
              <div>
                <strong>Pacote de suporte sanitizado</strong>
                <span>Gerado em {agentSupportBundle.generated_at}; {agentSupportBundle.recent_jobs.length} jobs recentes.</span>
              </div>
              <button type="button" className="secondary-button" onClick={() => setAgentSupportBundle(null)}>
                Ocultar
              </button>
            </div>
            <textarea readOnly value={JSON.stringify(agentSupportBundle, null, 2)} />
          </div>
        ) : null}
      </article>

      {rotatedAgentCredential ? (
        <article className="panel wide panel-section panel-agents">
          <div className="auth-step">
            <div>
              <strong>Credencial rotacionada</strong>
              <p className="muted">Copie agora. A credencial antiga já foi invalidada.</p>
              <code>{rotatedAgentCredential.credential}</code>
            </div>
            <button type="button" className="secondary-button" onClick={() => setRotatedAgentCredential(null)}>
              Ocultar
            </button>
          </div>
        </article>
      ) : null}
    </>
  );
}

function buildAgentRows(printers: PrinterRecord[], overviews: Record<number, AgentPairingOverview>) {
  return printers
    .flatMap((printer) => {
      const overview = overviews[printer.id];
      return (overview?.agents ?? [])
        .filter((agent) => agent.status !== "removed")
        .map((agent) => ({ agent, overview, printer }));
    })
    .sort((left, right) => (right.agent.last_seen_at ?? "").localeCompare(left.agent.last_seen_at ?? ""));
}
