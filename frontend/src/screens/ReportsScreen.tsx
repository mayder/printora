import { Badge, Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type ReportsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "Database"
  | "Gauge"
  | "ShieldCheck"
  | "audit"
  | "backupCompareBasePath"
  | "backupCompareResult"
  | "backupCompareTargetPath"
  | "backupDestinationPath"
  | "backupDryRunOnly"
  | "backupName"
  | "backupPolicies"
  | "backupRestoreArchivePath"
  | "backupRestoreConfirmation"
  | "backupRestoreFiles"
  | "backupRestoreGate"
  | "backupRestorePlan"
  | "backupRestoreRoot"
  | "backupRuns"
  | "backupSourcePath"
  | "checklist"
  | "compareBackupArchives"
  | "compareSnapshots"
  | "createBackupDryRun"
  | "createBackupPolicy"
  | "createBackupRestorePlan"
  | "executeLocalBackup"
  | "formatBoolean"
  | "formatChecklistDataState"
  | "formatClassification"
  | "formatDecision"
  | "formatHealthSeverity"
  | "formatMetricLabel"
  | "formatRedaction"
  | "formatSeverity"
  | "formatUnknown"
  | "fromSnapshotId"
  | "health"
  | "healthFindingClass"
  | "healthPanelClass"
  | "loadSanitizedReport"
  | "loading"
  | "sanitizedReport"
  | "selectedPrinterId"
  | "setBackupCompareBasePath"
  | "setBackupCompareTargetPath"
  | "setBackupDestinationPath"
  | "setBackupDryRunOnly"
  | "setBackupName"
  | "setBackupRestoreArchivePath"
  | "setBackupRestoreConfirmation"
  | "setBackupRestoreFiles"
  | "setBackupRestoreRoot"
  | "setBackupSourcePath"
  | "setFromSnapshotId"
  | "setToSnapshotId"
  | "snapshotDiff"
  | "snapshots"
  | "status"
  | "toSnapshotId"
  | "validateBackupRestoreGate"
>;

export function ReportsScreen(props: ReportsScreenProps) {
  const {
    AlertTriangle,
    Database,
    Gauge,
    ShieldCheck,
    audit,
    backupCompareBasePath,
    backupCompareResult,
    backupCompareTargetPath,
    backupDestinationPath,
    backupDryRunOnly,
    backupName,
    backupPolicies,
    backupRestoreArchivePath,
    backupRestoreConfirmation,
    backupRestoreFiles,
    backupRestoreGate,
    backupRestorePlan,
    backupRestoreRoot,
    backupRuns,
    backupSourcePath,
    checklist,
    compareBackupArchives,
    compareSnapshots,
    createBackupDryRun,
    createBackupPolicy,
    createBackupRestorePlan,
    executeLocalBackup,
    formatBoolean,
    formatChecklistDataState,
    formatClassification,
    formatDecision,
    formatHealthSeverity,
    formatMetricLabel,
    formatRedaction,
    formatSeverity,
    formatUnknown,
    fromSnapshotId,
    health,
    healthFindingClass,
    healthPanelClass,
    loadSanitizedReport,
    loading,
    sanitizedReport,
    selectedPrinterId,
    setBackupCompareBasePath,
    setBackupCompareTargetPath,
    setBackupDestinationPath,
    setBackupDryRunOnly,
    setBackupName,
    setBackupRestoreArchivePath,
    setBackupRestoreConfirmation,
    setBackupRestoreFiles,
    setBackupRestoreRoot,
    setBackupSourcePath,
    setFromSnapshotId,
    setToSnapshotId,
    snapshotDiff,
    snapshots,
    status,
    toSnapshotId,
    validateBackupRestoreGate,
  } = props;

  return (
    <>
        <article className={`panel wide health ${healthPanelClass(health?.decision)} panel-section panel-reports`}>
          <div className="panel-heading">
            <h2>Health Check</h2>
            <strong>{health?.summary ?? "Aguardando dados"}</strong>
          </div>
          {health ? (
            <div className="checklist-meta">
              <span>{formatChecklistDataState(health.data_state)}</span>
              <span>{health.source}</span>
            </div>
          ) : null}
          <div className="health-metrics">
            <Badge icon={Gauge} label="Decisão" value={formatDecision(health?.decision)} />
            <Badge icon={ShieldCheck} label="Bloqueios" value={health?.counts.blocker ?? 0} />
            <Badge icon={AlertTriangle} label="Alertas" value={health?.counts.warning ?? 0} />
            <Badge icon={Database} label="Snapshots" value={formatUnknown(health?.metrics.snapshot_count ?? "-")} />
          </div>
          <div className="section-summary">
            {health?.metrics
              ? Object.entries(health.metrics).map(([key, value]) => (
                  <Metric key={key} label={formatMetricLabel(key)} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {health?.items.map((item: any) => (
              <div key={item.key} className={`finding ${healthFindingClass(item.severity)}`}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{formatHealthSeverity(item.severity)}</span>
                </div>
                <p>{item.detail}</p>
                <small>{item.action}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-reports">
          <div className="panel-heading">
            <h2>Relatório sanitizado</h2>
            <button type="button" onClick={() => void loadSanitizedReport()} disabled={!selectedPrinterId || loading}>
              Gerar relatório
            </button>
          </div>
          <p className="muted">
            Markdown read-only para compartilhar diagnóstico sem URLs, IPs, caminhos locais ou valores sensíveis detectáveis.
          </p>
          {sanitizedReport ? (
            <>
              <div className="audit-counts">
                <Badge label="Formato" value={sanitizedReport.format} />
                <Badge label="Modo" value={sanitizedReport.safe_mode} />
                <Badge label="Origem" value={formatChecklistDataState(sanitizedReport.data_state)} />
                <Badge label="Redações" value={sanitizedReport.redactions.length} />
                <Badge label="Impressora" value={sanitizedReport.printer_id} />
              </div>
              <div className="redaction-list">
                {sanitizedReport.redactions.length === 0 ? (
                  <span>Nenhuma redação detectada nos dados usados.</span>
                ) : (
                  sanitizedReport.redactions.map((redaction: any) => <span key={redaction}>{formatRedaction(redaction)}</span>)
                )}
              </div>
              <pre className="report-preview">{sanitizedReport.markdown}</pre>
            </>
          ) : null}
        </article>

        <article className="panel wide panel-section panel-reports">
          <div className="panel-heading">
            <h2>Backups</h2>
            <strong>Dry-run seguro</strong>
          </div>
          <form className="backup-form" onSubmit={(event: any) => void createBackupPolicy(event)}>
            <input
              aria-label="Nome da política"
              value={backupName}
              onChange={(event: any) => setBackupName(event.target.value)}
              placeholder="Nome"
            />
            <input
              aria-label="Origem do backup"
              value={backupSourcePath}
              onChange={(event: any) => setBackupSourcePath(event.target.value)}
              placeholder="/home/pi/printer_data/config"
            />
            <input
              aria-label="Destino do backup"
              value={backupDestinationPath}
              onChange={(event: any) => setBackupDestinationPath(event.target.value)}
              placeholder="/home/pi/printer_data/backups/printora"
            />
            <label className="inline-check">
              <input
                type="checkbox"
                checked={backupDryRunOnly}
                onChange={(event: any) => setBackupDryRunOnly(event.target.checked)}
              />
              Somente dry-run
            </label>
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Criar política
            </button>
          </form>
          <div className="backup-list">
            {backupPolicies.length === 0 ? <p className="muted">Nenhuma política de backup cadastrada.</p> : null}
            {backupPolicies.map((policy: any) => (
              <div key={policy.id} className="backup-row">
                <div>
                  <strong>{policy.name}</strong>
                  <span>{policy.source_path}</span>
                  <small>
                    Destino: {policy.destination_path} · {policy.dry_run_only ? "somente dry-run" : "execução local habilitada"}
                  </small>
                </div>
                <div>
                  <small>Exclusões: {policy.exclude_patterns.join(", ")}</small>
                </div>
                <div className="backup-actions">
                  <button type="button" onClick={() => void createBackupDryRun(policy.id)} disabled={loading}>
                    Dry-run
                  </button>
                  <button
                    type="button"
                    onClick={() => void executeLocalBackup(policy.id)}
                    disabled={loading || policy.dry_run_only}
                  >
                    Executar local
                  </button>
                </div>
              </div>
            ))}
          </div>
          <details className="backup-runs collapsible-panel">
            <summary>Histórico de backups</summary>
            {backupRuns.length === 0 ? <p className="muted">Nenhum dry-run registrado.</p> : null}
            {backupRuns.map((run: any) => (
              <div key={run.id} className="backup-run-row">
                <strong>#{run.id} · {run.status}</strong>
                <span>{run.created_at}</span>
                <small>{run.message}</small>
              </div>
            ))}
          </details>
          <div className="backup-form">
            <input
              aria-label="Backup base"
              value={backupCompareBasePath}
              onChange={(event: any) => setBackupCompareBasePath(event.target.value)}
              placeholder="/path/base.zip"
            />
            <input
              aria-label="Backup alvo"
              value={backupCompareTargetPath}
              onChange={(event: any) => setBackupCompareTargetPath(event.target.value)}
              placeholder="/path/novo.zip"
            />
            <button type="button" onClick={() => void compareBackupArchives()} disabled={loading || !backupCompareBasePath || !backupCompareTargetPath}>
              Comparar backups
            </button>
          </div>
          {backupCompareResult ? (
            <div className="backup-run-row">
              <strong>{backupCompareResult.summary}</strong>
              <small>Adicionados: {backupCompareResult.added.join(", ") || "-"}</small>
              <small>Removidos: {backupCompareResult.removed.join(", ") || "-"}</small>
              <small>Alterados: {backupCompareResult.changed.join(", ") || "-"}</small>
            </div>
          ) : null}
          <div className="backup-form">
            <input
              aria-label="Arquivo de backup para restore"
              value={backupRestoreArchivePath}
              onChange={(event: any) => setBackupRestoreArchivePath(event.target.value)}
              placeholder="/path/backup.zip"
            />
            <input
              aria-label="Raiz de restore"
              value={backupRestoreRoot}
              onChange={(event: any) => setBackupRestoreRoot(event.target.value)}
              placeholder="/home/pi/printer_data/config"
            />
            <textarea
              aria-label="Arquivos para restore"
              value={backupRestoreFiles}
              onChange={(event: any) => setBackupRestoreFiles(event.target.value)}
              placeholder="printer.cfg"
            />
            <input
              aria-label="Confirmação do gate de restore"
              value={backupRestoreConfirmation}
              onChange={(event: any) => setBackupRestoreConfirmation(event.target.value)}
              placeholder="BLOCK_REAL_RESTORE"
            />
            <button type="button" onClick={() => void createBackupRestorePlan()} disabled={loading || !backupRestoreArchivePath || !backupRestoreRoot}>
              Planejar restore
            </button>
            <button type="button" onClick={() => void validateBackupRestoreGate()} disabled={loading || !backupRestoreArchivePath || !backupRestoreRoot}>
              Validar gate restore
            </button>
          </div>
          {backupRestorePlan ? (
            <details className="backup-run-row" open>
              <summary>
                Restore dry-run · {backupRestorePlan.selected_files.length} arquivo(s) · bloqueado: {formatBoolean(backupRestorePlan.blocked)}
              </summary>
              <small>{backupRestorePlan.message}</small>
              {backupRestorePlan.missing_files.length ? <small>Ausentes: {backupRestorePlan.missing_files.join(", ")}</small> : null}
              <pre>{backupRestorePlan.planned_commands.join("\n")}</pre>
            </details>
          ) : null}
          {backupRestoreGate ? (
            <details className="backup-run-row" open>
              <summary>
                Gate restore · confirmação: {formatBoolean(backupRestoreGate.accepted_confirmation)} · bloqueado:{" "}
                {formatBoolean(backupRestoreGate.blocked)}
              </summary>
              <small>{backupRestoreGate.message}</small>
              <small>Modo: {backupRestoreGate.safe_mode}</small>
              <strong>Rollback futuro obrigatório</strong>
              <ol>
                {backupRestoreGate.rollback_plan.map((item: any) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
              <pre>{backupRestoreGate.plan.planned_commands.join("\n")}</pre>
            </details>
          ) : null}
        </article>

        <article className="panel wide panel-section panel-reports">
          <h2>Snapshots</h2>
          {snapshots.length >= 2 ? (
            <div className="snapshot-compare">
              <label>
                Base
                <select
                  value={fromSnapshotId ?? ""}
                  onChange={(event: any) => setFromSnapshotId(Number(event.target.value))}
                >
                  {snapshots.map((snapshot: any) => (
                    <option key={snapshot.id} value={snapshot.id}>
                      #{snapshot.id} · {snapshot.created_at}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Atual
                <select
                  value={toSnapshotId ?? ""}
                  onChange={(event: any) => setToSnapshotId(Number(event.target.value))}
                >
                  {snapshots.map((snapshot: any) => (
                    <option key={snapshot.id} value={snapshot.id}>
                      #{snapshot.id} · {snapshot.created_at}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={() => void compareSnapshots()}
                disabled={!fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId || loading}
              >
                Comparar
              </button>
            </div>
          ) : null}
          {snapshotDiff ? (
            <div className={`snapshot-diff ${snapshotDiff.highest_severity}`}>
              <strong>{snapshotDiff.summary}</strong>
              {snapshotDiff.changes.length === 0 ? (
                <p className="muted">Nenhuma mudança relevante detectada.</p>
              ) : (
                <div className="diff-list">
                  {snapshotDiff.changes.map((change: any) => (
                    <div key={`${change.field}-${change.title}`} className={`diff-row ${change.severity}`}>
                      <div>
                        <strong>{change.title}</strong>
                        <span>{formatSeverity(change.severity)}</span>
                      </div>
                      <p>{change.detail}</p>
                      <small>
                        Antes: {formatUnknown(change.before)} · Depois: {formatUnknown(change.after)}
                      </small>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
          <div className="snapshot-list">
            {snapshots.length === 0 ? <p className="muted">Nenhum snapshot capturado.</p> : null}
            {snapshots.map((snapshot: any) => (
              <div key={snapshot.id} className="snapshot-row">
                <strong>#{snapshot.id}</strong>
                <span>{snapshot.created_at}</span>
                <span>{snapshot.snapshot_type}</span>
                <small>{formatUnknown(snapshot.summary)}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-section panel-reports">
          <h2>Moonraker</h2>
          <Metric label="Conexão" value={status?.connected ? "Conectado" : "Desconectado"} />
          <Metric label="URL" value={status?.moonraker_url ?? "-"} />
          <Metric label="Klippy" value={status?.server?.klippy_state ?? "-"} />
          <Metric label="Moonraker" value={status?.server?.moonraker_version ?? "-"} />
        </article>

        <article className="panel panel-section panel-reports">
          <h2>Klipper</h2>
          <Metric label="Estado" value={status?.printer?.state ?? "-"} />
          <Metric label="Mensagem" value={status?.printer?.state_message ?? "-"} />
          <Metric label="Versão" value={status?.printer?.software_version ?? "-"} />
        </article>

        <article className="panel wide panel-section panel-reports">
          <h2>Auditoria somente leitura</h2>
          <strong className="summary">{audit?.summary ?? "Aguardando dados"}</strong>
          {audit ? (
            <div className="checklist-meta">
              <span>{formatChecklistDataState(audit.data_state ?? "live")}</span>
              <span>{audit.source ?? "-"}</span>
            </div>
          ) : null}
          <div className="audit-counts">
            <Badge label="Corrigir agora" value={audit?.counts.corrigir_agora ?? 0} />
            <Badge label="Monitorar" value={audit?.counts.monitorar ?? 0} />
            <Badge label="Precisa confirmação" value={audit?.counts.precisa_confirmacao ?? 0} />
            <Badge label="Ignorar" value={audit?.counts.ignorar ?? 0} />
          </div>
          <div className="findings">
            {audit?.findings.map((finding: any) => (
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
        </article>


    </>
  );
}
