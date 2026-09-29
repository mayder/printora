import React from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, ShieldCheck } from "lucide-react";
import { financeApi } from "../services/financeApi";
import type { FinanceOverview, FinanceReadiness, FinanceRow } from "../types/finance";
import type { ScreenPropsFor } from "./ScreenProps";

type Props = ScreenPropsFor<"authUser" | "setError">;
type View = "summary" | "orders" | "ledger" | "reconciliations" | "disputes" | "payouts";

const emptyOverview: FinanceOverview = {
  counts: {}, orders: [], payments: [], ledger: [], disputes: [], payouts: [], reconciliations: [],
};

const views: Array<{ key: View; label: string }> = [
  { key: "summary", label: "Visão geral" },
  { key: "orders", label: "Pedidos e pagamentos" },
  { key: "ledger", label: "Ledger" },
  { key: "reconciliations", label: "Reconciliação" },
  { key: "disputes", label: "Disputas" },
  { key: "payouts", label: "Repasses" },
];

export function FinanceAdminScreen({ authUser, setError }: Props) {
  const [overview, setOverview] = React.useState<FinanceOverview>(emptyOverview);
  const [readiness, setReadiness] = React.useState<FinanceReadiness | null>(null);
  const [view, setView] = React.useState<View>("summary");
  const [selected, setSelected] = React.useState<FinanceRow | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [accessDenied, setAccessDenied] = React.useState(false);

  async function load() {
    if (!authUser) return;
    setLoading(true);
    setAccessDenied(false);
    try {
      const [overviewResult, readinessResult] = await Promise.allSettled([
        financeApi.overview(), financeApi.readiness(),
      ]);
      if (overviewResult.status === "rejected" && readinessResult.status === "rejected") {
        setAccessDenied(true);
        return;
      }
      if (overviewResult.status === "fulfilled") setOverview(overviewResult.value);
      if (readinessResult.status === "fulfilled") setReadiness(readinessResult.value);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao carregar finanças");
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => { void load(); }, [authUser?.id]);
  React.useEffect(() => { setSelected(null); }, [view]);

  if (accessDenied) {
    return (
      <section className="finance-access-state">
        <ShieldCheck size={28} />
        <h2>Acesso financeiro segregado</h2>
        <p>Sua conta não possui um papel financeiro ativo. Solicite acesso ao administrador da plataforma.</p>
      </section>
    );
  }

  const rows = rowsForView(view, overview);
  return (
    <div className="finance-screen">
      <section className="finance-heading">
        <div>
          <span className="eyebrow">Operação segregada</span>
          <h2>Finanças</h2>
          <p>Pedidos, ledger, reconciliação, disputas e repasses em superfícies independentes.</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void load()} disabled={loading}>
          <RefreshCw size={16} /> {loading ? "Atualizando" : "Atualizar"}
        </button>
      </section>

      <nav className="finance-tabs" aria-label="Áreas financeiras">
        {views.map((item) => (
          <button key={item.key} type="button" className={view === item.key ? "active" : ""} onClick={() => setView(item.key)}>
            {item.label}
          </button>
        ))}
      </nav>

      {view === "summary" ? (
        <FinanceSummary overview={overview} readiness={readiness} />
      ) : (
        <FinanceList view={view} rows={rows} selected={selected} onSelect={setSelected} />
      )}
    </div>
  );
}

function FinanceSummary({ overview, readiness }: { overview: FinanceOverview; readiness: FinanceReadiness | null }) {
  return (
    <div className="finance-summary">
      <section className="finance-metrics">
        {Object.entries(overview.counts).map(([key, value]) => (
          <article key={key}><span>{label(key)}</span><strong>{value}</strong></article>
        ))}
      </section>
      <section className="finance-readiness">
        <div className="finance-status-title">
          {readiness?.real_payments_allowed ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
          <div><h3>Prontidão para pagamentos</h3><p>Dinheiro real permanece indisponível.</p></div>
        </div>
        <dl>
          <div><dt>Modo atual</dt><dd>{readiness?.payment_mode ?? "indisponível"}</dd></div>
          <div><dt>Controles pendentes</dt><dd>{readiness?.pending_controls.length ?? "—"}</dd></div>
          <div><dt>Controles bloqueados</dt><dd>{readiness?.blocked_controls.length ?? "—"}</dd></div>
          <div><dt>Auditorias fora da retenção</dt><dd>{readiness?.expired_audit_rows_preview ?? "—"}</dd></div>
        </dl>
      </section>
    </div>
  );
}

function FinanceList({ view, rows, selected, onSelect }: {
  view: View; rows: FinanceRow[]; selected: FinanceRow | null; onSelect: (row: FinanceRow) => void;
}) {
  return (
    <div className="finance-list-layout">
      <section className="finance-list" aria-label={label(view)}>
        <h3>{label(view)}</h3>
        {rows.length === 0 ? <p className="muted">Nenhum registro nesta área.</p> : rows.map((row, index) => (
          <button key={`${view}-${index}`} type="button" onClick={() => onSelect(row)}>
            <strong>{String(row.public_id ?? row.external_key ?? "Registro")}</strong>
            <span>{String(row.status ?? row.operation_type ?? "")}</span>
            <small>{formatMoney(row.amount_minor ?? row.total_minor, row.currency)}</small>
          </button>
        ))}
      </section>
      <aside className="finance-detail" aria-label="Detalhe financeiro">
        <h3>Detalhe</h3>
        {!selected ? <p className="muted">Selecione um registro para inspecionar.</p> : (
          <dl>{Object.entries(selected).map(([key, value]) => <div key={key}><dt>{label(key)}</dt><dd>{String(value ?? "—")}</dd></div>)}</dl>
        )}
      </aside>
    </div>
  );
}

function rowsForView(view: View, data: FinanceOverview): FinanceRow[] {
  if (view === "orders") return [...data.orders, ...data.payments];
  if (view === "ledger") return data.ledger;
  if (view === "reconciliations") return data.reconciliations;
  if (view === "disputes") return data.disputes;
  if (view === "payouts") return data.payouts;
  return [];
}

function formatMoney(value: unknown, currency: unknown) {
  if (typeof value !== "number" || typeof currency !== "string") return "";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value / 100);
}

function label(value: string) {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}
