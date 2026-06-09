import * as React from "react";
import { Badge, Metric } from "../components/common";
import { formatDateTime } from "../utils/formatters";
import type { AgentPairingOverview, PairingTokenRecord, PrinterAgentRecord, PrinterRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type AgentsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "ClipboardCheck"
  | "Copy"
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
  | "loadPrinters"
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

const AGENT_ONLINE_WINDOW_SECONDS = 120;

export function AgentsScreen(props: AgentsScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    ClipboardCheck,
    Copy,
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
    loadPrinters,
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
  const selectedAgentRows = React.useMemo(
    () => buildSelectedAgentRows(selectedPrinter, selectedOverview),
    [selectedPrinter, selectedOverview],
  );
  const visibleAgentRows = embeddedPrinterContext ? selectedAgentRows : agentRows;
  const hasActivePairedAgent = selectedAgentRows.some((row) => row.agent.status === "active");
  const hasOfflineActivePairedAgent = selectedAgentRows.some((row) => row.agent.status === "active" && !isAgentHeartbeatRecent(row.agent));
  const activeTokens = selectedOverview?.pairing_tokens.filter((token) => token.status === "active") ?? [];
  const tokenHistory = selectedOverview?.pairing_tokens.filter((token) => token.status !== "active") ?? [];
  const latestToastTokenId = React.useRef<number | null>(null);
  const installReadyToastPrinterId = React.useRef<number | null>(null);

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

  async function copyCommand(command: string) {
    const copied = await copyTextToClipboard(command);
    showToast({
      tone: copied ? "success" : "danger",
      title: copied ? "Comando copiado" : "Falha ao copiar comando",
      detail: copied ? "Cole no terminal da impressora." : "Copie manualmente o comando exibido.",
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

  React.useEffect(() => {
    if (!embeddedPrinterContext || !selectedPrinterId || !agentInstallPlan || agentInstallStatus?.ready) {
      return;
    }
    let cancelled = false;
    const refreshInstallState = async () => {
      await Promise.allSettled([
        loadAgentInstallStatus(selectedPrinterId),
        loadFleetAgentPairings([selectedPrinterId]),
        loadAgentSupport(selectedPrinterId),
        loadPrinters(),
      ]);
    };
    const interval = window.setInterval(() => {
      if (!cancelled) {
        void refreshInstallState();
      }
    }, 4000);
    void refreshInstallState();
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [
    agentInstallPlan,
    agentInstallStatus?.ready,
    embeddedPrinterContext,
    selectedPrinterId,
  ]);

  React.useEffect(() => {
    if (!embeddedPrinterContext || !selectedPrinterId || !agentInstallStatus?.ready) {
      return;
    }
    if (installReadyToastPrinterId.current === selectedPrinterId) {
      return;
    }
    installReadyToastPrinterId.current = selectedPrinterId;
    showToast({
      tone: "success",
      title: "Agente conectado",
      detail: agentInstallStatus.diagnostic || "Instalação validada pelo heartbeat do agente.",
    });
  }, [agentInstallStatus?.diagnostic, agentInstallStatus?.ready, embeddedPrinterContext, selectedPrinterId, showToast]);

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
    if (!canRequestSystemAgentUpdate(row)) {
      showToast({
        tone: "warning",
        title: "Agente inativo",
        detail: "O agente precisa estar ativo para receber o job remoto de update.",
      });
      return;
    }
    await createAgentUpdateJob(row.agent.id, row.printer.id);
  }

  async function refreshAgentStatus(row: AgentFleetRow) {
    await Promise.allSettled([
      loadPrinters(),
      loadFleetAgentPairings([row.printer.id]),
      loadAgentSupport(row.printer.id),
    ]);
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
          <Badge icon={Server} label={embeddedPrinterContext ? "Impressora" : "Impressoras"} value={embeddedPrinterContext ? selectedPrinter?.name ?? "-" : printers.length} />
          <Badge icon={Radio} label="Agentes pareados" value={visibleAgentRows.length} />
          <Badge icon={CheckCircle2} label="Online agora" value={visibleAgentRows.filter((row) => isAgentHeartbeatRecent(row.agent)).length} />
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
                <span className="status-inline-actions">
                  <span className={`status-pill ${agentStatusTone(row)}`}>{agentStatusLabel(row)}</span>
                  {shouldShowAgentRefresh(row) ? (
                    <button
                      type="button"
                      className="icon-button status-refresh-button"
                      onClick={() => void refreshAgentStatus(row)}
                      disabled={loading}
                      title="Atualizar status do agente"
                      aria-label={`Atualizar status do agente ${row.printer.name}`}
                    >
                      <RefreshCw className={loading ? "button-busy-icon" : undefined} size={14} />
                    </button>
                  ) : null}
                </span>
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
                    {agentUpdateButtonLabel(row)}
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
                  <div className="status-inline-actions">
                    <span className={`status-pill ${agentStatusTone(selectedAgentRow)}`}>{agentStatusLabel(selectedAgentRow)}</span>
                    {shouldShowAgentRefresh(selectedAgentRow) ? (
                      <button
                        type="button"
                        className="icon-button status-refresh-button"
                        onClick={() => void refreshAgentStatus(selectedAgentRow)}
                        disabled={loading}
                        title="Atualizar status do agente"
                        aria-label={`Atualizar status do agente ${selectedAgentRow.printer.name}`}
                      >
                        <RefreshCw className={loading ? "button-busy-icon" : undefined} size={14} />
                      </button>
                    ) : null}
                  </div>
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
                    {agentUpdateButtonLabel(selectedAgentRow, "detail")}
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
            <h2>Agentes pareados</h2>
            <p className="muted">Agente pareado é o registro do host no Printora. Desinstalar no host não remove este vínculo.</p>
          </div>
        </div>
        {selectedAgentRows.length === 0 ? <p className="muted">Nenhum agente pareado para esta impressora.</p> : null}
        <div className="printer-dashboard">
          {selectedAgentRows.map((row) => (
            <div key={agentKey(row)} className="printer-card">
              <div className="printer-card-header">
                <div>
                  <strong>{row.agent.stable_id}</strong>
                  <span>{row.agent.platform || "-"} · v{row.agent.agent_version || "-"}</span>
                </div>
                <span className={`status-pill ${agentStatusTone(row)}`}>{agentStatusLabel(row)}</span>
              </div>
              <div className="printer-card-grid">
                <Metric label="Pareado em" value={row.agent.paired_at} />
                <Metric label="Último contato" value={row.agent.last_seen_at ?? "-"} />
                <Metric label="Credencial" value={row.agent.credential_prefix} />
                <Metric label="Online agora" value={isAgentHeartbeatRecent(row.agent) ? "sim" : "não"} />
              </div>
              <div className="printer-card-actions">
                <button type="button" className="secondary-button" onClick={() => openAgentDetail(row.printer.id, row.agent.id)} disabled={loading}>
                  <Radio size={15} />
                  Detalhar
                </button>
                {row.agent.status === "active" ? (
                  <button type="button" className="secondary-button" onClick={() => void revokeAgent(row)} disabled={loading}>
                    <Trash2 size={15} />
                    Revogar agente
                  </button>
                ) : null}
                {row.agent.status === "revoked" ? (
                  <button type="button" className="secondary-button" onClick={() => void removeAgent(row)} disabled={loading}>
                    <Trash2 size={15} />
                    Remover agente
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </article> : null}

      {embeddedPrinterContext ? <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Tokens de instalação</h2>
            <p className="muted">Token instala ou reinstala um agente. Remover token não remove agente já pareado.</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void createPairingToken()} disabled={!selectedPrinterId || loading}>
            <KeyRound size={15} />
            Gerar token
          </button>
        </div>
        {!selectedPrinterId ? <p className="muted">Selecione uma impressora para gerar instalação.</p> : null}
        <div className="overview-strip">
          <Badge icon={Server} label="Impressora" value={selectedPrinter?.name ?? "-"} />
          <Badge icon={Radio} label="Agentes pareados" value={agentInstallStatus?.active_agents ?? selectedAgentRows.length} />
          <Badge icon={CheckCircle2} label="Online agora" value={selectedAgentRows.filter((row) => isAgentHeartbeatRecent(row.agent)).length} />
          <Badge icon={Gauge} label="Token ativo" value={activeTokens.length ? activeTokens[0].token_prefix : "-"} />
        </div>
        {agentInstallStatus ? <p className="muted">{agentInstallStatus.diagnostic}</p> : null}
        {hasActivePairedAgent ? (
          <div className="auth-step">
            <AlertTriangle size={16} />
            <span>
              {hasOfflineActivePairedAgent
                ? "Esta impressora já tem um agente pareado sem heartbeat recente. Para reinstalar no mesmo host, revogue e remova o agente antigo antes de gerar novo comando."
                : "Esta impressora já tem um agente pareado. Para reinstalar no mesmo host, revogue/remova o agente antigo antes de gerar novo comando."}
            </span>
          </div>
        ) : null}

        {agentInstallPlan ? (
          <div className="agent-install-box">
            <div className="printer-card-header">
              <div>
                <strong>Comandos de instalação</strong>
                <span>Token {agentInstallPlan.token_prefix} expira em {formatDateTime(agentInstallPlan.expires_at)}.</span>
              </div>
              <button type="button" className="secondary-button" onClick={() => setAgentInstallPlan(null)}>
                Ocultar
              </button>
            </div>
            <CommandBlock
              Copy={Copy}
              label="Preflight sem instalação"
              command={agentInstallPlan.preflight_command}
              onCopy={copyCommand}
            />
            <CommandBlock
              Copy={Copy}
              label="Instalar e iniciar serviço"
              command={agentInstallPlan.install_command}
              onCopy={copyCommand}
            />
            <CommandBlock
              Copy={Copy}
              label="Uninstall preservando dados"
              command={agentInstallPlan.uninstall_command}
              onCopy={copyCommand}
            />
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

function CommandBlock({
  Copy,
  label,
  command,
  onCopy,
}: {
  Copy: AgentsScreenProps["Copy"];
  label: string;
  command: string;
  onCopy: (command: string) => Promise<void>;
}) {
  return (
    <div className="agent-command-block">
      <div className="agent-command-header">
        <span>{label}</span>
        <button type="button" className="icon-button" title={`Copiar ${label}`} aria-label={`Copiar ${label}`} onClick={() => void onCopy(command)}>
          <Copy size={15} />
        </button>
      </div>
      <textarea readOnly value={command} />
    </div>
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
            <span>{token.status} · expira {formatDateTime(token.expires_at)}</span>
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

function buildSelectedAgentRows(printer: PrinterRecord | null | undefined, overview: AgentPairingOverview | null): AgentFleetRow[] {
  if (!printer || !overview) {
    return [];
  }
  return overview.agents
    .filter((agent) => agent.status !== "removed")
    .map((agent) => ({ agent, overview, printer }))
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

function shouldShowAgentRefresh(row: AgentFleetRow) {
  return row.printer.cloud_status !== "online" || row.agent.status !== "active";
}

function isAgentHeartbeatRecent(agent: PrinterAgentRecord) {
  if (agent.status !== "active" || !agent.last_seen_at) {
    return false;
  }
  const normalized = agent.last_seen_at.includes("T")
    ? agent.last_seen_at
    : `${agent.last_seen_at.replace(" ", "T")}Z`;
  const timestamp = Date.parse(normalized);
  if (Number.isNaN(timestamp)) {
    return false;
  }
  return Date.now() - timestamp <= AGENT_ONLINE_WINDOW_SECONDS * 1000;
}

function agentVersionLabel(version: string | null | undefined, expectedVersion: string) {
  if (!version) return "-";
  if (expectedVersion !== "-" && version !== expectedVersion) {
    return `${version} -> ${expectedVersion}`;
  }
  return version;
}

function canRequestSystemAgentUpdate(row: AgentFleetRow) {
  return row.agent.status === "active" && Boolean(row.agent.agent_version);
}

function agentUpdateButtonLabel(row: AgentFleetRow, context: "row" | "detail" = "row") {
  void row;
  return context === "detail" ? "Atualizar agente" : "Atualizar";
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
