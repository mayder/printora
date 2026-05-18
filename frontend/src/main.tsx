import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type ChecklistItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: string;
  detail: string;
};

type ChecklistResponse = {
  can_print: boolean;
  summary: string;
  items: ChecklistItem[];
};

type MoonrakerStatus = {
  connected: boolean;
  moonraker_url: string;
  error?: string;
  printer?: {
    state?: string;
    state_message?: string;
    software_version?: string;
  };
  server?: {
    moonraker_version?: string;
    klippy_connected?: boolean;
    klippy_state?: string;
  };
};

type PrinterRecord = {
  id: number;
  name: string;
  moonraker_url: string;
  host_audit_mode: "disabled" | "local" | "ssh";
  host_audit_ssh_target?: string | null;
  location?: string | null;
  notes?: string | null;
  is_active: boolean;
};

type SnapshotRecord = {
  id: number;
  printer_id: number;
  created_at: string;
  snapshot_type: string;
  summary: Record<string, unknown>;
};

type SnapshotDiffItem = {
  field: string;
  title: string;
  severity: "info" | "monitorar" | "risco" | "bloqueio";
  before: unknown;
  after: unknown;
  detail: string;
};

type SnapshotDiff = {
  printer_id: number;
  from_snapshot_id: number;
  to_snapshot_id: number;
  summary: string;
  highest_severity: "info" | "monitorar" | "risco" | "bloqueio";
  changes: SnapshotDiffItem[];
};

type AuditFinding = {
  id: string;
  title: string;
  category: string;
  classification: "corrigir_agora" | "monitorar" | "ignorar" | "precisa_confirmacao";
  severity: "blocker" | "warning" | "info";
  detail: string;
  safe_action: string;
};

type AuditResponse = {
  connected: boolean;
  safe_mode: string;
  mode?: string;
  executed?: boolean;
  summary: string;
  counts: Record<string, number>;
  findings: AuditFinding[];
  section_summary?: Record<string, unknown>;
};

type HealthItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: "ok" | "info" | "warning" | "blocker";
  detail: string;
  action: string;
};

type HealthResponse = {
  connected: boolean;
  safe_mode: string;
  printer_id: number;
  moonraker_url: string;
  decision: "ok_para_imprimir" | "monitorar" | "nao_imprimir";
  summary: string;
  metrics: Record<string, unknown>;
  counts: Record<string, number>;
  items: HealthItem[];
};

type BackupPolicyRecord = {
  id: number;
  printer_id: number;
  name: string;
  source_path: string;
  destination_path: string;
  include_patterns: string[];
  exclude_patterns: string[];
  dry_run_only: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type BackupRunRecord = {
  id: number;
  printer_id: number;
  policy_id: number;
  created_at: string;
  status: string;
  dry_run: boolean;
  source_path: string;
  destination_path: string;
  include_patterns: string[];
  exclude_patterns: string[];
  total_files: number;
  total_bytes: number;
  message: string;
};

function App() {
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = React.useState<number | null>(null);
  const [newPrinterName, setNewPrinterName] = React.useState("Voron - Mayder");
  const [newPrinterUrl, setNewPrinterUrl] = React.useState("http://voron.local:7125");
  const [snapshots, setSnapshots] = React.useState<SnapshotRecord[]>([]);
  const [fromSnapshotId, setFromSnapshotId] = React.useState<number | null>(null);
  const [toSnapshotId, setToSnapshotId] = React.useState<number | null>(null);
  const [snapshotDiff, setSnapshotDiff] = React.useState<SnapshotDiff | null>(null);
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
  const [audit, setAudit] = React.useState<AuditResponse | null>(null);
  const [hostAudit, setHostAudit] = React.useState<AuditResponse | null>(null);
  const [backupPolicies, setBackupPolicies] = React.useState<BackupPolicyRecord[]>([]);
  const [backupRuns, setBackupRuns] = React.useState<BackupRunRecord[]>([]);
  const [backupName, setBackupName] = React.useState("Config backup");
  const [backupSourcePath, setBackupSourcePath] = React.useState("/home/pi/printer_data/config");
  const [backupDestinationPath, setBackupDestinationPath] = React.useState(
    "/home/pi/printer_data/backups/mayderprintlab",
  );
  const [backupDryRunOnly, setBackupDryRunOnly] = React.useState(true);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const statusResponse = await fetch("/api/moonraker/status");
      const statusPayload = (await statusResponse.json()) as MoonrakerStatus;
      setStatus(statusPayload);

      const checklistResponse = await fetch("/api/checklist/post-update");
      if (checklistResponse.ok) {
        setChecklist((await checklistResponse.json()) as ChecklistResponse);
      }

      const auditResponse = await fetch("/api/audit/read-only");
      if (auditResponse.ok) {
        setAudit((await auditResponse.json()) as AuditResponse);
      }

      const hostAuditResponse = await fetch("/api/audit/host-read-only");
      if (hostAuditResponse.ok) {
        setHostAudit((await hostAuditResponse.json()) as AuditResponse);
      }

      await loadPrinters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadPrinters() {
    const response = await fetch("/api/printers");
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { printers: PrinterRecord[] };
    setPrinters(payload.printers);
    const nextSelected = selectedPrinterId ?? payload.printers[0]?.id ?? null;
    setSelectedPrinterId(nextSelected);
    if (nextSelected) {
      await loadSnapshots(nextSelected);
      await loadPrinterHealth(nextSelected);
      await loadBackups(nextSelected);
    }
  }

  async function createPrinter(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/printers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newPrinterName,
          moonraker_url: newPrinterUrl,
          host_audit_mode: "disabled",
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const created = (await response.json()) as PrinterRecord;
      await loadPrinters();
      setSelectedPrinterId(created.id);
      await loadPrinterHealth(created.id);
      await loadBackups(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadSelectedPrinterStatus() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/moonraker/status`);
      const payload = (await response.json()) as MoonrakerStatus;
      setStatus(payload);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function captureSnapshot() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/snapshots/moonraker`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadSnapshots(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadSnapshots(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/snapshots`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { snapshots: SnapshotRecord[] };
    setSnapshots(payload.snapshots);
    setSnapshotDiff(null);
    if (payload.snapshots.length >= 2) {
      setFromSnapshotId(payload.snapshots[1].id);
      setToSnapshotId(payload.snapshots[0].id);
    } else {
      setFromSnapshotId(payload.snapshots[0]?.id ?? null);
      setToSnapshotId(payload.snapshots[0]?.id ?? null);
    }
  }

  async function loadPrinterHealth(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/health`);
    if (!response.ok) {
      return;
    }
    setHealth((await response.json()) as HealthResponse);
  }

  async function loadBackups(printerId: number) {
    const [policiesResponse, runsResponse] = await Promise.all([
      fetch(`/api/printers/${printerId}/backup/policies`),
      fetch(`/api/printers/${printerId}/backup/runs`),
    ]);
    if (policiesResponse.ok) {
      const payload = (await policiesResponse.json()) as { policies: BackupPolicyRecord[] };
      setBackupPolicies(payload.policies);
    }
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: BackupRunRecord[] };
      setBackupRuns(payload.runs);
    }
  }

  async function createBackupPolicy(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/backup/policies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: backupName,
          source_path: backupSourcePath,
          destination_path: backupDestinationPath,
          dry_run_only: backupDryRunOnly,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function executeLocalBackup(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/backup/policies/${policyId}/execute-local`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupDryRun(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/backup/policies/${policyId}/dry-run`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareSnapshots() {
    if (!selectedPrinterId || !fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/printers/${selectedPrinterId}/snapshots/diff?from_id=${fromSnapshotId}&to_id=${toSnapshotId}`,
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSnapshotDiff((await response.json()) as SnapshotDiff);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    void loadStatus();
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>MayderPrintLab</h1>
          <p>Toolkit de firmware, manutenção e diagnóstico para Klipper.</p>
        </div>
        <button type="button" onClick={() => void loadStatus()} disabled={loading}>
          {loading ? "Atualizando" : "Atualizar"}
        </button>
      </header>

      {error ? <section className="alert danger">{error}</section> : null}

      <section className="grid">
        <article className="panel wide">
          <h2>Impressoras</h2>
          <div className="printer-toolbar">
            <label>
              Impressora ativa
              <select
                value={selectedPrinterId ?? ""}
                onChange={(event) => {
                  const printerId = Number(event.target.value);
                  setSelectedPrinterId(printerId);
                  void loadSnapshots(printerId);
                  void loadPrinterHealth(printerId);
                  void loadBackups(printerId);
                }}
              >
                <option value="" disabled>
                  Selecione
                </option>
                {printers.map((printer) => (
                  <option key={printer.id} value={printer.id}>
                    {printer.name}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" onClick={() => void loadSelectedPrinterStatus()} disabled={!selectedPrinterId || loading}>
              Ler selecionada
            </button>
            <button type="button" onClick={() => void captureSnapshot()} disabled={!selectedPrinterId || loading}>
              Capturar snapshot
            </button>
          </div>
          <form className="printer-form" onSubmit={(event) => void createPrinter(event)}>
            <input
              aria-label="Nome da impressora"
              value={newPrinterName}
              onChange={(event) => setNewPrinterName(event.target.value)}
              placeholder="Nome da impressora"
            />
            <input
              aria-label="URL Moonraker"
              value={newPrinterUrl}
              onChange={(event) => setNewPrinterUrl(event.target.value)}
              placeholder="http://printer.local:7125"
            />
            <button type="submit" disabled={loading}>
              Cadastrar
            </button>
          </form>
          <div className="printer-list">
            {printers.map((printer) => (
              <div key={printer.id} className="printer-row">
                <strong>{printer.name}</strong>
                <span>{printer.moonraker_url}</span>
                <small>{printer.host_audit_mode}</small>
              </div>
            ))}
          </div>
        </article>

        <article className={`panel wide health ${healthPanelClass(health?.decision)}`}>
          <div className="panel-heading">
            <h2>Health Check</h2>
            <strong>{health?.summary ?? "Aguardando dados"}</strong>
          </div>
          <div className="health-metrics">
            <Badge label="Decisão" value={formatDecision(health?.decision)} />
            <Badge label="Bloqueios" value={health?.counts.blocker ?? 0} />
            <Badge label="Alertas" value={health?.counts.warning ?? 0} />
            <Badge label="Snapshots" value={formatUnknown(health?.metrics.snapshot_count ?? "-")} />
          </div>
          <div className="section-summary">
            {health?.metrics
              ? Object.entries(health.metrics).map(([key, value]) => (
                  <Metric key={key} label={key} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {health?.items.map((item) => (
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

        <article className="panel wide">
          <div className="panel-heading">
            <h2>Backups</h2>
            <strong>Dry-run seguro</strong>
          </div>
          <form className="backup-form" onSubmit={(event) => void createBackupPolicy(event)}>
            <input
              aria-label="Nome da política"
              value={backupName}
              onChange={(event) => setBackupName(event.target.value)}
              placeholder="Nome"
            />
            <input
              aria-label="Origem do backup"
              value={backupSourcePath}
              onChange={(event) => setBackupSourcePath(event.target.value)}
              placeholder="/home/pi/printer_data/config"
            />
            <input
              aria-label="Destino do backup"
              value={backupDestinationPath}
              onChange={(event) => setBackupDestinationPath(event.target.value)}
              placeholder="/home/pi/printer_data/backups/mayderprintlab"
            />
            <label className="inline-check">
              <input
                type="checkbox"
                checked={backupDryRunOnly}
                onChange={(event) => setBackupDryRunOnly(event.target.checked)}
              />
              Somente dry-run
            </label>
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Criar política
            </button>
          </form>
          <div className="backup-list">
            {backupPolicies.length === 0 ? <p className="muted">Nenhuma política de backup cadastrada.</p> : null}
            {backupPolicies.map((policy) => (
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
          <div className="backup-runs">
            <h3>Histórico</h3>
            {backupRuns.length === 0 ? <p className="muted">Nenhum dry-run registrado.</p> : null}
            {backupRuns.map((run) => (
              <div key={run.id} className="backup-run-row">
                <strong>#{run.id} · {run.status}</strong>
                <span>{run.created_at}</span>
                <small>{run.message}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide">
          <h2>Snapshots</h2>
          {snapshots.length >= 2 ? (
            <div className="snapshot-compare">
              <label>
                Base
                <select
                  value={fromSnapshotId ?? ""}
                  onChange={(event) => setFromSnapshotId(Number(event.target.value))}
                >
                  {snapshots.map((snapshot) => (
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
                  onChange={(event) => setToSnapshotId(Number(event.target.value))}
                >
                  {snapshots.map((snapshot) => (
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
                  {snapshotDiff.changes.map((change) => (
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
            {snapshots.map((snapshot) => (
              <div key={snapshot.id} className="snapshot-row">
                <strong>#{snapshot.id}</strong>
                <span>{snapshot.created_at}</span>
                <span>{snapshot.snapshot_type}</span>
                <small>{formatUnknown(snapshot.summary)}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Moonraker</h2>
          <Metric label="Conexão" value={status?.connected ? "Conectado" : "Desconectado"} />
          <Metric label="URL" value={status?.moonraker_url ?? "-"} />
          <Metric label="Klippy" value={status?.server?.klippy_state ?? "-"} />
          <Metric label="Moonraker" value={status?.server?.moonraker_version ?? "-"} />
        </article>

        <article className="panel">
          <h2>Klipper</h2>
          <Metric label="Estado" value={status?.printer?.state ?? "-"} />
          <Metric label="Mensagem" value={status?.printer?.state_message ?? "-"} />
          <Metric label="Versão" value={status?.printer?.software_version ?? "-"} />
        </article>

        <article className={`panel ${checklist?.can_print ? "ok" : "warn"}`}>
          <h2>Checklist pós-update</h2>
          <strong className="summary">{checklist?.summary ?? "Aguardando dados"}</strong>
          <div className="checks">
            {checklist?.items.map((item) => (
              <div key={item.key} className="check">
                <span className={item.ok ? "dot good" : "dot bad"} />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide">
          <h2>Auditoria somente leitura</h2>
          <strong className="summary">{audit?.summary ?? "Aguardando dados"}</strong>
          <div className="audit-counts">
            <Badge label="Corrigir agora" value={audit?.counts.corrigir_agora ?? 0} />
            <Badge label="Monitorar" value={audit?.counts.monitorar ?? 0} />
            <Badge label="Precisa confirmação" value={audit?.counts.precisa_confirmacao ?? 0} />
            <Badge label="Ignorar" value={audit?.counts.ignorar ?? 0} />
          </div>
          <div className="findings">
            {audit?.findings.map((finding) => (
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

        <article className="panel wide">
          <h2>Auditoria do host</h2>
          <strong className="summary">{hostAudit?.summary ?? "Aguardando dados"}</strong>
          <div className="audit-counts">
            <Badge label="Modo" value={hostAudit?.mode ?? "-"} />
            <Badge label="Executou" value={hostAudit?.executed ? "sim" : "não"} />
            <Badge label="Monitorar" value={hostAudit?.counts.monitorar ?? 0} />
            <Badge label="Corrigir" value={hostAudit?.counts.corrigir_agora ?? 0} />
          </div>
          <div className="section-summary">
            {hostAudit?.section_summary
              ? Object.entries(hostAudit.section_summary).map(([key, value]) => (
                  <Metric key={key} label={key} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {hostAudit?.findings.map((finding) => (
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
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Badge({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="badge">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatClassification(classification: AuditFinding["classification"]) {
  return classification.replace("_", " ");
}

function formatSeverity(severity: SnapshotDiffItem["severity"]) {
  const labels: Record<SnapshotDiffItem["severity"], string> = {
    info: "informativo",
    monitorar: "monitorar",
    risco: "risco",
    bloqueio: "bloqueio",
  };
  return labels[severity];
}

function formatHealthSeverity(severity: HealthItem["severity"]) {
  const labels: Record<HealthItem["severity"], string> = {
    ok: "ok",
    info: "informativo",
    warning: "atenção",
    blocker: "bloqueio",
  };
  return labels[severity];
}

function formatDecision(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "OK";
  }
  if (decision === "monitorar") {
    return "Monitorar";
  }
  if (decision === "nao_imprimir") {
    return "Não imprimir";
  }
  return "-";
}

function healthPanelClass(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "ok";
  }
  if (decision === "nao_imprimir") {
    return "danger";
  }
  return "warn";
}

function healthFindingClass(severity: HealthItem["severity"]) {
  if (severity === "blocker") {
    return "blocker";
  }
  if (severity === "warning") {
    return "warning";
  }
  return "info";
}

function formatUnknown(value: unknown) {
  if (typeof value === "string") {
    return value || "-";
  }
  return JSON.stringify(value);
}

createRoot(document.getElementById("root")!).render(<App />);
