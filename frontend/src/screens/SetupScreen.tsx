import { Metric } from "../components/common";
import type { SetupCanPlanStep, SetupFirmwarePlanStep, SetupFlashPlanStep, SetupPlanStep, SetupRunStatus } from "../types";
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
  | "Zap"
  | "setupAuthMethod"
  | "setupBusy"
  | "setupCanApplyResult"
  | "setupCanBitrate"
  | "setupCanConfirmation"
  | "setupCanHistory"
  | "setupCanInterfaceName"
  | "setupCanPlan"
  | "setupCanPreflight"
  | "setupFirmwareBoardName"
  | "setupFirmwareBoardRole"
  | "setupFirmwareBuildResult"
  | "setupFirmwareConfirmation"
  | "setupFirmwareHistory"
  | "setupFirmwareKlipperPath"
  | "setupFirmwareOutputRoot"
  | "setupFirmwarePlan"
  | "setupFirmwarePresetId"
  | "setupFirmwareVariantConfirmed"
  | "setupFlashArtifactPath"
  | "setupFlashChecklistConfirmed"
  | "setupFlashConfirmation"
  | "setupFlashExecuteResult"
  | "setupFlashExpectedUuid"
  | "setupFlashHistory"
  | "setupFlashMethod"
  | "setupFlashPlan"
  | "setupFlashPreflight"
  | "setupFlashPreviousBinaryPath"
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
  | "runSetupFirmwareBuild"
  | "runSetupFirmwarePlan"
  | "runSetupFlashExecute"
  | "runSetupFlashPlan"
  | "runSetupFlashPreflight"
  | "runSetupPreflight"
  | "setSetupAuthMethod"
  | "setSetupCanBitrate"
  | "setSetupCanConfirmation"
  | "setSetupCanInterfaceName"
  | "setSetupFirmwareBoardName"
  | "setSetupFirmwareBoardRole"
  | "setSetupFirmwareConfirmation"
  | "setSetupFirmwareKlipperPath"
  | "setSetupFirmwareOutputRoot"
  | "setSetupFirmwarePresetId"
  | "setSetupFirmwareVariantConfirmed"
  | "setSetupFlashArtifactPath"
  | "setSetupFlashChecklistConfirmed"
  | "setSetupFlashConfirmation"
  | "setSetupFlashExpectedUuid"
  | "setSetupFlashMethod"
  | "setSetupFlashPreviousBinaryPath"
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
    Zap,
    runSetupPlan,
    runSetupCanApply,
    runSetupCanPlan,
    runSetupCanPreflight,
    runSetupFirmwareBuild,
    runSetupFirmwarePlan,
    runSetupFlashExecute,
    runSetupFlashPlan,
    runSetupFlashPreflight,
    runSetupPreflight,
    setSetupAuthMethod,
    setSetupCanBitrate,
    setSetupCanConfirmation,
    setSetupCanInterfaceName,
    setSetupFirmwareBoardName,
    setSetupFirmwareBoardRole,
    setSetupFirmwareConfirmation,
    setSetupFirmwareKlipperPath,
    setSetupFirmwareOutputRoot,
    setSetupFirmwarePresetId,
    setSetupFirmwareVariantConfirmed,
    setSetupFlashArtifactPath,
    setSetupFlashChecklistConfirmed,
    setSetupFlashConfirmation,
    setSetupFlashExpectedUuid,
    setSetupFlashMethod,
    setSetupFlashPreviousBinaryPath,
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
    setupFirmwareBoardName,
    setupFirmwareBoardRole,
    setupFirmwareBuildResult,
    setupFirmwareConfirmation,
    setupFirmwareHistory,
    setupFirmwareKlipperPath,
    setupFirmwareOutputRoot,
    setupFirmwarePlan,
    setupFirmwarePresetId,
    setupFirmwareVariantConfirmed,
    setupFlashArtifactPath,
    setupFlashChecklistConfirmed,
    setupFlashConfirmation,
    setupFlashExecuteResult,
    setupFlashExpectedUuid,
    setupFlashHistory,
    setupFlashMethod,
    setupFlashPlan,
    setupFlashPreflight,
    setupFlashPreviousBinaryPath,
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
          <span className="setup-status setup-status-info">PKG-36</span>
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

      <article className="panel wide setup-firmware-panel">
        <div className="panel-header-row">
          <div>
            <h2>Firmware remoto</h2>
            <p>Selecione a placa física, gere .config, planeje build remoto e compile sem flash.</p>
          </div>
          <Zap size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Preset
            <select value={setupFirmwarePresetId} onChange={(event) => setSetupFirmwarePresetId(event.target.value)}>
              <option value="btt_octopus_pro_h723_usb_can">BTT Octopus Pro H723</option>
              <option value="btt_ebb36_g0b1_can">BTT EBB36 v1.2/G0B1</option>
              <option value="btt_kraken_h723_usb_can">BTT Kraken H723</option>
              <option value="btt_manta_m8p_v2_h723_usb_can">BTT Manta M8P v2 H723</option>
              <option value="mellow_fly_sht36_v3_rp2040_can">Mellow Fly SHT36 v3</option>
            </select>
          </label>
          <label>
            Nome físico
            <input value={setupFirmwareBoardName} onChange={(event) => setSetupFirmwareBoardName(event.target.value)} placeholder="Octopus Pro H723" />
          </label>
          <label>
            Papel
            <select value={setupFirmwareBoardRole} onChange={(event) => setSetupFirmwareBoardRole(event.target.value as "mainboard" | "toolhead" | "can_adapter" | "unknown")}>
              <option value="mainboard">MCU principal</option>
              <option value="toolhead">Toolhead</option>
              <option value="can_adapter">Adaptador CAN</option>
              <option value="unknown">Outro</option>
            </select>
          </label>
          <label>
            Klipper remoto
            <input value={setupFirmwareKlipperPath} onChange={(event) => setSetupFirmwareKlipperPath(event.target.value)} placeholder="~/klipper" />
          </label>
          <label>
            Artefatos
            <input value={setupFirmwareOutputRoot} onChange={(event) => setSetupFirmwareOutputRoot(event.target.value)} placeholder="~/.local/share/printora/firmware-setup" />
          </label>
          <label className="setup-checkbox-label">
            <input type="checkbox" checked={setupFirmwareVariantConfirmed} onChange={(event) => setSetupFirmwareVariantConfirmed(event.target.checked)} />
            Variante física conferida
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFirmwarePlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Plano firmware
          </button>
        </div>
        {setupFirmwarePlan ? (
          <div className="setup-step-list">
            {setupFirmwarePlan.blocked_reasons.length ? (
              <div className="action-result warning">
                <strong>Bloqueios firmware</strong>
                <span>{setupFirmwarePlan.blocked_reasons.join(" ")}</span>
              </div>
            ) : null}
            <div className="setup-artifact-summary">
              <Metric label="Config SHA" value={setupFirmwarePlan.config_sha256.slice(0, 12)} />
              <Metric label="Artefatos" value={setupFirmwarePlan.artifact_dir} />
              <Metric label="Binário" value={setupFirmwarePlan.expected_binary_path} />
            </div>
            {setupFirmwarePlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
          </div>
        ) : (
          <div className="empty-state">Confirme a variante física e gere o plano de firmware.</div>
        )}
        <div className="setup-apply-box">
          <label>
            Confirmação para build sem flash
            <input value={setupFirmwareConfirmation} onChange={(event) => setSetupFirmwareConfirmation(event.target.value)} placeholder="BUILD_FIRMWARE_NO_FLASH" />
          </label>
          <button type="button" className="danger-button" disabled={!canRun || setupBusy || setupFirmwareConfirmation !== "BUILD_FIRMWARE_NO_FLASH"} onClick={() => void runSetupFirmwareBuild()}>
            <AlertTriangle className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Build remoto
          </button>
          <p>O backend exige <code>PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote</code>; o build nunca executa flash.</p>
        </div>
        {setupFirmwareBuildResult ? (
          <div className={`action-result ${setupFirmwareBuildResult.status === "ok" ? "success" : "warning"}`}>
            <strong>{setupFirmwareBuildResult.summary}</strong>
            <span>{setupFirmwareBuildResult.blocked_reasons.length ? setupFirmwareBuildResult.blocked_reasons.join(" ") : setupFirmwareBuildResult.binary_path ?? "Artefato registrado."}</span>
          </div>
        ) : null}
      </article>

      <article className="panel wide setup-flash-panel">
        <div className="panel-header-row">
          <div>
            <h2>Flash supervisionado</h2>
            <p>Preflight crítico, plano revisável e execução CAN/Katapult com trava operacional.</p>
          </div>
          <AlertTriangle size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Método
            <select value={setupFlashMethod} onChange={(event) => setSetupFlashMethod(event.target.value as "can_katapult" | "usb_dfu" | "manual")}>
              <option value="can_katapult">CAN/Katapult</option>
              <option value="usb_dfu">USB/DFU (bloqueado)</option>
              <option value="manual">Manual (bloqueado)</option>
            </select>
          </label>
          <label>
            Artefato remoto
            <input value={setupFlashArtifactPath} onChange={(event) => setSetupFlashArtifactPath(event.target.value)} placeholder={setupFirmwareBuildResult?.binary_path ?? setupFirmwarePlan?.expected_binary_path ?? "~/.local/share/printora/firmware-setup/ebb36/klipper.bin"} />
          </label>
          <label>
            UUID esperado
            <input value={setupFlashExpectedUuid} onChange={(event) => setSetupFlashExpectedUuid(event.target.value)} placeholder="0123456789ab" />
          </label>
          <label>
            Binário anterior
            <input value={setupFlashPreviousBinaryPath} onChange={(event) => setSetupFlashPreviousBinaryPath(event.target.value)} placeholder="opcional: caminho do firmware anterior" />
          </label>
          <label className="setup-checkbox-label">
            <input type="checkbox" checked={setupFlashChecklistConfirmed} onChange={(event) => setSetupFlashChecklistConfirmed(event.target.checked)} />
            Checklist físico conferido
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFlashPreflight()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Preflight flash
          </button>
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFlashPlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Plano flash
          </button>
        </div>
        {setupFlashPreflight ? (
          <div className="setup-check-list setup-can-findings">
            {setupFlashPreflight.findings.map((finding) => (
              <div key={finding.key} className={`setup-check setup-${finding.status === "blocked" || finding.status === "requires_recovery" ? "error" : finding.status}`}>
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
          <div className="empty-state">Use o artefato do build remoto e execute o preflight antes do flash.</div>
        )}
        {setupFlashPlan ? (
          <div className="setup-step-list">
            {setupFlashPlan.blocked_reasons.length ? (
              <div className="action-result warning">
                <strong>Bloqueios flash</strong>
                <span>{setupFlashPlan.blocked_reasons.join(" ")}</span>
              </div>
            ) : null}
            <div className="setup-artifact-summary">
              <Metric label="Confirmação" value={setupFlashPlan.confirmation_phrase} />
              <Metric label="Artefato SHA" value={setupFlashPlan.artifact_sha256?.slice(0, 12) ?? "pendente"} />
              <Metric label="UUID" value={setupFlashPlan.expected_uuid ?? "pendente"} />
            </div>
            {setupFlashPlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
            <div className="action-result warning">
              <strong>Rollback manual</strong>
              <span>{setupFlashPlan.rollback.join(" ")}</span>
            </div>
          </div>
        ) : null}
        <div className="setup-apply-box">
          <label>
            Confirmação para flash real
            <input value={setupFlashConfirmation} onChange={(event) => setSetupFlashConfirmation(event.target.value)} placeholder={setupFlashPlan?.confirmation_phrase ?? "gere o plano primeiro"} />
          </label>
          <button type="button" className="danger-button" disabled={!canRun || setupBusy || !setupFlashPlan || setupFlashConfirmation !== setupFlashPlan.confirmation_phrase} onClick={() => void runSetupFlashExecute()}>
            <AlertTriangle className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Executar flash
          </button>
          <p>O backend exige <code>PRINTORA_REMOTE_FLASH_MODE=remote</code>; sem isso a tentativa fica bloqueada e registrada.</p>
        </div>
        {setupFlashExecuteResult ? (
          <div className={`action-result ${setupFlashExecuteResult.status === "ok" ? "success" : "warning"}`}>
            <strong>{setupFlashExecuteResult.summary}</strong>
            <span>{setupFlashExecuteResult.blocked_reasons.length ? setupFlashExecuteResult.blocked_reasons.join(" ") : setupFlashExecuteResult.artifact_sha256?.slice(0, 12) ?? "Resultado registrado."}</span>
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
        {setupFirmwareHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Firmware</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupFirmwareHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{run.created_at}</td>
                    <td>{run.run_type} · {run.board_name} · {run.preset_id}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status === "blocked" ? "error" : run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {setupFlashHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Flash</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupFlashHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{run.created_at}</td>
                    <td>{run.run_type} · {run.board_name} · {run.flash_method}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status} /></td>
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

function StatusBadge({ status }: { status: SetupRunStatus | "blocked" | "requires_recovery" }) {
  const tone = status === "ok" ? "success" : status === "warning" ? "warning" : "danger";
  const label = status === "ok" ? "OK" : status === "warning" ? "Atenção" : status === "requires_recovery" ? "Recuperação" : "Erro";
  return <span className={`setup-status setup-status-${tone}`}>{label}</span>;
}

function SetupStepCard({ step }: { step: SetupPlanStep | SetupCanPlanStep | SetupFirmwarePlanStep | SetupFlashPlanStep }) {
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
