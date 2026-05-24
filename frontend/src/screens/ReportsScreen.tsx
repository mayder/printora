import React from "react";
import type { ScreenPropsFor } from "./ScreenProps";
import { ReportModals, type ReportModalKind } from "./reports/ReportModals";
import "./reports/ReportsScreen.css";
import {
  explainPrintDecision,
  formatReportMetricValue,
  formatReportValue,
  primaryHealthReason,
  reportHealthAction,
  reportHealthDetail,
  reportHealthTitle,
  reportMetricHelp,
  reportMetricLabel,
} from "./reports/reportFormatters";

type ReportsScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "Camera"
  | "Database"
  | "FileText"
  | "Gauge"
  | "History"
  | "Radio"
  | "RefreshCw"
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
  | "formatSeverity"
  | "formatUnknown"
  | "fromSnapshotId"
  | "health"
  | "healthFindingClass"
  | "loadSanitizedReport"
  | "loading"
  | "networkDiagnostics"
  | "sanitizedReport"
  | "selectedPrinter"
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
  const [activeModal, setActiveModal] = React.useState<ReportModalKind>(null);
  const {
    AlertTriangle,
    Camera,
    Database,
    FileText,
    Gauge,
    History,
    Radio,
    RefreshCw,
    ShieldCheck,
    audit,
    backupCompareResult,
    backupPolicies,
    backupRestoreGate,
    backupRestorePlan,
    backupRuns,
    checklist,
    compareSnapshots,
    createBackupDryRun,
    executeLocalBackup,
    formatBoolean,
    formatChecklistDataState,
    formatClassification,
    formatDecision,
    formatSeverity,
    formatUnknown,
    fromSnapshotId,
    health,
    healthFindingClass,
    loading,
    networkDiagnostics,
    sanitizedReport,
    selectedPrinter,
    setFromSnapshotId,
    setToSnapshotId,
    snapshotDiff,
    snapshots,
    status,
    toSnapshotId,
  } = props;

  const reason = primaryHealthReason(health);
  const diagnosticSource = health ? formatChecklistDataState(health.data_state) : "sem leitura";
  const moonrakerState = status?.connected ? "Conectado" : "Sem resposta";
  const currentSnapshot = snapshots[0];

  return (
    <>
      <article className="panel wide panel-section panel-reports report-page">
        <div className="report-hero">
          <div>
            <span className="report-kicker">Relatório da impressora</span>
            <h2>{selectedPrinter?.name ?? "Impressora selecionada"}</h2>
            <p>
              Esta tela resume se a impressora está pronta, por que o Printora recomenda imprimir ou não imprimir,
              quais evidências foram usadas e o que pode ser compartilhado com segurança.
            </p>
          </div>
          <div className={`report-decision ${health?.decision ?? "unknown"}`}>
            <span>Recomendação</span>
            <strong>{formatDecision(health?.decision)}</strong>
            <p>{explainPrintDecision(health)}</p>
          </div>
        </div>

        <div className="report-status-grid">
          <ReportStatusCard icon={Radio} label="Moonraker" value={moonrakerState} detail="Comunicação com a Raspberry ou host Klipper." tone={status?.connected ? "ok" : "danger"} />
          <ReportStatusCard icon={Gauge} label="Dados usados" value={diagnosticSource} detail="Origem da análise exibida neste relatório." tone={health?.data_state === "live" ? "ok" : "warning"} />
          <ReportStatusCard icon={AlertTriangle} label="Bloqueios" value={health?.counts.blocker ?? 0} detail="Itens que podem impedir uma impressão segura." tone={(health?.counts.blocker ?? 0) > 0 ? "danger" : "ok"} />
          <ReportStatusCard icon={Database} label="Snapshots" value={snapshots.length} detail="Leituras salvas para comparação histórica." tone="neutral" />
        </div>
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Por que imprimir ou não imprimir</h2>
            <p>O relatório mostra o motivo principal e a ação segura. Não fica só na frase “não imprimir”.</p>
          </div>
          <strong>{health?.summary ?? "Aguardando dados"}</strong>
        </div>

        <div className="report-reason-grid">
          <div className={`report-primary-reason ${reason ? healthFindingClass(reason.severity) : "info"}`}>
            <span>Motivo principal</span>
            <strong>{reason ? reportHealthTitle(reason) : "Sem motivo crítico detectado"}</strong>
            <p>{reason ? reportHealthDetail(reason) : "Nenhum bloqueio ou alerta foi retornado pela análise atual."}</p>
            <small>{reason ? reportHealthAction(reason) : "Continue monitorando os indicadores antes de iniciar uma impressão longa."}</small>
          </div>
          <div className="report-plain-box">
            <span>Leitura para operador</span>
            <p>
              “Não imprimir” significa que o Printora encontrou um bloqueio objetivo, como Klipper fora de ready,
              Moonraker sem resposta ou comparação crítica de snapshot. “Monitorar” significa atenção, mas não bloqueio automático.
            </p>
          </div>
        </div>

        <div className="report-findings report-health-findings">
          {health?.items.length ? (
            health.items.map((item) => (
              <div key={item.key} className={`report-finding ${healthFindingClass(item.severity)}`}>
                <div>
                  <strong>{reportHealthTitle(item)}</strong>
                  <span>{item.ok ? "OK" : item.severity === "blocker" ? "Bloqueia" : "Revisar"}</span>
                </div>
                <p>{reportHealthDetail(item)}</p>
                <small>{reportHealthAction(item)}</small>
              </div>
            ))
          ) : (
            <p className="muted">Nenhum item de health carregado.</p>
          )}
        </div>
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Indicadores explicados</h2>
            <p>Cada número informa o que significa. A latência é da comunicação Printora ↔ Moonraker na rede local.</p>
          </div>
        </div>
        <div className="report-metric-grid">
          {health?.metrics
            ? Object.entries(health.metrics).map(([key, value]) => (
                <div key={key} className={key === "api_latency_ms" ? "report-metric-card report-metric-card-emphasis" : "report-metric-card"}>
                  <span>{reportMetricLabel(key)}</span>
                  <strong>{formatReportMetricValue(key, value)}</strong>
                  <p>{reportMetricHelp(key)}</p>
                </div>
              ))
            : <p className="muted">Sem métricas carregadas.</p>}
        </div>
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Rede e DNS</h2>
            <p>Teste read-only do caminho Android → Raspberry e, quando há SSH, do Moonraker visto pela própria Raspberry.</p>
          </div>
          <strong>{networkDiagnostics?.recommendation ?? "Aguardando diagnóstico"}</strong>
        </div>
        <div className="report-metric-grid">
          <div className="report-metric-card">
            <span>DNS no Android</span>
            <strong>{formatMilliseconds(networkDiagnostics?.dns.duration_ms)}</strong>
            <p>{networkDiagnostics?.dns.addresses[0] ? `${networkDiagnostics.host} → ${networkDiagnostics.dns.addresses[0]}` : networkDiagnostics?.dns.error ?? "Sem leitura."}</p>
          </div>
          <div className="report-metric-card">
            <span>URL cadastrada</span>
            <strong>{formatMilliseconds(networkDiagnostics?.configured_http.total_ms)}</strong>
            <p>{networkDiagnostics?.configured_http.ok ? "Moonraker respondeu pela URL configurada." : networkDiagnostics?.configured_http.error ?? "Sem leitura."}</p>
          </div>
          <div className="report-metric-card">
            <span>IP direto</span>
            <strong>{formatMilliseconds(networkDiagnostics?.direct_ip_http?.total_ms)}</strong>
            <p>{networkDiagnostics?.direct_ip_http?.url ?? "Sem IP resolvido para comparar."}</p>
          </div>
          <div className="report-metric-card">
            <span>Ping</span>
            <strong>{networkDiagnostics?.ping.rtt ? networkDiagnostics.ping.rtt.split("/")[1] + " ms" : "-"}</strong>
            <p>{typeof networkDiagnostics?.ping.packet_loss_percent === "number" ? `${networkDiagnostics.ping.packet_loss_percent}% de perda` : networkDiagnostics?.ping.error ?? "Sem leitura."}</p>
          </div>
          <div className="report-metric-card report-metric-card-emphasis">
            <span>Moonraker local via SSH</span>
            <strong>{formatMilliseconds(networkDiagnostics?.ssh?.moonraker_local_ms)}</strong>
            <p>{networkDiagnostics?.ssh?.ok ? `Host ${networkDiagnostics.ssh.hostname ?? networkDiagnostics.ssh.target}` : networkDiagnostics?.ssh?.error ?? "SSH não executado ou sem credencial."}</p>
          </div>
          <div className="report-metric-card">
            <span>Wi-Fi Raspberry</span>
            <strong>{networkDiagnostics?.ssh?.wifi?.signal ?? "-"}</strong>
            <p>{networkDiagnostics?.ssh?.wifi?.tx_bitrate ?? networkDiagnostics?.ssh?.wifi?.ssid ?? "Sem leitura via SSH."}</p>
          </div>
        </div>
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Evidências e compartilhamento</h2>
            <p>Snapshots, comparação e relatório sanitizado para enviar sem dados sensíveis.</p>
          </div>
          <button type="button" onClick={() => setActiveModal("sanitized-report")}>
            <FileText size={16} />
            Relatório seguro
          </button>
        </div>

        <div className="report-snapshot-layout">
          <div className="report-snapshot-current">
            <span>Snapshot atual</span>
            <strong>{currentSnapshot ? `#${currentSnapshot.id}` : "Nenhum snapshot"}</strong>
            <p>{currentSnapshot?.created_at ?? "Use o botão Snapshot no topo para registrar uma leitura."}</p>
            <small>{currentSnapshot ? formatUnknown(currentSnapshot.summary) : "Snapshots ajudam a comparar mudanças depois de updates ou ajustes."}</small>
          </div>

          <div className="report-snapshot-compare">
            <div className="form-grid two-columns">
              <label className="form-field">
                <span>Base</span>
                <select value={fromSnapshotId ?? ""} onChange={(event) => setFromSnapshotId(Number(event.target.value))}>
                  {snapshots.map((snapshot) => (
                    <option key={snapshot.id} value={snapshot.id}>
                      #{snapshot.id} · {snapshot.created_at}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-field">
                <span>Atual</span>
                <select value={toSnapshotId ?? ""} onChange={(event) => setToSnapshotId(Number(event.target.value))}>
                  {snapshots.map((snapshot) => (
                    <option key={snapshot.id} value={snapshot.id}>
                      #{snapshot.id} · {snapshot.created_at}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button
              type="button"
              onClick={() => void compareSnapshots()}
              disabled={!fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId || loading}
            >
              <RefreshCw size={16} />
              Comparar snapshots
            </button>
          </div>
        </div>

        {snapshotDiff ? (
          <div className={`report-diff ${snapshotDiff.highest_severity}`}>
            <strong>{snapshotDiff.summary}</strong>
            <div className="report-findings">
              {snapshotDiff.changes.length === 0 ? <p className="muted">Nenhuma mudança relevante detectada.</p> : null}
              {snapshotDiff.changes.map((change) => (
                <div key={`${change.field}-${change.title}`} className={`report-finding ${change.severity}`}>
                  <div>
                    <strong>{change.title}</strong>
                    <span>{formatSeverity(change.severity)}</span>
                  </div>
                  <p>{change.detail}</p>
                  <small>Antes: {formatUnknown(change.before)} · Depois: {formatUnknown(change.after)}</small>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Backup e restore seguro</h2>
            <p>Relatório não cadastra nada por padrão. As ações técnicas ficam em modal e continuam protegidas.</p>
          </div>
          <div className="report-action-row">
            <button type="button" onClick={() => setActiveModal("backup-policy")}>Criar política</button>
            <button type="button" onClick={() => setActiveModal("backup-compare")}>Comparar backups</button>
            <button type="button" onClick={() => setActiveModal("restore-plan")}>Planejar restore</button>
          </div>
        </div>

        <div className="report-backup-grid">
          <div className="report-plain-box">
            <span>Políticas</span>
            <strong>{backupPolicies.length}</strong>
            <p>Define o que deve entrar no backup. A criação é opcional e abre em modal.</p>
          </div>
          <div className="report-plain-box">
            <span>Histórico</span>
            <strong>{backupRuns.length}</strong>
            <p>Registros de simulação ou execução local da impressora selecionada.</p>
          </div>
          <div className="report-plain-box">
            <span>Restore real</span>
            <strong>Bloqueado</strong>
            <p>O Printora monta plano e gate, mas não sobrescreve arquivo de configuração automaticamente.</p>
          </div>
        </div>

        <div className="report-list">
          {backupPolicies.length === 0 ? <p className="muted">Nenhuma política de backup cadastrada.</p> : null}
          {backupPolicies.map((policy) => (
            <div key={policy.id} className="report-list-row">
              <div>
                <strong>{policy.name}</strong>
                <span>{policy.source_path}</span>
                <small>Destino: {policy.destination_path} · {policy.dry_run_only ? "somente simulação" : "execução local habilitada"}</small>
              </div>
              <div className="report-action-row">
                <button type="button" onClick={() => void createBackupDryRun(policy.id)} disabled={loading}>Simular</button>
                <button type="button" onClick={() => void executeLocalBackup(policy.id)} disabled={loading || policy.dry_run_only}>Executar local</button>
              </div>
            </div>
          ))}
        </div>

        {backupCompareResult ? (
          <div className="report-result-box">
            <strong>{backupCompareResult.summary}</strong>
            <small>Adicionados: {backupCompareResult.added.join(", ") || "-"}</small>
            <small>Removidos: {backupCompareResult.removed.join(", ") || "-"}</small>
            <small>Alterados: {backupCompareResult.changed.join(", ") || "-"}</small>
          </div>
        ) : null}
        {backupRestorePlan ? (
          <div className="report-result-box">
            <strong>Restore planejado · bloqueado: {formatBoolean(backupRestorePlan.blocked)}</strong>
            <small>{backupRestorePlan.message}</small>
            <pre>{backupRestorePlan.planned_commands.join("\n")}</pre>
          </div>
        ) : null}
        {backupRestoreGate ? (
          <div className="report-result-box">
            <strong>Gate restore · confirmação aceita: {formatBoolean(backupRestoreGate.accepted_confirmation)}</strong>
            <small>{backupRestoreGate.message}</small>
          </div>
        ) : null}
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Detalhes técnicos</h2>
            <p>Dados para diagnóstico avançado, sem virar a leitura principal para o usuário leigo.</p>
          </div>
        </div>
        <div className="report-tech-grid">
          <TechBlock title="Moonraker" rows={[
            ["Conexão", moonrakerState],
            ["URL cadastrada", status?.moonraker_url ?? "-"],
            ["Klippy", status?.server?.klippy_state ?? "-"],
            ["Versão Moonraker", status?.server?.moonraker_version ?? "-"],
          ]} />
          <TechBlock title="Klipper" rows={[
            ["Estado", status?.printer?.state ?? "-"],
            ["Mensagem", status?.printer?.state_message ?? "-"],
            ["Versão", status?.printer?.software_version ?? "-"],
          ]} />
          <TechBlock title="Checklist" rows={[
            ["Pode imprimir", checklist?.can_print ? "Sim" : "Não"],
            ["Origem", checklist ? formatChecklistDataState(checklist.data_state) : "-"],
            ["Resumo", checklist?.summary ?? "-"],
          ]} />
        </div>
      </article>

      <article className="panel wide panel-section panel-reports report-section">
        <div className="report-section-heading">
          <div>
            <h2>Auditoria somente leitura</h2>
            <p>Achados de plugins e configuração. O Printora orienta, mas não remove nada daqui.</p>
          </div>
          <strong>{audit?.summary ?? "Aguardando dados"}</strong>
        </div>
        <div className="report-status-grid">
          <ReportStatusCard icon={ShieldCheck} label="Corrigir agora" value={audit?.counts.corrigir_agora ?? 0} detail="Itens com risco maior." tone={(audit?.counts.corrigir_agora ?? 0) > 0 ? "danger" : "ok"} />
          <ReportStatusCard icon={History} label="Monitorar" value={audit?.counts.monitorar ?? 0} detail="Itens aceitáveis com acompanhamento." tone={(audit?.counts.monitorar ?? 0) > 0 ? "warning" : "neutral"} />
          <ReportStatusCard icon={AlertTriangle} label="Confirmar" value={audit?.counts.precisa_confirmacao ?? 0} detail="Itens que dependem de decisão humana." tone="neutral" />
          <ReportStatusCard icon={ShieldCheck} label="Ignorar" value={audit?.counts.ignorar ?? 0} detail="Itens sem ação necessária." tone="ok" />
        </div>
        <div className="report-findings">
          {audit?.findings.length ? audit.findings.map((finding) => (
            <div key={finding.id} className={`report-finding ${finding.severity}`}>
              <div>
                <strong>{finding.title}</strong>
                <span>{finding.category} · {formatClassification(finding.classification)}</span>
              </div>
              <p>{finding.detail}</p>
              <small>{finding.safe_action}</small>
            </div>
          )) : <p className="muted">Nenhum achado de auditoria carregado.</p>}
        </div>
      </article>

      <ReportModals
        {...props}
        activeModal={activeModal}
        onClose={() => setActiveModal(null)}
        sanitizedMarkdown={sanitizedReport?.markdown ?? null}
      />
    </>
  );
}

function ReportStatusCard({
  detail,
  icon: Icon,
  label,
  tone,
  value,
}: {
  detail: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
  label: string;
  tone: "ok" | "warning" | "danger" | "neutral";
  value: number | string;
}) {
  return (
    <div className={`report-status-card ${tone}`}>
      <Icon size={19} strokeWidth={2.1} />
      <span>{label}</span>
      <strong>{formatReportValue(value)}</strong>
      <p>{detail}</p>
    </div>
  );
}

function formatMilliseconds(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(2).replace(".", ",")} s`;
  }
  return `${Math.round(value)} ms`;
}

function TechBlock({ rows, title }: { rows: Array<[string, string]>; title: string }) {
  return (
    <div className="report-tech-block">
      <h3>{title}</h3>
      {rows.map(([label, value]) => (
        <div key={label} className="metric">
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}
