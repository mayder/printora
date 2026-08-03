import * as React from "react";
import { CircleAlert, Download, LoaderCircle, ShieldCheck, XCircle } from "lucide-react";
import { meshRevisionApi } from "../../services/meshRevisionApi";
import type { MeshRepairOperation, MeshRevision, MeshRevisionReview } from "../../types/meshRevision";

interface Props {
  jobId: number;
  rawUnit: string;
  rawChecks: Record<string, unknown>;
  rawDimensions?: { x: number; y: number; z: number };
  setError: (message: string | null) => void;
  onModelApproved?: () => Promise<void>;
}

interface Suggestion {
  operation: MeshRepairOperation;
  label: string;
  explanation: string;
}

const numberCheck = (checks: Record<string, unknown>, key: string) => Number(checks[key] ?? 0);

const operationLabels: Record<MeshRepairOperation, string> = {
  clean: "limpeza de triângulos inválidos",
  orient_normals: "orientação das superfícies",
  close_holes: "fechamento controlado de buracos",
  remove_small_components: "remoção de fragmentos soltos",
  decimate: "redução controlada da malha",
  convert: "conversão do formato",
  scale: "ajuste de escala informado pela pessoa",
};

function suggest(checks: Record<string, unknown>): Suggestion | null {
  if (numberCheck(checks, "degenerate_triangle_count") > 0) return { operation: "clean", label: "Limpar a malha", explanation: "Remove triângulos quebrados e pontos repetidos sem alterar a peça original." };
  if (numberCheck(checks, "winding_conflict_count") > 0 || checks.inverted_closed_volume === true) return { operation: "orient_normals", label: "Corrigir o lado das superfícies", explanation: "Faz as superfícies apontarem para o lado correto." };
  if (numberCheck(checks, "hole_count") > 0) return { operation: "close_holes", label: "Fechar buracos pequenos", explanation: "Fecha apenas aberturas simples e preserva a versão anterior." };
  if (numberCheck(checks, "component_count") > 1) return { operation: "remove_small_components", label: "Remover fragmentos pequenos", explanation: "Mantém o objeto principal e remove pequenos pedaços soltos." };
  return null;
}

function exportBlocker(checks: Record<string, unknown>, unitKnown: boolean): string | null {
  if (!unitKnown) return "Confirme uma medida conhecida em milímetros antes de criar o arquivo final.";
  if (checks.self_intersection_count === "limit_exceeded") return "A malha é complexa demais para uma conferência automática segura.";
  if (numberCheck(checks, "self_intersection_count") > 0) return "Há superfícies cruzando umas às outras. Esta correção precisa de revisão especializada.";
  if (numberCheck(checks, "non_manifold_edge_count") > 0) return "Há junções complexas que não podem ser corrigidas automaticamente com segurança.";
  if (checks.watertight !== true) return "A superfície ainda não está completamente fechada.";
  return null;
}

export function MeshRepairPanel({ jobId, rawUnit, rawChecks, rawDimensions, setError, onModelApproved }: Props) {
  const [revisions, setRevisions] = React.useState<MeshRevision[]>([]);
  const [reviews, setReviews] = React.useState<MeshRevisionReview[]>([]);
  const [busy, setBusy] = React.useState(false);
  const [knownAxis, setKnownAxis] = React.useState<"x" | "y" | "z">("x");
  const [knownDimension, setKnownDimension] = React.useState("");
  const [reviewAxis, setReviewAxis] = React.useState<"x" | "y" | "z">("x");
  const [reviewDimension, setReviewDimension] = React.useState("");
  const [intendedUse, setIntendedUse] = React.useState<"decorative" | "prototype">("decorative");
  const [shapeReviewed, setShapeReviewed] = React.useState(false);
  const [limitationsAccepted, setLimitationsAccepted] = React.useState(false);
  const active = revisions.find((revision) => ["queued", "processing"].includes(revision.status));
  const latest = [...revisions].reverse().find((revision) => revision.status === "succeeded");
  const checks = latest?.qualification.checks ?? rawChecks;
  const dimensions = latest?.qualification.dimensions ?? rawDimensions;
  const recommendation = suggest(checks);
  const unit = latest?.unit ?? rawUnit;
  const unitKnown = ["mm", "millimeter", "millimetre"].includes(unit.toLowerCase());
  const finalBlocker = exportBlocker(checks, unitKnown);
  const finalFormatReady = latest?.output_format === "stl" || latest?.output_format === "3mf";
  const latestReview = latest ? [...reviews].reverse().find((review) => review.revision_id === latest.id) : undefined;

  React.useEffect(() => {
    let mounted = true;
    void Promise.all([meshRevisionApi.list(jobId), meshRevisionApi.listReviews(jobId)]).then(([rows, reviewRows]) => {
      if (mounted) { setRevisions(rows); setReviews(reviewRows); }
    }).catch(() => undefined);
    return () => { mounted = false; };
  }, [jobId]);

  React.useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => {
      void meshRevisionApi.list(jobId).then(setRevisions).catch(() => undefined);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [active?.id, jobId]);

  async function create(
    operation: MeshRepairOperation,
    outputFormat: "obj" | "stl" | "3mf",
    extraParameters: Record<string, unknown> = {},
  ) {
    setBusy(true);
    setError(null);
    try {
      const created = await meshRevisionApi.create(jobId, {
        operation,
        ...(latest ? { source_revision_id: latest.id } : {}),
        parameters: { output_format: outputFormat, ...extraParameters },
      });
      setRevisions((current) => [...current, created]);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível preparar a nova versão.");
    } finally {
      setBusy(false);
    }
  }

  function confirmScale() {
    const expected = Number(knownDimension);
    const observed = dimensions?.[knownAxis] ?? 0;
    if (!Number.isFinite(expected) || expected <= 0 || observed <= 0) {
      setError("Informe uma medida válida em milímetros.");
      return;
    }
    void create("scale", "obj", {
      scale_factor: expected / observed,
      known_axis: knownAxis,
      known_dimension_mm: expected,
    });
  }

  async function review(decision: "approve" | "reject") {
    if (!latest) return;
    const measured = Number(reviewDimension);
    if (decision === "approve" && (!Number.isFinite(measured) || measured <= 0)) {
      setError("Informe a medida que você conferiu no objeto.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const completed = await meshRevisionApi.review(jobId, latest.id, {
        decision,
        intended_use: intendedUse,
        ...(decision === "approve" ? { known_axis: reviewAxis, known_dimension_mm: measured } : {}),
        shape_reviewed: shapeReviewed,
        limitations_accepted: limitationsAccepted,
      });
      setReviews((current) => [...current, completed]);
      if (completed.decision === "approved_for_slicing") await onModelApproved?.();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível registrar sua revisão.");
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    if (!active) return;
    setBusy(true);
    try {
      const cancelled = await meshRevisionApi.cancel(jobId, active.id);
      setRevisions((current) => current.map((revision) => revision.id === cancelled.id ? cancelled : revision));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível cancelar a correção.");
    } finally {
      setBusy(false);
    }
  }

  async function download() {
    if (!latest?.output_format) return;
    setBusy(true);
    try {
      const blob = await meshRevisionApi.download(jobId, latest.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `modelo-revisado-${latest.id}.${latest.output_format}`;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível baixar esta versão.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="mesh-repair-panel" aria-labelledby="mesh-repair-title">
    <div className="photo-capture-heading"><ShieldCheck size={20} aria-hidden="true" /><div><h4 id="mesh-repair-title">Preparar para o fatiador</h4><p>Cada correção cria uma nova versão. A malha bruta nunca é alterada.</p></div></div>
    {active ? <div className="mesh-repair-status" role="status"><LoaderCircle className="reconstruction-spinner" size={18} /><div><strong>Preparando uma nova versão</strong><p>{active.next_action}</p></div><button type="button" className="secondary-button" disabled={busy} onClick={() => void cancel()}><XCircle size={16} /> Cancelar</button></div> : null}
    {!active && recommendation ? <div className="mesh-repair-recommendation"><div><strong>Próxima correção recomendada</strong><p>{recommendation.explanation}</p></div><button type="button" className="primary-button" disabled={busy} onClick={() => void create(recommendation.operation, "obj")}>{recommendation.label}</button></div> : null}
    {!active && !recommendation && !unitKnown ? <div className="mesh-scale-confirmation"><div><strong>Confirmar o tamanho real</strong><p>Meça um lado do objeto com régua ou paquímetro. Depois indique qual lado do modelo você mediu.</p></div><label>Lado medido<select value={knownAxis} onChange={(event) => setKnownAxis(event.target.value as "x" | "y" | "z")}><option value="x">Largura (X){dimensions ? ` — ${dimensions.x}` : ""}</option><option value="y">Profundidade (Y){dimensions ? ` — ${dimensions.y}` : ""}</option><option value="z">Altura (Z){dimensions ? ` — ${dimensions.z}` : ""}</option></select></label><label>Medida real em milímetros<input inputMode="decimal" type="number" min="0.1" max="2000" step="0.1" value={knownDimension} onChange={(event) => setKnownDimension(event.target.value)} /></label><button type="button" className="primary-button" disabled={busy || !knownDimension} onClick={confirmScale}>Aplicar medida</button><p className="photo-capture-note"><CircleAlert size={16} /> Confira se escolheu o lado correto. A alteração cria outra versão e pode ser desfeita.</p></div> : null}
    {!active && !recommendation && unitKnown && finalBlocker ? <div className="mesh-repair-export"><CircleAlert size={18} aria-hidden="true" /><div><strong>O arquivo final ainda está bloqueado</strong><p>{finalBlocker}</p></div></div> : null}
    {!active && !recommendation && !finalBlocker && !finalFormatReady ? <div className="mesh-repair-export"><div><strong>Escolha o arquivo para continuar</strong><p>O fatiador ainda deve conferir escala, espessura, suporte e limites da impressora.</p></div><div className="reconstruction-actions"><button type="button" className="primary-button" disabled={busy} onClick={() => void create("convert", "stl")}>Criar STL</button><button type="button" className="secondary-button" disabled={busy} onClick={() => void create("convert", "3mf")}>Criar 3MF</button></div></div> : null}
    {!active && finalFormatReady && !finalBlocker && !latestReview ? <div className="mesh-review-form"><div><strong>Revisão final antes do fatiamento</strong><p>Compare o modelo com o objeto real. Esta aprovação libera o arquivo no projeto, mas não envia nada à impressora.</p></div><label>Uso pretendido<select value={intendedUse} onChange={(event) => setIntendedUse(event.target.value as "decorative" | "prototype")}><option value="decorative">Peça decorativa</option><option value="prototype">Protótipo visual</option></select></label><label>Medida conferida<select value={reviewAxis} onChange={(event) => setReviewAxis(event.target.value as "x" | "y" | "z")}><option value="x">Largura (X){dimensions ? ` — ${dimensions.x} mm` : ""}</option><option value="y">Profundidade (Y){dimensions ? ` — ${dimensions.y} mm` : ""}</option><option value="z">Altura (Z){dimensions ? ` — ${dimensions.z} mm` : ""}</option></select></label><label>Medida do objeto em milímetros<input type="number" inputMode="decimal" min="0.1" max="2000" step="0.1" value={reviewDimension} onChange={(event) => setReviewDimension(event.target.value)} /></label><label><input type="checkbox" checked={shapeReviewed} onChange={(event) => setShapeReviewed(event.target.checked)} /> Comparei a forma e não vi partes faltando.</label><label><input type="checkbox" checked={limitationsAccepted} onChange={(event) => setLimitationsAccepted(event.target.checked)} /> Entendo que o Printora não garante encaixe, rosca ou tolerância mecânica.</label><div className="reconstruction-actions"><button type="button" className="primary-button" disabled={busy || !shapeReviewed || !limitationsAccepted || !reviewDimension} onClick={() => void review("approve")}>Aprovar para fatiamento</button><button type="button" className="secondary-button" disabled={busy} onClick={() => void review("reject")}>Rejeitar esta versão</button></div></div> : null}
    {latestReview?.decision === "approved_for_slicing" ? <div className="mesh-repair-export" role="status"><ShieldCheck size={18} /><div><strong>Modelo adicionado ao projeto</strong><p>Ele está aprovado somente para seguir ao fatiamento. A escolha da impressora, do material e o preflight continuam obrigatórios.</p><button type="button" className="primary-button" onClick={() => document.getElementById("project-slicing")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Continuar para o fatiamento</button></div></div> : null}
    {latestReview?.decision === "rejected" ? <div className="mesh-repair-export" role="status"><CircleAlert size={18} /><div><strong>Versão rejeitada</strong><p>A malha bruta e as versões anteriores continuam preservadas. Faça outra correção ou gere uma nova reconstrução.</p></div></div> : null}
    {revisions.some((revision) => revision.status === "succeeded") ? <details className="mesh-repair-history"><summary>O que foi reparado?</summary><ol>{revisions.filter((revision) => revision.status === "succeeded").map((revision) => <li key={revision.id}>Versão {revision.id}: {operationLabels[revision.operation]}. O resultado foi salvo separadamente com checksum {revision.sha256?.slice(0, 12)}.</li>)}</ol></details> : null}
    {latest ? <div className="mesh-repair-history"><p><strong>Última versão:</strong> {latest.output_format?.toUpperCase()} — {latest.next_action}</p><button type="button" className="secondary-button" disabled={busy} onClick={() => void download()}><Download size={16} /> Baixar última versão</button></div> : null}
    <p className="photo-capture-note"><CircleAlert size={16} /> Uma correção automática não significa que a peça foi aprovada para impressão.</p>
  </div>;
}
