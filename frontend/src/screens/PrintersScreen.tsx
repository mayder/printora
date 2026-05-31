import { Badge, Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type PrintersScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "Camera"
  | "CheckCircle2"
  | "ClipboardCheck"
  | "Database"
  | "FileText"
  | "Gauge"
  | "History"
  | "KeyRound"
  | "Plus"
  | "Printer"
  | "Radio"
  | "Server"
  | "Settings"
  | "ShieldAlert"
  | "agentInstallPlan"
  | "agentInstallStatus"
  | "agentSupport"
  | "agentSupportBundle"
  | "audit"
  | "cancelRemoteOperationJob"
  | "captureSnapshot"
  | "createAgentInstallPlan"
  | "createAgentDoctorJob"
  | "createPairingToken"
  | "createRemoteOperationPreflight"
  | "createdPairingToken"
  | "executeRemoteOperation"
  | "formatDecision"
  | "formatSshStatus"
  | "health"
  | "loadSelectedPrinterStatus"
  | "loadAgentInstallStatus"
  | "loadAgentSupport"
  | "loadAgentSupportBundle"
  | "loading"
  | "openCreatePrinterModal"
  | "openEditPrinterModal"
  | "pairingOverview"
  | "printers"
  | "revokePairingToken"
  | "revokePrinterAgent"
  | "rotatePrinterAgent"
  | "rotatedAgentCredential"
  | "remoteOperationConfirmation"
  | "remoteOperationExecution"
  | "remoteOperationPreflight"
  | "remoteOperations"
  | "setCreatedPairingToken"
  | "setAgentInstallPlan"
  | "setAgentSupportBundle"
  | "setRemoteOperationConfirmation"
  | "setRotatedAgentCredential"
  | "selectPrinter"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "snapshots"
  | "status"
>;

export function PrintersScreen(props: PrintersScreenProps) {
  const {
    AlertTriangle,
    Camera,
    CheckCircle2,
    ClipboardCheck,
    Database,
    FileText,
    Gauge,
    History,
    KeyRound,
    Plus,
    Printer,
    Radio,
    Server,
    Settings,
    ShieldAlert,
    agentInstallPlan,
    agentInstallStatus,
    agentSupport,
    agentSupportBundle,
    audit,
    cancelRemoteOperationJob,
    captureSnapshot,
    createAgentInstallPlan,
    createAgentDoctorJob,
    createPairingToken,
    createRemoteOperationPreflight,
    createdPairingToken,
    executeRemoteOperation,
    formatDecision,
    formatSshStatus,
    health,
    loadSelectedPrinterStatus,
    loadAgentInstallStatus,
    loadAgentSupport,
    loadAgentSupportBundle,
    loading,
    openCreatePrinterModal,
    openEditPrinterModal,
    pairingOverview,
    printers,
    revokePairingToken,
    revokePrinterAgent,
    rotatePrinterAgent,
    rotatedAgentCredential,
    remoteOperationConfirmation,
    remoteOperationExecution,
    remoteOperationPreflight,
    remoteOperations,
    setCreatedPairingToken,
    setAgentInstallPlan,
    setAgentSupportBundle,
    setRemoteOperationConfirmation,
    setRotatedAgentCredential,
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

        <article className="panel wide panel-section panel-printers">
          <div className="panel-heading">
            <div>
              <h2>Operação remota segura</h2>
              <p className="muted">Ações mutáveis via agente com preflight, confirmação forte, expiração e rollback visível.</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId && void loadAgentInstallStatus(selectedPrinterId)} disabled={!selectedPrinterId || loading}>
              <Radio size={15} />
              Atualizar agente
            </button>
          </div>
          {!selectedPrinterId ? <p className="muted">Selecione uma impressora para operar remotamente.</p> : null}
          <div className="overview-strip">
            <Badge icon={ShieldAlert} label="Modo" value={remoteOperations?.safe_mode ?? "-"} />
            <Badge icon={Gauge} label="Ações" value={remoteOperations?.actions.length ?? 0} />
            <Badge icon={History} label="Jobs recentes" value={remoteOperations?.recent_jobs.length ?? 0} />
            <Badge icon={Radio} label="Agente" value={agentInstallStatus?.ready ? "pronto" : "pendente"} />
          </div>
          <div className="printer-dashboard">
            {(remoteOperations?.actions ?? []).slice(0, 6).map((action) => (
              <div key={action.action_id} className="printer-card">
                <div className="printer-card-header">
                  <div>
                    <strong>{action.label}</strong>
                    <span>{action.criticality} · {action.risk}</span>
                  </div>
                  <span className="status-pill">{action.blocks_when_printing ? "bloqueia imprimindo" : "avaliar"}</span>
                </div>
                <div className="auth-list">
                  {action.rollback_plan.map((step) => (
                    <span key={step}>{step}</span>
                  ))}
                </div>
                <div className="printer-card-actions">
                  <button type="button" className="secondary-button" onClick={() => void createRemoteOperationPreflight(action.action_id)} disabled={!selectedPrinterId || loading || !agentInstallStatus?.ready}>
                    <ClipboardCheck size={15} />
                    Preflight
                  </button>
                </div>
              </div>
            ))}
          </div>
          {remoteOperationPreflight ? (
            <div className="agent-install-box">
              <div className="printer-card-header">
                <div>
                  <strong>Preflight remoto #{remoteOperationPreflight.id}</strong>
                  <span>{remoteOperationPreflight.status} · expira {String(remoteOperationPreflight.payload.expires_at ?? "-")}</span>
                </div>
                {remoteOperationPreflight.status === "pending" ? (
                  <button type="button" className="secondary-button" onClick={() => void cancelRemoteOperationJob(remoteOperationPreflight.id)} disabled={loading}>
                    Cancelar
                  </button>
                ) : null}
              </div>
              <label>
                Frase exigida
                <textarea readOnly value={String(remoteOperationPreflight.payload.confirmation_phrase ?? "")} />
              </label>
              <label>
                Confirmação
                <input value={remoteOperationConfirmation} onChange={(event) => setRemoteOperationConfirmation(event.target.value)} placeholder="Digite a frase exata após o preflight aprovado" />
              </label>
              <button type="button" className="primary-button" onClick={() => void executeRemoteOperation()} disabled={loading || remoteOperationPreflight.status !== "succeeded"}>
                <ShieldAlert size={16} />
                Criar execução remota
              </button>
            </div>
          ) : null}
          {remoteOperationExecution ? (
            <div className="auth-step">
              <div>
                <strong>Execução remota #{remoteOperationExecution.id}</strong>
                <p className="muted">{remoteOperationExecution.status} · {remoteOperationExecution.job_type}</p>
              </div>
              {remoteOperationExecution.status === "pending" ? (
                <button type="button" className="secondary-button" onClick={() => void cancelRemoteOperationJob(remoteOperationExecution.id)} disabled={loading}>
                  Cancelar
                </button>
              ) : null}
            </div>
          ) : null}
        </article>

        <article className="panel wide panel-section panel-printers">
          <div className="panel-heading">
            <div>
              <h2>Pareamento do agente</h2>
              <p className="muted">Token curto para instalar o agente sem expor credencial permanente.</p>
            </div>
            <button type="button" className="primary-button" onClick={() => void createPairingToken()} disabled={!selectedPrinterId || loading}>
              <KeyRound size={16} />
              Gerar token
            </button>
          </div>
          {!selectedPrinterId ? <p className="muted">Selecione uma impressora para gerenciar o pareamento.</p> : null}
          {createdPairingToken ? (
            <div className="auth-step">
              <div>
                <strong>Token criado</strong>
                <p className="muted">Copie agora. Ele expira em {createdPairingToken.expires_at} e não aparece novamente.</p>
                <code>{createdPairingToken.token}</code>
              </div>
              <button type="button" className="secondary-button" onClick={() => setCreatedPairingToken(null)}>
                Ocultar
              </button>
            </div>
          ) : null}
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
              </div>
              <div className="auth-list">
                {(pairingOverview?.pairing_tokens ?? []).map((token) => (
                  <div key={token.id}>
                    <strong>{token.token_prefix}</strong>
                    <span>{token.status} · expira {token.expires_at}</span>
                    {token.status === "active" ? (
                      <button type="button" className="secondary-button" onClick={() => void revokePairingToken(token.id)} disabled={loading}>
                        Revogar
                      </button>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
            <div className="printer-card">
              <div className="printer-card-header">
                <div>
                  <strong>Agentes</strong>
                  <span>{pairingOverview?.agents.length ?? 0} registros</span>
                </div>
              </div>
              <div className="auth-list">
                {(pairingOverview?.agents ?? []).map((agent) => (
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
        </article>

        <article className="panel wide panel-section panel-printers">
          <div className="panel-heading">
            <div>
              <h2>Instalação assistida do agente</h2>
              <p className="muted">Comando por impressora, preflight local e confirmação de heartbeat.</p>
            </div>
            <div className="printer-card-actions">
              <button type="button" className="secondary-button" onClick={() => void loadAgentInstallStatus()} disabled={!selectedPrinterId || loading}>
                <Radio size={15} />
                Validar
              </button>
              <button type="button" className="primary-button" onClick={() => void createAgentInstallPlan()} disabled={!selectedPrinterId || loading}>
                <ClipboardCheck size={16} />
                Gerar instalação
              </button>
            </div>
          </div>
          {!selectedPrinterId ? <p className="muted">Selecione uma impressora para gerar o instalador.</p> : null}
          {agentInstallStatus ? (
            <div className="overview-strip">
              <Badge icon={CheckCircle2} label="Instalação" value={agentInstallStatus.ready ? "validada" : "pendente"} />
              <Badge icon={Server} label="Agentes ativos" value={agentInstallStatus.active_agents} />
              <Badge icon={Gauge} label="Versão esperada" value={agentInstallStatus.expected_agent_version} />
              <Badge icon={Radio} label="Último heartbeat" value={agentInstallStatus.latest_last_seen_at ?? "-"} />
            </div>
          ) : null}
          {agentInstallStatus ? <p className="muted">{agentInstallStatus.diagnostic}</p> : null}
          {agentInstallPlan ? (
            <div className="agent-install-box">
              <div className="printer-card-header">
                <div>
                  <strong>Comandos gerados</strong>
                  <span>Token {agentInstallPlan.token_prefix} expira em {agentInstallPlan.expires_at}. O token será consumido uma única vez.</span>
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
        </article>

        <article className="panel wide panel-section panel-printers">
          <div className="panel-heading">
            <div>
              <h2>Saúde e suporte do agente</h2>
              <p className="muted">Diagnóstico operacional para diferenciar agente, API, credencial, Moonraker, Klipper, versão e fila.</p>
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
          {!selectedPrinterId ? <p className="muted">Selecione uma impressora para ver suporte do agente.</p> : null}
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
          {agentSupport?.latest_doctor ? (
            <div className="auth-step">
              <div>
                <strong>Último doctor remoto</strong>
                <p className="muted">Job #{agentSupport.latest_doctor.id} · {agentSupport.latest_doctor.status} · {agentSupport.latest_doctor.finished_at ?? agentSupport.latest_doctor.created_at}</p>
              </div>
            </div>
          ) : null}
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
