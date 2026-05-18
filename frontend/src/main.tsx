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

function App() {
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = React.useState<number | null>(null);
  const [newPrinterName, setNewPrinterName] = React.useState("Voron - Mayder");
  const [newPrinterUrl, setNewPrinterUrl] = React.useState("http://voron.local:7125");
  const [snapshots, setSnapshots] = React.useState<SnapshotRecord[]>([]);
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
  const [audit, setAudit] = React.useState<AuditResponse | null>(null);
  const [hostAudit, setHostAudit] = React.useState<AuditResponse | null>(null);
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

        <article className="panel wide">
          <h2>Snapshots</h2>
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

function formatUnknown(value: unknown) {
  if (typeof value === "string") {
    return value || "-";
  }
  return JSON.stringify(value);
}

createRoot(document.getElementById("root")!).render(<App />);
