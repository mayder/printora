import { Badge, Metric } from "../components/common";
import { formatDateTime } from "../utils/formatters";
import type { AgentJobRecord, AgentPairingOverview, PrinterAgentRecord, PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";
import * as React from "react";

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
  | "RefreshCw"
  | "Server"
  | "ShieldAlert"
  | "Trash2"
  | "agentInstallStatus"
  | "agentSupport"
  | "agentSupportBundle"
  | "agentUpdateManifest"
  | "createAgentDoctorJob"
  | "createAgentUpdateJob"
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
  | "showToast"
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
    RefreshCw,
    Server,
    ShieldAlert,
    Trash2,
    agentInstallStatus,
    agentSupport,
    agentSupportBundle,
    agentUpdateManifest,
    createAgentDoctorJob,
    createAgentUpdateJob,
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
    showToast,
  } = props;
  const rows = buildAgentRows(printers, fleetPairingOverviews);
  const row = rows.find((candidate) => candidate.agent.id === selectedAgentId) ?? rows.find((candidate) => candidate.printer.id === selectedPrinterId) ?? rows[0] ?? null;
  const health = agentSupport?.agents.find((item) => item.agent?.id === row?.agent.id) ?? null;
  const expectedAgentVersion = agentUpdateManifest?.recommended_version ?? health?.expected_version ?? agentInstallStatus?.expected_agent_version ?? "-";
  const outdated = row ? expectedAgentVersion !== "-" && row.agent.agent_version !== expectedAgentVersion : false;
  const latestDoctor = agentSupport?.latest_doctor ?? null;

  async function updateAgent(rowToUpdate: AgentFleetRow) {
    if (!canRequestSystemAgentUpdate(rowToUpdate)) {
      showToast({
        tone: "warning",
        title: "Agente inativo",
        detail: "O agente precisa estar ativo para receber o job remoto de update.",
      });
      return;
    }
    await createAgentUpdateJob(rowToUpdate.agent.id, rowToUpdate.printer.id);
  }

  if (!row) {
    return (
      <article className="panel wide panel-section panel-agents agent-detail-hero">
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

  const raspberryCheck = getDoctorCheck(latestDoctor, "raspberry_throttling");
  const devicePlatform = stringFromRecord(latestDoctor?.result, "platform") || row.agent.platform || "-";
  const doctorGeneratedAt = formatDateTime(latestDoctor?.finished_at ?? latestDoctor?.updated_at);
  const hostMetrics = parseHostMetrics(row.agent.capabilities.host_metrics);
  const moonrakerStatus = getDoctorCheck(latestDoctor, "moonraker");
  const printoraService = hostMetrics ? findPrintoraService(hostMetrics.services) : null;

  return (
    <>
      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <button type="button" className="ghost-button compact" onClick={() => setActiveSection("agents")} aria-label="Voltar para agentes">
              <ArrowLeft size={15} />
              Voltar para agentes
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
            <button type="button" className="primary-button" onClick={() => void updateAgent(row)} disabled={loading || row.agent.status !== "active"}>
              <RefreshCw size={15} />
              {agentUpdateButtonLabel(row)}
            </button>
          </div>
        </div>
        <div className="overview-strip agent-summary-strip">
          <Badge icon={Server} label="Status" value={row.agent.status} />
          <Badge icon={Gauge} label="Versão instalada" value={row.agent.agent_version ?? "-"} />
          <Badge icon={RefreshCw} label="Versão esperada" value={expectedAgentVersion} />
          <Badge icon={Radio} label="Último contato" value={formatDateTime(row.agent.last_seen_at)} />
          <Badge icon={KeyRound} label="Credencial" value={row.agent.status === "revoked" ? "revogada" : "configurada"} />
        </div>
        {outdated ? (
          <div className="auth-step">
            <AlertTriangle size={16} />
            <span>
              Agente em {row.agent.agent_version || "-"}; esperado {expectedAgentVersion}. Use Atualizar agente para
              enviar a ação remota de autoatualização ao agente instalado.
            </span>
          </div>
        ) : null}
        <div className="printer-card-grid">
          <Metric label="Impressora vinculada" value={row.printer.name} />
          <Metric label="Organização" value={row.printer.organization_id ? `org #${row.printer.organization_id}` : "individual"} />
          <Metric label="Pareado em" value={formatDateTime(row.agent.paired_at)} />
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
            <h2>Dispositivo do agente</h2>
            <p className="muted">Host onde o agente roda: versão, conectividade, serviço e sinais físicos do Raspberry quando disponíveis.</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void createAgentDoctorJob(row.printer.id)} disabled={loading || row.agent.status !== "active"}>
            <ClipboardCheck size={15} />
            Doctor remoto
          </button>
        </div>
        <div className="overview-strip agent-summary-strip">
          <Badge icon={Server} label="Plataforma" value={devicePlatform} />
          <Badge icon={Gauge} label="Agente" value={row.agent.agent_version ?? "-"} />
          <Badge icon={RefreshCw} label="Esperada" value={expectedAgentVersion} />
          <Badge icon={Radio} label="Moonraker" value={moonrakerStatus?.status ?? "sem doctor"} />
          <Badge icon={AlertTriangle} label="Raio Raspberry" value={formatRaspberryStatus(raspberryCheck)} />
        </div>
        <div className="agent-device-grid">
          <div className="agent-device-card moonraker-card">
            <div className="agent-device-card-heading">
              <Radio size={18} />
              <div>
                <span>Moonraker local</span>
                <strong>{moonrakerStatus?.status ?? "sem doctor"}</strong>
              </div>
            </div>
            <code>{row.printer.moonraker_url}</code>
            <p>{moonrakerStatus?.detail ?? "Execute o doctor remoto para confirmar a leitura ao vivo do Moonraker."}</p>
          </div>
          <div className="agent-device-card">
            <div className="agent-device-card-heading">
              <ClipboardCheck size={18} />
              <div>
                <span>Último doctor</span>
                <strong>{doctorGeneratedAt}</strong>
              </div>
            </div>
            <div className="agent-mini-grid">
              <Metric label="API" value={getDoctorCheck(latestDoctor, "api")?.status ?? "-"} />
              <Metric label="Fila local" value={getDoctorCheck(latestDoctor, "queue")?.detail ?? "-"} />
              <Metric label="Log local" value={getDoctorCheck(latestDoctor, "log")?.detail ?? "-"} />
              <Metric label="Throttling" value={raspberryCheck?.detail ?? "Sem leitura do agente"} />
            </div>
          </div>
        </div>
        <div className="panel-heading compact-heading">
          <div>
            <h3>Consumo no host</h3>
            <p className="muted">
              Snapshot atual enviado pelo agente a cada 5 minutos. Rede é agregada do host; CPU e memória são por serviço detectado.
            </p>
          </div>
        </div>
        {hostMetrics ? (
          <>
            <div className="agent-consumption-grid">
              <ResourceGauge
                label="RAM usada"
                value={formatPercent(hostMetrics.host.memoryUsedPercent)}
                percent={hostMetrics.host.memoryUsedPercent}
                detail={`Livre: ${formatBytes(hostMetrics.host.memoryAvailableBytes)}`}
              />
              <ResourceGauge
                label="CPU total dos serviços"
                value={formatPercent(sumServiceCpu(hostMetrics.services))}
                percent={Math.min(sumServiceCpu(hostMetrics.services) ?? 0, 100)}
                detail={`${hostMetrics.services.length} serviços detectados`}
              />
              <ResourceGauge
                label="Rede RX"
                value={formatNetworkRate(hostMetrics.network.rxBytesPerSecond)}
                percent={networkPercent(hostMetrics.network.rxBytesPerSecond)}
                detail="agregado no host"
              />
              <ResourceGauge
                label="Rede TX"
                value={formatNetworkRate(hostMetrics.network.txBytesPerSecond)}
                percent={networkPercent(hostMetrics.network.txBytesPerSecond)}
                detail="agregado no host"
              />
              <div className="agent-consumption-stamp">
                <History size={18} />
                <span>Coletado em</span>
                <strong>{formatDateTime(hostMetrics.collectedAt)}</strong>
              </div>
            </div>
            {printoraService ? (
              <div className="printora-consumption-focus">
                <div>
                  <span>Consumo do Printora</span>
                  <strong>{formatPercent(printoraService.cpuPercent)} CPU · {formatBytes(printoraService.rssBytes)} RAM</strong>
                  <p>{printoraService.command || "printora-agent"}</p>
                </div>
                <div className="printora-consumption-bars">
                  <ResourceBar label="CPU do agente" value={formatPercent(printoraService.cpuPercent)} percent={printoraService.cpuPercent} />
                  <ResourceBar label="Memória RSS" value={formatBytes(printoraService.rssBytes)} percent={serviceMemoryPercent(printoraService, hostMetrics)} />
                </div>
              </div>
            ) : null}
            {hostMetrics.services.length ? (
              <div className="agent-service-grid">
                {hostMetrics.services.map((service) => (
                  <div key={service.name} className={isPrintoraService(service) ? "agent-service-card printora-service" : "agent-service-card"}>
                    <div className="agent-service-card-header">
                      <div>
                        <strong>{service.name}</strong>
                        <code title={service.command || undefined}>{service.command || `${service.pidCount} processo(s)`}</code>
                      </div>
                      <span className="status-pill active">{service.pidCount} proc.</span>
                    </div>
                    <div className="service-bars">
                      <ResourceBar label="CPU" value={formatPercent(service.cpuPercent)} percent={service.cpuPercent} />
                      <ResourceBar label="Memória RSS" value={formatBytes(service.rssBytes)} percent={serviceMemoryPercent(service, hostMetrics)} />
                      <ResourceBar label="Memória virtual" value={formatBytes(service.vszBytes)} percent={null} />
                      <ResourceBar label="Rede" value="agregada no host" percent={null} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted">Nenhum serviço Klipper/Printora detectado nesta leitura.</p>
            )}
          </>
        ) : (
          <p className="muted">Sem métricas do host ainda. Aguarde o próximo heartbeat ou atualize o agente.</p>
        )}
        {latestDoctor?.status === "failed" ? (
          <div className="auth-step">
            <AlertTriangle size={16} />
            <span>{latestDoctor.error_message ?? "O doctor remoto falhou. Atualize o agente ou verifique conectividade."}</span>
          </div>
        ) : null}
      </article>

      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Saúde e suporte</h2>
            <p className="muted">Diagnóstico do agente sem expor token, segredo ou payload sensível.</p>
          </div>
          <div className="printer-card-actions">
            <button type="button" className="secondary-button" onClick={() => void createAgentDoctorJob(row.printer.id)} disabled={loading || row.agent.status !== "active"}>
              <ClipboardCheck size={15} />
              Doctor remoto
            </button>
            <button type="button" className="primary-button" onClick={() => void loadAgentSupportBundle(row.printer.id)} disabled={loading}>
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
              <Metric label="Versão esperada" value={expectedAgentVersion} />
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
                <span>Gerado em {formatDateTime(agentSupportBundle.generated_at)}; {agentSupportBundle.recent_jobs.length} jobs recentes.</span>
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

function ResourceGauge({ label, value, percent, detail }: { label: string; value: string; percent: number | null; detail: string }) {
  const cleanPercent = clampPercent(percent);
  return (
    <div className="agent-resource-gauge">
      <div className="agent-radial" style={{ "--progress": `${cleanPercent}%` } as React.CSSProperties}>
        <div>
          <strong>{value}</strong>
          <span>{label}</span>
        </div>
      </div>
      <p>{detail}</p>
    </div>
  );
}

function ResourceBar({ label, value, percent }: { label: string; value: string; percent: number | null }) {
  const cleanPercent = percent == null ? null : clampPercent(percent);
  return (
    <div className="agent-resource-bar">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      {cleanPercent == null ? (
        <span className="agent-resource-note">sem percentual</span>
      ) : (
        <div className="agent-resource-track" aria-hidden="true">
          <span style={{ width: `${cleanPercent}%` }} />
        </div>
      )}
    </div>
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

function supportsRemoteAgentUpdate(version: string | null | undefined) {
  return Boolean(version);
}

function canRequestSystemAgentUpdate(row: AgentFleetRow) {
  return row.agent.status === "active" && supportsRemoteAgentUpdate(row.agent.agent_version);
}

function agentUpdateButtonLabel(row: AgentFleetRow) {
  void row;
  return "Atualizar agente";
}

type RemoteDoctorCheck = {
  name?: unknown;
  status?: unknown;
  detail?: unknown;
};

type HostMetricsSnapshot = {
  collectedAt: string;
  host: {
    memoryAvailableBytes: number | null;
    memoryUsedPercent: number | null;
  };
  network: {
    rxBytesPerSecond: number | null;
    txBytesPerSecond: number | null;
  };
  services: Array<{
    name: string;
    command: string;
    pidCount: number;
    cpuPercent: number | null;
    rssBytes: number | null;
    vszBytes: number | null;
  }>;
};

function getDoctorCheck(job: AgentJobRecord | null | undefined, name: string): { status: string; detail: string } | null {
  const checks = Array.isArray(job?.result?.checks) ? (job?.result?.checks as RemoteDoctorCheck[]) : [];
  const check = checks.find((candidate) => candidate.name === name);
  if (!check) return null;
  return {
    status: typeof check.status === "string" ? check.status : "-",
    detail: typeof check.detail === "string" ? check.detail : "-",
  };
}

function stringFromRecord(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key];
  return typeof value === "string" ? value : "";
}

function parseHostMetrics(value: unknown): HostMetricsSnapshot | null {
  if (!isRecord(value) || value.status !== "ok") {
    return null;
  }
  const host = isRecord(value.host) ? value.host : {};
  const network = isRecord(value.network) ? value.network : {};
  const services = Array.isArray(value.services) ? value.services : [];
  return {
    collectedAt: typeof value.collected_at === "string" ? value.collected_at : "",
    host: {
      memoryAvailableBytes: numberOrNull(host.memory_available_bytes),
      memoryUsedPercent: numberOrNull(host.memory_used_percent),
    },
    network: {
      rxBytesPerSecond: numberOrNull(network.rx_bytes_per_second),
      txBytesPerSecond: numberOrNull(network.tx_bytes_per_second),
    },
    services: services
      .filter(isRecord)
      .map((service) => ({
        name: typeof service.name === "string" ? service.name : "serviço",
        command: typeof service.command === "string" ? service.command : "",
        pidCount: numberOrNull(service.pid_count) ?? 0,
        cpuPercent: numberOrNull(service.cpu_percent),
        rssBytes: numberOrNull(service.rss_bytes),
        vszBytes: numberOrNull(service.vsz_bytes),
      })),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function numberOrNull(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatPercent(value: number | null) {
  return value == null ? "-" : `${value.toFixed(1)}%`;
}

function formatBytes(value: number | null) {
  if (value == null) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let current = value;
  let index = 0;
  while (current >= 1024 && index < units.length - 1) {
    current /= 1024;
    index++;
  }
  return `${current.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatNetworkRate(value: number | null) {
  if (value == null) return "calculando";
  return `${formatBytes(value)}/s`;
}

function sumServiceCpu(services: HostMetricsSnapshot["services"]) {
  if (!services.length) return null;
  const measured = services.filter((service) => service.cpuPercent != null);
  if (!measured.length) return null;
  return measured.reduce((total, service) => total + (service.cpuPercent ?? 0), 0);
}

function findPrintoraService(services: HostMetricsSnapshot["services"]) {
  return services.find(isPrintoraService) ?? null;
}

function isPrintoraService(service: HostMetricsSnapshot["services"][number]) {
  return service.name.toLowerCase().includes("printora") || service.command.toLowerCase().includes("printora-agent");
}

function networkPercent(value: number | null) {
  if (value == null) return null;
  return Math.min((value / (1024 * 1024)) * 100, 100);
}

function serviceMemoryPercent(service: HostMetricsSnapshot["services"][number], snapshot: HostMetricsSnapshot) {
  const available = snapshot.host.memoryAvailableBytes;
  const used = snapshot.host.memoryUsedPercent;
  if (service.rssBytes == null || available == null || used == null) return null;
  const total = available / Math.max(0.01, 1 - used / 100);
  return total > 0 ? (service.rssBytes / total) * 100 : null;
}

function clampPercent(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(value, 100));
}

function formatRaspberryStatus(check: { status: string; detail: string } | null) {
  if (!check) return "sem leitura";
  const detail = check.detail.toLowerCase();
  if (check.status === "warn" || check.status === "fail" || detail.includes("ativo") || detail.includes("undervoltage")) {
    return "throttled";
  }
  if (detail.includes("não é raspberry") || detail.includes("nao e raspberry")) {
    return "não aplicável";
  }
  if (check.status === "ok") return "normal";
  return check.status;
}
