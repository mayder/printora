import * as React from "react";
import { Badge, Metric } from "../components/common";
import type { AgentPairingOverview, PairingTokenRecord, PrinterAgentRecord, PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type AgentsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
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
  | "agentInstallPlan"
  | "agentInstallStatus"
  | "agentSupport"
  | "agentSupportBundle"
  | "agentUpdateManifest"
  | "createAgentInstallPlan"
  | "createAgentDoctorJob"
  | "createAgentUpdateJob"
  | "createPairingToken"
  | "createdPairingToken"
  | "fleetPairingOverviews"
  | "loadAgentInstallStatus"
  | "loadAgentSupport"
  | "loadAgentSupportBundle"
  | "loadFleetAgentPairings"
  | "loading"
  | "openAgentDetail"
  | "pairingOverview"
  | "printers"
  | "removePairingToken"
  | "removePrinterAgent"
  | "revokePairingToken"
  | "revokePrinterAgent"
  | "rotatePrinterAgent"
  | "rotatedAgentCredential"
  | "selectPrinter"
  | "setAgentInstallPlan"
  | "setAgentSupportBundle"
  | "setRotatedAgentCredential"
  | "showToast"
  | "selectedPrinter"
  | "selectedPrinterId"
> & {
  embeddedPrinterContext?: boolean;
};

type AgentFleetRow = {
  agent: PrinterAgentRecord;
  overview: AgentPairingOverview;
  printer: PrinterRecord;
};

const manualAgentUpdateCommand = "sudo printora-agent -config /etc/printora-agent/config.json update-check";

export function AgentsScreen(props: AgentsScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
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
    agentInstallPlan,
    agentInstallStatus,
    agentSupport,
    agentSupportBundle,
    agentUpdateManifest,
    createAgentInstallPlan,
    createAgentDoctorJob,
    createAgentUpdateJob,
    createPairingToken,
    createdPairingToken,
    fleetPairingOverviews,
    loadAgentInstallStatus,
    loadAgentSupport,
    loadAgentSupportBundle,
    loadFleetAgentPairings,
    loading,
    openAgentDetail,
    pairingOverview,
    printers,
    removePairingToken,
    removePrinterAgent,
    revokePairingToken,
    revokePrinterAgent,
    rotatePrinterAgent,
    rotatedAgentCredential,
    selectPrinter,
    setAgentInstallPlan,
    setAgentSupportBundle,
    setRotatedAgentCredential,
    showToast,
    selectedPrinter,
    selectedPrinterId,
    embeddedPrinterContext,
  } = props;

  const agentRows = React.useMemo(
    () => buildAgentRows(printers, fleetPairingOverviews),
    [printers, fleetPairingOverviews],
  );
  const [selectedAgentKey, setSelectedAgentKey] = React.useState<string | null>(null);
  const selectedAgentRow = agentRows.find((row) => agentKey(row) === selectedAgentKey) ?? agentRows[0] ?? null;
  const selectedOverview = selectedPrinterId ? pairingOverview : null;
  const activeTokens = selectedOverview?.pairing_tokens.filter((token) => token.status === "active") ?? [];
  const tokenHistory = selectedOverview?.pairing_tokens.filter((token) => token.status !== "active") ?? [];
  const latestToastTokenId = React.useRef<number | null>(null);

  React.useEffect(() => {
    if (!selectedAgentRow) {
      setSelectedAgentKey(null);
      return;
    }
    if (!selectedAgentKey || !agentRows.some((row) => agentKey(row) === selectedAgentKey)) {
      setSelectedAgentKey(agentKey(selectedAgentRow));
    }
  }, [agentRows, selectedAgentKey, selectedAgentRow]);

  async function copyToken(token: string) {
    const copied = await copyTextToClipboard(token);
    showToast({
      tone: copied ? "success" : "danger",
      title: copied ? "Token copiado" : "Falha ao copiar token",
      detail: copied ? "Cole o token no instalador antes de sair da tela." : "Copie manualmente o token exibido.",
    });
  }

  React.useEffect(() => {
    if (!createdPairingToken || latestToastTokenId.current === createdPairingToken.id) {
      return;
    }
    latestToastTokenId.current = createdPairingToken.id;
    showToast({
      tone: "success",
      title: "Token criado",
      detail: createdPairingToken.token,
      actionLabel: "Copiar token",
      onAction: () => copyToken(createdPairingToken.token),
    });
  }, [createdPairingToken]);

  function selectAgent(row: AgentFleetRow) {
    setSelectedAgentKey(agentKey(row));
    if (row.printer.id !== selectedPrinterId) {
      selectPrinter(row.printer.id);
    }
  }

  async function rotateAgent(row: AgentFleetRow) {
    selectAgent(row);
    await rotatePrinterAgent(row.agent.id, row.printer.id);
  }

  async function revokeAgent(row: AgentFleetRow) {
    selectAgent(row);
    await revokePrinterAgent(row.agent.id, row.printer.id);
    await loadFleetAgentPairings();
  }

  async function removeAgent(row: AgentFleetRow) {
    selectAgent(row);
    await removePrinterAgent(row.agent.id, row.printer.id);
    await loadFleetAgentPairings();
  }

  async function updateAgent(row: AgentFleetRow) {
    selectAgent(row);
    if (!supportsRemoteAgentUpdate(row.agent.agent_version)) {
      const copied = await copyTextToClipboard(manualAgentUpdateCommand);
      showToast({
        tone: "info",
        title: "Atualização manual necessária",
        detail: copied ? `Comando copiado: ${manualAgentUpdateCommand}` : manualAgentUpdateCommand,
      });
      return;
    }
    await createAgentUpdateJob(row.agent.id, row.printer.id);
  }

  const expectedAgentVersion = agentUpdateManifest?.recommended_version ?? agentInstallStatus?.expected_agent_version ?? "-";

  return (
    <>
      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>{embeddedPrinterContext ? "Agentes da impressora" : "Agentes"}</h2>
            <p className="muted">{embeddedPrinterContext ? "Pareamento, instalação e suporte vinculados à impressora aberta." : "Veja todos os agentes pareados e abra um registro para diagnóstico completo."}</p>
          </div>
          {embeddedPrinterContext ? (
            <button type="button" className="primary-button" onClick={() => void createAgentInstallPlan()} disabled={!selectedPrinterId || loading}>
              <ClipboardCheck size={16} />
              Gerar instalação
            </button>
          ) : (
            <button type="button" className="primary-button" onClick={() => void loadFleetAgentPairings()} disabled={loading}>
              <Radio size={16} />
              Atualizar frota
            </button>
          )}
        </div>
        <div className="overview-strip">
          <Badge icon={Server} label="Impressoras" value={printers.length} />
          <Badge icon={Radio} label="Agentes" value={agentRows.length} />
          <Badge icon={CheckCircle2} label="Online" value={agentRows.filter((row) => row.printer.cloud_status === "online").length} />
          <Badge icon={Gauge} label="Versão esperada" value={expectedAgentVersion} />
        </div>
      </article>

      {!embeddedPrinterContext ? <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Agentes da frota</h2>
            <p className="muted">A listagem é por agente; o detalhe concentra saúde, fila, doctor remoto e credencial.</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void loadFleetAgentPairings()} disabled={loading}>
            <Radio size={15} />
            Atualizar
          </button>
        </div>
        <div className="agent-fleet-layout">
          <div className="agent-fleet-table">
            <div className="agent-fleet-header">
              <span>Agente</span>
              <span>Impressora</span>
              <span>Status</span>
              <span>Versão</span>
              <span>Último contato</span>
              <span>Ações</span>
            </div>
            {agentRows.length === 0 ? <div className="agent-fleet-empty">Nenhum agente pareado ainda.</div> : null}
            {agentRows.map((row) => (
              <div key={agentKey(row)} className={`agent-fleet-row ${selectedAgentRow && agentKey(row) === agentKey(selectedAgentRow) ? "active" : ""}`}>
                <strong>{row.agent.stable_id}</strong>
                <span>{row.printer.name}</span>
                <span className={`status-pill ${agentStatusTone(row)}`}>{agentStatusLabel(row)}</span>
                <span>{agentVersionLabel(row.agent.agent_version, expectedAgentVersion)}</span>
                <span>{row.agent.last_seen_at ?? "-"}</span>
                <div className="printer-card-actions">
                  <button type="button" className="secondary-button" onClick={() => selectAgent(row)} disabled={loading}>
                    <Printer size={15} />
                    Contexto
                  </button>
                  <button type="button" className="secondary-button" onClick={() => openAgentDetail(row.printer.id, row.agent.id)} disabled={loading}>
                    <Radio size={15} />
                    Detalhar
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void updateAgent(row)} disabled={loading || row.agent.status !== "active"}>
                    <RefreshCw size={15} />
                    {supportsRemoteAgentUpdate(row.agent.agent_version) ? "Atualizar" : "Comando"}
                  </button>
                  {row.agent.status === "revoked" ? (
                    <button type="button" className="secondary-button" onClick={() => void removeAgent(row)} disabled={loading}>
                      <Trash2 size={15} />
                      Remover
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div className="printer-card agent-detail-card">
            {selectedAgentRow ? (
              <>
                <div className="printer-card-header">
                  <div>
                    <strong>{selectedAgentRow.agent.stable_id}</strong>
                    <span>{selectedAgentRow.printer.name} · {selectedAgentRow.agent.platform || "-"}</span>
                  </div>
                  <span className={`status-pill ${agentStatusTone(selectedAgentRow)}`}>{agentStatusLabel(selectedAgentRow)}</span>
                </div>
                <div className="printer-card-grid">
                  <Metric label="Impressora" value={selectedAgentRow.printer.name} />
                  <Metric label="URL" value={selectedAgentRow.printer.moonraker_url} />
                  <Metric label="Versão" value={selectedAgentRow.agent.agent_version ?? "-"} />
                  <Metric label="Versão esperada" value={expectedAgentVersion} />
                  <Metric label="Plataforma" value={selectedAgentRow.agent.platform ?? "-"} />
                  <Metric label="Pareado em" value={selectedAgentRow.agent.paired_at} />
                  <Metric label="Último contato" value={selectedAgentRow.agent.last_seen_at ?? "-"} />
                  <Metric label="Credencial" value={selectedAgentRow.agent.credential_prefix} />
                  <Metric label="Status" value={selectedAgentRow.agent.status} />
                </div>
                <div className="printer-card-actions">
                  <button type="button" className="secondary-button" onClick={() => selectAgent(selectedAgentRow)} disabled={loading}>
                    <Printer size={15} />
                    Contexto
                  </button>
                  <button type="button" className="primary-button" onClick={() => openAgentDetail(selectedAgentRow.printer.id, selectedAgentRow.agent.id)} disabled={loading}>
                    <Radio size={15} />
                    Abrir detalhe
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void updateAgent(selectedAgentRow)} disabled={loading || selectedAgentRow.agent.status !== "active"}>
                    <RefreshCw size={15} />
                    {supportsRemoteAgentUpdate(selectedAgentRow.agent.agent_version) ? "Atualizar agente" : "Copiar comando"}
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void rotateAgent(selectedAgentRow)} disabled={loading || selectedAgentRow.agent.status === "revoked"}>
                    <KeyRound size={15} />
                    Rotacionar
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void revokeAgent(selectedAgentRow)} disabled={loading || selectedAgentRow.agent.status === "revoked"}>
                    <Trash2 size={15} />
                    Revogar
                  </button>
                  {selectedAgentRow.agent.status === "revoked" ? (
                    <button type="button" className="secondary-button" onClick={() => void removeAgent(selectedAgentRow)} disabled={loading}>
                      <Trash2 size={15} />
                      Remover
                    </button>
                  ) : null}
                </div>
              </>
            ) : (
              <p className="muted">Selecione um agente para ver detalhes.</p>
            )}
          </div>
        </div>
      </article> : null}

      {embeddedPrinterContext ? <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Instalação por token</h2>
            <p className="muted">Cada token ativo é de uso único para parear uma instalação. Ao gerar outro token, o pendente anterior é revogado.</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void createPairingToken()} disabled={!selectedPrinterId || loading}>
            <KeyRound size={15} />
            Gerar token
          </button>
        </div>
        {!selectedPrinterId ? <p className="muted">Selecione uma impressora para gerar instalação.</p> : null}
        <div className="overview-strip">
          <Badge icon={Server} label="Impressora" value={selectedPrinter?.name ?? "-"} />
          <Badge icon={CheckCircle2} label="Instalação" value={agentInstallStatus?.ready ? "validada" : "pendente"} />
          <Badge icon={Radio} label="Agentes ativos" value={agentInstallStatus?.active_agents ?? 0} />
          <Badge icon={Gauge} label="Token ativo" value={activeTokens.length ? activeTokens[0].token_prefix : "-"} />
        </div>
        {agentInstallStatus ? <p className="muted">{agentInstallStatus.diagnostic}</p> : null}

        {agentInstallPlan ? (
          <div className="agent-install-box">
            <div className="printer-card-header">
              <div>
                <strong>Comandos de instalação</strong>
                <span>Token {agentInstallPlan.token_prefix} expira em {agentInstallPlan.expires_at}.</span>
              </div>
              <button type="button" className="secondary-button" onClick={() => setAgentInstallPlan(null)}>
                Ocultar
              </button>
            </div>
            <label>
              Preflight sem instalação
              <textarea readOnly value={agentInstallPlan.preflight_command} />
            </label>
            <label>
              Instalar e iniciar serviço
              <textarea readOnly value={agentInstallPlan.install_command} />
            </label>
            <label>
              Uninstall preservando dados
              <textarea readOnly value={agentInstallPlan.uninstall_command} />
            </label>
          </div>
        ) : null}

        <div className="agent-token-grid">
          <TokenTable
            title="Token ativo"
            emptyText="Nenhum token pendente para esta impressora."
            tokens={activeTokens}
            createdPairingToken={createdPairingToken}
            loading={loading}
            onCopy={copyToken}
            onRevoke={(tokenId) => revokePairingToken(tokenId)}
            onRemove={(tokenId) => removePairingToken(tokenId)}
          />
          <TokenTable
            title="Histórico de tokens"
            emptyText="Nenhum token antigo."
            tokens={tokenHistory}
            createdPairingToken={createdPairingToken}
            loading={loading}
            onCopy={copyToken}
            onRevoke={(tokenId) => revokePairingToken(tokenId)}
            onRemove={(tokenId) => removePairingToken(tokenId)}
          />
        </div>
      </article> : null}

      {embeddedPrinterContext && rotatedAgentCredential ? (
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

      {embeddedPrinterContext ? <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Saúde e suporte</h2>
            <p className="muted">Diagnóstico da impressora selecionada para diferenciar agente, API, credencial, Moonraker, Klipper, versão e fila.</p>
          </div>
          <div className="printer-card-actions">
            <button type="button" className="secondary-button" onClick={() => void loadAgentSupport()} disabled={!selectedPrinterId || loading}>
              <Radio size={15} />
              Atualizar
            </button>
            <button type="button" className="secondary-button" onClick={() => void createAgentDoctorJob()} disabled={!selectedPrinterId || loading || !agentInstallStatus?.ready}>
              <ClipboardCheck size={15} />
              Doctor remoto
            </button>
            <button type="button" className="primary-button" onClick={() => void loadAgentSupportBundle()} disabled={!selectedPrinterId || loading}>
              <FileText size={16} />
              Pacote
            </button>
          </div>
        </div>
        <div className="overview-strip">
          <Badge icon={ShieldAlert} label="Alertas" value={agentSupport?.alerts.length ?? 0} />
          <Badge icon={Server} label="Agentes" value={agentSupport?.agents.length ?? 0} />
          <Badge icon={History} label="Eventos" value={agentSupport?.recent_events.length ?? 0} />
          <Badge icon={Gauge} label="Retenção" value={`${agentSupport?.retention_days ?? 180} dias`} />
        </div>
        {agentSupport?.alerts.length ? (
          <div className="auth-list">
            {agentSupport.alerts.map((alert) => (
              <div key={`${alert.code}-${alert.detail}`}>
                <strong>{alert.severity === "critical" ? "Crítico" : "Atenção"} · {alert.title}</strong>
                <span>{alert.detail} · {alert.action}</span>
              </div>
            ))}
          </div>
        ) : null}
        <div className="printer-dashboard">
          {(agentSupport?.agents ?? []).map((item) => (
            <div key={item.agent.id} className="printer-card">
              <div className="printer-card-header">
                <div>
                  <strong>{item.agent.stable_id}</strong>
                  <span>{item.state} · {item.agent.platform || "-"} · v{item.agent.agent_version || "-"}</span>
                </div>
                <span className={item.online ? "status-pill active" : "status-pill"}>{item.online ? "online" : "offline"}</span>
              </div>
              <div className="printer-card-grid">
                <Metric label="Heartbeat" value={item.heartbeat_age_seconds == null ? "-" : `${item.heartbeat_age_seconds}s`} />
                <Metric label="Protocolo" value={item.protocol_compatible ? "compatível" : `v${item.protocol_version ?? "-"}`} />
                <Metric label="Fila" value={`${item.pending_jobs} pend. / ${item.in_progress_jobs} exec.`} />
                <Metric label="Falhas 24h" value={String(item.failed_jobs_24h)} />
              </div>
              <p className="muted">{item.diagnostic}</p>
              {item.latest_failure ? (
                <div className="auth-step">
                  <AlertTriangle size={16} />
                  <span>Última falha: {item.latest_failure.job_type} · {item.latest_failure.error_message || item.latest_failure.status}</span>
                </div>
              ) : null}
            </div>
          ))}
        </div>
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
      </article> : null}
    </>
  );
}

function TokenTable({
  title,
  emptyText,
  tokens,
  createdPairingToken,
  loading,
  onCopy,
  onRevoke,
  onRemove,
}: {
  title: string;
  emptyText: string;
  tokens: PairingTokenRecord[];
  createdPairingToken: PairingTokenRecord & { token?: string } | null;
  loading: boolean;
  onCopy: (token: string) => void;
  onRevoke: (tokenId: number) => void;
  onRemove: (tokenId: number) => void;
}) {
  return (
    <div className="printer-card">
      <div className="printer-card-header">
        <div>
          <strong>{title}</strong>
          <span>{tokens.length} registros</span>
        </div>
      </div>
      <div className="auth-list">
        {tokens.length === 0 ? <span className="muted">{emptyText}</span> : null}
        {tokens.map((token) => (
          <div key={token.id}>
            <strong>{token.token_prefix}</strong>
            <span>{token.status} · expira {token.expires_at}</span>
            <div className="printer-card-actions">
              {token.status === "active" && createdPairingToken?.id === token.id && createdPairingToken.token ? (
                <button type="button" className="secondary-button" onClick={() => onCopy(createdPairingToken.token!)} disabled={loading}>
                  Copiar
                </button>
              ) : null}
              {token.status === "active" ? (
                <button type="button" className="secondary-button" onClick={() => onRevoke(token.id)} disabled={loading}>
                  Revogar
                </button>
              ) : (
                <button type="button" className="secondary-button" onClick={() => onRemove(token.id)} disabled={loading}>
                  Remover
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
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
    .sort((left, right) => {
      const statusOrder = statusWeight(left.agent.status) - statusWeight(right.agent.status);
      if (statusOrder !== 0) return statusOrder;
      return (right.agent.last_seen_at ?? "").localeCompare(left.agent.last_seen_at ?? "");
    });
}

function statusWeight(status: PrinterAgentRecord["status"]) {
  if (status === "active") return 0;
  if (status === "revoked") return 1;
  return 2;
}

function agentKey(row: AgentFleetRow) {
  return `${row.printer.id}:${row.agent.id}`;
}

function agentStatusLabel(row: AgentFleetRow) {
  if (row.agent.status === "revoked") return "revogado";
  if (row.printer.cloud_status === "online") return "online";
  if (row.printer.cloud_status === "offline") return "offline";
  if (row.printer.cloud_status === "degradado") return "degradado";
  return row.agent.status;
}

function agentStatusTone(row: AgentFleetRow) {
  if (row.agent.status === "revoked") return "silenced";
  if (row.printer.cloud_status === "online") return "up_to_date";
  if (row.printer.cloud_status === "offline" || row.printer.cloud_status === "degradado") return "warning";
  return "update_available";
}

function agentVersionLabel(version: string | null | undefined, expectedVersion: string) {
  if (!version) return "-";
  if (expectedVersion !== "-" && version !== expectedVersion) {
    return `${version} -> ${expectedVersion}`;
  }
  return version;
}

function supportsRemoteAgentUpdate(version: string | null | undefined) {
  const [major, minor, patch] = versionTuple(version);
  return major > 0 || minor > 1 || (minor === 1 && patch >= 8);
}

function versionTuple(version: string | null | undefined) {
  const numbers = (version ?? "")
    .trim()
    .replace(/^v/, "")
    .split(".")
    .slice(0, 3)
    .map((part) => Number.parseInt(part, 10))
    .map((value) => (Number.isFinite(value) ? value : 0));
  while (numbers.length < 3) numbers.push(0);
  return numbers as [number, number, number];
}

async function copyTextToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "true");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(textarea);
    return copied;
  }
}
