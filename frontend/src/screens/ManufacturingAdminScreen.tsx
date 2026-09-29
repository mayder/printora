import React from "react";
import { Factory, RefreshCw, ShieldCheck } from "lucide-react";
import { apiRequest } from "../services/http";
import type { ScreenPropsFor } from "./ScreenProps";

type Row = Record<string, string | number | null>;
type Overview = { orders: Row[]; incidents: Row[] };
type Props = ScreenPropsFor<"authUser" | "setError">;

export function ManufacturingAdminScreen({ authUser, setError }: Props) {
  const [data, setData] = React.useState<Overview>({ orders: [], incidents: [] });
  const [view, setView] = React.useState<"orders" | "incidents">("orders");
  const [selected, setSelected] = React.useState<Row | null>(null);
  const [denied, setDenied] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  async function load() {
    if (!authUser) return;
    setLoading(true);
    try {
      setData(await apiRequest<Overview>("/api/admin/manufacturing/overview"));
      setDenied(false);
    } catch (error) {
      if (error instanceof Error && error.message.includes("403")) setDenied(true);
      else setError(error instanceof Error ? error.message : "Falha ao carregar fabricação");
    } finally { setLoading(false); }
  }
  React.useEffect(() => { void load(); }, [authUser?.id]);
  React.useEffect(() => { setSelected(null); }, [view]);
  if (denied) return <section className="manufacturing-state"><ShieldCheck/><h2>Acesso produtivo segregado</h2><p>Sua conta não possui papel de produção, qualidade, logística ou segurança.</p></section>;
  const rows = data[view];
  return <div className="manufacturing-screen">
    <header><div><span className="eyebrow">Cadeia de custódia privada</span><h2><Factory size={24}/> Fabricação</h2><p>Ordens, qualidade, entrega e incidentes sem controle direto da impressora.</p></div><button className="secondary-button" onClick={() => void load()} disabled={loading}><RefreshCw size={16}/>{loading ? "Atualizando" : "Atualizar"}</button></header>
    <nav aria-label="Áreas de fabricação"><button className={view === "orders" ? "active" : ""} onClick={() => setView("orders")}>Ordens</button><button className={view === "incidents" ? "active" : ""} onClick={() => setView("incidents")}>Incidentes e recall</button></nav>
    <div className="manufacturing-layout"><section><h3>{view === "orders" ? "Ordens produtivas" : "Incidentes"}</h3>{rows.length === 0 ? <p className="muted">Nenhum registro.</p> : rows.map((row, index) => <button key={index} onClick={() => setSelected(row)}><strong>{String(row.public_id)}</strong><span>{String(row.state ?? row.status)}</span></button>)}</section><aside><h3>Detalhe</h3>{!selected ? <p className="muted">Selecione um registro.</p> : <dl>{Object.entries(selected).map(([key,value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{String(value ?? "—")}</dd></div>)}</dl>}</aside></div>
  </div>;
}
