import React from "react";
import { BrainCircuit, RefreshCw, ShieldCheck, ToggleLeft, ToggleRight } from "lucide-react";
import { dataIntelligenceApi } from "../services/dataIntelligenceApi";
import type {
  IntelligenceDashboard,
  IntelligenceLineage,
  IntelligenceModel,
  ModerationCase,
  RetentionPreview,
} from "../types/dataIntelligence";
import type { ScreenPropsFor } from "./ScreenProps";

type Props = ScreenPropsFor<"authUser" | "setError">;
type View = "dashboard" | "moderation" | "models" | "lineage";

const emptyDashboard: IntelligenceDashboard = {
  pipeline: [],
  impact: [],
  moderation: [],
  models: [],
  temporary_records: 0,
  lineage: [],
  replays: [],
  isolation: { source: "sanitized_events_only", oltp_writes: false, transformation_version: "analytics-v1" },
};

export function DataIntelligenceScreen({ authUser, setError }: Props) {
  const [dashboard, setDashboard] = React.useState(emptyDashboard);
  const [moderation, setModeration] = React.useState<ModerationCase[]>([]);
  const [retention, setRetention] = React.useState<RetentionPreview | null>(null);
  const [view, setView] = React.useState<View>("dashboard");
  const [selectedCase, setSelectedCase] = React.useState<ModerationCase | null>(null);
  const [selectedModel, setSelectedModel] = React.useState<IntelligenceModel | null>(null);
  const [selectedLineage, setSelectedLineage] = React.useState<IntelligenceLineage | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [accessDenied, setAccessDenied] = React.useState(false);

  async function load() {
    if (!authUser) return;
    setLoading(true);
    setAccessDenied(false);
    try {
      const [dashboardResult, moderationResult, retentionResult] = await Promise.all([
        dataIntelligenceApi.dashboard(),
        dataIntelligenceApi.moderation(),
        dataIntelligenceApi.retentionPreview(),
      ]);
      setDashboard(dashboardResult);
      setModeration(moderationResult.items);
      setRetention(retentionResult);
    } catch (error) {
      if (error instanceof Error && error.message.toLowerCase().includes("restrita")) {
        setAccessDenied(true);
      } else {
        setError(error instanceof Error ? error.message : "Falha ao carregar inteligência de dados");
      }
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => { void load(); }, [authUser?.id]);
  React.useEffect(() => {
    setSelectedCase(null);
    setSelectedModel(null);
    setSelectedLineage(null);
  }, [view]);

  if (accessDenied) {
    return <section className="intelligence-access"><ShieldCheck /><h2>Acesso segregado</h2><p>Esta área exige permissão administrativa.</p></section>;
  }

  return (
    <div className="intelligence-screen">
      <section className="intelligence-heading">
        <div><span className="eyebrow">Consumidor isolado</span><h2>Dados e inteligência</h2><p>Eventos sanitizados, moderação humana e modelos com fallback controlado.</p></div>
        <button type="button" className="secondary-button" onClick={() => void load()} disabled={loading}><RefreshCw size={16} />{loading ? "Atualizando" : "Atualizar"}</button>
      </section>
      <nav className="intelligence-tabs" aria-label="Áreas de inteligência">
        {(["dashboard", "moderation", "models", "lineage"] as View[]).map((item) => (
          <button key={item} type="button" className={view === item ? "active" : ""} onClick={() => setView(item)}>{label(item)}</button>
        ))}
      </nav>
      {view === "dashboard" && <Dashboard data={dashboard} retention={retention} />}
      {view === "moderation" && <ModerationList items={moderation} selected={selectedCase} onSelect={setSelectedCase} onReviewed={load} />}
      {view === "models" && <ModelList items={dashboard.models} selected={selectedModel} onSelect={setSelectedModel} onChanged={load} />}
      {view === "lineage" && <LineageList items={dashboard.lineage} selected={selectedLineage} onSelect={setSelectedLineage} replays={dashboard.replays} />}
    </div>
  );
}

function Dashboard({ data, retention }: { data: IntelligenceDashboard; retention: RetentionPreview | null }) {
  const counts = Object.fromEntries(data.pipeline.map((item) => [item.status, item.total]));
  return <div className="intelligence-dashboard">
    <section className="intelligence-metrics">
      <article><span>Processados</span><strong>{counts.processed ?? 0}</strong></article>
      <article><span>Pendentes</span><strong>{counts.pending ?? 0}</strong></article>
      <article><span>Modelos</span><strong>{data.models.length}</strong></article>
      <article><span>Temporários</span><strong>{data.temporary_records}</strong></article>
    </section>
    <section className="intelligence-isolation"><BrainCircuit /><div><h3>Contrato de isolamento</h3><p>Fonte: eventos sanitizados. Escrita em OLTP: {data.isolation.oltp_writes ? "permitida" : "bloqueada"}. Transformação {data.isolation.transformation_version}.</p></div></section>
    <section className="intelligence-table"><h3>Impacto e qualidade</h3>{data.impact.length === 0 ? <p className="muted">Nenhuma métrica processada.</p> : data.impact.map((metric) => <div key={`${metric.metric_name}:${metric.dimension_key}`}><strong>{metric.metric_name}</strong><span>{metric.dimension_key}</span><small>{metric.samples} amostras · média {Number(metric.average_value).toFixed(2)}</small></div>)}</section>
    <section className="intelligence-table"><h3>Retenção</h3><p>Modo {retention?.mode ?? "indisponível"}; nenhuma exclusão executada. Expirados: {retention?.expired.reduce((total, item) => total + Number(item.total ?? 0), 0) ?? 0}.</p></section>
  </div>;
}

function ModerationList({ items, selected, onSelect, onReviewed }: { items: ModerationCase[]; selected: ModerationCase | null; onSelect: (item: ModerationCase) => void; onReviewed: () => Promise<void> }) {
  async function review(decision: "approved" | "rejected") {
    if (!selected) return;
    await dataIntelligenceApi.reviewCase(selected.case_key, decision, "Revisão humana registrada no console administrativo.");
    await onReviewed();
  }
  return <div className="intelligence-split"><section className="intelligence-list"><h3>Fila multilíngue</h3>{items.map((item) => <button key={item.case_key} type="button" onClick={() => onSelect(item)}><strong>{item.entity_type}</strong><span>{item.detected_language} · {Math.round(item.confidence * 100)}%</span><small>{item.status}</small></button>)}</section><aside className="intelligence-detail"><h3>Revisão humana</h3>{!selected ? <p className="muted">Selecione um caso.</p> : <><p>Rótulos: {selected.labels.join(", ") || "nenhum"}</p><p>Alto impacto: {selected.human_review_required ? "sim" : "não"}</p><div className="button-row"><button type="button" className="secondary-button" onClick={() => void review("approved")}>Aprovar</button><button type="button" className="danger-button" onClick={() => void review("rejected")}>Rejeitar</button></div><small>Recursos são registrados pela API e sempre exigem nova revisão humana.</small></>}</aside></div>;
}

function ModelList({ items, selected, onSelect, onChanged }: { items: IntelligenceModel[]; selected: IntelligenceModel | null; onSelect: (item: IntelligenceModel) => void; onChanged: () => Promise<void> }) {
  async function toggle() {
    if (!selected) return;
    await dataIntelligenceApi.controlModel(selected, { enabled: selected.enabled, kill_switch: !selected.kill_switch, canary_percent: selected.canary_percent, drift_score: selected.drift_score });
    await onChanged();
  }
  return <div className="intelligence-split"><section className="intelligence-list"><h3>Registro de modelos</h3>{items.map((item) => <button key={`${item.model_key}:${item.version}`} type="button" onClick={() => onSelect(item)}><strong>{item.model_key}</strong><span>{item.version} · {item.owner}</span><small>{item.kill_switch ? "fallback ativo" : "modelo ativo"}</small></button>)}</section><aside className="intelligence-detail"><h3>Contrato do modelo</h3>{!selected ? <p className="muted">Selecione um modelo.</p> : <><dl><div><dt>Dataset</dt><dd>{selected.dataset_name} {selected.dataset_version}</dd></div><div><dt>Licença</dt><dd>{selected.dataset_license}</dd></div><div><dt>Canário</dt><dd>{selected.canary_percent}%</dd></div><div><dt>Fallback</dt><dd>{selected.fallback_strategy}</dd></div></dl><button type="button" className="secondary-button" onClick={() => void toggle()}>{selected.kill_switch ? <ToggleLeft size={17} /> : <ToggleRight size={17} />}{selected.kill_switch ? "Desativar kill switch" : "Ativar kill switch"}</button></>}</aside></div>;
}

function LineageList({ items, selected, onSelect, replays }: { items: IntelligenceLineage[]; selected: IntelligenceLineage | null; onSelect: (item: IntelligenceLineage) => void; replays: Array<Record<string, unknown>> }) {
  return <div className="intelligence-split"><section className="intelligence-list"><h3>Lineage e replay</h3>{items.map((item) => <button key={`${item.source_event_id}:${item.derivative_key}`} type="button" onClick={() => onSelect(item)}><strong>{item.derivative_type}</strong><span>{item.derivative_key}</span><small>{item.transformation_version}</small></button>)}</section><aside className="intelligence-detail"><h3>Proveniência</h3>{selected ? <dl>{Object.entries(selected).map(([key, value]) => <div key={key}><dt>{label(key)}</dt><dd>{String(value)}</dd></div>)}</dl> : <p className="muted">Selecione uma derivação.</p>}<p>Replays registrados: {replays.length}. A repetição preserva chaves determinísticas.</p></aside></div>;
}

function label(value: string) { return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase()); }
