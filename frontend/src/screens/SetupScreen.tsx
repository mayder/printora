import { Metric } from "../components/common";
import type { SetupCanPlanStep, SetupPlanStep, SetupRunStatus } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type SetupScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "ClipboardCheck"
  | "History"
  | "Radio"
  | "RefreshCw"
  | "Server"
  | "ShieldCheck"
  | "setupAuthMethod"
  | "setupBusy"
  | "setupCanApplyResult"
  | "setupCanBitrate"
  | "setupCanConfirmation"
  | "setupCanHistory"
  | "setupCanInterfaceName"
  | "setupCanPlan"
  | "setupCanPreflight"
  | "setupHistory"
  | "setupHost"
  | "setupKeyPath"
  | "setupPlan"
  | "setupPort"
  | "setupPreflight"
  | "setupTimeoutSeconds"
  | "setupUsername"
  | "runSetupPlan"
  | "runSetupCanApply"
  | "runSetupCanPlan"
  | "runSetupCanPreflight"
  | "runSetupPreflight"
  | "setSetupAuthMethod"
  | "setSetupCanBitrate"
  | "setSetupCanConfirmation"
  | "setSetupCanInterfaceName"
  | "setSetupHost"
  | "setSetupKeyPath"
  | "setSetupPort"
  | "setSetupTimeoutSeconds"
  | "setSetupUsername"
>;

export function SetupScreen(props: SetupScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    ClipboardCheck,
    History,
    Radio,
    RefreshCw,
    Server,
    ShieldCheck,
    runSetupPlan,
    runSetupCanApply,
    runSetupCanPlan,
    runSetupCanPreflight,
    runSetupPreflight,
    setSetupAuthMethod,
    setSetupCanBitrate,
    setSetupCanConfirmation,
    setSetupCanInterfaceName,
    setSetupHost,
    setSetupKeyPath,
    setSetupPort,
    setSetupTimeoutSeconds,
    setSetupUsername,
    setupAuthMethod,
    setupBusy,
    setupCanApplyResult,
    setupCanBitrate,
    setupCanConfirmation,
    setupCanHistory,
    setupCanInterfaceName,
    setupCanPlan,
    setupCanPreflight,
    setupHistory,
    setupHost,
    setupKeyPath,
    setupPlan,
    setupPort,
    setupPreflight,
    setupTimeoutSeconds,
    setupUsername,
  } = props;

  const canRun = Boolean(setupHost.trim() && setupUsername.trim() && setupPort > 0);

  return (
    <>
      <article className="panel wide setup-hero-panel">
        <div className="panel-header-row">
          <div>
            <h2>Setup do Zero</h2>
            <p>O fluxo começa quando a Pi já tem Linux, rede e SSH ativo. Placa virgem precisa de mídia de boot antes do SSH.</p>
          </div>
          <span className="setup-status setup-status-info">PKG-35</span>
        </div>
        <div className="setup-boundary-grid">
          <Metric label="Fase atual" value="SSH + CAN" />
          <Metric label="Modo" value="Read-only / dry-run" />
          <Metric label="Apply CAN" value="Gateado" />
        </div>
      </article>

      <article className="panel setup-connection-panel">
        <div className="panel-header-row">
          <div>
            <h2>Acesso SSH</h2>
            <p>Use chave ou agente SSH. Senhas e chaves privadas não são armazenadas.</p>
          </div>
          <Server size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Host/IP
            <input value={setupHost} onChange={(event) => setSetupHost(event.target.value)} placeholder="btt-pi.local" />
          </label>
          <label>
            Porta
            <input type="number" min={1} max={65535} value={setupPort} onChange={(event) => setSetupPort(Number(event.target.value))} />
          </label>
          <label>
            Usuário
            <input value={setupUsername} onChange={(event) => setSetupUsername(event.target.value)} placeholder="pi" />
          </label>
          <label>
            Timeout
            <input type="number" min={2} max={60} value={setupTimeoutSeconds} onChange={(event) => setSetupTimeoutSeconds(Number(event.target.value))} />
          </label>
          <label>
            Autenticação
            <select value={setupAuthMethod} onChange={(event) => setSetupAuthMethod(event.target.value as "agent" | "key_path")}>
              <option value="agent">SSH agent / chave padrão</option>
              <option value="key_path">Caminho de chave no host local</option>
            </select>
          </label>
          {setupAuthMethod === "key_path" ? (
            <label>
              Caminho da chave
              <input value={setupKeyPath} onChange={(event) => setSetupKeyPath(event.target.value)} placeholder="~/.ssh/id_ed25519" />
            </label>
          ) : null}
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupPreflight()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Preflight SSH
          </button>
          <button type="button" className="primary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupPlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Gerar plano
          </button>
        </div>
      </article>

      <article className="panel setup-result-panel">
        <div className="panel-header-row">
          <div>
            <h2>Preflight</h2>
            <p>{setupPreflight?.summary ?? "Nenhum preflight executado."}</p>
          </div>
          {setupPreflight ? <StatusBadge status={setupPreflight.status} /> : null}
        </div>
        {setupPreflight ? (
          <div className="setup-check-list">
            {setupPreflight.checks.map((check) => (
              <div key={check.key} className={`setup-check setup-${check.status}`}>
                {check.status === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                <div>
                  <strong>{check.label}</strong>
                  <span>{check.detail}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">Informe o SSH da Pi e execute o preflight.</div>
        )}
      </article>

      <article className="panel wide setup-plan-panel">
        <div className="panel-header-row">
          <div>
            <h2>Plano dry-run</h2>
            <p>{setupPlan?.summary ?? "O plano aparece depois do preflight completo."}</p>
          </div>
          {setupPlan ? <StatusBadge status={setupPlan.status} /> : <RefreshCw size={18} />}
        </div>
        {setupPlan?.blocked_reasons.length ? (
          <div className="action-result warning">
            <strong>Bloqueios</strong>
            <span>{setupPlan.blocked_reasons.join(" ")}</span>
          </div>
        ) : null}
        {setupPlan ? (
          <div className="setup-step-list">
            {setupPlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
          </div>
        ) : (
          <div className="empty-state">Nenhum comando será executado nesta tela. O pacote gera plano revisável.</div>
        )}
      </article>

      <article className="panel wide setup-can-panel">
        <div className="panel-header-row">
          <div>
            <h2>CAN/U2C</h2>
            <p>Diagnóstico remoto de U2C, módulos CAN, interface can0, bitrate, UUIDs e plano de configuração.</p>
          </div>
          <Radio size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Interface
            <input value={setupCanInterfaceName} onChange={(event) => setSetupCanInterfaceName(event.target.value)} placeholder="can0" />
          </label>
          <label>
            Bitrate
            <input type="number" min={10000} max={5000000} step={10000} value={setupCanBitrate} onChange={(event) => setSetupCanBitrate(Number(event.target.value))} />
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupCanPreflight()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Diagnosticar CAN
          </button>
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupCanPlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Plano CAN
          </button>
        </div>
        {setupCanPreflight ? (
          <div className="setup-check-list setup-can-findings">
            {setupCanPreflight.findings.map((finding) => (
              <div key={finding.key} className={`setup-check setup-${finding.status === "blocked" ? "error" : finding.status}`}>
                {finding.status === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.detail}</span>
                  <small>{finding.action}</small>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">Execute o diagnóstico CAN depois de informar o SSH.</div>
        )}
        {setupCanPlan ? (
          <div className="setup-step-list">
            {setupCanPlan.blocked_reasons.length ? (
              <div className="action-result warning">
                <strong>Bloqueios CAN</strong>
                <span>{setupCanPlan.blocked_reasons.join(" ")}</span>
              </div>
            ) : null}
            {setupCanPlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
          </div>
        ) : null}
        <div className="setup-apply-box">
          <label>
            Confirmação para apply CAN
            <input value={setupCanConfirmation} onChange={(event) => setSetupCanConfirmation(event.target.value)} placeholder="CONFIGURAR CAN0" />
          </label>
          <button type="button" className="danger-button" disabled={!canRun || setupBusy || setupCanConfirmation !== "CONFIGURAR CAN0"} onClick={() => void runSetupCanApply()}>
            <AlertTriangle className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Aplicar CAN
          </button>
          <p>O backend ainda exige <code>PRINTORA_CAN_SETUP_MODE=remote</code>; sem isso a tentativa fica registrada como bloqueada.</p>
        </div>
        {setupCanApplyResult ? (
          <div className={`action-result ${setupCanApplyResult.status === "ok" ? "success" : "warning"}`}>
            <strong>{setupCanApplyResult.summary}</strong>
            <span>{setupCanApplyResult.blocked_reasons.length ? setupCanApplyResult.blocked_reasons.join(" ") : "Resultado registrado no histórico."}</span>
          </div>
        ) : null}
      </article>

      <article className="panel wide setup-history-panel">
        <div className="panel-header-row">
          <div>
            <h2>Histórico</h2>
            <p>Registros locais sem senha, token ou chave privada.</p>
          </div>
          <History size={18} />
        </div>
        {setupHistory.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Tipo</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{run.created_at}</td>
                    <td>{run.run_type === "plan" ? "Plano" : "Preflight"}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">Sem histórico de setup.</div>
        )}
        {setupCanHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>CAN</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupCanHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{run.created_at}</td>
                    <td>{run.run_type} · {run.interface_name} · {run.bitrate}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status === "blocked" ? "error" : run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </article>
    </>
  );
}

function StatusBadge({ status }: { status: SetupRunStatus }) {
  const tone = status === "ok" ? "success" : status === "warning" ? "warning" : "danger";
  const label = status === "ok" ? "OK" : status === "warning" ? "Atenção" : "Erro";
  return <span className={`setup-status setup-status-${tone}`}>{label}</span>;
}

function SetupStepCard({ step }: { step: SetupPlanStep | SetupCanPlanStep }) {
  return (
    <section className={`setup-step setup-step-${step.status}`}>
      <div className="setup-step-header">
        <div>
          <strong>{step.title}</strong>
          <span>{step.detail}</span>
        </div>
        <span className={`setup-status setup-status-${step.status === "ready" ? "success" : step.status === "blocked" ? "danger" : "warning"}`}>{step.status}</span>
      </div>
      {step.commands.length ? (
        <div className="setup-command-list">
          {step.commands.map((command) => (
            <div key={`${step.key}-${command.command}`} className={`setup-command setup-command-${command.risk}`}>
              <code>{command.command}</code>
              <span>{command.reason}</span>
            </div>
          ))}
        </div>
      ) : null}
      {step.rollback ? <p className="setup-rollback">Rollback: {step.rollback}</p> : null}
    </section>
  );
}
