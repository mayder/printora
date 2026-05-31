import * as React from "react";
import { Badge, Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type AgentsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "ClipboardCheck"
  | "FileText"
  | "Gauge"
  | "History"
  | "KeyRound"
  | "Radio"
  | "Server"
  | "ShieldAlert"
  | "agentInstallPlan"
  | "agentInstallStatus"
  | "agentSupport"
  | "agentSupportBundle"
  | "createAgentInstallPlan"
  | "createAgentDoctorJob"
  | "createPairingToken"
  | "createdPairingToken"
  | "loadAgentInstallStatus"
  | "loadAgentSupport"
  | "loadAgentSupportBundle"
  | "loading"
  | "pairingOverview"
  | "removePairingToken"
  | "removePrinterAgent"
  | "revokePairingToken"
  | "revokePrinterAgent"
  | "rotatePrinterAgent"
  | "rotatedAgentCredential"
  | "setAgentInstallPlan"
  | "setAgentSupportBundle"
  | "setRotatedAgentCredential"
  | "showToast"
  | "selectedPrinter"
  | "selectedPrinterId"
>;

export function AgentsScreen(props: AgentsScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    ClipboardCheck,
    FileText,
    Gauge,
    History,
    KeyRound,
    Radio,
    Server,
    ShieldAlert,
    agentInstallPlan,
    agentInstallStatus,
    agentSupport,
    agentSupportBundle,
    createAgentInstallPlan,
    createAgentDoctorJob,
    createPairingToken,
    createdPairingToken,
    loadAgentInstallStatus,
    loadAgentSupport,
    loadAgentSupportBundle,
    loading,
    pairingOverview,
    removePairingToken,
    removePrinterAgent,
    revokePairingToken,
    revokePrinterAgent,
    rotatePrinterAgent,
    rotatedAgentCredential,
    setAgentInstallPlan,
    setAgentSupportBundle,
    setRotatedAgentCredential,
    showToast,
    selectedPrinter,
    selectedPrinterId,
  } = props;

  const agents = pairingOverview?.agents ?? [];
  const activeAgents = agents.filter((agent) => agent.status !== "revoked");
  const revokedAgents = agents.filter((agent) => agent.status === "revoked");
  const latestToastTokenId = React.useRef<number | null>(null);

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

  return (
    <>
      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Agente da impressora</h2>
            <p className="muted">Selecione a impressora, gere o instalador e copie o comando pronto com token curto.</p>
          </div>
          <button type="button" className="primary-button" onClick={() => void createAgentInstallPlan()} disabled={!selectedPrinterId || loading}>
            <ClipboardCheck size={16} />
            Gerar instalação
          </button>
        </div>
        {!selectedPrinterId ? <p className="muted">Selecione uma impressora no topo para cadastrar o agente.</p> : null}
        <div className="overview-strip">
          <Badge icon={Server} label="Impressora" value={selectedPrinter?.name ?? "-"} />
          <Badge icon={CheckCircle2} label="Instalação" value={agentInstallStatus?.ready ? "validada" : "pendente"} />
          <Badge icon={Radio} label="Agentes ativos" value={agentInstallStatus?.active_agents ?? 0} />
          <Badge icon={Gauge} label="Versão esperada" value={agentInstallStatus?.expected_agent_version ?? "-"} />
        </div>
        {agentInstallStatus ? <p className="muted">{agentInstallStatus.diagnostic}</p> : null}
        <div className="printer-card-actions">
          <button type="button" className="secondary-button" onClick={() => void loadAgentInstallStatus()} disabled={!selectedPrinterId || loading}>
            <Radio size={15} />
            Validar instalação
          </button>
          <button type="button" className="secondary-button" onClick={() => void createPairingToken()} disabled={!selectedPrinterId || loading}>
            <KeyRound size={15} />
            Gerar token avulso
          </button>
        </div>
      </article>

      {agentInstallPlan ? (
        <article className="panel wide panel-section panel-agents">
          <div className="panel-heading">
            <div>
              <h2>Comandos de instalação</h2>
              <p className="muted">Token {agentInstallPlan.token_prefix} expira em {agentInstallPlan.expires_at} e será consumido uma única vez.</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => setAgentInstallPlan(null)}>
              Ocultar
            </button>
          </div>
          <div className="agent-install-box">
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
        </article>
      ) : null}

      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Tokens e agentes vinculados</h2>
            <p className="muted">Tokens aparecem uma vez; agentes pareados ficam listados por status e último contato.</p>
          </div>
        </div>
        {rotatedAgentCredential ? (
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
        ) : null}
        <div className="printer-dashboard">
          <div className="printer-card">
            <div className="printer-card-header">
              <div>
                <strong>Tokens</strong>
                <span>{pairingOverview?.pairing_tokens.length ?? 0} registros</span>
              </div>
              <button type="button" className="secondary-button" onClick={() => void createPairingToken()} disabled={!selectedPrinterId || loading}>
                <KeyRound size={15} />
                Gerar token
              </button>
            </div>
            <div className="auth-list">
              {(pairingOverview?.pairing_tokens ?? []).map((token) => (
                <div key={token.id}>
                  <strong>{token.token_prefix}</strong>
                  <span>{token.status} · expira {token.expires_at}</span>
                  {token.status === "active" ? (
                    <>
                      {createdPairingToken?.id === token.id ? (
                        <button type="button" className="secondary-button" onClick={() => void copyToken(createdPairingToken.token)} disabled={loading}>
                          Copiar
                        </button>
                      ) : null}
                      <button type="button" className="secondary-button" onClick={() => void revokePairingToken(token.id)} disabled={loading}>
                        Revogar
                      </button>
                    </>
                  ) : (
                    <button type="button" className="secondary-button" onClick={() => void removePairingToken(token.id)} disabled={loading}>
                      Remover
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="printer-card">
            <div className="printer-card-header">
              <div>
                <strong>Agentes ativos</strong>
                <span>{activeAgents.length} registros</span>
              </div>
            </div>
            <div className="auth-list">
              {activeAgents.length === 0 ? <span className="muted">Nenhum agente ativo pareado nesta impressora.</span> : null}
              {activeAgents.map((agent) => (
                <div key={agent.id}>
                  <strong>{agent.stable_id}</strong>
                  <span>{agent.status} · {agent.platform || "-"} · último contato {agent.last_seen_at || "-"}</span>
                  <button type="button" className="secondary-button" onClick={() => void rotatePrinterAgent(agent.id)} disabled={loading || agent.status === "revoked"}>
                    Rotacionar
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void revokePrinterAgent(agent.id)} disabled={loading || agent.status === "revoked"}>
                    Revogar
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
        {revokedAgents.length ? (
          <div className="auth-step">
            <div>
              <strong>Acessos removidos</strong>
              <p className="muted">Mantidos apenas para auditoria. Eles não conseguem mais comunicar com a API.</p>
              <div className="auth-list">
                {revokedAgents.map((agent) => (
                  <div key={agent.id}>
                    <span>{agent.stable_id} · revogado · último contato {agent.last_seen_at || "-"}</span>
                    <button type="button" className="secondary-button" onClick={() => void removePrinterAgent(agent.id)} disabled={loading}>
                      Remover
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </article>

      <article className="panel wide panel-section panel-agents">
        <div className="panel-heading">
          <div>
            <h2>Saúde e suporte</h2>
            <p className="muted">Diagnóstico para diferenciar agente, API, credencial, Moonraker, Klipper, versão e fila.</p>
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
      </article>
    </>
  );
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
