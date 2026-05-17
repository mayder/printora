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

function App() {
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
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

createRoot(document.getElementById("root")!).render(<App />);
