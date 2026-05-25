import { useState } from "react";
import { Badge, Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type SettingsScreenProps = ScreenPropsFor<
  | "Activity"
  | "AlertTriangle"
  | "ClipboardCheck"
  | "FileText"
  | "History"
  | "HelpCircle"
  | "RefreshCw"
  | "Settings"
  | "ShieldAlert"
  | "ShieldCheck"
  | "Undo2"
  | "X"
  | "audit"
  | "canBitrate"
  | "canBusState"
  | "canComparison"
  | "canInterfaceName"
  | "canNotes"
  | "canRawOutput"
  | "canRecords"
  | "canRollbackSelfUpdateRun"
  | "canRxError"
  | "canSummary"
  | "canTxError"
  | "canTxRetries"
  | "compareLatestCanRecords"
  | "createCanRecord"
  | "displayedReleaseRows"
  | "error"
  | "formatCanAlert"
  | "formatClassification"
  | "formatMetricLabel"
  | "formatOptionalInt"
  | "formatReleaseSourceStatus"
  | "formatReleaseUpdateStatus"
  | "formatSelfUpdateStatus"
  | "formatUnknown"
  | "hostAudit"
  | "installDiagnostics"
  | "loadInstallDiagnostics"
  | "isSelfUpdateEnvironmentSupported"
  | "loadSelfUpdateHistory"
  | "loadSystemReleases"
  | "loading"
  | "parseCanRawOutput"
  | "releaseError"
  | "releaseLoading"
  | "reconcileSelfUpdateHistory"
  | "releasePanelClass"
  | "releaseStatusPillClass"
  | "selectedPrinterId"
  | "selfUpdateConnectionLost"
  | "selfUpdateHistory"
  | "selfUpdateMessage"
  | "selfUpdateReconciling"
  | "selfUpdateRunClass"
  | "setCanBitrate"
  | "setCanBusState"
  | "setCanInterfaceName"
  | "setCanNotes"
  | "setCanRawOutput"
  | "setCanRxError"
  | "setCanTxError"
  | "setCanTxRetries"
  | "setSelfUpdateConfirmation"
  | "setSelfUpdateModalOpen"
  | "setSelfUpdatePlan"
  | "setSelfUpdateRollbackConfirmation"
  | "startSelfUpdateFlow"
  | "status"
  | "systemReleases"
>;

export function SettingsScreen(props: SettingsScreenProps) {
  const {
    Activity,
    AlertTriangle,
    ClipboardCheck,
    FileText,
    History,
    HelpCircle,
    RefreshCw,
    Settings,
    ShieldAlert,
    ShieldCheck,
    Undo2,
    X,
    audit,
    canBitrate,
    canBusState,
    canComparison,
    canInterfaceName,
    canNotes,
    canRawOutput,
    canRecords,
    canRollbackSelfUpdateRun,
    canRxError,
    canSummary,
    canTxError,
    canTxRetries,
    compareLatestCanRecords,
    createCanRecord,
    displayedReleaseRows,
    error,
    formatCanAlert,
    formatClassification,
    formatMetricLabel,
    formatOptionalInt,
    formatReleaseSourceStatus,
    formatReleaseUpdateStatus,
    formatSelfUpdateStatus,
    formatUnknown,
    hostAudit,
    installDiagnostics,
    loadInstallDiagnostics,
    isSelfUpdateEnvironmentSupported,
    loadSelfUpdateHistory,
    loadSystemReleases,
    loading,
    parseCanRawOutput,
    releaseError,
    releaseLoading,
    reconcileSelfUpdateHistory,
    releasePanelClass,
    releaseStatusPillClass,
    selectedPrinterId,
    selfUpdateConnectionLost,
    selfUpdateHistory,
    selfUpdateMessage,
    selfUpdateReconciling,
    selfUpdateRunClass,
    setCanBitrate,
    setCanBusState,
    setCanInterfaceName,
    setCanNotes,
    setCanRawOutput,
    setCanRxError,
    setCanTxError,
    setCanTxRetries,
    setSelfUpdateConfirmation,
    setSelfUpdateModalOpen,
    setSelfUpdatePlan,
    setSelfUpdateRollbackConfirmation,
    startSelfUpdateFlow,
    status,
    systemReleases,
  } = props;
  const [settingsHelpTopic, setSettingsHelpTopic] = useState<"can" | "host" | null>(null);
  const [installDiagnosticCopied, setInstallDiagnosticCopied] = useState(false);

  const helpTitle = settingsHelpTopic === "can" ? "Registro técnico CAN" : "Diagnóstico avançado do host";

  return (
    <>
        {settingsHelpTopic ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Ajuda: ${helpTitle}`}>
            <div className="modal-card settings-help-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{helpTitle}</h2>
                  <p>{settingsHelpTopic === "can" ? "Histórico técnico da comunicação CAN da impressora." : "Auditoria técnica do computador onde o Printora roda."}</p>
                </div>
                <button type="button" className="icon-button" onClick={() => setSettingsHelpTopic(null)} aria-label="Fechar ajuda">
                  <X size={18} />
                </button>
              </div>
              {settingsHelpTopic === "can" ? (
                <div className="settings-help-content">
                  <p>Use para guardar uma leitura técnica da interface CAN e comparar se erros aumentaram depois de manutenção, update, troca de cabo ou troca de placa.</p>
                  <p>O fluxo esperado é rodar <code>ip -details -statistics link show can0</code> no host, colar a saída, extrair a leitura e registrar.</p>
                  <p>Indicadores como <code>rx</code>, <code>tx</code>, <code>retries</code>, estado do barramento e bitrate ajudam a separar falha de comunicação CAN de problema mecânico ou de configuração.</p>
                </div>
              ) : (
                <div className="settings-help-content">
                  <p>Use para verificar o ambiente Linux/Raspberry/host do Printora quando houver suspeita de problema estrutural fora da impressão.</p>
                  <p>A auditoria olha sinais como systemd, CAN, symlinks, caminhos legados e repositórios locais. Ela não corrige nada sozinha.</p>
                  <p>Se aparecerem itens em monitorar ou corrigir, investigue o detalhe antes de update, rollback ou manutenção longa.</p>
                </div>
              )}
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setSettingsHelpTopic(null)}>
                  Fechar
                </button>
              </div>
            </div>
          </div>
        ) : null}

        <article className={`panel wide panel-section panel-settings releases-panel ${releasePanelClass(systemReleases)}`}>
          <div className="panel-header-row">
            <div>
              <h2>Releases do Printora</h2>
              <p>{releaseLoading ? "Consultando GitHub Releases..." : systemReleases?.message ?? "Status ainda não carregado."}</p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={() => void loadSystemReleases()}
              disabled={releaseLoading}
            >
              <RefreshCw size={16} />
              {releaseLoading ? "Verificando" : "Verificar releases"}
            </button>
          </div>
          <div className="release-summary-grid">
            <Metric label="Versão instalada" value={systemReleases?.installed_version ?? "-"} />
            <Metric label="Última release" value={systemReleases?.latest_release?.tag ?? "-"} />
            <Metric label="Canal" value={systemReleases?.channel ?? "-"} />
            <Metric label="Status" value={formatReleaseUpdateStatus(systemReleases, releaseLoading, releaseError)} />
          </div>
          {releaseError ? (
            <div className="action-result warning">
              <strong>Erro de rede</strong>
              <span>{releaseError}</span>
            </div>
          ) : null}
          {systemReleases?.error ? (
            <div className="action-result warning">
              <strong>{formatReleaseSourceStatus(systemReleases.status)}</strong>
              <span>{systemReleases.error}</span>
            </div>
          ) : null}
          {systemReleases?.latest_release ? (
            <div className="release-latest-card">
              <div>
                <span className={`status-pill ${releaseStatusPillClass(systemReleases)}`}>
                  {formatReleaseUpdateStatus(systemReleases, false, null)}
                </span>
                <strong>{systemReleases.latest_release.name}</strong>
                <small>
                  {systemReleases.latest_release.tag} · {systemReleases.latest_release.published_at ?? "sem data"} · {systemReleases.latest_release.channel}
                </small>
              </div>
              <p>{systemReleases.latest_release.changelog_summary || "Sem changelog informado."}</p>
              {systemReleases.latest_release_available ? (
                <div className="update-actions">
                  <button type="button" className="secondary-button" onClick={() => void startSelfUpdateFlow()} disabled={releaseLoading}>
                    <ShieldAlert size={16} />
                    Atualizar agora
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
          {selfUpdateMessage ? (
            <div className={`action-result ${selfUpdateConnectionLost ? "warning" : ""}`}>
              <strong>{selfUpdateConnectionLost ? "Conexão interrompida" : "Updater do Printora"}</strong>
              <span>{selfUpdateMessage}</span>
            </div>
          ) : null}
        </article>

        <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel release-history-panel">
          <summary className="settings-advanced-summary">
            <span>Releases anteriores</span>
          </summary>
          <div className="release-list">
            {releaseLoading ? <p className="muted">Carregando releases de produção...</p> : null}
            {!releaseLoading && displayedReleaseRows.length === 0 ? (
              <p className="muted">Nenhuma release anterior para listar.</p>
            ) : null}
            {displayedReleaseRows.map((release: any) => (
              <div key={release.tag} className={`release-row ${release.installed ? "installed" : ""}`}>
                <div>
                  <strong>{release.name}</strong>
                  <span>
                    {release.tag} · {release.published_at ?? "sem data"} · {release.installed ? "instalada" : release.channel}
                  </span>
                </div>
                <p>{release.changelog_summary || "Sem changelog informado."}</p>
              </div>
            ))}
          </div>
        </details>

        <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel self-update-history">
          <summary className="settings-advanced-summary">
            <span>Histórico de updates</span>
            <button
              type="button"
              className="secondary-button compact-summary-action"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                void loadSelfUpdateHistory();
              }}
            >
              <History size={15} />
              Recarregar
            </button>
            <button
              type="button"
              className="secondary-button compact-summary-action"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                void reconcileSelfUpdateHistory();
              }}
              disabled={selfUpdateReconciling}
            >
              <RefreshCw size={15} />
              {selfUpdateReconciling ? "Reconciliando" : "Reconciliar travados"}
            </button>
          </summary>
          {selfUpdateHistory.length === 0 ? <p className="muted">Nenhum update do Printora registrado.</p> : null}
          {selfUpdateHistory.slice(0, 5).map((run: any) => (
            <div key={run.id} className={`update-row ${selfUpdateRunClass(run.status)}`}>
              <div className="update-main">
                <div>
                  <strong>#{run.id} · {run.target_tag}</strong>
                  <span>
                    {formatSelfUpdateStatus(run.status)} · {run.created_at}
                  </span>
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setSelfUpdateConfirmation("");
                    setSelfUpdateRollbackConfirmation("");
                    setSelfUpdatePlan({
                      safe_mode: "history",
                      update_supported: isSelfUpdateEnvironmentSupported(run.environment),
                      can_apply: false,
                      message: "Detalhes do update registrado.",
                      run,
                    });
                    setSelfUpdateModalOpen(true);
                  }}
                >
                  <FileText size={15} />
                  Ver detalhes
                </button>
                {run.status === "running" ? (
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void reconcileSelfUpdateHistory()}
                    disabled={selfUpdateReconciling}
                  >
                    <RefreshCw size={15} />
                    {selfUpdateReconciling ? "Reconciliando" : "Atualizar status"}
                  </button>
                ) : null}
                {canRollbackSelfUpdateRun(run) ? (
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                      setSelfUpdateConfirmation("");
                      setSelfUpdateRollbackConfirmation("");
                      setSelfUpdatePlan({
                        safe_mode: "history",
                        update_supported: isSelfUpdateEnvironmentSupported(run.environment),
                        can_apply: false,
                        message: "Revise os detalhes antes do rollback.",
                        run,
                      });
                      setSelfUpdateModalOpen(true);
                    }}
                  >
                    <Undo2 size={15} />
                    Rollback
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </details>

        <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel install-diagnostics-panel">
          <summary className="settings-advanced-summary">
            <span>Diagnóstico da instalação</span>
            <button
              type="button"
              className="secondary-button compact-summary-action"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                void loadInstallDiagnostics();
              }}
            >
              <RefreshCw size={15} />
              Atualizar
            </button>
            <button
              type="button"
              className="secondary-button compact-summary-action"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                if (!installDiagnostics?.copy_text) {
                  return;
                }
                void navigator.clipboard.writeText(installDiagnostics.copy_text).then(() => {
                  setInstallDiagnosticCopied(true);
                  window.setTimeout(() => setInstallDiagnosticCopied(false), 1800);
                });
              }}
              disabled={!installDiagnostics?.copy_text}
            >
              <ClipboardCheck size={15} />
              {installDiagnosticCopied ? "Copiado" : "Copiar diagnóstico"}
            </button>
          </summary>
          <p className="muted">Use este painel quando a instalação, atualização ou inicialização local não estiver clara.</p>
          <strong className="summary">{installDiagnostics?.summary ?? "Aguardando diagnóstico"}</strong>
          <div className="install-diagnostics-grid">
            <Badge icon={Settings} label="Versão" value={installDiagnostics?.installed_version ?? "-"} />
            <Badge icon={Activity} label="Ambiente" value={installDiagnostics?.environment ?? "-"} />
            <Badge icon={ShieldCheck} label="OK" value={installDiagnostics?.counts.ok ?? 0} />
            <Badge icon={AlertTriangle} label="Atenção" value={(installDiagnostics?.counts.warning ?? 0) + (installDiagnostics?.counts.error ?? 0)} />
          </div>
          <div className="install-diagnostics-meta">
            <span>Porta: {installDiagnostics?.port ?? "-"}</span>
            <span>Dados: {installDiagnostics?.data_dir ?? "-"}</span>
            <span>Banco: {installDiagnostics?.database_path ?? "-"}</span>
          </div>
          <div className="install-diagnostics-list">
            {installDiagnostics?.items.map((item: any) => (
              <div key={item.key} className={`install-diagnostic-row ${item.status}`}>
                <div>
                  <strong>{item.label}</strong>
                  <span>{item.status}</span>
                </div>
                <p>{item.detail}</p>
                {item.command ? <code>{item.command}</code> : null}
              </div>
            ))}
          </div>
        </details>

        <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel can-technical-panel">
          <summary className="settings-advanced-summary">
            <span>Registro técnico CAN</span>
            <button
              type="button"
              className="icon-button help-icon-button"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                setSettingsHelpTopic("can");
              }}
              aria-label="Ajuda sobre Registro técnico CAN"
              title="Ajuda"
            >
              <HelpCircle size={16} />
            </button>
            <strong>{formatCanAlert(canSummary?.overall_alert ?? canRecords[0]?.alert_level ?? "ok")}</strong>
          </summary>
          <div className="can-summary">
            <Badge label="Modo" value={canSummary?.safe_mode ?? "manual_read_only"} />
            <Badge label="Dados" value={canSummary?.data_state === "manual_records" ? "registros manuais" : "sem registros"} />
            <Badge label="OK" value={canSummary?.counts.ok ?? 0} />
            <Badge label="Monitorar" value={canSummary?.counts.monitorar ?? 0} />
            <Badge label="Problemas" value={canSummary?.counts.problema ?? 0} />
          </div>
          <div className="panel-actions">
            <button type="button" className="secondary-button" onClick={() => void compareLatestCanRecords()} disabled={!selectedPrinterId || loading || canRecords.length < 2}>
              Comparar últimas leituras
            </button>
          </div>
          {canSummary?.data_state === "no_data" ? (
            <p className="muted">Nenhuma leitura CAN local registrada. Este formulário é técnico e não aparece na tela de monitoramento.</p>
          ) : null}
          {canComparison ? (
            <div className={`can-row ${canComparison.alert_level}`}>
              <strong>Comparação #{canComparison.before_record_id} → #{canComparison.after_record_id}</strong>
              <span>
                {canComparison.interface_name} · rx={canComparison.delta_rx_error} · tx={canComparison.delta_tx_error} · retries={canComparison.delta_tx_retries}
              </span>
              <small>{canComparison.diagnosis}</small>
              <small>{canComparison.recommended_actions.join(" · ")}</small>
            </div>
          ) : null}
          <div className="can-parser">
            <textarea
              aria-label="Saída bruta ip link CAN"
              value={canRawOutput}
              onChange={(event: any) => setCanRawOutput(event.target.value)}
              placeholder="Cole aqui a saída de ip -details -statistics link show can0 para preencher os campos."
            />
            <button type="button" className="secondary-button" onClick={() => void parseCanRawOutput()} disabled={!selectedPrinterId || loading || !canRawOutput.trim()}>
              Extrair leitura
            </button>
          </div>
          <form className="can-form" onSubmit={(event: any) => void createCanRecord(event)}>
            <input
              aria-label="Interface CAN"
              value={canInterfaceName}
              onChange={(event: any) => setCanInterfaceName(event.target.value)}
              placeholder="can0"
            />
            <input
              aria-label="RX error"
              type="number"
              min="0"
              value={canRxError}
              onChange={(event: any) => setCanRxError(Number(event.target.value))}
            />
            <input
              aria-label="TX error"
              type="number"
              min="0"
              value={canTxError}
              onChange={(event: any) => setCanTxError(Number(event.target.value))}
            />
            <input
              aria-label="TX retries"
              type="number"
              min="0"
              value={canTxRetries}
              onChange={(event: any) => setCanTxRetries(Number(event.target.value))}
            />
            <input
              aria-label="Estado do barramento"
              value={canBusState}
              onChange={(event: any) => setCanBusState(event.target.value)}
              placeholder="ERROR-ACTIVE"
            />
            <input
              aria-label="Bitrate CAN"
              type="number"
              min="1"
              value={canBitrate}
              onChange={(event: any) => setCanBitrate(Number(event.target.value))}
            />
            <textarea
              aria-label="Notas CAN"
              value={canNotes}
              onChange={(event: any) => setCanNotes(event.target.value)}
              placeholder="Ex.: leitura manual de ip -details -statistics link show can0"
            />
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Registrar
            </button>
          </form>
          <div className="can-list">
            {canRecords.length === 0 ? <p className="muted">Nenhuma leitura CAN registrada.</p> : null}
            {canRecords.map((record: any) => (
              <div key={record.id} className={`can-row ${record.alert_level}`}>
                <strong>{formatCanAlert(record.alert_level)}</strong>
                <span>
                  {record.interface_name} · rx={record.rx_error} · tx={record.tx_error} · retries={record.tx_retries} ·{" "}
                  {record.recorded_at}
                </span>
                <small>
                  Delta rx={formatOptionalInt(record.delta_rx_error)} · tx={formatOptionalInt(record.delta_tx_error)} ·
                  retries={formatOptionalInt(record.delta_tx_retries)}
                </small>
                <small>
                  Estado: {record.bus_state ?? "-"} · bitrate: {record.bitrate ?? "-"}
                </small>
                <small>{record.diagnosis}</small>
                {record.recommended_actions.length ? <small>{record.recommended_actions.join(" · ")}</small> : null}
                {record.notes ? <small>{record.notes}</small> : null}
              </div>
            ))}
          </div>
        </details>

        <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel host-diagnostics-panel">
          <summary className="settings-advanced-summary">
            <span>Diagnóstico avançado do host</span>
            <button
              type="button"
              className="icon-button help-icon-button"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                setSettingsHelpTopic("host");
              }}
              aria-label="Ajuda sobre Diagnóstico avançado do host"
              title="Ajuda"
            >
              <HelpCircle size={16} />
            </button>
          </summary>
          <p className="muted">Leitura técnica do computador onde o Printora roda. Use quando precisar investigar systemd, CAN, symlinks ou repositórios locais.</p>
          <strong className="summary">{hostAudit?.summary ?? "Aguardando dados"}</strong>
          <div className="audit-counts">
            <Badge icon={Settings} label="Modo" value={hostAudit?.mode ?? "-"} />
            <Badge icon={Activity} label="Executou" value={hostAudit?.executed ? "sim" : "não"} />
            <Badge icon={AlertTriangle} label="Monitorar" value={hostAudit?.counts.monitorar ?? 0} />
            <Badge icon={ShieldCheck} label="Corrigir" value={hostAudit?.counts.corrigir_agora ?? 0} />
          </div>
          <div className="section-summary">
            {hostAudit?.section_summary
              ? Object.entries(hostAudit.section_summary).map(([key, value]) => (
                  <Metric key={key} label={formatMetricLabel(key)} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {hostAudit?.findings.map((finding: any) => (
              <div key={finding.id} className={`finding ${finding.severity}`}>
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.category} · {formatClassification(finding.classification)}</span>
                </div>
                <p>{finding.detail}</p>
                <small>{finding.safe_action}</small>
              </div>
            ))}
          </div>
        </details>

    </>
  );
}
